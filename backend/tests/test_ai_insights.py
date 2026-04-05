import os
import unittest
from unittest.mock import patch

from app.services.ai_insights import call_llm_chat


class AIInsightsTests(unittest.TestCase):
    def test_call_llm_raises_without_api_key(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                call_llm_chat("sys", "user")

    def test_call_llm_parses_gemini_response(self):
        fake_json = {
            "modelVersion": "gemini-2.0-flash",
            "candidates": [{"content": {"parts": [{"text": "Resposta de teste."}]}}],
        }

        class FakeResp:
            def raise_for_status(self):
                return None

            def json(self):
                return fake_json

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False):
            with patch("app.services.gemini_llm.httpx.Client") as mock_client:
                mock_client.return_value.__enter__.return_value.post.return_value = FakeResp()
                text, model = call_llm_chat("s", "u")
                self.assertEqual(text, "Resposta de teste.")
                self.assertEqual(model, "gemini-2.0-flash")


if __name__ == "__main__":
    unittest.main(verbosity=2)
