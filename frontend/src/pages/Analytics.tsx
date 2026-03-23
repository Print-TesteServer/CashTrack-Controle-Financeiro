import { useEffect, useState, useRef } from 'react';
import { analyticsService } from '../services/api';
import type {
  CategoryAnalysis,
  MonthlyAnalysis,
  CashFlowProjection,
  BreakEvenAnalysis,
  BalanceAlert,
  ExpenseForecast,
  SpendingAnomaly,
  Recommendation,
} from '../types';
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
  AreaChart,
  Area,
} from 'recharts';
import { formatCurrency } from '../utils/currency';
import { AlertTriangle, TrendingUp, DollarSign, BrainCircuit } from 'lucide-react';

const formatMonthYear = (value: string): string => {
  const [year, month] = value.split('-').map(Number);
  if (!year || !month) {
    return value;
  }
  return new Date(year, month - 1, 1).toLocaleDateString('pt-BR', {
    month: 'short',
    year: 'numeric',
  });
};

const getModelLabel = (model: string): string => {
  const labels: Record<string, string> = {
    moving_average_fallback: 'Media movel (historico curto)',
    moving_average: 'Media movel',
    linear_trend: 'Tendencia linear',
    insufficient_data: 'Dados insuficientes',
  };
  return labels[model] ?? model;
};

const getPriorityLabel = (priority: Recommendation['priority']): string => {
  const labels = { high: 'Alta', medium: 'Media', low: 'Baixa' };
  return labels[priority];
};

const getSeverityLabel = (severity: SpendingAnomaly['severity']): string => {
  const labels = { high: 'Alta', medium: 'Media', low: 'Baixa' };
  return labels[severity];
};

const getDateRangeFromMonths = (months: number): { startDate: string; endDate: string } => {
  const endDate = new Date();
  const startDate = new Date(endDate);
  startDate.setMonth(startDate.getMonth() - months);
  return {
    startDate: startDate.toISOString(),
    endDate: endDate.toISOString(),
  };
};

