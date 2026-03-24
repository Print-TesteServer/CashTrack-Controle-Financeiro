import unittest

import numpy as np

from app.ml.metrics import mean_absolute_error, root_mean_squared_error


class MlMetricsTests(unittest.TestCase):
    def test_mae_matches_numpy(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.0, 2.5])
        self.assertAlmostEqual(mean_absolute_error(y_true, y_pred), np.mean(np.abs(y_true - y_pred)))

    def test_rmse_matches_numpy(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([2.0, 2.0, 2.0])
        expected = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        self.assertAlmostEqual(root_mean_squared_error(y_true, y_pred), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
