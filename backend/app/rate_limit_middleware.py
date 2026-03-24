"""Rate limit simples em memoria para rotas sensíveis (ex.: /api/ai/*)."""

import os
import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

_lock = Lock()
_timestamps: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _prune_and_check(ip: str, max_requests: int, window_sec: float) -> bool:
    now = time.monotonic()
    with _lock:
        bucket = _timestamps[ip]
        cutoff = now - window_sec
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= max_requests:
            return False
        bucket.append(now)
        return True


class AIRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Limita requisicoes por IP para prefixo /api/ai (LLM).
    Variaveis: AI_RATE_LIMIT_PER_MINUTE (padrao 40), AI_RATE_LIMIT_ENABLED (padrao true).
    """

    def __init__(self, app, path_prefix: str = "/api/ai"):
        super().__init__(app)
        self.path_prefix = path_prefix

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        if not path.startswith(self.path_prefix):
            return await call_next(request)
        if os.getenv("AI_RATE_LIMIT_ENABLED", "true").strip().lower() in ("0", "false", "no"):
            return await call_next(request)
        try:
            per_min = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "40"))
        except ValueError:
            per_min = 40
        per_min = max(5, min(per_min, 500))
        ip = _client_ip(request)
        if not _prune_and_check(ip, per_min, 60.0):
            return JSONResponse(
                {"detail": "Muitas requisicoes de IA. Aguarde um minuto e tente novamente."},
                status_code=429,
            )
        return await call_next(request)
