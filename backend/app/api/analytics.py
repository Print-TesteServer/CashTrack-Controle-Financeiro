from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.services.analytics import AnalyticsService
from app.schemas import CategoryAnalysis, MonthlyAnalysis, ChartData

router = APIRouter()

@router.get("/expenses/categories", response_model=list[CategoryAnalysis])
def get_expenses_by_category(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Análise de gastos por categoria"""
    service = AnalyticsService(db)
    return service.analyze_expenses_by_category(start_date, end_date)

@router.get("/income/categories", response_model=list[CategoryAnalysis])
def get_income_by_category(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Análise de receitas por categoria"""
    service = AnalyticsService(db)
    return service.analyze_income_by_category(start_date, end_date)

@router.get("/trends/monthly", response_model=list[MonthlyAnalysis])
def get_monthly_trends(
    months: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Tendências mensais"""
    service = AnalyticsService(db)
    return service.analyze_monthly_trends(months)

@router.get("/chart/expenses", response_model=ChartData)
def get_expense_chart_data(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Dados para gráfico de pizza de gastos"""
    service = AnalyticsService(db)
    return service.get_expense_chart_data(start_date, end_date)

@router.get("/chart/income", response_model=ChartData)
def get_income_chart_data(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Dados para gráfico de pizza de receitas"""
    service = AnalyticsService(db)
    return service.get_income_chart_data(start_date, end_date)

@router.get("/chart/trends")
def get_trends_chart_data(
    months: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Dados para gráfico de linha de tendências"""
    service = AnalyticsService(db)
    return service.get_monthly_trends_chart_data(months)

@router.get("/summary")
def get_summary_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """Estatísticas resumidas"""
    service = AnalyticsService(db)
    return service.get_summary_statistics(start_date, end_date)