export default function Analytics() {
  const [expenseCategories, setExpenseCategories] = useState<CategoryAnalysis[]>([]);
  const [incomeCategories, setIncomeCategories] = useState<CategoryAnalysis[]>([]);
  const [monthlyTrends, setMonthlyTrends] = useState<MonthlyAnalysis[]>([]);
  const [cashFlowProjection, setCashFlowProjection] = useState<CashFlowProjection[]>([]);
  const [breakEvenAnalysis, setBreakEvenAnalysis] = useState<BreakEvenAnalysis | null>(null);
  const [balanceAlert, setBalanceAlert] = useState<BalanceAlert | null>(null);
  const [forecast, setForecast] = useState<ExpenseForecast | null>(null);
  const [anomalies, setAnomalies] = useState<SpendingAnomaly[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState(12);
  const [projectionMonths, setProjectionMonths] = useState(12);
  const [minBalance, setMinBalance] = useState<string>('');
  const minBalanceDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (minBalanceDebounceRef.current) {
        clearTimeout(minBalanceDebounceRef.current);
      }
    };
  }, []);

  useEffect(() => {
    loadAnalytics();
  }, [selectedPeriod, projectionMonths]);

  const loadAnalytics = async () => {
    try {
      const { startDate, endDate } = getDateRangeFromMonths(selectedPeriod);
      const [expenses, income, trends, cashFlow, breakEven, alert, forecastData, anomaliesData, recommendationsData] = await Promise.all([
        analyticsService.getExpensesByCategory(startDate, endDate),
        analyticsService.getIncomeByCategory(startDate, endDate),
        analyticsService.getMonthlyTrends(selectedPeriod),
        analyticsService.getCashFlowProjection(projectionMonths),
        analyticsService.getBreakEvenAnalysis(),
        analyticsService.getBalanceAlert(minBalance ? parseFloat(minBalance) : undefined),
        analyticsService.getExpenseForecast(1, Math.min(6, selectedPeriod), selectedPeriod),
        analyticsService.getSpendingAnomalies(selectedPeriod, 2.0),
        analyticsService.getRecommendations(selectedPeriod),
      ]);

      setExpenseCategories(expenses);
      setIncomeCategories(income);
      setMonthlyTrends(trends);
      setCashFlowProjection(cashFlow);
      setBreakEvenAnalysis(breakEven);
      setBalanceAlert(alert);
      setForecast(forecastData);
      setAnomalies(anomaliesData);
      setRecommendations(recommendationsData);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMinBalanceChange = (value: string) => {
    setMinBalance(value);
    if (minBalanceDebounceRef.current) {
      clearTimeout(minBalanceDebounceRef.current);
    }
    minBalanceDebounceRef.current = setTimeout(() => {
      minBalanceDebounceRef.current = null;
      if (value === '' || !isNaN(parseFloat(value))) {
        analyticsService
          .getBalanceAlert(value ? parseFloat(value) : undefined)
          .then(setBalanceAlert)
          .catch(console.error);
      }
    }, 400);
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

      {/* Intelligent Layer */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center space-x-2">
          <BrainCircuit className="w-6 h-6" />
          <span>Camada Inteligente</span>
        </h2>

        {forecast && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-indigo-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Previsao de Gastos ({formatMonthYear(forecast.target_month)})</div>
              <div className="text-2xl font-bold text-indigo-700">{formatCurrency(forecast.predicted_amount)}</div>
              <div className="text-xs text-gray-500 mt-1">
                Modelo: {getModelLabel(forecast.model_used)} • Historico: {forecast.history_months} {forecast.history_months === 1 ? 'mes' : 'meses'}
              </div>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Faixa Inferior (95%)</div>
              <div className="text-2xl font-bold text-indigo-600">{formatCurrency(forecast.confidence_low)}</div>
            </div>
            <div className="bg-indigo-50 p-4 rounded-lg">
              <div className="text-sm text-gray-600">Faixa Superior (95%)</div>
              <div className="text-2xl font-bold text-indigo-600">{formatCurrency(forecast.confidence_high)}</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 items-stretch">
          <div className="bg-gray-50 rounded-lg p-4 h-full flex flex-col">
            <h3 className="font-semibold text-gray-800 mb-3">Anomalias Detectadas</h3>
            {anomalies.length > 0 ? (
              <div className="space-y-2 flex-1">
                {anomalies.slice(0, 5).map((item, idx) => (
                  <div key={`${item.category}-${item.month}-${idx}`} className="border border-gray-200 rounded p-3 bg-white">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{item.category} ({formatMonthYear(item.month)})</div>
                      <span className={`text-xs px-2 py-1 rounded ${
                        item.severity === 'high'
                          ? 'bg-red-100 text-red-700'
                          : item.severity === 'medium'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}>
                        {getSeverityLabel(item.severity)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">{item.reason}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="border border-gray-200 rounded p-3 bg-white flex-1">
                <p className="text-sm text-gray-500">Nenhuma anomalia relevante detectada.</p>
              </div>
            )}
          </div>

          <div className="bg-gray-50 rounded-lg p-4 h-full flex flex-col">
            <h3 className="font-semibold text-gray-800 mb-3">Recomendações Automáticas</h3>
            {recommendations.length > 0 ? (
              <div className="space-y-2 flex-1">
                {recommendations.slice(0, 5).map((item, idx) => (
                  <div key={`${item.title}-${idx}`} className="border border-gray-200 rounded p-3 bg-white">
                    <div className="font-medium">{item.title || 'Recomendacao financeira'}</div>
                    <div className="text-sm text-gray-600 mt-1">{item.reason}</div>
                    <div className="text-sm text-gray-700 mt-1">Ação: {item.action}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Impacto estimado: {formatCurrency(item.estimated_impact)} • Prioridade: {getPriorityLabel(item.priority)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="border border-gray-200 rounded p-3 bg-white flex-1">
                <p className="text-sm text-gray-500">Sem recomendações no momento.</p>
              </div>
            )}
          </div>
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

      {/* Advanced Analytics Section */}
      <div className="border-t-2 border-gray-300 pt-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">Análises Avançadas</h2>

        {/* Break-Even Analysis */}
        {breakEvenAnalysis && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center space-x-2">
              <DollarSign className="w-6 h-6" />
              <span>Ponto de Ruptura (Break-Even)</span>
            </h3>
            <div className={`p-4 rounded-lg mb-4 ${
              breakEvenAnalysis.is_sustainable 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              <p className={`font-semibold ${
                breakEvenAnalysis.is_sustainable ? 'text-green-800' : 'text-red-800'
              }`}>
                {breakEvenAnalysis.message}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Receita Média Mensal</div>
                <div className="text-xl font-bold text-blue-600">
                  {formatCurrency(breakEvenAnalysis.monthly_income_avg)}
                </div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Despesa Média Mensal</div>
                <div className="text-xl font-bold text-red-600">
                  {formatCurrency(breakEvenAnalysis.monthly_expense_avg)}
                </div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Saldo Líquido Mensal</div>
                <div className={`text-xl font-bold ${
                  breakEvenAnalysis.monthly_net >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(breakEvenAnalysis.monthly_net)}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Saldo Atual</div>
                <div className={`text-xl font-bold ${
                  breakEvenAnalysis.current_balance >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(breakEvenAnalysis.current_balance)}
                </div>
              </div>
            </div>
            {breakEvenAnalysis.months_until_break_even && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm text-gray-600">Tempo até Break-Even</div>
                <div className="text-lg font-bold text-yellow-700">
                  {breakEvenAnalysis.months_until_break_even} meses
                  {breakEvenAnalysis.break_even_date && (
                    <span className="text-sm font-normal text-gray-600 ml-2">
                      (aproximadamente {new Date(breakEvenAnalysis.break_even_date).toLocaleDateString('pt-BR')})
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Balance Alert */}
        {balanceAlert && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800 flex items-center space-x-2">
                <AlertTriangle className="w-6 h-6" />
                <span>Alerta de Saldo</span>
              </h3>
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-600">Saldo Mínimo:</label>
                <input
                  type="number"
                  value={minBalance}
                  onChange={(e) => handleMinBalanceChange(e.target.value)}
                  placeholder="Opcional"
                  className="border border-gray-300 rounded-lg px-3 py-1 w-32 text-sm"
                />
              </div>
            </div>
            <div className={`p-4 rounded-lg mb-4 ${
              balanceAlert.alert_level === 'critical' 
                ? 'bg-red-50 border-2 border-red-300' 
                : balanceAlert.alert_level === 'warning'
                ? 'bg-yellow-50 border-2 border-yellow-300'
                : 'bg-green-50 border-2 border-green-300'
            }`}>
              <div className={`font-semibold ${
                balanceAlert.alert_level === 'critical' 
                  ? 'text-red-800' 
                  : balanceAlert.alert_level === 'warning'
                  ? 'text-yellow-800'
                  : 'text-green-800'
              }`}>
                {balanceAlert.message}
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Saldo Atual</div>
                <div className={`text-xl font-bold ${
                  balanceAlert.current_balance >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(balanceAlert.current_balance)}
                </div>
              </div>
              {balanceAlert.days_until_zero !== null && balanceAlert.days_until_zero !== undefined && (
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Dias até Saldo Zero</div>
                  <div className={`text-xl font-bold ${
                    balanceAlert.days_until_zero <= 30 ? 'text-red-600' : 
                    balanceAlert.days_until_zero <= 60 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {balanceAlert.days_until_zero} dias
                  </div>
                </div>
              )}
              {balanceAlert.suggested_deposit && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm text-gray-600">Aporte Sugerido</div>
                  <div className="text-xl font-bold text-blue-600">
                    {formatCurrency(balanceAlert.suggested_deposit)}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Cash Flow Projection */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-gray-800 flex items-center space-x-2">
              <TrendingUp className="w-6 h-6" />
              <span>Fluxo de Caixa Projetado</span>
            </h3>
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">Meses:</label>
              <select
                value={projectionMonths}
                onChange={(e) => setProjectionMonths(parseInt(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2"
              >
                <option value={6}>6 meses</option>
                <option value={12}>12 meses</option>
                <option value={18}>18 meses</option>
                <option value={24}>24 meses</option>
              </select>
            </div>
          </div>
          {cashFlowProjection.length > 0 ? (
            <div className="space-y-4">
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={cashFlowProjection}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="projected_income" 
                    stroke="#22c55e" 
                    fill="#22c55e" 
                    fillOpacity={0.3}
                    name="Receita Projetada"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="projected_expense" 
                    stroke="#ef4444" 
                    fill="#ef4444" 
                    fillOpacity={0.3}
                    name="Despesa Projetada"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="projected_balance" 
                    stroke="#3b82f6" 
                    fill="#3b82f6" 
                    fillOpacity={0.5}
                    name="Saldo Projetado"
                  />
                </AreaChart>
              </ResponsiveContainer>
              
              {/* Critical Months Alert */}
              {cashFlowProjection.some(p => p.is_critical) && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="font-semibold text-red-800 mb-2">⚠️ Meses Críticos (Saldo Negativo Projetado):</div>
                  <div className="space-y-1">
                    {cashFlowProjection
                      .filter(p => p.is_critical)
                      .map((projection, index) => (
                        <div key={index} className="text-sm text-red-700">
                          • {projection.month}: Saldo projetado de {formatCurrency(projection.projected_balance)}
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">Nenhum dado de projeção disponível</p>
          )}
        </div>
      </div>
    </div>
  );
}


