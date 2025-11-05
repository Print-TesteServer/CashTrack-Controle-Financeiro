import { useEffect, useState } from 'react';
import { analyticsService } from '../services/api';
import type { CategoryAnalysis, MonthlyAnalysis } from '../types';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts';
import { formatCurrency } from '../utils/currency';

export default function Analytics() {
  const [expenseCategories, setExpenseCategories] = useState<CategoryAnalysis[]>([]);
  const [incomeCategories, setIncomeCategories] = useState<CategoryAnalysis[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<MonthlyAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(12);

  useEffect(() => {
    loadAnalytics();
  }, [selectedPeriod]);

  const loadAnalytics = async () => {
    try {
      const [expenses, income, trends] = await Promise.all([
        analyticsService.getExpensesByCategory(),
        analyticsService.getIncomeByCategory(),
        analyticsService.getMonthlyTrends(selectedPeriod),
      ]);

      setExpenseCategories(expenses);
      setIncomeCategories(income);
      setMonthlyTrends(trends);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Carregando análises...</div>;
  }

  const expenseChartData = expenseCategories.map((cat) => ({
    name: cat.category,
    value: cat.total,
    percentage: cat.percentage,
  }));

  const incomeChartData = incomeCategories.map((cat) => ({
    name: cat.category,
    value: cat.total,
    percentage: cat.percentage,
  }));

  const trendsChartData = monthlyTrends.map((trend) => ({
    month: trend.month,
    receita: trend.income,
    despesa: trend.expense,
    saldo: trend.balance,
  }));

  const COLORS = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF'];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Análises e Gráficos</h1>
        <div className="flex items-center space-x-2">
          <label className="text-sm text-gray-600">Período:</label>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(parseInt(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value={3}>3 meses</option>
            <option value={6}>6 meses</option>
            <option value={12}>12 meses</option>
            <option value={24}>24 meses</option>
          </select>
        </div>
      </div>

      {/* Expense Categories */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Gastos por Categoria</h2>
        {expenseCategories.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={expenseChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} ${percentage}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {expenseChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-2">
              {expenseCategories.map((cat, index) => (
                <div key={cat.category} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <span className="font-medium">{cat.category}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{formatCurrency(cat.total)}</div>
                    <div className="text-sm text-gray-500">{cat.percentage}% • {cat.count} transações</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Nenhum dado de gastos disponível</p>
        )}
      </div>

      {/* Income Categories */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Receitas por Categoria</h2>
        {incomeCategories.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={incomeChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name} ${percentage}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {incomeChartData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-2">
              {incomeCategories.map((cat, index) => (
                <div key={cat.category} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <span className="font-medium">{cat.category}</span>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{formatCurrency(cat.total)}</div>
                    <div className="text-sm text-gray-500">{cat.percentage}% • {cat.count} transações</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Nenhum dado de receitas disponível</p>
        )}
      </div>

      {/* Monthly Trends */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Tendências Mensais</h2>
        {trendsChartData.length > 0 ? (
          <div className="space-y-4">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={trendsChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Line type="monotone" dataKey="receita" stroke="#22c55e" strokeWidth={2} />
                <Line type="monotone" dataKey="despesa" stroke="#ef4444" strokeWidth={2} />
                <Line type="monotone" dataKey="saldo" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Média Mensal de Receita</div>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(
                    trendsChartData.reduce((sum, item) => sum + item.receita, 0) /
                    trendsChartData.length
                  )}
                </div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Média Mensal de Despesa</div>
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(
                    trendsChartData.reduce((sum, item) => sum + item.despesa, 0) /
                    trendsChartData.length
                  )}
                </div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Média Mensal de Saldo</div>
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(
                    trendsChartData.reduce((sum, item) => sum + item.saldo, 0) /
                    trendsChartData.length
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Nenhum dado de tendências disponível</p>
        )}
      </div>
    </div>
  );
}


