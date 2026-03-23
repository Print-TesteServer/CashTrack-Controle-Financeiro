import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app import models
from app.schemas import CategoryAnalysis, MonthlyAnalysis, ChartData, CashFlowProjection, BalanceAlert, BreakEvenAnalysis

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
    
    def _filter_cash_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra transações de caixa (exclui cartão de crédito e cofrinhos)
        
        Cofrinhos: dinheiro ainda está na conta, apenas separado
        Cartão de crédito: compromisso futuro, não é dinheiro que saiu agora
        """
        return df[
            (df['payment_method'] != 'credit') & 
            (df['category'] != 'Cofrinho')
        ].copy()
    
    def analyze_expenses_by_category(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[CategoryAnalysis]:
        """Análise de gastos por categoria (excluindo cartão de crédito e cofrinhos para consistência com o resumo)"""
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        # Aplica o mesmo filtro usado no resumo para manter consistência
        df_filtered = self._filter_cash_transactions(df)
        
        expenses = df_filtered[df_filtered['type'] == 'expense']
        
        if expenses.empty:
            return []
        
        category_summary = expenses.groupby('category').agg({
            'amount': ['sum', 'count']
        }).reset_index()
        
        category_summary.columns = ['category', 'total', 'count']
        total_expenses = expenses['amount'].sum()
        # Proteção contra divisão por zero
        if total_expenses > 0:
            category_summary['percentage'] = (category_summary['total'] / total_expenses * 100).round(2)
        else:
            category_summary['percentage'] = 0.0
        
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
        """Análise de receitas por categoria (excluindo cartão de crédito e cofrinhos para consistência com o resumo)"""
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        # Aplica o mesmo filtro usado no resumo para manter consistência
        df_filtered = self._filter_cash_transactions(df)
        
        income = df_filtered[df_filtered['type'] == 'income']
        
        if income.empty:
            return []
        
        category_summary = income.groupby('category').agg({
            'amount': ['sum', 'count']
        }).reset_index()
        
        category_summary.columns = ['category', 'total', 'count']
        total_income = income['amount'].sum()
        # Proteção contra divisão por zero
        if total_income > 0:
            category_summary['percentage'] = (category_summary['total'] / total_income * 100).round(2)
        else:
            category_summary['percentage'] = 0.0
        
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
        """Análise de tendências mensais (excluindo cartão de crédito e cofrinhos para consistência com o resumo)"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        # Aplica o mesmo filtro usado no resumo para manter consistência
        df_filtered = self._filter_cash_transactions(df)
        
        if df_filtered.empty:
            return []
        
        df_filtered['month'] = pd.to_datetime(df_filtered['date']).dt.to_period('M')
        df_filtered['month_str'] = df_filtered['month'].astype(str)
        
        monthly = df_filtered.groupby(['month_str', 'type']).agg({'amount': 'sum'}).reset_index()
        
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
        df_filtered = self._filter_cash_transactions(df)
        
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
    
    def get_cash_flow_projection(self, months: int = 12) -> List[CashFlowProjection]:
        """Projeta fluxo de caixa futuro baseado em médias históricas"""
        # Busca dados históricos dos últimos 6 meses para calcular médias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 meses de histórico
        
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return []
        
        df_filtered = self._filter_cash_transactions(df)
        
        if df_filtered.empty:
            return []
        
        # Calcula médias mensais
        df_filtered['month'] = pd.to_datetime(df_filtered['date']).dt.to_period('M')
        monthly_income = df_filtered[df_filtered['type'] == 'income'].groupby('month')['amount'].sum()
        monthly_expense = df_filtered[df_filtered['type'] == 'expense'].groupby('month')['amount'].sum()
        
        avg_monthly_income = monthly_income.mean() if not monthly_income.empty else 0
        avg_monthly_expense = monthly_expense.mean() if not monthly_expense.empty else 0
        
        # Saldo atual
        current_balance = df_filtered[df_filtered['type'] == 'income']['amount'].sum() - \
                         df_filtered[df_filtered['type'] == 'expense']['amount'].sum()
        
        # Gera projeção
        projections = []
        running_balance = current_balance
        
        for i in range(months):
            # Calcula data do mês projetado
            projection_date = end_date + timedelta(days=30 * (i + 1))
            month_str = projection_date.strftime('%Y-%m')
            
            running_balance += (avg_monthly_income - avg_monthly_expense)
            
            projections.append(CashFlowProjection(
                month=month_str,
                projected_income=round(avg_monthly_income, 2),
                projected_expense=round(avg_monthly_expense, 2),
                projected_balance=round(running_balance, 2),
                is_critical=running_balance < 0
            ))
        
        return projections
    
    def get_break_even_analysis(self) -> BreakEvenAnalysis:
        """Calcula ponto de equilíbrio e projeção até break-even"""
        # Busca dados históricos dos últimos 12 meses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        df = self.get_transactions_dataframe(start_date, end_date)
        
        if df.empty:
            return BreakEvenAnalysis(
                monthly_income_avg=0,
                monthly_expense_avg=0,
                current_balance=0,
                monthly_net=0,
                months_until_break_even=None,
                break_even_date=None,
                is_sustainable=False,
                message="Dados insuficientes para análise"
            )
        
        df_filtered = self._filter_cash_transactions(df)
        
        if df_filtered.empty:
            return BreakEvenAnalysis(
                monthly_income_avg=0,
                monthly_expense_avg=0,
                current_balance=0,
                monthly_net=0,
                months_until_break_even=None,
                break_even_date=None,
                is_sustainable=False,
                message="Dados insuficientes para análise"
            )
        
        # Calcula médias mensais
        df_filtered['month'] = pd.to_datetime(df_filtered['date']).dt.to_period('M')
        monthly_income = df_filtered[df_filtered['type'] == 'income'].groupby('month')['amount'].sum()
        monthly_expense = df_filtered[df_filtered['type'] == 'expense'].groupby('month')['amount'].sum()
        
        avg_monthly_income = monthly_income.mean() if not monthly_income.empty else 0
        avg_monthly_expense = monthly_expense.mean() if not monthly_expense.empty else 0
        monthly_net = avg_monthly_income - avg_monthly_expense
        
        # Saldo atual
        current_balance = df_filtered[df_filtered['type'] == 'income']['amount'].sum() - \
                         df_filtered[df_filtered['type'] == 'expense']['amount'].sum()
        
        # Calcula break-even
        is_sustainable = monthly_net > 0
        months_until_break_even = None
        break_even_date = None
        message = ""
        
        if monthly_net == 0:
            message = "Receitas e despesas estão equilibradas. Saldo permanecerá estável."
        elif monthly_net > 0:
            message = f"Situação sustentável! Você tem um saldo positivo mensal de R$ {monthly_net:.2f}."
        else:
            # Se despesas > receitas, calcula quando saldo chegará a zero
            if current_balance > 0:
                months_until_break_even = int(abs(current_balance / monthly_net))
                break_even_date_obj = end_date + timedelta(days=30 * months_until_break_even)
                break_even_date = break_even_date_obj.strftime('%Y-%m-%d')
                message = f"Atenção! Com as despesas atuais, seu saldo chegará a zero em aproximadamente {months_until_break_even} meses ({break_even_date})."
            else:
                message = "Saldo já está negativo. É necessário aumentar receitas ou reduzir despesas."
        
        return BreakEvenAnalysis(
            monthly_income_avg=round(avg_monthly_income, 2),
            monthly_expense_avg=round(avg_monthly_expense, 2),
            current_balance=round(current_balance, 2),
            monthly_net=round(monthly_net, 2),
            months_until_break_even=months_until_break_even,
            break_even_date=break_even_date,
            is_sustainable=is_sustainable,
            message=message
        )
    
    def get_balance_alert_analysis(self, min_balance: Optional[float] = None) -> BalanceAlert:
        """Analisa quando o saldo pode atingir um nível crítico"""
        # Busca saldo atual
        df = self.get_transactions_dataframe()
        
        if df.empty:
            return BalanceAlert(
                current_balance=0,
                min_balance_threshold=min_balance,
                days_until_zero=None,
                suggested_deposit=None,
                alert_level="safe",
                message="Nenhuma transação encontrada"
            )
        
        df_filtered = self._filter_cash_transactions(df)
        
        if df_filtered.empty:
            return BalanceAlert(
                current_balance=0,
                min_balance_threshold=min_balance,
                days_until_zero=None,
                suggested_deposit=None,
                alert_level="safe",
                message="Nenhuma transação de caixa encontrada"
            )
        
        current_balance = df_filtered[df_filtered['type'] == 'income']['amount'].sum() - \
                         df_filtered[df_filtered['type'] == 'expense']['amount'].sum()
        
        # Calcula média diária de despesas (últimos 30 dias)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        df_recent = df_filtered[df_filtered['date'] >= start_date]
        recent_expenses = df_recent[df_recent['type'] == 'expense']
        
        avg_daily_expense = recent_expenses['amount'].sum() / 30 if not recent_expenses.empty else 0
        
        # Calcula dias até saldo zero
        days_until_zero = None
        suggested_deposit = None
        alert_level = "safe"
        message = ""
        
        if avg_daily_expense > 0 and current_balance > 0:
            days_until_zero = int(current_balance / avg_daily_expense)
        elif current_balance <= 0:
            days_until_zero = 0
        
        # Verifica alerta de saldo mínimo
        if min_balance is not None:
            if current_balance < min_balance:
                alert_level = "critical"
                suggested_deposit = min_balance - current_balance
                message = f"Saldo abaixo do mínimo desejado (R$ {min_balance:.2f}). Sugestão de aporte: R$ {suggested_deposit:.2f}"
            elif current_balance < min_balance * 1.2:  # 20% acima do mínimo
                alert_level = "warning"
                message = f"Saldo próximo do mínimo desejado. Mantenha atenção."
            else:
                alert_level = "safe"
                message = f"Saldo saudável. {days_until_zero} dias até saldo zero (baseado em média atual)."
        else:
            # Sem saldo mínimo configurado, usa dias até zero
            if days_until_zero is not None:
                if days_until_zero <= 0:
                    alert_level = "critical"
                    message = "Saldo negativo ou zerado! Ação imediata necessária."
                elif days_until_zero <= 30:
                    alert_level = "critical"
                    message = f"Alerta crítico! Saldo pode chegar a zero em {days_until_zero} dias."
                elif days_until_zero <= 60:
                    alert_level = "warning"
                    message = f"Atenção! Saldo pode chegar a zero em {days_until_zero} dias."
                else:
                    alert_level = "safe"
                    message = f"Saldo saudável. Projeção: {days_until_zero} dias até saldo zero."
            else:
                alert_level = "safe"
                message = "Saldo positivo. Não há despesas recentes para calcular projeção."
        
        return BalanceAlert(
            current_balance=round(current_balance, 2),
            min_balance_threshold=min_balance,
            days_until_zero=days_until_zero,
            suggested_deposit=round(suggested_deposit, 2) if suggested_deposit else None,
            alert_level=alert_level,
            message=message
        )


