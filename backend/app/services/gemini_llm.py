"""Chamadas à API Gemini (Google AI) via REST — usado por insights e consulta em linguagem natural."""

from __future__ import annotations

import os
from typing import Any, Dict, Tuple

import httpx

_DEFAULT_MODEL = "gemini-2.0-flash"
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _timeout_seconds() -> float:
    return float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60"))


def _extract_text(data: Dict[str, Any]) -> str:
    cands = data.get("candidates") or []
    if not cands:
        fb = data.get("promptFeedback")
        if fb:
            raise ValueError(f"Resposta bloqueada ou vazia do modelo: {fb}")
        raise ValueError("Resposta vazia do modelo (sem candidates).")
    parts = (cands[0].get("content") or {}).get("parts") or []
    chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    text = "".join(chunks).strip()
    if not text:
        raise ValueError("Resposta vazia do modelo (sem texto).")
    return text


def _model_label(data: Dict[str, Any], fallback: str) -> str:
    return str(data.get("modelVersion") or data.get("model") or fallback)


def gemini_generate(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float,
    max_output_tokens: int,
    json_mode: bool = False,
) -> Tuple[str, str]:
    """
    Chama `models.generateContent`.
    Retorna (texto, id do modelo reportado pela API ou o configurado).
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY nao configurada. Copie backend/.env.example para backend/.env, defina GEMINI_API_KEY "
            "(chave em https://aistudio.google.com/apikey), reinicie o servidor ou exporte a variavel no ambiente."
        )

    model = os.getenv("GEMINI_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL
    url = f"{_API_BASE}/models/{model}:generateContent"
    timeout = _timeout_seconds()

    generation_config: Dict[str, Any] = {
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
    }
    if json_mode:
        generation_config["responseMimeType"] = "application/json"

    body: Dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": generation_config,
    }

    headers = {"Content-Type": "application/json"}

    def _post(payload: Dict[str, Any]) -> httpx.Response:
        with httpx.Client(timeout=timeout) as client:
            return client.post(url, headers=headers, params={"key": api_key}, json=payload)

    r = _post(body)
    if json_mode and r.status_code == 400 and _should_retry_without_json_mime(r.text):
        body["generationConfig"] = {k: v for k, v in generation_config.items() if k != "responseMimeType"}
        r = _post(body)

    r.raise_for_status()
    data = r.json()
    return _extract_text(data), _model_label(data, model)


def _should_retry_without_json_mime(response_text: str) -> bool:
    """Alguns modelos/versões podem rejeitar responseMimeType application/json."""
    t = (response_text or "").lower()
    return "responsemimetype" in t or "response mime" in t or "json mime" in t


def should_retry_json_mime_error(status_code: int, response_text: str) -> bool:
    """Expõe a heurística de retry para testes."""
    if status_code != 400:
        return False
    return _should_retry_without_json_mime(response_text)


def call_llm_chat(system_prompt: str, user_prompt: str) -> Tuple[str, str]:
    """Insight financeiro em texto livre."""
    return gemini_generate(
        system_prompt,
        user_prompt,
        temperature=0.4,
        max_output_tokens=1200,
        json_mode=False,
    )
