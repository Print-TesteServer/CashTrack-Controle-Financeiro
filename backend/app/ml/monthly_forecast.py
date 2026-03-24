from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from statsmodels.tsa.arima.model import ARIMA

from app.ml.metrics import mean_absolute_error, root_mean_squared_error

# Small grid — monthly series are short; keep orders parsimonious
_ARIMA_ORDERS: List[Tuple[int, int, int]] = [
    (1, 1, 1),
    (0, 1, 1),
    (1, 1, 0),
    (2, 1, 0),
    (0, 1, 0),
    (1, 0, 0),
]

_MIN_LEN_FOR_HOLDOUT = 12
_MIN_TRAIN_FOR_ARIMA = 8


def _holdout_size(n: int) -> int:
    if n < _MIN_LEN_FOR_HOLDOUT:
        return 0
    return int(min(3, max(2, n // 6)))


def _predict_moving_average_level(values: np.ndarray, months_ahead: int) -> float:
    if len(values) >= 3:
        level = float(np.mean(values[-3:]))
    else:
        level = float(np.mean(values))
    return max(0.0, level)


def _predict_linear(values: np.ndarray, months_ahead: int) -> float:
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    x_future = len(values) + months_ahead - 1
    return max(0.0, float(slope * x_future + intercept))


def _holdout_preds_ma(train: np.ndarray, h: int) -> np.ndarray:
    level = float(np.mean(train[-3:])) if len(train) >= 3 else float(np.mean(train))
    return np.full(h, level, dtype=float)


def _holdout_preds_linear(train: np.ndarray, h: int) -> np.ndarray:
    x = np.arange(len(train), dtype=float)
    slope, intercept = np.polyfit(x, train, 1)
    out = np.empty(h, dtype=float)
    for i in range(h):
        x_f = len(train) + i
        out[i] = slope * x_f + intercept
    return out


def _fit_arima_forecast(train: np.ndarray, h: int, order: Tuple[int, int, int]) -> Optional[np.ndarray]:
    try:
        model = ARIMA(train, order=order)
        fitted = model.fit(method_kwargs={"warn_convergence": False})
        fc = fitted.forecast(steps=h)
        return np.asarray(fc, dtype=float).ravel()
    except Exception:
        return None


def _best_arima_holdout(train: np.ndarray, test: np.ndarray) -> Tuple[Optional[Tuple[int, int, int]], float, float]:
    h = len(test)
    best_order: Optional[Tuple[int, int, int]] = None
    best_mae = float("inf")
    best_rmse = float("inf")
    for order in _ARIMA_ORDERS:
        preds = _fit_arima_forecast(train, h, order)
        if preds is None or preds.shape[0] != h:
            continue
        mae = mean_absolute_error(test, preds)
        rmse = root_mean_squared_error(test, preds)
        if mae < best_mae:
            best_mae = mae
            best_rmse = rmse
            best_order = order
    if best_order is None:
        return None, float("inf"), float("inf")
    return best_order, best_mae, best_rmse


def _arima_predict_full(values: np.ndarray, months_ahead: int, order: Tuple[int, int, int]) -> float:
    model = ARIMA(values, order=order)
    fitted = model.fit(method_kwargs={"warn_convergence": False})
    fc = fitted.forecast(steps=months_ahead)
    pred = float(np.asarray(fc, dtype=float).ravel()[-1])
    return max(0.0, pred)


def _in_sample_scores_ma_linear(values: np.ndarray) -> Tuple[float, float, str]:
    """Returns (mae_ma, mae_linear, better_model) where better_model is moving_average or linear_trend."""
    x = np.arange(len(values), dtype=float)
    baseline = float(np.mean(values[-3:])) if len(values) >= 3 else float(np.mean(values))
    baseline_hist = np.full_like(values, baseline, dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    linear_hist = slope * x + intercept
    mae_ma = mean_absolute_error(values, baseline_hist)
    mae_li = mean_absolute_error(values, linear_hist)
    if mae_li < mae_ma:
        return mae_ma, mae_li, "linear_trend"
    return mae_ma, mae_li, "moving_average"


def _residual_std(values: np.ndarray, model_used: str, arima_order: Optional[Tuple[int, int, int]]) -> float:
    values = np.asarray(values, dtype=float)
    if model_used == "moving_average":
        baseline = float(np.mean(values[-3:])) if len(values) >= 3 else float(np.mean(values))
        fitted = np.full_like(values, baseline, dtype=float)
    elif model_used == "linear_trend":
        x = np.arange(len(values), dtype=float)
        slope, intercept = np.polyfit(x, values, 1)
        fitted = slope * x + intercept
    else:
        if arima_order is None:
            return float(np.std(values, ddof=0)) if len(values) > 1 else float(values[-1] * 0.15)
        try:
            model = ARIMA(values, order=arima_order)
            fitted_model = model.fit(method_kwargs={"warn_convergence": False})
            res = np.asarray(fitted_model.resid, dtype=float).ravel()
            res = res[np.isfinite(res)]
            if res.size > 1:
                return float(np.std(res, ddof=0))
            return float(np.std(values, ddof=0)) if len(values) > 1 else float(abs(float(values[-1])) * 0.15)
        except Exception:
            return float(np.std(values, ddof=0)) if len(values) > 1 else float(abs(float(values[-1])) * 0.15)

    residuals = values - fitted[: values.size]
    if len(residuals) > 1:
        return float(np.std(residuals, ddof=0))
    return float(abs(float(values[-1])) * 0.15)


@dataclass
class MonthlyForecastResult:
    predicted_amount: float
    confidence_low: float
    confidence_high: float
    model_used: str
    evaluation_mae: Optional[float]
    evaluation_rmse: Optional[float]
    holdout_months: Optional[int]
    model_comparison: List[Tuple[str, float, float]]
    arima_order: Optional[Tuple[int, int, int]] = None


def select_and_predict_monthly_expenses(values: np.ndarray, months_ahead: int) -> MonthlyForecastResult:
    """
    Select among moving average (last-3 level), linear trend, and ARIMA using holdout
    when enough history exists; otherwise in-sample MA vs linear only (no ARIMA).
    """
    values = np.asarray(values, dtype=float).ravel()
    n = len(values)
    comparison: List[Tuple[str, float, float]] = []
    h = _holdout_size(n)

    if h == 0 or n - h < _MIN_TRAIN_FOR_ARIMA:
        # Short history: same logic as original — pick MA vs linear by in-sample MAE
        _, _, better = _in_sample_scores_ma_linear(values)
        if better == "linear_trend":
            pred = _predict_linear(values, months_ahead)
            model_used = "linear_trend"
        else:
            pred = _predict_moving_average_level(values, months_ahead)
            model_used = "moving_average"

        mae_ma, mae_li, _ = _in_sample_scores_ma_linear(values)
        x = np.arange(n, dtype=float)
        baseline = float(np.mean(values[-3:])) if n >= 3 else float(np.mean(values))
        baseline_hist = np.full_like(values, baseline, dtype=float)
        slope, intercept = np.polyfit(x, values, 1)
        linear_hist = slope * x + intercept
        comparison.append(("moving_average", mae_ma, root_mean_squared_error(values, baseline_hist)))
        comparison.append(("linear_trend", mae_li, root_mean_squared_error(values, linear_hist)))

        rs = _residual_std(values, model_used, None)
        z = 1.96 * rs
        return MonthlyForecastResult(
            predicted_amount=round(pred, 2),
            confidence_low=round(max(0.0, pred - z), 2),
            confidence_high=round(max(0.0, pred + z), 2),
            model_used=model_used,
            evaluation_mae=None,
            evaluation_rmse=None,
            holdout_months=None,
            model_comparison=comparison,
            arima_order=None,
        )

    train = values[:-h]
    test = values[-h:]

    # Holdout predictions
    pred_ma = _holdout_preds_ma(train, h)
    pred_li = _holdout_preds_linear(train, h)
    mae_ma = mean_absolute_error(test, pred_ma)
    rmse_ma = root_mean_squared_error(test, pred_ma)
    mae_li = mean_absolute_error(test, pred_li)
    rmse_li = root_mean_squared_error(test, pred_li)
    comparison.append(("moving_average", mae_ma, rmse_ma))
    comparison.append(("linear_trend", mae_li, rmse_li))

    arima_order: Optional[Tuple[int, int, int]] = None
    mae_ar = float("inf")
    rmse_ar = float("inf")
    if len(train) >= _MIN_TRAIN_FOR_ARIMA:
        arima_order, mae_ar, rmse_ar = _best_arima_holdout(train, test)
        if arima_order is not None:
            comparison.append((f"arima{arima_order}", mae_ar, rmse_ar))

    # Pick winner
    candidates: List[Tuple[str, float]] = [
        ("moving_average", mae_ma),
        ("linear_trend", mae_li),
    ]
    if arima_order is not None:
        candidates.append(("arima", mae_ar))

    winner = min(candidates, key=lambda x: x[1])[0]

    eval_mae = mae_ma if winner == "moving_average" else (mae_li if winner == "linear_trend" else mae_ar)
    eval_rmse = rmse_ma if winner == "moving_average" else (rmse_li if winner == "linear_trend" else rmse_ar)

    if winner == "moving_average":
        pred = _predict_moving_average_level(values, months_ahead)
        model_used = "moving_average"
        arima_order = None
    elif winner == "linear_trend":
        pred = _predict_linear(values, months_ahead)
        model_used = "linear_trend"
        arima_order = None
    else:
        assert arima_order is not None
        try:
            pred = _arima_predict_full(values, months_ahead, arima_order)
            model_used = "arima"
        except Exception:
            pred = _predict_linear(values, months_ahead)
            model_used = "linear_trend"
            arima_order = None
            eval_mae = mae_li
            eval_rmse = rmse_li

    rs = _residual_std(values, model_used, arima_order if model_used == "arima" else None)
    z = 1.96 * rs

    return MonthlyForecastResult(
        predicted_amount=round(pred, 2),
        confidence_low=round(max(0.0, pred - z), 2),
        confidence_high=round(max(0.0, pred + z), 2),
        model_used=model_used,
        evaluation_mae=round(eval_mae, 4),
        evaluation_rmse=round(eval_rmse, 4),
        holdout_months=h,
        model_comparison=[(name, round(m, 4), round(r, 4)) for name, m, r in comparison],
        arima_order=arima_order if model_used == "arima" else None,
    )
