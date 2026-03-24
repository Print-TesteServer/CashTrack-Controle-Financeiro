from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session

from app import models

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
PIPELINE_PATH = ARTIFACT_DIR / "category_pipeline.joblib"
META_PATH = ARTIFACT_DIR / "category_pipeline.meta.json"

MIN_SAMPLES_TOTAL = 15
MIN_SAMPLES_PER_CLASS = 2


def _normalize_text(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def training_dataframe_from_db(db: Session) -> pd.DataFrame:
    txs = db.query(models.Transaction).filter(models.Transaction.type == models.TransactionType.EXPENSE).all()
    rows: List[Tuple[str, str]] = []
    for t in txs:
        desc = _normalize_text(t.description or "")
        if len(desc) < 2:
            continue
        cat = (t.category or "").strip()
        if not cat:
            continue
        rows.append((desc, cat))
    return pd.DataFrame(rows, columns=["description", "category"])


def _filter_rare_classes(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["category"].value_counts()
    keep = counts[counts >= MIN_SAMPLES_PER_CLASS].index
    return df[df["category"].isin(keep)].reset_index(drop=True)


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95,
                    max_features=8000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=400,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=None,
                ),
            ),
        ]
    )


def train_from_dataframe(df: pd.DataFrame) -> Tuple[Pipeline, Dict[str, Any]]:
    df = df.dropna(subset=["description", "category"])
    df = df[df["description"].str.len() >= 2]
    df = _filter_rare_classes(df)
    if len(df) < MIN_SAMPLES_TOTAL:
        raise ValueError(
            f"Dados insuficientes: precisa de pelo menos {MIN_SAMPLES_TOTAL} transacoes de despesa "
            f"com descricao e categorias com pelo menos {MIN_SAMPLES_PER_CLASS} exemplos cada."
        )
    n_classes = df["category"].nunique()
    if n_classes < 2:
        raise ValueError("E preciso pelo menos 2 categorias distintas com amostras suficientes.")

    X = df["description"].values
    y = df["category"].values
    strat = y if len(np.unique(y)) > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=strat
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    meta: Dict[str, Any] = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_samples": int(len(df)),
        "n_classes": int(n_classes),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
    }
    return pipeline, meta


def save_artifacts(pipeline: Pipeline, meta: Dict[str, Any]) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, PIPELINE_PATH)
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_pipeline() -> Optional[Pipeline]:
    if not PIPELINE_PATH.exists():
        return None
    return joblib.load(PIPELINE_PATH)


def load_meta() -> Optional[Dict[str, Any]]:
    if not META_PATH.exists():
        return None
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def train_and_persist(db: Session) -> Dict[str, Any]:
    df = training_dataframe_from_db(db)
    pipeline, meta = train_from_dataframe(df)
    save_artifacts(pipeline, meta)
    return meta


@dataclass
class CategoryPrediction:
    predicted_category: Optional[str]
    confidence: float
    top_categories: List[Tuple[str, float]]
    model_trained: bool
    message: Optional[str] = None


def _prediction_from_pipeline(pipeline: Pipeline, description: str) -> CategoryPrediction:
    text = _normalize_text(description)
    if len(text) < 2:
        return CategoryPrediction(
            predicted_category=None,
            confidence=0.0,
            top_categories=[],
            model_trained=True,
            message="Descricao muito curta; informe pelo menos 2 caracteres.",
        )
    proba = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    order = np.argsort(proba)[::-1][:8]
    top = [(str(classes[i]), float(proba[i])) for i in order]
    best_idx = int(order[0])
    return CategoryPrediction(
        predicted_category=str(classes[best_idx]),
        confidence=float(proba[best_idx]),
        top_categories=top,
        model_trained=True,
        message=None,
    )


def predict_category(description: str) -> CategoryPrediction:
    text = _normalize_text(description)
    if len(text) < 2:
        return CategoryPrediction(
            predicted_category=None,
            confidence=0.0,
            top_categories=[],
            model_trained=PIPELINE_PATH.exists(),
            message="Descricao muito curta; informe pelo menos 2 caracteres.",
        )
    pipeline = load_pipeline()
    if pipeline is None:
        return CategoryPrediction(
            predicted_category=None,
            confidence=0.0,
            top_categories=[],
            model_trained=False,
            message="Modelo nao treinado. Execute o treinamento (POST /api/ml/train-category-classifier ou script).",
        )
    return _prediction_from_pipeline(pipeline, description)
