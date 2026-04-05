"""Insights em linguagem natural a partir de agregados financeiros (sem enviar transações brutas)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.services.analytics import AnalyticsService
from app.services.gemini_llm import call_llm_chat


def _format_currency_br(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_finance_context_text(db: Session, lookback_months: int) -> str:
    """Monta texto só com totais e categorias (privacidade)."""
    service = AnalyticsService(db)
    end = datetime.now()
    start = end - timedelta(days=30 * max(lookback_months, 1))
    summary = service.get_summary_statistics(start, end)
    expenses = service.analyze_expenses_by_category(start, end)
    income_cats = service.analyze_income_by_category(start, end)

    lines: List[str] = []
    lines.append(f"Periodo analisado: aproximadamente {lookback_months} meses ate a data atual.")
    lines.append(
        f"Totais (caixa, sem cartao/cofrinhos no saldo): receitas {_format_currency_br(float(summary.get('total_income', 0)))}, "
        f"despesas {_format_currency_br(float(summary.get('total_expense', 0)))}, "
        f"saldo caixa {_format_currency_br(float(summary.get('balance', 0)))}."
    )
    lines.append(
        f"Medias mensais: receita {_format_currency_br(float(summary.get('avg_monthly_income', 0)))}, "
        f"despesa {_format_currency_br(float(summary.get('avg_monthly_expense', 0)))}."
    )
    lines.append(
        f"Cartoes (divida): {_format_currency_br(float(summary.get('total_credit_debt', 0)))}; "
        f"Cofrinhos: {_format_currency_br(float(summary.get('total_savings', 0)))}; "
        f"Saldo liquido (caixa - cartao): {_format_currency_br(float(summary.get('net_balance', 0)))}."
    )
    lines.append(f"Transacoes no periodo (filtradas): {summary.get('transaction_count', 0)}.")

    if expenses:
        lines.append("Top despesas por categoria:")
        for c in expenses[:8]:
            lines.append(f"  - {c.category}: {_format_currency_br(c.total)} ({c.percentage}% do total de despesas)")
    else:
        lines.append("Sem despesas registradas no periodo.")

    if income_cats:
        lines.append("Receitas por categoria (resumo):")
        for c in income_cats[:6]:
            lines.append(f"  - {c.category}: {_format_currency_br(c.total)}")

    try:
        fc = service.get_expense_forecast(1, min(6, lookback_months), min(24, lookback_months + 6))
        lines.append(
            f"Previsao de gasto (proximo mes alvo {fc.target_month}): {_format_currency_br(fc.predicted_amount)} "
            f"(modelo: {fc.model_used})."
        )
    except Exception:
        lines.append("Previsao de gasto: indisponivel no momento.")

    try:
        anom = service.get_spending_anomalies(lookback_months, 2.0, method="zscore")
        if anom:
            lines.append(f"Anomalias (z-score) detectadas: {len(anom)}. Exemplos:")
            for a in anom[:5]:
                lines.append(f"  - {a.category} ({a.month}): {a.reason}")
        else:
            lines.append("Nenhuma anomalia z-score forte no periodo.")
    except Exception:
        lines.append("Anomalias: indisponivel.")

    return "\n".join(lines)


def generate_finance_explanation(
    db: Session,
    lookback_months: int,
    user_question: Optional[str],
) -> Tuple[str, str, str]:
    """
    Retorna (resposta_llm, model_id, contexto_texto_para_debug).
    """
    context = build_finance_context_text(db, lookback_months)
    q = (user_question or "").strip()
    if not q:
        q = "Explique meu panorama financeiro neste periodo em portugues do Brasil, de forma clara e objetiva. Destaque riscos e uma acao pratica."

    system = (
        "Voce e um assistente financeiro. Use apenas os dados fornecidos no contexto. "
        "Nao invente valores. Se faltar dado, diga que nao ha informacao suficiente. "
        "Responda em portugues do Brasil, tom profissional e acessivel."
    )
    user = f"Contexto agregado (sem dados pessoais identificaveis alem de categorias):\n\n{context}\n\n---\nPergunta do usuario:\n{q}"
    answer, model = call_llm_chat(system, user)
    return answer, model, context
