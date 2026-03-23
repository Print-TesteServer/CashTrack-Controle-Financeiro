import axios from 'axios';
import type {
  Transaction,
  CreditCard,
  Savings,
  CategoryAnalysis,
  MonthlyAnalysis,
  ChartData,
  SummaryStatistics,
  CashFlowProjection,
  BalanceAlert,
  BreakEvenAnalysis,
  ExpenseForecast,
  SpendingAnomaly,
  Recommendation,
} from '../types';

/**
 * Base URL da API.
 * - Vazio ou ausente: requisições relativas (`/api/...`) — funcionam com o proxy do Vite em `dev` e `preview`.
 * - URL completa: necessário no build servido sem proxy (ex.: arquivos estáticos em outro domínio).
 */
const rawBase = import.meta.env.VITE_API_URL;
const baseURL =
  typeof rawBase === 'string' && rawBase.trim() !== '' ? rawBase.trim().replace(/\/+$/, '') : '';
const apiKey = import.meta.env.VITE_API_KEY;

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
  },
});

// Transactions
export const transactionService = {
  getAll: async (params?: {
    type?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }): Promise<Transaction[]> => {
    const response = await api.get('/api/transactions/', { params });
    return response.data;
  },

  getById: async (id: string): Promise<Transaction> => {
    const response = await api.get(`/api/transactions/${id}`);
    return response.data;
  },

  create: async (transaction: Omit<Transaction, 'id' | 'created_at'>): Promise<Transaction> => {
    const response = await api.post('/api/transactions/', transaction);
    return response.data;
  },

  update: async (id: string, transaction: Partial<Transaction>): Promise<Transaction> => {
    const response = await api.put(`/api/transactions/${id}`, transaction);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/transactions/${id}`);
  },
};

// Credit Cards
export const creditCardService = {
  getAll: async (): Promise<CreditCard[]> => {
    const response = await api.get('/api/credit-cards/');
    return response.data;
  },

  getById: async (id: string): Promise<CreditCard> => {
    const response = await api.get(`/api/credit-cards/${id}`);
    return response.data;
  },

  create: async (card: Omit<CreditCard, 'id' | 'current_balance' | 'created_at'>): Promise<CreditCard> => {
    const response = await api.post('/api/credit-cards/', card);
    return response.data;
  },

  update: async (id: string, card: Partial<CreditCard>): Promise<CreditCard> => {
    const response = await api.put(`/api/credit-cards/${id}`, card);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/credit-cards/${id}`);
  },

  payBill: async (id: string, amount: number): Promise<CreditCard> => {
    const response = await api.post(`/api/credit-cards/${id}/pay`, { amount });
    return response.data;
  },

  recalculateBalance: async (id: string): Promise<CreditCard> => {
    const response = await api.post(`/api/credit-cards/${id}/recalculate`);
    return response.data;
  },
};

