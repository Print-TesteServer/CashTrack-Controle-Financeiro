import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class APIKeyMiddlewareTests(unittest.TestCase):
    def test_root_always_accessible(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_api_accessible_when_api_key_unset(self):
        with patch.dict(os.environ, {"API_KEY": ""}):
            response = client.get("/api/transactions/")
            self.assertEqual(response.status_code, 200)

    @patch.dict(os.environ, {"API_KEY": "secret-key"}, clear=False)
    def test_api_requires_header_when_api_key_set(self):
        response = client.get("/api/transactions/")
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.json())

    @patch.dict(os.environ, {"API_KEY": "secret-key"}, clear=False)
    def test_api_ok_with_valid_header(self):
        response = client.get("/api/transactions/", headers={"X-API-Key": "secret-key"})
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
