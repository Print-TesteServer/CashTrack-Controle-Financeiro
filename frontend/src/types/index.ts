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

export interface ForecastModelScore {
  model: string;
  mae: number;
  rmse: number;
}

export interface ExpenseForecast {
  predicted_amount: number;
  confidence_low: number;
  confidence_high: number;
  model_used:
    | 'moving_average_fallback'
    | 'moving_average'
    | 'linear_trend'
    | 'arima'
    | 'insufficient_data';
  history_months: number;
  target_month: string;
  evaluation_mae?: number | null;
  evaluation_rmse?: number | null;
  holdout_months?: number | null;
  model_comparison?: ForecastModelScore[] | null;
  arima_order?: [number, number, number] | null;
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
  detector?: 'zscore' | 'isolation_forest' | 'both';
  isolation_score?: number | null;
}

export interface Recommendation {
  title: string;
  reason: string;
  action: string;
  estimated_impact: number;
  priority: 'low' | 'medium' | 'high';
  confidence: number;
}

export interface CategoryScore {
  category: string;
  probability: number;
}

export interface CategoryPredictResponse {
  predicted_category: string | null;
  confidence: number;
  top_categories: CategoryScore[];
  model_trained: boolean;
  message: string | null;
}

export interface CategoryTrainResponse {
  trained_at: string;
  n_samples: number;
  n_classes: number;
  accuracy: number;
  macro_f1: number;
}

export interface CategoryModelInfo {
  trained: boolean;
  trained_at?: string;
  n_samples?: number;
  n_classes?: number;
  accuracy?: number;
  macro_f1?: number;
}

export interface AIExplainResponse {
  answer: string;
  model: string;
  lookback_months: number;
}

export interface AIQueryResponse {
  answer: string;
  intent: string;
  months_back: number;
  value: number | null;
  model: string;
}


