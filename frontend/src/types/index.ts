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


