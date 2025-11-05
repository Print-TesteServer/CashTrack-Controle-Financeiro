from pydantic import BaseModel
from datetime import datetime
from typing import Optional
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
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

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


