import unittest

from app.constants import is_cashflow_excluded_category


class CashflowConstantsTests(unittest.TestCase):
    def test_cofrinho_case_insensitive(self):
        self.assertTrue(is_cashflow_excluded_category("Cofrinho"))
        self.assertTrue(is_cashflow_excluded_category("COFRINHO"))
        self.assertTrue(is_cashflow_excluded_category("  cofrinho  "))

    def test_other_categories_not_excluded(self):
        self.assertFalse(is_cashflow_excluded_category("Alimentação"))
        self.assertFalse(is_cashflow_excluded_category(""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
