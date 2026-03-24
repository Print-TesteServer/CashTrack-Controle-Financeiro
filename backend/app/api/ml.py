from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import require_training_endpoint_allowed
from app.database import get_db
from app.ml.category_classifier import CategoryPrediction, load_meta, predict_category, train_and_persist
from app.schemas import (
    CategoryModelInfo,
    CategoryPredictRequest,
    CategoryPredictResponse,
    CategoryScore,
    CategoryTrainResponse,
)

router = APIRouter()


def _to_response(pred: CategoryPrediction) -> CategoryPredictResponse:
    return CategoryPredictResponse(
        predicted_category=pred.predicted_category,
        confidence=pred.confidence,
        top_categories=[CategoryScore(category=c, probability=p) for c, p in pred.top_categories],
        model_trained=pred.model_trained,
        message=pred.message,
    )


@router.post("/predict-category", response_model=CategoryPredictResponse)
def post_predict_category(body: CategoryPredictRequest) -> CategoryPredictResponse:
    return _to_response(predict_category(body.description))


@router.post("/train-category-classifier", response_model=CategoryTrainResponse)
def post_train_category_classifier(
    db: Session = Depends(get_db),
    _training_ok: bool = Depends(require_training_endpoint_allowed),
) -> CategoryTrainResponse:
    try:
        meta = train_and_persist(db)
        return CategoryTrainResponse(**meta)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/category-model", response_model=CategoryModelInfo)
def get_category_model_info() -> CategoryModelInfo:
    meta = load_meta()
    if not meta:
        return CategoryModelInfo(trained=False)
    return CategoryModelInfo(trained=True, **meta)
