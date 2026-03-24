from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal, Optional
from datetime import datetime
from app.database import get_db
from app.services.analytics import AnalyticsService
from app.schemas import (
    CategoryAnalysis,
    MonthlyAnalysis,
    ChartData,
    CashFlowProjection,
    BalanceAlert,
    BreakEvenAnalysis,
    ExpenseForecast,
    SpendingAnomaly,
    Recommendation,
)

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

@router.get("/cash-flow", response_model=list[CashFlowProjection])
def get_cash_flow_projection(
    months: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """Projeção de fluxo de caixa futuro"""
    service = AnalyticsService(db)
    return service.get_cash_flow_projection(months)

@router.get("/break-even", response_model=BreakEvenAnalysis)
def get_break_even_analysis(
    db: Session = Depends(get_db)
):
    """Análise de ponto de ruptura (break-even)"""
    service = AnalyticsService(db)
    return service.get_break_even_analysis()

@router.get("/balance-alert", response_model=BalanceAlert)
def get_balance_alert(
    min_balance: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    """Análise de alerta de saldo"""
    service = AnalyticsService(db)
    return service.get_balance_alert_analysis(min_balance)


@router.get("/forecast-expenses", response_model=ExpenseForecast)
def get_expense_forecast(
    months_ahead: int = Query(1, ge=1, le=6),
    min_history_months: int = Query(6, ge=3, le=24),
    lookback_months: int = Query(24, ge=3, le=24),
    db: Session = Depends(get_db)
):
    """Previsão de gastos com baseline + tendência linear"""
    service = AnalyticsService(db)
    return service.get_expense_forecast(months_ahead, min_history_months, lookback_months)


@router.get("/anomalies", response_model=list[SpendingAnomaly])
def get_spending_anomalies(
    window_months: int = Query(6, ge=3, le=24),
    z_threshold: float = Query(2.0, ge=1.0, le=4.0),
    method: Literal["zscore", "isolation_forest", "both"] = Query(
        "zscore",
        description="zscore: regras clássicas; isolation_forest: sklearn; both: união",
    ),
    db: Session = Depends(get_db),
):
    """Detecção de anomalias por categoria (z-score e/ou Isolation Forest)"""
    service = AnalyticsService(db)
    return service.get_spending_anomalies(window_months, z_threshold, method)


@router.get("/recommendations", response_model=list[Recommendation])
def get_recommendations(
    lookback_months: int = Query(12, ge=3, le=24),
    db: Session = Depends(get_db)
):
    """Recomendações automáticas baseadas em regras"""
    service = AnalyticsService(db)
    return service.get_recommendations(lookback_months)


