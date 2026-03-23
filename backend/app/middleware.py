"""Middlewares opcionais da API."""

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class OptionalAPIKeyMiddleware(BaseHTTPMiddleware):
    """
    Se a variável de ambiente API_KEY estiver definida (não vazia),
    exige o header X-API-Key nas rotas /api/*. Caso contrário, não aplica restrição.
    OPTIONS (CORS preflight) é sempre liberado.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        if not path.startswith("/api"):
            return await call_next(request)
        expected = os.getenv("API_KEY", "").strip()
        if not expected:
            return await call_next(request)
        if request.headers.get("x-api-key") != expected:
            return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
        return await call_next(request)