// Savings
export const savingsService = {
  getAll: async (): Promise<Savings[]> => {
    const response = await api.get('/api/savings/');
    return response.data;
  },

  getById: async (id: string): Promise<Savings> => {
    const response = await api.get(`/api/savings/${id}`);
    return response.data;
  },

  create: async (savings: Omit<Savings, 'id' | 'current_amount' | 'created_at'>): Promise<Savings> => {
    const response = await api.post('/api/savings/', savings);
    return response.data;
  },

  update: async (id: string, savings: Partial<Savings>): Promise<Savings> => {
    const response = await api.put(`/api/savings/${id}`, savings);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api/savings/${id}`);
  },

  deposit: async (id: string, amount: number): Promise<Savings> => {
    const response = await api.post(`/api/savings/${id}/deposit`, { amount });
    return response.data;
  },

  withdraw: async (id: string, amount: number): Promise<Savings> => {
    const response = await api.post(`/api/savings/${id}/withdraw`, { amount });
    return response.data;
  },

  getAvailableBalance: async (): Promise<number> => {
    const response = await api.get('/api/savings/available-balance');
    return response.data.available_balance;
  },

  getCurrentCDI: async (): Promise<{ cdi: number; unit: string }> => {
    const response = await api.get('/api/savings/current-cdi');
    return response.data;
  },

  calculateYield: async (id: string): Promise<{
    message: string;
    yield_amount: number;
    old_amount: number;
    new_amount: number;
    cdi_used: number;
    annual_rate: number;
    savings: Savings;
  }> => {
    const response = await api.post(`/api/savings/${id}/calculate-yield`);
    return response.data;
  },

  calculateAllYields: async (): Promise<{
    message: string;
    updated: Array<{ name: string; yield: number }>;
    total_yield: number;
    cdi_used: number;
  }> => {
    const response = await api.post('/api/savings/calculate-all-yields');
    return response.data;
  },

  getYieldSummary: async (id: string): Promise<{
    total_deposits: number;
    total_yields: number;
    current_amount: number;
  }> => {
    const response = await api.get(`/api/savings/${id}/yield-summary`);
    return response.data;
  },
};

// Analytics
export const analyticsService = {
  getExpensesByCategory: async (start_date?: string, end_date?: string): Promise<CategoryAnalysis[]> => {
    const response = await api.get('/api/analytics/expenses/categories', {
      params: { start_date, end_date },
    });
    return response.data;
  },

  getIncomeByCategory: async (start_date?: string, end_date?: string): Promise<CategoryAnalysis[]> => {
    const response = await api.get('/api/analytics/income/categories', {
      params: { start_date, end_date },
    });
    return response.data;
  },

  getMonthlyTrends: async (months: number = 12): Promise<MonthlyAnalysis[]> => {
    const response = await api.get('/api/analytics/trends/monthly', { params: { months } });
    return response.data;
  },

  getExpenseChartData: async (start_date?: string, end_date?: string): Promise<ChartData> => {
    const response = await api.get('/api/analytics/chart/expenses', {
      params: { start_date, end_date },
    });
    return response.data;
  },

  getIncomeChartData: async (start_date?: string, end_date?: string): Promise<ChartData> => {
    const response = await api.get('/api/analytics/chart/income', {
      params: { start_date, end_date },
    });
    return response.data;
  },

  getTrendsChartData: async (months: number = 12) => {
    const response = await api.get('/api/analytics/chart/trends', { params: { months } });
    return response.data;
  },

  getSummary: async (start_date?: string, end_date?: string): Promise<SummaryStatistics> => {
    const response = await api.get('/api/analytics/summary', {
      params: { start_date, end_date },
    });
    return response.data;
  },

  getCashFlowProjection: async (months: number = 12): Promise<CashFlowProjection[]> => {
    const response = await api.get('/api/analytics/cash-flow', {
      params: { months },
    });
    return response.data;
  },

  getBreakEvenAnalysis: async (): Promise<BreakEvenAnalysis> => {
    const response = await api.get('/api/analytics/break-even');
    return response.data;
  },

  getBalanceAlert: async (min_balance?: number): Promise<BalanceAlert> => {
    const response = await api.get('/api/analytics/balance-alert', {
      params: min_balance ? { min_balance } : {},
    });
    return response.data;
  },

  getExpenseForecast: async (
    months_ahead: number = 1,
    min_history_months: number = 6,
    lookback_months: number = 24
  ): Promise<ExpenseForecast> => {
    const response = await api.get('/api/analytics/forecast-expenses', {
      params: { months_ahead, min_history_months, lookback_months },
    });
    return response.data;
  },

  getSpendingAnomalies: async (
    window_months: number = 6,
    z_threshold: number = 2.0
  ): Promise<SpendingAnomaly[]> => {
    const response = await api.get('/api/analytics/anomalies', {
      params: { window_months, z_threshold },
    });
    return response.data;
  },

  getRecommendations: async (lookback_months: number = 12): Promise<Recommendation[]> => {
    const response = await api.get('/api/analytics/recommendations', {
      params: { lookback_months },
    });
    return response.data;
  },
};


