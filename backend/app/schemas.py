from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal, List, Tuple
from app.models import TransactionType, PaymentMethod

# Transaction Schemas
class TransactionBase(BaseModel):
    type: TransactionType
    category: str
    amount: float
    description: Optional[str] = None
    date: datetime
    payment_method: PaymentMethod = PaymentMethod.CASH
    credit_card_id: Optional[str] = None  # ID do cartão usado (se payment_method == credit)

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Credit Card Schemas
class CreditCardBase(BaseModel):
    name: str
    limit: float
    due_date: int
    closing_date: int

class CreditCardCreate(CreditCardBase):
    pass

class CreditCardResponse(CreditCardBase):
    id: str
    current_balance: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Savings Schemas
class SavingsBase(BaseModel):
    name: str
    goal_amount: float
    description: Optional[str] = None
    institution: Optional[str] = None  # Inter, Itaú, Rico, etc.
    cdi_percentage: Optional[float] = None  # % do CDI (ex: 114.12 = 114.12% do CDI)

class SavingsCreate(SavingsBase):
    pass

class SavingsUpdate(BaseModel):
    current_amount: Optional[float] = None
    goal_amount: Optional[float] = None
    description: Optional[str] = None
    institution: Optional[str] = None
    cdi_percentage: Optional[float] = None

class SavingsResponse(SavingsBase):
    id: str
    current_amount: float
    last_yield_calculation: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Analytics Schemas
class CategoryAnalysis(BaseModel):
    category: str
    total: float
    count: int
    percentage: float

class MonthlyAnalysis(BaseModel):
    month: str
    income: float
    expense: float
    balance: float

class ChartData(BaseModel):
    labels: list[str]
    values: list[float]
    colors: Optional[list[str]] = None

# Advanced Analytics Schemas
class CashFlowProjection(BaseModel):
    month: str
    projected_income: float
    projected_expense: float
    projected_balance: float
    is_critical: bool  # Se saldo projetado é negativo

class BalanceAlert(BaseModel):
    current_balance: float
    min_balance_threshold: Optional[float] = None
    days_until_zero: Optional[int] = None
    suggested_deposit: Optional[float] = None
    alert_level: str  # "safe", "warning", "critical"
    message: str

class BreakEvenAnalysis(BaseModel):
    monthly_income_avg: float
    monthly_expense_avg: float
    current_balance: float
    monthly_net: float  # Receita - Despesa mensal
    months_until_break_even: Optional[int] = None
    break_even_date: Optional[str] = None
    is_sustainable: bool  # Se receitas > despesas
    message: str


class ForecastModelScore(BaseModel):
    model: str
    mae: float
    rmse: float


class ExpenseForecast(BaseModel):
    predicted_amount: float
    confidence_low: float
    confidence_high: float
    model_used: Literal[
        "moving_average_fallback",
        "moving_average",
        "linear_trend",
        "arima",
        "insufficient_data",
    ]
    history_months: int
    target_month: str
    evaluation_mae: Optional[float] = None
    evaluation_rmse: Optional[float] = None
    holdout_months: Optional[int] = None
    model_comparison: Optional[List[ForecastModelScore]] = None
    arima_order: Optional[Tuple[int, int, int]] = None


class SpendingAnomaly(BaseModel):
    category: str
    month: str
    amount: float
    expected_amount: float
    deviation_percent: float
    z_score: float
    severity: Literal["low", "medium", "high"]
    reason: str
    detector: Literal["zscore", "isolation_forest", "both"] = "zscore"
    isolation_score: Optional[float] = None


class Recommendation(BaseModel):
    title: str
    reason: str
    action: str
    estimated_impact: float
    priority: Literal["low", "medium", "high"]
    confidence: float


class CategoryScore(BaseModel):
    category: str
    probability: float


class CategoryPredictRequest(BaseModel):
    description: str


class CategoryPredictResponse(BaseModel):
    predicted_category: Optional[str] = None
    confidence: float = 0.0
    top_categories: List[CategoryScore] = []
    model_trained: bool = False
    message: Optional[str] = None


class CategoryTrainResponse(BaseModel):
    trained_at: str
    n_samples: int
    n_classes: int
    accuracy: float
    macro_f1: float


class CategoryModelInfo(BaseModel):
    trained: bool
    trained_at: Optional[str] = None
    n_samples: Optional[int] = None
    n_classes: Optional[int] = None
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None


class AIExplainRequest(BaseModel):
    """Pergunta opcional; o contexto e sempre agregado no servidor."""

    question: Optional[str] = None
    lookback_months: int = Field(6, ge=1, le=24)


class AIExplainResponse(BaseModel):
    answer: str
    model: str
    lookback_months: int


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    """Se informado, sobrescreve months_back inferido pelo modelo (alinha ao periodo da UI)."""

    months_back_override: Optional[int] = Field(None, ge=1, le=36)


class AIQueryResponse(BaseModel):
    answer: str
    intent: str
    months_back: int
    value: Optional[float] = None
    model: str


