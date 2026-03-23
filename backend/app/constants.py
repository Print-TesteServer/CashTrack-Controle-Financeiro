"""Constantes de negócio compartilhadas (analytics, filtros de fluxo de caixa)."""

# Categorias equivalentes a "Cofrinho" para exclusão do fluxo de caixa (normalizado: strip + casefold).
EXCLUDED_CASHFLOW_CATEGORY_NORMALIZED = frozenset({"cofrinho"})


def is_cashflow_excluded_category(category: str | None) -> bool:
    """True se a categoria deve ser ignorada no saldo/analytics de caixa (ex.: reservas tipo cofrinho)."""
    return (category or "").strip().casefold() in EXCLUDED_CASHFLOW_CATEGORY_NORMALIZED
