import unittest
from datetime import datetime
from unittest.mock import patch

import pandas as pd

from app.ml.monthly_anomaly_isolation import compute_isolation_monthly_category_anomalies
from app.services.analytics import AnalyticsService


class MonthlyAnomalyIsolationTests(unittest.TestCase):
    def test_compute_finds_obvious_outlier_row(self):
        """Série longa com um ponto extremo deve ser sinalizado pelo IF."""
        months = pd.period_range("2024-01", periods=14, freq="M")
        rows = []
        for p in months:
            rows.append({"category": "Casa", "month": str(p), "amount": 500.0})
        rows.append({"category": "Casa", "month": "2025-03", "amount": 9000.0})
        for p in months:
            rows.append({"category": "Lazer", "month": str(p), "amount": 80.0})
        df = pd.DataFrame(rows)
        anomalies = compute_isolation_monthly_category_anomalies(df)
        self.assertTrue(anomalies)
        top = anomalies[0]
        self.assertGreater(top["amount"], 1000.0)
        self.assertIn("isolation_score", top)

    def test_service_isolation_method_returns_list(self):
        base = pd.date_range(end=datetime.now(), periods=8, freq="MS")
        rows = []
        for d in base:
            rows.append(
                {
                    "id": f"x-{d}",
                    "type": "expense",
                    "category": "Alimentação",
                    "amount": 300.0,
                    "date": d.to_pydatetime(),
                    "payment_method": "cash",
                }
            )
        for d in base:
            rows.append(
                {
                    "id": f"y-{d}",
                    "type": "expense",
                    "category": "Transporte",
                    "amount": 120.0,
                    "date": d.to_pydatetime(),
                    "payment_method": "cash",
                }
            )
        df = pd.DataFrame(rows)
        service = AnalyticsService(db=None)
        with patch.object(service, "get_transactions_dataframe", return_value=df):
            out = service.get_spending_anomalies(window_months=12, z_threshold=2.0, method="isolation_forest")
        self.assertIsInstance(out, list)
        for a in out:
            self.assertEqual(a.detector, "isolation_forest")


if __name__ == "__main__":
    unittest.main(verbosity=2)
