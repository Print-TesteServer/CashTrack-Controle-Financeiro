from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.services.cdi_service import CDIService
import uuid

router = APIRouter()

def calculate_available_balance(db: Session) -> float:
    """Calcula o saldo disponível (receitas - despesas, excluindo cartão de crédito e cofrinhos)"""
    # Busca todas as transações que não são de cartão de crédito
    # Exclui também transações de cofrinho para evitar dupla contagem
    transactions = db.query(models.Transaction).filter(
        models.Transaction.payment_method != models.PaymentMethod.CREDIT,
        models.Transaction.category != "Cofrinho"
    ).all()
    
    total_income = 0.0
    total_expense = 0.0
    
    for transaction in transactions:
        if transaction.type.value == "income":
            total_income += transaction.amount
        elif transaction.type.value == "expense":
            total_expense += transaction.amount
    
    # Calcula o saldo base
    base_balance = total_income - total_expense
    
    # Subtrai o valor total já alocado nos cofrinhos
    all_savings = db.query(models.Savings).all()
    total_in_savings = sum(savings.current_amount for savings in all_savings)
    
    return base_balance - total_in_savings

@router.post("/", response_model=schemas.SavingsResponse)
def create_savings(savings: schemas.SavingsCreate, db: Session = Depends(get_db)):
    db_savings = models.Savings(
        id=str(uuid.uuid4()),
        **savings.dict(),
        current_amount=0.0
    )
    db.add(db_savings)
    db.commit()
    db.refresh(db_savings)
    return db_savings

@router.get("/", response_model=List[schemas.SavingsResponse])
def get_savings(db: Session = Depends(get_db)):
    return db.query(models.Savings).all()

@router.get("/available-balance")
def get_available_balance(db: Session = Depends(get_db)):
    """Retorna o saldo disponível para depósito em cofrinhos"""
    balance = calculate_available_balance(db)
    return {"available_balance": round(balance, 2)}

@router.get("/current-cdi")
def get_current_cdi():
    """Retorna o CDI atualizado"""
    cdi = CDIService.get_current_cdi()
    return {
        "cdi": round(cdi, 2),
        "unit": "% a.a."
    }

@router.get("/{savings_id}/yield-summary")
def get_yield_summary(savings_id: str, db: Session = Depends(get_db)):
    """Retorna o resumo de depósitos e rendimentos do cofrinho"""
    savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    
    # Busca todas as transações relacionadas ao cofrinho
    transactions = db.query(models.Transaction).filter(
        models.Transaction.category == "Cofrinho",
        models.Transaction.description.like(f"%{savings.name}%")
    ).all()
    
    total_deposits = 0.0
    total_yields = 0.0
    
    for transaction in transactions:
        if "Depósito no cofrinho" in transaction.description:
            total_deposits += transaction.amount
        elif "Rendimento do cofrinho" in transaction.description:
            total_yields += transaction.amount
    
    return {
        "total_deposits": round(total_deposits, 2),
        "total_yields": round(total_yields, 2),
        "current_amount": round(savings.current_amount, 2)
    }

@router.get("/{savings_id}", response_model=schemas.SavingsResponse)
def get_savings_by_id(savings_id: str, db: Session = Depends(get_db)):
    savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    return savings

@router.put("/{savings_id}", response_model=schemas.SavingsResponse)
def update_savings(
    savings_id: str,
    savings_update: schemas.SavingsUpdate,
    db: Session = Depends(get_db)
):
    db_savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not db_savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    
    update_data = savings_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_savings, key, value)
    
    db.commit()
    db.refresh(db_savings)
    return db_savings

@router.delete("/{savings_id}")
def delete_savings(savings_id: str, db: Session = Depends(get_db)):
    db_savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not db_savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    
    db.delete(db_savings)
    db.commit()
    return {"message": "Savings deleted successfully"}

