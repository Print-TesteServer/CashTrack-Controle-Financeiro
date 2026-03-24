"""Testes para dependencias FastAPI (ex.: treino ML)."""

import pytest
from fastapi import HTTPException

from app.deps import require_training_endpoint_allowed


def test_training_allowed_when_flag_true_without_api_key(monkeypatch):
    monkeypatch.setenv("ALLOW_TRAINING_WITHOUT_API_KEY", "true")
    monkeypatch.delenv("API_KEY", raising=False)
    assert require_training_endpoint_allowed() is True


def test_training_allowed_when_api_key_set_even_if_flag_false(monkeypatch):
    monkeypatch.setenv("ALLOW_TRAINING_WITHOUT_API_KEY", "false")
    monkeypatch.setenv("API_KEY", "secret")
    assert require_training_endpoint_allowed() is True


def test_training_blocked_when_flag_false_and_no_api_key(monkeypatch):
    monkeypatch.setenv("ALLOW_TRAINING_WITHOUT_API_KEY", "false")
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        require_training_endpoint_allowed()
    assert exc.value.status_code == 503
    assert "Treinamento" in (exc.value.detail or "")
