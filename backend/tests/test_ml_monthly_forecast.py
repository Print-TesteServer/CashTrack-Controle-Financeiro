import unittest

import numpy as np

from app.ml.monthly_forecast import select_and_predict_monthly_expenses


class MonthlyForecastTests(unittest.TestCase):
    def test_short_series_uses_in_sample_without_holdout(self):
        """Menos de 12 meses: sem holdout; retorna comparacao in-sample."""
        values = np.array([100.0, 110.0, 105.0, 108.0, 112.0, 109.0], dtype=float)
        result = select_and_predict_monthly_expenses(values, months_ahead=1)
        self.assertIsNone(result.holdout_months)
        self.assertIsNone(result.evaluation_mae)
        self.assertGreaterEqual(len(result.model_comparison), 2)
        self.assertIn(result.model_used, ("moving_average", "linear_trend"))

    def test_long_series_has_holdout_metrics(self):
        """12+ meses: holdout e metricas de avaliacao preenchidas."""
        rng = np.random.default_rng(42)
        base = np.linspace(800.0, 1200.0, 18)
        noise = rng.normal(0, 15.0, size=base.shape)
        values = np.maximum(50.0, base + noise)
        result = select_and_predict_monthly_expenses(values, months_ahead=1)
        self.assertIsNotNone(result.holdout_months)
        self.assertGreater(result.holdout_months or 0, 0)
        self.assertIsNotNone(result.evaluation_mae)
        self.assertIsNotNone(result.evaluation_rmse)
        self.assertGreater(len(result.model_comparison), 0)
        self.assertIn(
            result.model_used,
            ("moving_average", "linear_trend", "arima"),
        )

    def test_prediction_is_non_negative(self):
        values = np.ones(14, dtype=float) * 200.0
        result = select_and_predict_monthly_expenses(values, months_ahead=2)
        self.assertGreaterEqual(result.predicted_amount, 0.0)
        self.assertGreaterEqual(result.confidence_low, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
