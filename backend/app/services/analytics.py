import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Literal, Tuple
from sqlalchemy.orm import Session
from app import models
from app.constants import is_cashflow_excluded_category
from app.schemas import (
    CategoryAnalysis,
    MonthlyAnalysis,
    ChartData,
    CashFlowProjection,
    BalanceAlert,
    BreakEvenAnalysis,
    ExpenseForecast,
    ForecastModelScore,
    SpendingAnomaly,
    Recommendation,
)
from app.ml import select_and_predict_monthly_expenses
from app.ml.monthly_anomaly_isolation import compute_isolation_monthly_category_anomalies

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
        excluded_cat = df["category"].apply(lambda c: is_cashflow_excluded_category(str(c)))
        return df[(df["payment_method"] != "credit") & (~excluded_cat)].copy()
    
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
                months_until_break_even = math.ceil(abs(current_balance / monthly_net))
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

    def get_expense_forecast(
        self,
        months_ahead: int = 1,
        min_history_months: int = 6,
        lookback_months: int = 24,
    ) -> ExpenseForecast:
        """Prevê gastos futuros com baseline sazonal + tendência linear simples"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * lookback_months)
        df = self.get_transactions_dataframe(start_date, end_date)

        if df.empty:
            return ExpenseForecast(
                predicted_amount=0,
                confidence_low=0,
                confidence_high=0,
                model_used="insufficient_data",
                history_months=0,
                target_month=(end_date + timedelta(days=30 * months_ahead)).strftime("%Y-%m"),
                evaluation_mae=None,
                evaluation_rmse=None,
                holdout_months=None,
                model_comparison=None,
                arima_order=None,
            )

        df_filtered = self._filter_cash_transactions(df)
        expenses = df_filtered[df_filtered["type"] == "expense"].copy()

        if expenses.empty:
            return ExpenseForecast(
                predicted_amount=0,
                confidence_low=0,
                confidence_high=0,
                model_used="insufficient_data",
                history_months=0,
                target_month=(end_date + timedelta(days=30 * months_ahead)).strftime("%Y-%m"),
                evaluation_mae=None,
                evaluation_rmse=None,
                holdout_months=None,
                model_comparison=None,
                arima_order=None,
            )

        expenses["month"] = pd.to_datetime(expenses["date"]).dt.to_period("M")
        monthly_expenses = expenses.groupby("month")["amount"].sum().sort_index()
        history_months = len(monthly_expenses)
        target_month = (end_date + timedelta(days=30 * months_ahead)).strftime("%Y-%m")

        if history_months < min_history_months:
            baseline = float(monthly_expenses.mean())
            confidence_margin = float(monthly_expenses.std(ddof=0)) if history_months > 1 else baseline * 0.2
            return ExpenseForecast(
                predicted_amount=round(max(0, baseline), 2),
                confidence_low=round(max(0, baseline - confidence_margin), 2),
                confidence_high=round(max(0, baseline + confidence_margin), 2),
                model_used="moving_average_fallback",
                history_months=history_months,
                target_month=target_month,
                evaluation_mae=None,
                evaluation_rmse=None,
                holdout_months=None,
                model_comparison=None,
                arima_order=None,
            )

        values = monthly_expenses.values.astype(float)
        result = select_and_predict_monthly_expenses(values, months_ahead)
        comparison = (
            [ForecastModelScore(model=m, mae=mae, rmse=rmse) for m, mae, rmse in result.model_comparison]
            if result.model_comparison
            else None
        )
        return ExpenseForecast(
            predicted_amount=result.predicted_amount,
            confidence_low=result.confidence_low,
            confidence_high=result.confidence_high,
            model_used=result.model_used,
            history_months=history_months,
            target_month=target_month,
            evaluation_mae=result.evaluation_mae,
            evaluation_rmse=result.evaluation_rmse,
            holdout_months=result.holdout_months,
            model_comparison=comparison,
            arima_order=result.arima_order,
        )

    def _spending_anomalies_zscore(
        self, monthly_category: pd.DataFrame, z_threshold: float
    ) -> List[SpendingAnomaly]:
        """Último mês por categoria vs média da série — z-score + desvio percentual."""
        anomalies: List[SpendingAnomaly] = []
        severity_rank = {"high": 3, "medium": 2, "low": 1}
        for category, group in monthly_category.groupby("category"):
            group = group.sort_values("month")
            amounts = group["amount"].values.astype(float)
            if len(amounts) < 3:
                continue

            mean_val = float(np.mean(amounts))
            std_val = float(np.std(amounts, ddof=0))
            latest_amount = float(amounts[-1])
            latest_month = str(group.iloc[-1]["month"])

            if std_val <= 0:
                z_score = 0.0
            else:
                z_score = (latest_amount - mean_val) / std_val

            deviation_percent = ((latest_amount - mean_val) / mean_val * 100) if mean_val > 0 else 0.0
            abs_deviation_percent = abs(deviation_percent)

            is_anomaly = abs(z_score) >= z_threshold or abs_deviation_percent >= 30
            if not is_anomaly:
                continue

            abs_z = abs(z_score)
            if abs_z >= 3 or abs_deviation_percent >= 60:
                severity = "high"
            elif abs_z >= 2.5 or abs_deviation_percent >= 45:
                severity = "medium"
            else:
                severity = "low"

            direction_text = "acima" if deviation_percent >= 0 else "abaixo"
            reason = (
                f"Gasto em {category} está {abs(deviation_percent):.1f}% {direction_text} da média recente "
                f"(z-score {z_score:.2f})."
            )

            anomalies.append(
                SpendingAnomaly(
                    category=category,
                    month=latest_month,
                    amount=round(latest_amount, 2),
                    expected_amount=round(mean_val, 2),
                    deviation_percent=round(deviation_percent, 2),
                    z_score=round(z_score, 2),
                    severity=severity,
                    reason=reason,
                    detector="zscore",
                    isolation_score=None,
                )
            )

        anomalies.sort(
            key=lambda x: (severity_rank.get(x.severity, 0), abs(x.deviation_percent)),
            reverse=True,
        )
        return anomalies

    @staticmethod
    def _merge_spending_anomalies(
        z_list: List[SpendingAnomaly], i_list: List[SpendingAnomaly]
    ) -> List[SpendingAnomaly]:
        severity_rank = {"high": 3, "medium": 2, "low": 1}

        def key(a: SpendingAnomaly) -> Tuple[str, str]:
            return (a.category, a.month)

        zm = {key(a): a for a in z_list}
        im = {key(a): a for a in i_list}
        out: List[SpendingAnomaly] = []
        for k in sorted(set(zm) | set(im), key=lambda x: (x[0], x[1])):
            z = zm.get(k)
            i = im.get(k)
            if z and i:
                zr = severity_rank.get(z.severity, 0)
                ir = severity_rank.get(i.severity, 0)
                sev = z.severity if zr >= ir else i.severity
                out.append(
                    SpendingAnomaly(
                        category=z.category,
                        month=z.month,
                        amount=z.amount,
                        expected_amount=z.expected_amount,
                        deviation_percent=z.deviation_percent,
                        z_score=z.z_score,
                        severity=sev,
                        reason=f"{z.reason} | {i.reason}",
                        detector="both",
                        isolation_score=i.isolation_score,
                    )
                )
            elif z:
                out.append(
                    SpendingAnomaly(
                        category=z.category,
                        month=z.month,
                        amount=z.amount,
                        expected_amount=z.expected_amount,
                        deviation_percent=z.deviation_percent,
                        z_score=z.z_score,
                        severity=z.severity,
                        reason=z.reason,
                        detector="zscore",
                        isolation_score=None,
                    )
                )
            elif i:
                out.append(i)

        out.sort(
            key=lambda x: (severity_rank.get(x.severity, 0), abs(x.deviation_percent)),
            reverse=True,
        )
        return out

    def get_spending_anomalies(
        self,
        window_months: int = 6,
        z_threshold: float = 2.0,
        method: Literal["zscore", "isolation_forest", "both"] = "zscore",
    ) -> List[SpendingAnomaly]:
        """Anomalias: z-score (regras), Isolation Forest (sklearn) ou união dos dois."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * max(window_months, 3))
        df = self.get_transactions_dataframe(start_date, end_date)

        if df.empty:
            return []

        df_filtered = self._filter_cash_transactions(df)
        expenses = df_filtered[df_filtered["type"] == "expense"].copy()
        if expenses.empty:
            return []

        expenses["month"] = pd.to_datetime(expenses["date"]).dt.to_period("M").astype(str)
        monthly_category = expenses.groupby(["category", "month"])["amount"].sum().reset_index()

        if method == "zscore":
            return self._spending_anomalies_zscore(monthly_category, z_threshold)
        if method == "isolation_forest":
            raw = compute_isolation_monthly_category_anomalies(monthly_category)
            return [
                SpendingAnomaly(
                    detector="isolation_forest",
                    isolation_score=r.get("isolation_score"),
                    category=r["category"],
                    month=r["month"],
                    amount=r["amount"],
                    expected_amount=r["expected_amount"],
                    deviation_percent=r["deviation_percent"],
                    z_score=r["z_score"],
                    severity=r["severity"],
                    reason=r["reason"],
                )
                for r in raw
            ]

        z_list = self._spending_anomalies_zscore(monthly_category, z_threshold)
        raw = compute_isolation_monthly_category_anomalies(monthly_category)
        i_list = [
            SpendingAnomaly(
                detector="isolation_forest",
                isolation_score=r.get("isolation_score"),
                category=r["category"],
                month=r["month"],
                amount=r["amount"],
                expected_amount=r["expected_amount"],
                deviation_percent=r["deviation_percent"],
                z_score=r["z_score"],
                severity=r["severity"],
                reason=r["reason"],
            )
            for r in raw
        ]
        return self._merge_spending_anomalies(z_list, i_list)

    def get_recommendations(self, lookback_months: int = 12) -> List[Recommendation]:
        """Gera recomendações práticas com base em regras transparentes"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * max(lookback_months, 3))

        summary = self.get_summary_statistics(start_date, end_date)
        categories = self.analyze_expenses_by_category(start_date, end_date)
        recommendations: List[Recommendation] = []

        total_income = float(summary.get("total_income", 0))
        total_expense = float(summary.get("total_expense", 0))
        net_balance = float(summary.get("net_balance", 0))

        if total_income > 0 and total_expense > 0:
            for cat in categories[:5]:
                if cat.percentage >= 30:
                    impact = cat.total * 0.15
                    recommendations.append(
                        Recommendation(
                            title=f"Otimizar gastos com {cat.category}",
                            reason=f"{cat.category} representa {cat.percentage}% das suas despesas.",
                            action=f"Reduza 15% nesta categoria para abrir folga no orçamento.",
                            estimated_impact=round(impact, 2),
                            priority="high" if cat.percentage >= 40 else "medium",
                            confidence=0.82,
                        )
                    )

        if net_balance < 0:
            recommendations.append(
                Recommendation(
                    title="Reequilibrar fluxo mensal",
                    reason="Seu saldo líquido está negativo.",
                    action="Defina teto semanal para despesas variáveis e revise assinaturas/recorrências.",
                    estimated_impact=round(abs(net_balance), 2),
                    priority="high",
                    confidence=0.88,
                )
            )

        anomalies = self.get_spending_anomalies(
            window_months=max(lookback_months, 3),
            z_threshold=2.0,
            method="zscore",
        )
        for anomaly in anomalies[:2]:
            recommendations.append(
                Recommendation(
                    title=f"Investigar aumento em {anomaly.category}",
                    reason=anomaly.reason,
                    action="Valide compras recentes e aplique limite mensal para essa categoria.",
                    estimated_impact=round(max(0, anomaly.amount - anomaly.expected_amount), 2),
                    priority="high" if anomaly.severity == "high" else "medium",
                    confidence=0.78,
                )
            )

        if not recommendations:
            recommendations.append(
                Recommendation(
                    title="Orçamento estável",
                    reason="Não foram detectados riscos relevantes no período recente.",
                    action="Mantenha o acompanhamento semanal e atualize metas de economia.",
                    estimated_impact=0,
                    priority="low",
                    confidence=0.7,
                )
            )

        return recommendations[:6]


