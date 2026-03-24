"""Configuracao de testes: desabilita rate limit de IA por padrao."""

import os

os.environ.setdefault("AI_RATE_LIMIT_ENABLED", "false")
