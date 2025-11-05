from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas
import uuid

router = APIRouter()

@router.post("/", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    db_transaction = models.Transaction(
        id=str(uuid.uuid4()),
        **transaction.dict()
    )
    db.add(db_transaction)
    
    # Se for pagamento com cartão de crédito, atualizar saldo do cartão
    if transaction.payment_method.value == "credit" and transaction.credit_card_id:
        credit_card = db.query(models.CreditCard).filter(
            models.CreditCard.id == transaction.credit_card_id
        ).first()
        
        if credit_card:
            if transaction.type.value == "expense":
                # Adiciona despesa ao saldo
                credit_card.current_balance += transaction.amount
            elif transaction.type.value == "income":
                # Remove receita do saldo (estorno/pagamento que reduz a fatura)
                credit_card.current_balance = max(0, credit_card.current_balance - transaction.amount)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/", response_model=List[schemas.TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Transaction)
    
    if type:
        query = query.filter(models.Transaction.type == type)
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    return query.order_by(models.Transaction.date.desc()).offset(skip).limit(limit).all()

@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.put("/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(
    transaction_id: str,
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Salva valores antigos para reverter mudanças no cartão
    old_amount = db_transaction.amount
    old_card_id = db_transaction.credit_card_id
    old_type = db_transaction.type.value
    old_payment_method = db_transaction.payment_method.value
    
    # Reverter mudanças no cartão anterior se existir
    if old_card_id and old_payment_method == "credit":
        old_card = db.query(models.CreditCard).filter(models.CreditCard.id == old_card_id).first()
        if old_card:
            # Reverte o valor anterior
            if old_type == "expense":
                old_card.current_balance = max(0, old_card.current_balance - old_amount)
            elif old_type == "income":
                old_card.current_balance += old_amount
    
    # Aplica mudanças
    for key, value in transaction.dict().items():
        setattr(db_transaction, key, value)
    
    # Atualiza novo cartão se for crédito
    if transaction.payment_method.value == "credit" and transaction.credit_card_id:
        credit_card = db.query(models.CreditCard).filter(
            models.CreditCard.id == transaction.credit_card_id
        ).first()
        
        if credit_card:
            if transaction.type.value == "expense":
                credit_card.current_balance += transaction.amount
            elif transaction.type.value == "income":
                credit_card.current_balance = max(0, credit_card.current_balance - transaction.amount)
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str, db: Session = Depends(get_db)):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Reverte saldo do cartão se for transação de crédito
    if db_transaction.payment_method.value == "credit" and db_transaction.credit_card_id:
        credit_card = db.query(models.CreditCard).filter(
            models.CreditCard.id == db_transaction.credit_card_id
        ).first()
        
        if credit_card:
            if db_transaction.type.value == "expense":
                # Remove a despesa do saldo (reverte - estava somando, agora subtrai)
                credit_card.current_balance = max(0, credit_card.current_balance - db_transaction.amount)
            elif db_transaction.type.value == "income":
                # Adiciona de volta (era um pagamento que reduzia a fatura)
                credit_card.current_balance += db_transaction.amount
    
    db.delete(db_transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}


