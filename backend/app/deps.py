"""Dependencias FastAPI reutilizaveis (auth de treino, etc.)."""

import os

from fastapi import HTTPException


def require_training_endpoint_allowed() -> bool:
    """
    Treinar modelo no servidor pode ser restrito em producao.

    - Se ALLOW_TRAINING_WITHOUT_API_KEY for false (ou 0), exige API_KEY definida no ambiente
      (o cliente deve enviar X-API-Key; o middleware global ja valida quando API_KEY esta setada).
    - Desenvolvimento local: ALLOW_TRAINING_WITHOUT_API_KEY=true (padrao) permite treinar sem chave.
    """
    allow = os.getenv("ALLOW_TRAINING_WITHOUT_API_KEY", "true").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    has_api_key_env = bool(os.getenv("API_KEY", "").strip())
    if not allow and not has_api_key_env:
        raise HTTPException(
            status_code=503,
            detail=(
                "Treinamento do classificador esta desabilitado: defina API_KEY no servidor "
                "ou, para desenvolvimento local, ALLOW_TRAINING_WITHOUT_API_KEY=true."
            ),
        )
    return True
