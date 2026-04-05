from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import AIExplainRequest, AIExplainResponse, AIQueryRequest, AIQueryResponse
from app.services.ai_insights import generate_finance_explanation
from app.services.nl_query import run_nl_query

router = APIRouter()


@router.post("/explain", response_model=AIExplainResponse)
def post_explain_finances(body: AIExplainRequest, db: Session = Depends(get_db)) -> AIExplainResponse:
    """
    Gera explicacao em linguagem natural com base em totais e categorias.
    Requer `GEMINI_API_KEY` no servidor (Google AI / Gemini).
    """
    lb = max(1, min(24, body.lookback_months))
    try:
        answer, model, _ctx = generate_finance_explanation(db, lb, body.question)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao chamar o modelo: {e!s}") from e

    return AIExplainResponse(answer=answer, model=model, lookback_months=lb)


@router.post("/query", response_model=AIQueryResponse)
def post_nl_query(body: AIQueryRequest, db: Session = Depends(get_db)) -> AIQueryResponse:
    """
    Pergunta em linguagem natural -> JSON estruturado (LLM) -> agregados seguros.
    Nao executa SQL livre; apenas intents whitelisted.
    """
    try:
        result = run_nl_query(db, body.question, months_back_override=body.months_back_override)
    except ValueError as e:
        msg = str(e)
        code = 503 if "GEMINI_API_KEY" in msg else 400
        raise HTTPException(status_code=code, detail=msg) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao processar consulta: {e!s}") from e

    return AIQueryResponse(
        answer=result.answer,
        intent=result.intent,
        months_back=result.months_back,
        value=result.value,
        model=result.model,
    )
