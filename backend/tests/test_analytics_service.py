import unittest
from datetime import datetime
from unittest.mock import patch

import pandas as pd

from app.schemas import CategoryAnalysis
from app.services.analytics import AnalyticsService


class AnalyticsServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AnalyticsService(db=None)

    @staticmethod
    def _build_monthly_rows(category: str, base_amount: float, spike_amount: float, periods: int = 6) -> list[dict]:
        dates = pd.date_range(end=datetime.now(), periods=periods, freq="MS")
        rows: list[dict] = []
        for i, date in enumerate(dates):
            rows.append(
                {
                    "id": f"{category}-{i}",
                    "type": "expense",
                    "category": category,
                    "amount": spike_amount if i == len(dates) - 1 else base_amount,
                    "date": date.to_pydatetime(),
                    "payment_method": "cash",
                }
            )
        return rows

    def test_spending_anomaly_reason_uses_correct_direction(self):
        """Deve descrever queda de gasto com 'abaixo da média'."""
        rows = self._build_monthly_rows(category="Transporte", base_amount=200.0, spike_amount=10.0)

        with patch.object(self.service, "get_transactions_dataframe", return_value=pd.DataFrame(rows)):
            anomalies = self.service.get_spending_anomalies(window_months=6, z_threshold=2.0)

        self.assertTrue(anomalies)
        self.assertIn("abaixo da média", anomalies[0].reason)

    def test_spending_anomalies_are_sorted_by_severity_then_deviation(self):
        """Deve priorizar severidade alta antes da média no ranking final."""
        rows = []
        rows.extend(self._build_monthly_rows(category="Alimentação", base_amount=100.0, spike_amount=220.0))
        rows.extend(self._build_monthly_rows(category="Lazer", base_amount=100.0, spike_amount=180.0))

        with patch.object(self.service, "get_transactions_dataframe", return_value=pd.DataFrame(rows)):
            anomalies = self.service.get_spending_anomalies(window_months=6, z_threshold=2.0)

        self.assertGreaterEqual(len(anomalies), 2)
        self.assertEqual(anomalies[0].severity, "high")
        self.assertEqual(anomalies[0].category, "Alimentação")

    def test_spending_anomaly_detects_strong_negative_deviation_by_percentage(self):
        """Deve detectar queda forte de gasto mesmo com z-threshold alto."""
        rows = self._build_monthly_rows(category="Transporte", base_amount=100.0, spike_amount=20.0)

        with patch.object(self.service, "get_transactions_dataframe", return_value=pd.DataFrame(rows)):
            anomalies = self.service.get_spending_anomalies(window_months=6, z_threshold=10.0)

        self.assertTrue(anomalies)
        self.assertEqual(anomalies[0].severity, "high")
        self.assertLess(anomalies[0].deviation_percent, 0)

    def test_break_even_uses_ceil_for_months_until_zero(self):
        """Deve arredondar para cima o tempo até saldo zero quando houver fração de mês."""
        rows = []
        dates = pd.date_range(end=datetime.now(), periods=12, freq="MS")
        for i, date in enumerate(dates):
            rows.append(
                {
                    "id": f"income-{i}",
                    "type": "income",
                    "category": "Salário",
                    "amount": 100.0,
                    "date": date.to_pydatetime(),
                    "payment_method": "cash",
                }
            )
            if i == len(dates) - 1:
                rows.append(
                    {
                        "id": f"expense-{i}",
                        "type": "expense",
                        "category": "Casa",
                        "amount": 500.0,
                        "date": date.to_pydatetime(),
                        "payment_method": "cash",
                    }
                )

        with patch.object(self.service, "get_transactions_dataframe", return_value=pd.DataFrame(rows)):
            analysis = self.service.get_break_even_analysis()

        self.assertEqual(analysis.current_balance, 700.0)
        self.assertEqual(analysis.monthly_net, -400.0)
        self.assertEqual(analysis.months_until_break_even, 2)

    def test_recommendations_respect_lookback_months(self):
        """Deve propagar lookback para summary/categories/anomalias."""
        captured = {"summary": None, "categories": None, "window_months": None}

        def fake_summary(start_date, end_date):
            captured["summary"] = (start_date, end_date)
            return {"total_income": 1000.0, "total_expense": 900.0, "net_balance": 100.0}

        def fake_categories(start_date, end_date):
            captured["categories"] = (start_date, end_date)
            return [
                CategoryAnalysis(category="Lazer", total=500.0, count=5, percentage=55.0),
            ]

        def fake_anomalies(window_months=6, z_threshold=2.0, method="zscore", **_kwargs):
            captured["window_months"] = window_months
            return []

        with patch.object(self.service, "get_summary_statistics", side_effect=fake_summary), patch.object(
            self.service, "analyze_expenses_by_category", side_effect=fake_categories
        ), patch.object(self.service, "get_spending_anomalies", side_effect=fake_anomalies):
            recs = self.service.get_recommendations(lookback_months=6)

        self.assertTrue(recs)
        self.assertIsNotNone(captured["summary"])
        self.assertIsNotNone(captured["categories"])
        self.assertEqual(captured["window_months"], 6)

    def test_recommendations_fallback_when_no_signals(self):
        """Deve retornar recomendação padrão quando não há sinais de risco."""
        with patch.object(
            self.service,
            "get_summary_statistics",
            return_value={"total_income": 1000.0, "total_expense": 500.0, "net_balance": 500.0},
        ), patch.object(
            self.service,
            "analyze_expenses_by_category",
            return_value=[CategoryAnalysis(category="Casa", total=200.0, count=3, percentage=20.0)],
        ), patch.object(self.service, "get_spending_anomalies", return_value=[]):
            recs = self.service.get_recommendations(lookback_months=12)

        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].title, "Orçamento estável")


if __name__ == "__main__":
    unittest.main(verbosity=2)
