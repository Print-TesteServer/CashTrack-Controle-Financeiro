import unittest
from unittest.mock import MagicMock, patch

from app.services.nl_query import (
    NLQueryPlan,
    _match_category,
    _parse_json_from_llm,
    _should_retry_without_response_format,
    execute_plan,
)


class NLQueryHelpersTests(unittest.TestCase):
    def test_parse_json_plain(self):
        d = _parse_json_from_llm('{"intent": "unknown", "months_back": 3, "category": null}')
        self.assertEqual(d["intent"], "unknown")
        self.assertEqual(d["months_back"], 3)

    def test_parse_json_with_extra_text(self):
        raw = 'Aqui esta o JSON: {"intent": "total_expenses", "months_back": 6, "category": null} fim.'
        d = _parse_json_from_llm(raw)
        self.assertEqual(d["intent"], "total_expenses")
        self.assertEqual(d["months_back"], 6)

    def test_should_retry_only_on_400_with_keywords(self):
        self.assertFalse(_should_retry_without_response_format(400, "bad request"))
        self.assertTrue(_should_retry_without_response_format(400, "response_format not supported"))
        self.assertTrue(_should_retry_without_response_format(400, "json_object"))
        self.assertFalse(_should_retry_without_response_format(500, "response_format"))

    def test_match_category_fuzzy(self):
        self.assertEqual(_match_category("alimentação", ["Alimentação", "X"]), "Alimentação")
        self.assertEqual(_match_category("Aliment", ["Alimentação"]), "Alimentação")
        self.assertIsNone(_match_category("zzz", ["A", "B"]))

    def test_plan_intent_alias(self):
        p = NLQueryPlan.model_validate({"months_back": 2, "intent": "total_despesas", "category": None})
        self.assertEqual(p.intent, "total_expenses")


class NLQueryExecuteTests(unittest.TestCase):
    def test_execute_plan_total_expenses_mocked(self):
        db = MagicMock()
        plan = NLQueryPlan(months_back=2, intent="total_expenses")

        with patch("app.services.nl_query.AnalyticsService") as msvc:
            inst = msvc.return_value
            inst.get_summary_statistics.return_value = {
                "total_expense": 1234.5,
                "total_income": 0.0,
                "balance": 0.0,
                "net_balance": 0.0,
            }
            text, val = execute_plan(db, plan)
            self.assertEqual(val, 1234.5)
            self.assertIn("totalizaram", text.casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
