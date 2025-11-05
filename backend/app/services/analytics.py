import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app import models
from app.schemas import CategoryAnalysis, MonthlyAnalysis, ChartData

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_transactions_dataframe(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Busca transações e converte para DataFrame"""
        query = self.db.query(models.Transaction)
        
        if start_date:
            query = query.filter(models.Transaction.date >= start_date)
        if end_date:
            query = query.filter(models.Transaction.date <= end_date)
        
        transactions = query.all()
        
        data = [{
            'id': t.id,
            'type': t.type.value,
            'category': t.category,
            'amount': t.amount,
            'date': t.date,
            'payment_method': t.payment_method.value
        } for t in transactions]
        
        return pd.DataFrame(data)
    
    def analyze_expenses_by_category(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CategoryAnalysis]:
        """Análise de gastos por categoria"""
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        expenses = df[df['type'] == 'expense']
        
        if expenses.empty:
            return []
        
        category_summary = expenses.groupby('category').agg({
            'amount': ['sum', 'count']
        }).reset_index()
        
        category_summary.columns = ['category', 'total', 'count']
        total_expenses = expenses['amount'].sum()
        category_summary['percentage'] = (category_summary['total'] / total_expenses * 100).round(2)
        
        category_summary = category_summary.sort_values('total', ascending=False)
        
        return [
            CategoryAnalysis(
                category=row['category'],
                total=round(row['total'], 2),
                count=int(row['count']),
                percentage=round(row['percentage'], 2)
            )
            for _, row in category_summary.iterrows()
        ]
    
    def analyze_income_by_category(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CategoryAnalysis]:
        """Análise de receitas por categoria"""
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        income = df[df['type'] == 'income']
        
        if income.empty:
            return []
        
        category_summary = income.groupby('category').agg({
            'amount': ['sum', 'count']
        }).reset_index()
        
        category_summary.columns = ['category', 'total', 'count']
        total_income = income['amount'].sum()
        category_summary['percentage'] = (category_summary['total'] / total_income * 100).round(2)
        
        category_summary = category_summary.sort_values('total', ascending=False)
        
        return [
            CategoryAnalysis(
                category=row['category'],
                total=round(row['total'], 2),
                count=int(row['count']),
                percentage=round(row['percentage'], 2)
            )
            for _, row in category_summary.iterrows()
        ]
    
    def analyze_monthly_trends(self, months: int = 12) -> List[MonthlyAnalysis]:
        """Análise de tendências mensais"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
        df['month_str'] = df['month'].astype(str)
        
        monthly = df.groupby(['month_str', 'type']).agg({'amount': 'sum'}).reset_index()
        
        monthly_pivot = monthly.pivot(index='month_str', columns='type', values='amount').fillna(0)
        
        monthly_pivot['balance'] = monthly_pivot.get('income', 0) - monthly_pivot.get('expense', 0)
        
        result = []
        for month, row in monthly_pivot.iterrows():
            result.append(MonthlyAnalysis(
                month=month,
                income=round(row.get('income', 0), 2),
                expense=round(row.get('expense', 0), 2),
                balance=round(row.get('balance', 0), 2)
            ))
        
        return sorted(result, key=lambda x: x.month)
    
    def get_expense_chart_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> ChartData:
        """Dados para gráfico de pizza de gastos"""
        categories = self.analyze_expenses_by_category(start_date, end_date)
        
        if not categories:
            return ChartData(labels=[], values=[])
        
        labels = [cat.category for cat in categories]
        values = [cat.total for cat in categories]
        
        # Cores padrão
        colors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ]
        
        return ChartData(
            labels=labels,
            values=values,
            colors=colors[:len(labels)]
        )
    
    def get_income_chart_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> ChartData:
        """Dados para gráfico de pizza de receitas"""
        categories = self.analyze_income_by_category(start_date, end_date)
        
        if not categories:
            return ChartData(labels=[], values=[])
        
        labels = [cat.category for cat in categories]
        values = [cat.total for cat in categories]
        
        colors = [
            '#4BC0C0', '#9966FF', '#FF9F40', '#36A2EB', '#FFCE56'
        ]
        
        return ChartData(
            labels=labels,
            values=values,
            colors=colors[:len(labels)]
        )
    
    def get_monthly_trends_chart_data(self, months: int = 12) -> Dict:
        """Dados para gráfico de linha de tendências mensais"""
        monthly = self.analyze_monthly_trends(months)
        
        if not monthly:
            return {
                "labels": [],
                "income": [],
                "expense": [],
                "balance": []
            }
        
        return {
            "labels": [m.month for m in monthly],
            "income": [m.income for m in monthly],
            "expense": [m.expense for m in monthly],
            "balance": [m.balance for m in monthly]
        }
    
    def get_summary_statistics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict:
        """Estatísticas resumidas (excluindo cartão de crédito e cofrinhos do saldo)"""
        df = self.get_transactions_dataframe(start_date, end_date)
        
        # Exclui transações de cartão de crédito e cofrinhos para cálculo do saldo de caixa
        # Cofrinhos: dinheiro ainda está na conta, apenas separado
        # Cartão de crédito: compromisso futuro, não é dinheiro que saiu agora
        df_filtered = df[
            (df['payment_method'] != 'credit') & 
            (df['category'] != 'Cofrinho')
        ].copy()
        
        # Calcula saldo de caixa (receitas - despesas, sem cartão e sem cofrinhos)
        if df_filtered.empty:
            total_income = 0
            total_expense = 0
            balance = 0
            avg_monthly_income = 0
            avg_monthly_expense = 0
            transaction_count = 0
        else:
            total_income = df_filtered[df_filtered['type'] == 'income']['amount'].sum()
            total_expense = df_filtered[df_filtered['type'] == 'expense']['amount'].sum()
            balance = total_income - total_expense
            
            # Média mensal
            df_filtered['month'] = pd.to_datetime(df_filtered['date']).dt.to_period('M')
            monthly_income = df_filtered[df_filtered['type'] == 'income'].groupby('month')['amount'].sum()
            monthly_expense = df_filtered[df_filtered['type'] == 'expense'].groupby('month')['amount'].sum()
            
            avg_monthly_income = monthly_income.mean() if not monthly_income.empty else 0
            avg_monthly_expense = monthly_expense.mean() if not monthly_expense.empty else 0
            transaction_count = len(df_filtered)
        
        # Calcula total devido em cartões de crédito
        credit_cards = self.db.query(models.CreditCard).all()
        total_credit_debt = sum(card.current_balance for card in credit_cards)
        
        # Calcula total em cofrinhos
        savings = self.db.query(models.Savings).all()
        total_savings = sum(saving.current_amount for saving in savings)
        
        # Saldo líquido (caixa - dívidas de cartão)
        net_balance = balance - total_credit_debt
        
        return {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "balance": round(balance, 2),  # Saldo de caixa
            "total_credit_debt": round(total_credit_debt, 2),  # Total devido em cartões
            "total_savings": round(total_savings, 2),  # Total em cofrinhos
            "net_balance": round(net_balance, 2),  # Saldo líquido (caixa - dívidas)
            "avg_monthly_income": round(avg_monthly_income, 2),
            "avg_monthly_expense": round(avg_monthly_expense, 2),
            "transaction_count": transaction_count
        }


