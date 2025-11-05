from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
import uuid

router = APIRouter()

@router.post("/", response_model=schemas.CreditCardResponse)
def create_credit_card(credit_card: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    db_card = models.CreditCard(
        id=str(uuid.uuid4()),
        **credit_card.dict(),
        current_balance=0.0
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

@router.get("/", response_model=List[schemas.CreditCardResponse])
def get_credit_cards(db: Session = Depends(get_db)):
    return db.query(models.CreditCard).all()

@router.get("/{card_id}", response_model=schemas.CreditCardResponse)
def get_credit_card(card_id: str, db: Session = Depends(get_db)):
    card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    return card

@router.put("/{card_id}", response_model=schemas.CreditCardResponse)
def update_credit_card(
    card_id: str,
    credit_card: schemas.CreditCardCreate,
    db: Session = Depends(get_db)
):
    db_card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    for key, value in credit_card.dict().items():
        setattr(db_card, key, value)
    
    db.commit()
    db.refresh(db_card)
    return db_card

@router.delete("/{card_id}")
def delete_credit_card(card_id: str, db: Session = Depends(get_db)):
    db_card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    db.delete(db_card)
    db.commit()
    return {"message": "Credit card deleted successfully"}

@router.post("/{card_id}/pay", response_model=schemas.CreditCardResponse)
def pay_credit_card_bill(
    card_id: str,
    amount: float = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Registra pagamento da fatura do cartão"""
    db_card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    # Reduz o saldo do cartão (pagamento reduz a fatura)
    db_card.current_balance = max(0, db_card.current_balance - amount)
    
    db.commit()
    db.refresh(db_card)
    return db_card

@router.post("/{card_id}/recalculate", response_model=schemas.CreditCardResponse)
def recalculate_credit_card_balance(
    card_id: str,
    db: Session = Depends(get_db)
):
    """Recalcula o saldo do cartão baseado em todas as transações"""
    db_card = db.query(models.CreditCard).filter(models.CreditCard.id == card_id).first()
    if not db_card:
        raise HTTPException(status_code=404, detail="Credit card not found")
    
    # Busca todas as transações deste cartão
    transactions = db.query(models.Transaction).filter(
        models.Transaction.credit_card_id == card_id,
        models.Transaction.payment_method == models.PaymentMethod.CREDIT
    ).all()
    
    # Recalcula o saldo
    balance = 0.0
    for transaction in transactions:
        if transaction.type.value == "expense":
            balance += transaction.amount
        elif transaction.type.value == "income":
            balance = max(0, balance - transaction.amount)
    
    db_card.current_balance = balance
    db.commit()
    db.refresh(db_card)
    return db_card


