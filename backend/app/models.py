from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CREDIT = "credit"
    DEBIT = "debit"
    PIX = "pix"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, index=True)
    type = Column(SQLEnum(TransactionType), nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.CASH)
    credit_card_id = Column(String, nullable=True)  # ID do cartão usado (se payment_method == credit)
    created_at = Column(DateTime, server_default=func.now())

class CreditCard(Base):
    __tablename__ = "credit_cards"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    limit = Column(Float, nullable=False)
    current_balance = Column(Float, default=0.0)
    due_date = Column(Integer, nullable=False)  # dia do mês
    closing_date = Column(Integer, nullable=False)  # dia do mês
    created_at = Column(DateTime, server_default=func.now())

class Savings(Base):
    __tablename__ = "savings"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    current_amount = Column(Float, default=0.0)
    goal_amount = Column(Float, nullable=False)
    description = Column(String)
    institution = Column(String, nullable=True)  # Inter, Itaú, Rico, etc.
    cdi_percentage = Column(Float, nullable=True)  # % do CDI (ex: 114.12 = 114.12% do CDI)
    last_yield_calculation = Column(DateTime, nullable=True)  # Última atualização de rendimento
    created_at = Column(DateTime, server_default=func.now())


