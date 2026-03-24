"""Detecção de anomalias em agregados mensais por categoria com Isolation Forest."""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder

# Poucos pontos: IF fica instável; alinhar com necessidade de histórico em z-score
MIN_MONTHLY_ROWS = 10

_SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1}


def compute_isolation_monthly_category_anomalies(monthly_category: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    `monthly_category` com colunas: category, month (string período YYYY-MM), amount (soma do mês).
    Retorna lista de dicts compatíveis com SpendingAnomaly (exceto detector, preenchido no serviço).
    """
    if monthly_category.empty or len(monthly_category) < MIN_MONTHLY_ROWS:
        return []

    df = monthly_category.copy()
    df["amount"] = df["amount"].astype(float)
    try:
        df["_period"] = pd.PeriodIndex(df["month"].astype(str), freq="M")
    except (ValueError, TypeError):
        return []

    df["_m"] = df["_period"].map(lambda p: float(p.month))
    df["_log"] = np.log1p(df["amount"].clip(lower=0.0))
    le = LabelEncoder()
    df["_cat"] = le.fit_transform(df["category"].astype(str)).astype(float)
    df["_m_sin"] = np.sin(2 * np.pi * df["_m"] / 12.0)
    df["_m_cos"] = np.cos(2 * np.pi * df["_m"] / 12.0)

    X = df[["_log", "_m_sin", "_m_cos", "_cat"]].values.astype(np.float64)
    n_samples = len(df)
    contamination = min(0.15, max(0.05, 3.0 / max(n_samples, 1)))

    iso = IsolationForest(
        random_state=42,
        contamination=contamination,
        n_estimators=min(200, max(50, n_samples * 4)),
        max_samples=min(256, max(2, n_samples)),
    )
    iso.fit(X)
    pred = iso.predict(X)
    scores = iso.decision_function(X)

    medians = df.groupby("category")["amount"].median()
    out: List[Dict[str, Any]] = []

    for idx in range(len(df)):
        if pred[idx] != -1:
            continue
        row = df.iloc[idx]
        cat = str(row["category"])
        month = str(row["month"])
        amount = float(row["amount"])
        med = float(medians.loc[cat]) if cat in medians.index else float(np.median(df.loc[df["category"] == cat, "amount"]))
        dev_pct = ((amount - med) / med * 100.0) if med > 0 else 0.0
        sc = float(scores[idx])

        if sc < -0.12:
            severity = "high"
        elif sc < -0.02:
            severity = "medium"
        else:
            severity = "low"

        reason = (
            f"Isolation Forest: padrão atípico de gasto mensal em {cat} "
            f"(score {sc:.3f}; mediana da categoria no período R$ {med:.2f})."
        )
        out.append(
            {
                "category": cat,
                "month": month,
                "amount": round(amount, 2),
                "expected_amount": round(med, 2),
                "deviation_percent": round(dev_pct, 2),
                "z_score": 0.0,
                "severity": severity,
                "reason": reason,
                "isolation_score": round(sc, 4),
            }
        )

    out.sort(
        key=lambda r: (_SEVERITY_RANK.get(r["severity"], 0), abs(r["deviation_percent"])),
        reverse=True,
    )
    return out