@router.post("/{savings_id}/deposit", response_model=schemas.SavingsResponse)
def deposit_to_savings(
    savings_id: str,
    amount: float = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Deposita um valor existente no cofrinho, validando saldo disponível e criando transação"""
    db_savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not db_savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    # Calcula o saldo disponível
    available_balance = calculate_available_balance(db)
    
    # Verifica se há saldo suficiente
    if amount > available_balance:
        raise HTTPException(
            status_code=400, 
            detail=f"Saldo insuficiente. Saldo disponível: R$ {available_balance:.2f}"
        )
    
    # Cria uma transação de despesa para o depósito no cofrinho
    transaction = models.Transaction(
        id=str(uuid.uuid4()),
        type=models.TransactionType.EXPENSE,
        category="Cofrinho",
        amount=amount,
        description=f"Depósito no cofrinho: {db_savings.name}",
        date=datetime.utcnow(),
        payment_method=models.PaymentMethod.CASH,
        credit_card_id=None
    )
    db.add(transaction)
    
    # Adiciona o valor ao current_amount do cofrinho
    db_savings.current_amount += amount
    
    db.commit()
    db.refresh(db_savings)
    return db_savings

@router.post("/{savings_id}/withdraw", response_model=schemas.SavingsResponse)
def withdraw_from_savings(
    savings_id: str,
    amount: float = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Retira um valor do cofrinho e cria transação de receita"""
    db_savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not db_savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser maior que zero")
    
    if amount > db_savings.current_amount:
        raise HTTPException(status_code=400, detail="Valor não pode ser maior que o valor atual do cofrinho")
    
    # Cria uma transação de receita para a retirada do cofrinho
    transaction = models.Transaction(
        id=str(uuid.uuid4()),
        type=models.TransactionType.INCOME,
        category="Cofrinho",
        amount=amount,
        description=f"Retirada do cofrinho: {db_savings.name}",
        date=datetime.utcnow(),
        payment_method=models.PaymentMethod.CASH,
        credit_card_id=None
    )
    db.add(transaction)
    
    # Remove o valor do current_amount do cofrinho
    db_savings.current_amount -= amount
    
    db.commit()
    db.refresh(db_savings)
    return db_savings

def calculate_yield(savings: models.Savings, db: Session) -> float:
    """Calcula o rendimento acumulado desde a última atualização baseado em CDI"""
    if not savings.cdi_percentage or savings.cdi_percentage <= 0:
        return 0.0
    
    if savings.current_amount <= 0:
        return 0.0
    
    # Busca CDI atualizado
    current_cdi = CDIService.get_current_cdi()
    
    # Calcula taxa anual efetiva: CDI × percentual do banco
    annual_rate = current_cdi * (savings.cdi_percentage / 100)
    
    # Data de referência: última atualização ou criação do cofrinho
    if savings.last_yield_calculation:
        start_date = savings.last_yield_calculation
    else:
        start_date = savings.created_at
    
    end_date = datetime.utcnow()
    
    # Calcula dias decorridos (calendário)
    days_elapsed = (end_date - start_date).days
    
    if days_elapsed <= 0:
        return 0.0
    
    # Calcula rendimento usando a função do serviço CDI
    yield_amount = CDIService.calculate_yield_amount(
        savings.current_amount,
        annual_rate,
        days_elapsed
    )
    
    return yield_amount

@router.post("/{savings_id}/calculate-yield")
def calculate_savings_yield(
    savings_id: str,
    db: Session = Depends(get_db)
):
    """Calcula e aplica o rendimento ao cofrinho baseado em CDI"""
    db_savings = db.query(models.Savings).filter(models.Savings.id == savings_id).first()
    if not db_savings:
        raise HTTPException(status_code=404, detail="Savings not found")
    
    if not db_savings.cdi_percentage or db_savings.cdi_percentage <= 0:
        raise HTTPException(
            status_code=400, 
            detail="Cofrinho não possui percentual de CDI configurado"
        )
    
    if db_savings.current_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Cofrinho não possui valor para calcular rendimento"
        )
    
    # Calcula o rendimento
    yield_amount = calculate_yield(db_savings, db)
    
    if yield_amount <= 0:
        return {
            "message": "Nenhum rendimento acumulado no período",
            "yield_amount": 0.0,
            "savings": db_savings
        }
    
    # Busca CDI atual para mostrar na descrição
    current_cdi = CDIService.get_current_cdi()
    annual_rate = current_cdi * (db_savings.cdi_percentage / 100)
    
    # Atualiza o valor atual
    old_amount = db_savings.current_amount
    db_savings.current_amount += yield_amount
    
    # Cria transação de receita para o rendimento
    transaction = models.Transaction(
        id=str(uuid.uuid4()),
        type=models.TransactionType.INCOME,
        category="Cofrinho",
        amount=yield_amount,
        description=f"Rendimento do cofrinho: {db_savings.name} ({db_savings.cdi_percentage}% do CDI - {annual_rate:.2f}% a.a.)",
        date=datetime.utcnow(),
        payment_method=models.PaymentMethod.CASH,
        credit_card_id=None
    )
    db.add(transaction)
    
    # Atualiza data da última cálculo
    db_savings.last_yield_calculation = datetime.utcnow()
    
    db.commit()
    db.refresh(db_savings)
    
    return {
        "message": f"Rendimento calculado com sucesso!",
        "yield_amount": round(yield_amount, 2),
        "old_amount": round(old_amount, 2),
        "new_amount": round(db_savings.current_amount, 2),
        "cdi_used": round(current_cdi, 2),
        "annual_rate": round(annual_rate, 2),
        "savings": db_savings
    }

@router.post("/calculate-all-yields")
def calculate_all_yields(db: Session = Depends(get_db)):
    """Calcula rendimento de todos os cofrinhos que possuem CDI configurado"""
    all_savings = db.query(models.Savings).filter(
        models.Savings.cdi_percentage.isnot(None),
        models.Savings.cdi_percentage > 0,
        models.Savings.current_amount > 0
    ).all()
    
    if not all_savings:
        return {
            "message": "Nenhum cofrinho com rendimento configurado encontrado",
            "updated": []
        }
    
    # Busca CDI uma vez para todos
    current_cdi = CDIService.get_current_cdi()
    
    updated = []
    total_yield = 0.0
    
    for savings in all_savings:
        try:
            yield_amount = calculate_yield(savings, db)
            if yield_amount > 0:
                annual_rate = current_cdi * (savings.cdi_percentage / 100)
                
                savings.current_amount += yield_amount
                total_yield += yield_amount
                
                # Cria transação de receita
                transaction = models.Transaction(
                    id=str(uuid.uuid4()),
                    type=models.TransactionType.INCOME,
                    category="Cofrinho",
                    amount=yield_amount,
                    description=f"Rendimento do cofrinho: {savings.name} ({savings.cdi_percentage}% do CDI - {annual_rate:.2f}% a.a.)",
                    date=datetime.utcnow(),
                    payment_method=models.PaymentMethod.CASH,
                    credit_card_id=None
                )
                db.add(transaction)
                
                savings.last_yield_calculation = datetime.utcnow()
                updated.append({
                    "name": savings.name,
                    "yield": round(yield_amount, 2)
                })
        except Exception as e:
            print(f"Erro ao calcular rendimento de {savings.name}: {e}")
    
    db.commit()
    return {
        "message": f"Rendimentos calculados para {len(updated)} cofrinho(s)",
        "updated": updated,
        "total_yield": round(total_yield, 2),
        "cdi_used": round(current_cdi, 2)
    }


