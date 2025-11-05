import axios from 'axios';
import type { Transaction, CreditCard, Savings, CategoryAnalysis, MonthlyAnalysis, ChartData, SummaryStatistics } from '../types';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Transactions
export const transactionService = {
  getAll: async (params?: {
    type?: string;
    start_date?: string;
    end_date?: string;
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
};


