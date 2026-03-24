"""Consultas em linguagem natural -> plano JSON validado -> agregados seguros (sem SQL livre)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.services.analytics import AnalyticsService

ALLOWED_INTENTS = frozenset(
    {
        "total_expenses",
        "total_income",
        "net_balance",
        "expense_category_sum",
        "income_category_sum",
        "top_expense_categories",
        "unknown",
    }
)


class NLQueryPlan(BaseModel):
    months_back: int = Field(3, ge=1, le=36)
    intent: str = "unknown"
    category: Optional[str] = None

    @field_validator("intent", mode="before")
    @classmethod
    def _normalize_intent(cls, v: Any) -> str:
        if not isinstance(v, str):
            return "unknown"
        s = v.strip().lower().replace("-", "_")
        # aliases comuns
        aliases = {
            "total_despesas": "total_expenses",
            "despesas": "total_expenses",
            "total_receitas": "total_income",
            "receitas": "total_income",
            "saldo": "net_balance",
            "saldo_liquido": "net_balance",
        }
        s = aliases.get(s, s)
        return s if s in ALLOWED_INTENTS else "unknown"


class NLQueryResult(BaseModel):
    answer: str
    intent: str
    months_back: int
    value: Optional[float] = None
    model: str
    plan: NLQueryPlan


def _format_currency_br(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _distinct_categories_from_db(db: Session) -> Tuple[List[str], List[str]]:
    from app import models

    exp = (
        db.query(models.Transaction.category)
        .filter(models.Transaction.type == models.TransactionType.EXPENSE)
        .distinct()
        .all()
    )
    inc = (
        db.query(models.Transaction.category)
        .filter(models.Transaction.type == models.TransactionType.INCOME)
        .distinct()
        .all()
    )
    return sorted({str(r[0]) for r in exp if r[0]}), sorted({str(r[0]) for r in inc if r[0]})


def _parse_json_from_llm(content: str) -> Dict[str, Any]:
    """Parse JSON do LLM; tolera markdown ou texto extra."""
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError as e:
                raise ValueError("JSON invalido na resposta do modelo.") from e
        raise ValueError("JSON invalido na resposta do modelo.")


def _should_retry_without_response_format(status_code: int, response_text: str) -> bool:
    if status_code != 400:
        return False
    t = (response_text or "").lower()
    return "response_format" in t or "json_object" in t


def _match_category(hint: Optional[str], names: List[str]) -> Optional[str]:
    if not hint or not names:
        return None
    h = hint.strip().casefold()
    for n in names:
        if n.casefold() == h:
            return n
    for n in names:
        if h in n.casefold() or n.casefold() in h:
            return n
    return None


def _call_openai_json(system: str, user: str) -> Tuple[dict, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY nao configurada no ambiente do servidor.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/chat/completions"
    timeout = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, headers=headers, json=payload)
        if r.status_code == 400 and "response_format" in payload:
            if _should_retry_without_response_format(r.status_code, r.text):
                payload.pop("response_format", None)
                r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not content:
        raise ValueError("Resposta JSON vazia do modelo.")
    used = str(data.get("model", model))
    return _parse_json_from_llm(content), used


def _parse_plan(raw: dict) -> NLQueryPlan:
    raw = dict(raw)
    if "months_back" not in raw:
        raw["months_back"] = 3
    return NLQueryPlan.model_validate(raw)


def llm_parse_question(db: Session, question: str) -> Tuple[NLQueryPlan, str]:
    exp_cats, inc_cats = _distinct_categories_from_db(db)
    system = (
        "Voce converte perguntas sobre financas pessoais em um UNICO objeto JSON. "
        "Campos obrigatorios: intent (string), months_back (inteiro 1-36), category (string ou null). "
        f"Valores permitidos para intent: {', '.join(sorted(ALLOWED_INTENTS))}. "
        "Use expense_category_sum ou income_category_sum quando a pergunta citar uma categoria especifica. "
        "Use top_expense_categories para 'onde gasto mais', 'maiores categorias', 'ranking de gastos'. "
        "Escolha category EXATAMENTE de uma das listas quando aplicavel (ou null).\n"
        f"Categorias de DESPESA conhecidas: {exp_cats}\n"
        f"Categorias de RECEITA conhecidas: {inc_cats}\n"
        "Se a pergunta nao for sobre numeros do app, intent=unknown."
    )
    user = f'Pergunta do usuario: """{question.strip()}"""\nResponda so o JSON.'
    raw, model = _call_openai_json(system, user)
    plan = _parse_plan(raw)
    return plan, model


def execute_plan(db: Session, plan: NLQueryPlan) -> Tuple[str, Optional[float]]:
    service = AnalyticsService(db)
    end = datetime.now()
    start = end - timedelta(days=30 * plan.months_back)
    summary = service.get_summary_statistics(start, end)

    if plan.intent == "unknown":
        return (
            "Nao consegui mapear sua pergunta. Exemplos: "
            "'Quanto gastei no total nos ultimos 3 meses?', "
            "'Quanto gastei com Alimentação?', "
            "'Quanto recebi?', "
            "'Quais minhas maiores categorias de gasto?'.",
            None,
        )

    if plan.intent == "total_expenses":
        v = float(summary.get("total_expense", 0))
        return (
            f"No periodo (aproximadamente {plan.months_back} meses), suas despesas de caixa totalizaram {_format_currency_br(v)}.",
            v,
        )

    if plan.intent == "total_income":
        v = float(summary.get("total_income", 0))
        return (
            f"No periodo (aproximadamente {plan.months_back} meses), suas receitas de caixa totalizaram {_format_currency_br(v)}.",
            v,
        )

    if plan.intent == "net_balance":
        v = float(summary.get("net_balance", 0))
        return (
            f"Saldo liquido (caixa menos faturas de cartao) no periodo: {_format_currency_br(v)}. "
            f"(Saldo de caixa antes de cartao: {_format_currency_br(float(summary.get('balance', 0)))}.)",
            v,
        )

    if plan.intent == "expense_category_sum":
        cats = service.analyze_expenses_by_category(start, end)
        names = [c.category for c in cats]
        name = _match_category(plan.category, names)
        if not name:
            return (
                f"Nao encontrei a categoria '{plan.category or ''}' nas despesas deste periodo. "
                f"Categorias disponiveis: {', '.join(names[:15])}{'...' if len(names) > 15 else ''}.",
                None,
            )
        for c in cats:
            if c.category == name:
                return (
                    f"Gasto em **{name}**: {_format_currency_br(c.total)} "
                    f"({c.percentage}% das suas despesas no periodo).",
                    float(c.total),
                )
        return ("Categoria nao encontrada.", None)

    if plan.intent == "income_category_sum":
        cats = service.analyze_income_by_category(start, end)
        names = [c.category for c in cats]
        name = _match_category(plan.category, names)
        if not name:
            return (
                f"Nao encontrei a categoria '{plan.category or ''}' nas receitas deste periodo. "
                f"Categorias disponiveis: {', '.join(names[:15])}{'...' if len(names) > 15 else ''}.",
                None,
            )
        for c in cats:
            if c.category == name:
                return (
                    f"Receita em **{name}**: {_format_currency_br(c.total)} "
                    f"({c.percentage}% das suas receitas no periodo).",
                    float(c.total),
                )
        return ("Categoria nao encontrada.", None)

    if plan.intent == "top_expense_categories":
        cats = service.analyze_expenses_by_category(start, end)[:8]
        if not cats:
            return ("Nao ha despesas registradas no periodo.", None)
        lines = [f"{i + 1}. {c.category}: {_format_currency_br(c.total)} ({c.percentage}%)" for i, c in enumerate(cats)]
        total_e = float(summary.get("total_expense", 0))
        return (
            f"Maiores categorias de despesa (aprox. {plan.months_back} meses, total despesas {_format_currency_br(total_e)}):\n"
            + "\n".join(lines),
            total_e,
        )

    return ("Intent nao implementado.", None)


def run_nl_query(
    db: Session,
    question: str,
    months_back_override: Optional[int] = None,
) -> NLQueryResult:
    if not question.strip():
        raise ValueError("Pergunta vazia.")
    plan, model = llm_parse_question(db, question)
    if months_back_override is not None:
        plan = plan.model_copy(update={"months_back": months_back_override})
    answer, value = execute_plan(db, plan)
    return NLQueryResult(
        answer=answer.replace("**", ""),
        intent=plan.intent,
        months_back=plan.months_back,
        value=value,
        model=model,
        plan=plan,
    )
