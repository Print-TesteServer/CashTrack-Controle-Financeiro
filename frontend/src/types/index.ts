export interface Transaction {
  id: string;
  type: 'income' | 'expense';
  category: string;
  amount: number;
  description?: string;
  date: string;
  payment_method: 'cash' | 'credit' | 'debit' | 'pix';
  credit_card_id?: string;
  created_at: string;
}

export interface CreditCard {
  id: string;
  name: string;
  limit: number;
  current_balance: number;
  due_date: number;
  closing_date: number;
  created_at: string;
}

export interface Savings {
  id: string;
  name: string;
  current_amount: number;
  goal_amount: number;
  description?: string;
  institution?: string;
  cdi_percentage?: number;
  last_yield_calculation?: string;
  created_at: string;
}

export interface CategoryAnalysis {
  category: string;
  total: number;
  count: number;
  percentage: number;
}

export interface MonthlyAnalysis {
  month: string;
  income: number;
  expense: number;
  balance: number;
}

export interface ChartData {
  labels: string[];
  values: number[];
  colors?: string[];
}

export interface SummaryStatistics {
  total_income: number;
  total_expense: number;
  balance: number; // Saldo de caixa
  total_credit_debt: number; // Total devido em cartões
  total_savings: number; // Total em cofrinhos
  net_balance: number; // Saldo líquido (caixa - dívidas)
  avg_monthly_income: number;
  avg_monthly_expense: number;
  transaction_count: number;
}

// Advanced Analytics Types
export interface CashFlowProjection {
  month: string;
  projected_income: number;
  projected_expense: number;
  projected_balance: number;
  is_critical: boolean;
}

export interface BalanceAlert {
  current_balance: number;
  min_balance_threshold?: number;
  days_until_zero?: number;
  suggested_deposit?: number;
  alert_level: 'safe' | 'warning' | 'critical';
  message: string;
}

export interface BreakEvenAnalysis {
  monthly_income_avg: number;
  monthly_expense_avg: number;
  current_balance: number;
  monthly_net: number;
  months_until_break_even?: number;
  break_even_date?: string;
  is_sustainable: boolean;
  message: string;
}

export interface ExpenseForecast {
  predicted_amount: number;
  confidence_low: number;
  confidence_high: number;
  model_used: 'moving_average_fallback' | 'moving_average' | 'linear_trend' | 'insufficient_data';
  history_months: number;
  target_month: string;
}

export interface SpendingAnomaly {
  category: string;
  month: string;
  amount: number;
  expected_amount: number;
  deviation_percent: number;
  z_score: number;
  severity: 'low' | 'medium' | 'high';
  reason: string;
}

export interface Recommendation {
  title: string;
  reason: string;
  action: string;
  estimated_impact: number;
  priority: 'low' | 'medium' | 'high';
  confidence: number;
}


