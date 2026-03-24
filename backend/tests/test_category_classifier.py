import unittest

import pandas as pd

from app.ml.category_classifier import (
    _prediction_from_pipeline,
    train_from_dataframe,
)


class CategoryClassifierTests(unittest.TestCase):
    def test_train_from_dataframe_learns_simple_pattern(self):
        rows = []
        for _ in range(10):
            rows.append({"description": "mercado alimentacao compra comida", "category": "Alimentação"})
        for _ in range(10):
            rows.append({"description": "uber taxi transporte onibus", "category": "Transporte"})
        for _ in range(10):
            rows.append({"description": "cinema lazer show ingresso", "category": "Lazer"})
        df = pd.DataFrame(rows)
        pipeline, meta = train_from_dataframe(df)
        self.assertGreaterEqual(meta["n_samples"], 15)
        self.assertEqual(meta["n_classes"], 3)
        self.assertGreater(meta["accuracy"], 0.0)

        p = _prediction_from_pipeline(pipeline, "uber taxi para o centro")
        self.assertEqual(p.predicted_category, "Transporte")
        self.assertGreater(p.confidence, 0.2)

    def test_train_raises_when_too_few_rows(self):
        df = pd.DataFrame(
            {
                "description": ["a", "b"],
                "category": ["X", "Y"],
            }
        )
        with self.assertRaises(ValueError):
            train_from_dataframe(df)


if __name__ == "__main__":
    unittest.main(verbosity=2)
