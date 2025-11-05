import { useEffect, useState, useRef } from 'react';
import { savingsService } from '../services/api';
import type { Savings } from '../types';
import { Plus, Trash2, Edit, ArrowDown, ArrowUp } from 'lucide-react';
import { parseBrazilianCurrency, formatCurrency, formatForInput, handleInputChange } from '../utils/currency';

export default function Savings() {
  const [savings, setSavings] = useState<Savings[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingSavings, setEditingSavings] = useState<Savings | null>(null);
  const scrollPositionRef = useRef<number>(0);
  const formRef = useRef<HTMLDivElement>(null);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [showWithdrawModal, setShowWithdrawModal] = useState(false);
  const [selectedSaving, setSelectedSaving] = useState<Savings | null>(null);
  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [operationError, setOperationError] = useState('');
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);
  const [availableBalance, setAvailableBalance] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    goal_amount: '',
    description: '',
    institution: '',
    cdi_percentage: '',
  });
  
  const [currentCDI, setCurrentCDI] = useState<number | null>(null);
  const [yieldSummaries, setYieldSummaries] = useState<Record<string, {total_deposits: number, total_yields: number}>>({});

  useEffect(() => {
    loadSavings();
    loadCurrentCDI();
  }, []);

  // Faz scroll para o topo quando abrir o formulário em modo de edição
  useEffect(() => {
    if (showForm && editingSavings && formRef.current) {
      // Pequeno delay para garantir que o DOM foi atualizado
      setTimeout(() => {
        formRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 50);
    }
  }, [showForm, editingSavings]);

  const loadCurrentCDI = async () => {
    try {
      const data = await savingsService.getCurrentCDI();
      setCurrentCDI(data.cdi);
    } catch (error) {
      console.error('Error loading CDI:', error);
    }
  };

  const loadSavings = async () => {
    try {
      const data = await savingsService.getAll();
      setSavings(data);
      
      // Carregar resumos de rendimentos para cada cofrinho
      const summaries: Record<string, {total_deposits: number, total_yields: number}> = {};
      for (const saving of data) {
        try {
          const summary = await savingsService.getYieldSummary(saving.id);
          summaries[saving.id] = {
            total_deposits: summary.total_deposits,
            total_yields: summary.total_yields
          };
        } catch (error) {
          console.error(`Error loading yield summary for ${saving.id}:`, error);
          summaries[saving.id] = { total_deposits: 0, total_yields: 0 };
        }
      }
      setYieldSummaries(summaries);
    } catch (error) {
      console.error('Error loading savings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const goalValue = parseBrazilianCurrency(formData.goal_amount);
      
      const cdiValue = formData.cdi_percentage ? parseFloat(formData.cdi_percentage.replace(',', '.')) : undefined;
      
      const savingsData: any = {
        name: formData.name,
        goal_amount: goalValue,
        description: formData.description || undefined,
        institution: formData.institution || undefined,
        cdi_percentage: cdiValue,
      };
      
      if (editingSavings) {
        await savingsService.update(editingSavings.id, savingsData);
      } else {
        await savingsService.create(savingsData);
      }
      await loadSavings();
      resetForm();
    } catch (error) {
      console.error('Error saving savings:', error);
      alert('Erro ao salvar cofrinho');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este cofrinho?')) return;
    try {
      await savingsService.delete(id);
      await loadSavings();
    } catch (error) {
      console.error('Error deleting savings:', error);
      alert('Erro ao excluir cofrinho');
    }
  };

  const handleEdit = (saving: Savings) => {
    // Salva a posição atual do scroll
    scrollPositionRef.current = window.scrollY;
    
    setEditingSavings(saving);
    setFormData({
      name: saving.name,
      goal_amount: formatForInput(saving.goal_amount),
      description: saving.description || '',
      institution: saving.institution || '',
      cdi_percentage: saving.cdi_percentage ? saving.cdi_percentage.toString().replace('.', ',') : '',
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      goal_amount: '',
      description: '',
      institution: '',
      cdi_percentage: '',
    });
    setEditingSavings(null);
    setShowForm(false);
    
    // Restaura a posição de scroll se estava editando
    if (scrollPositionRef.current > 0) {
      setTimeout(() => {
        window.scrollTo({
          top: scrollPositionRef.current,
          behavior: 'smooth'
        });
        scrollPositionRef.current = 0;
      }, 100);
    }
  };

  const handleCalculateYield = async (id: string) => {
    try {
      const result = await savingsService.calculateYield(id);
      await loadSavings();
      
      // Recarregar resumos após calcular rendimento
      const updatedSavings = await savingsService.getAll();
      await loadYieldSummaries(updatedSavings);
      
      if (result.yield_amount > 0) {
        alert(
          `💰 Rendimento Calculado!\n\n` +
          `Valor anterior: R$ ${result.old_amount.toFixed(2)}\n` +
          `Rendimento: R$ ${result.yield_amount.toFixed(2)}\n` +
          `Novo valor: R$ ${result.new_amount.toFixed(2)}\n\n` +
          `CDI usado: ${result.cdi_used}% a.a.\n` +
          `Taxa efetiva: ${result.annual_rate.toFixed(2)}% a.a.`
        );
      } else {
        alert(result.message || 'Nenhum rendimento acumulado no período');
      }
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao calcular rendimento');
    }
  };

  const loadYieldSummaries = async (savingsList?: Savings[]) => {
    const savingsToProcess = savingsList || savings;
    const summaries: Record<string, {total_deposits: number, total_yields: number}> = {};
    for (const saving of savingsToProcess) {
      try {
        const summary = await savingsService.getYieldSummary(saving.id);
        summaries[saving.id] = {
          total_deposits: summary.total_deposits,
          total_yields: summary.total_yields
        };
      } catch (error) {
        console.error(`Error loading yield summary for ${saving.id}:`, error);
        summaries[saving.id] = { total_deposits: 0, total_yields: 0 };
      }
    }
    setYieldSummaries(summaries);
  };

  const handleCalculateAllYields = async () => {
    try {
      const result = await savingsService.calculateAllYields();
      alert(`${result.message}\nTotal: R$ ${result.total_yield.toFixed(2)}\nCDI usado: ${result.cdi_used}% a.a.`);
      await loadSavings();
      await loadCurrentCDI();
      // Recarregar resumos após calcular rendimentos
      await loadYieldSummaries();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Erro ao calcular rendimentos');
    }
  };

  const getProgressPercentage = (saving: Savings) => {
    return (saving.current_amount / saving.goal_amount) * 100;
  };

  const handleDeposit = async (saving: Savings) => {
    setSelectedSaving(saving);
    setDepositAmount('');
    setOperationError('');
    try {
      const balance = await savingsService.getAvailableBalance();
      setAvailableBalance(balance);
    } catch (error) {
      console.error('Error loading available balance:', error);
      setAvailableBalance(null);
    }
    setShowDepositModal(true);
  };

  const handleWithdraw = (saving: Savings) => {
    setSelectedSaving(saving);
    setWithdrawAmount('');
    setOperationError('');
    setShowWithdrawModal(true);
  };

  const handleSubmitDeposit = async () => {
    if (!selectedSaving) return;
    
    setOperationError('');
    
    if (!depositAmount || depositAmount.trim() === '') {
      setOperationError('Por favor, informe o valor a depositar');
      return;
    }
    
    try {
      const amount = parseBrazilianCurrency(depositAmount);
      if (amount <= 0) {
        setOperationError('Valor deve ser maior que zero');
        return;
      }
      
      await savingsService.deposit(selectedSaving.id, amount);
      await loadSavings();
      // Atualiza o saldo disponível
      const balance = await savingsService.getAvailableBalance();
      setAvailableBalance(balance);
      // Recarregar resumos após depositar
      const updatedSavings = await savingsService.getAll();
      await loadYieldSummaries(updatedSavings);
      setShowDepositModal(false);
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } catch (error: any) {
      console.error('Error depositing:', error);
      if (error.response?.status === 404) {
        setOperationError('Cofrinho não encontrado. Recarregue a página.');
      } else if (error.response?.data?.detail) {
        setOperationError(error.response.data.detail);
      } else if (error.message) {
        setOperationError(error.message);
      } else {
        setOperationError('Erro ao depositar. Verifique se o backend está rodando e tente novamente.');
      }
    }
  };

  const handleSubmitWithdraw = async () => {
    if (!selectedSaving) return;
    
    setOperationError('');
    
    if (!withdrawAmount || withdrawAmount.trim() === '') {
      setOperationError('Por favor, informe o valor a retirar');
      return;
    }
    
    try {
      const amount = parseBrazilianCurrency(withdrawAmount);
      if (amount <= 0) {
        setOperationError('Valor deve ser maior que zero');
        return;
      }
      
      if (amount > selectedSaving.current_amount) {
        setOperationError('Valor não pode ser maior que o valor atual do cofrinho');
        return;
      }
      
      await savingsService.withdraw(selectedSaving.id, amount);
      await loadSavings();
      // Atualiza o saldo disponível após retirada
      const balance = await savingsService.getAvailableBalance();
      setAvailableBalance(balance);
      // Recarregar resumos após retirar
      const updatedSavings = await savingsService.getAll();
      await loadYieldSummaries(updatedSavings);
      setShowWithdrawModal(false);
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } catch (error: any) {
      console.error('Error withdrawing:', error);
      if (error.response?.status === 404) {
        setOperationError('Cofrinho não encontrado. Recarregue a página.');
      } else if (error.response?.data?.detail) {
        setOperationError(error.response.data.detail);
      } else if (error.message) {
        setOperationError(error.message);
      } else {
        setOperationError('Erro ao retirar. Verifique se o backend está rodando e tente novamente.');
      }
    }
  };

  const handleCloseDepositModal = () => {
    setShowDepositModal(false);
    setSelectedSaving(null);
    setDepositAmount('');
    setOperationError('');
    setAvailableBalance(null);
  };

  const handleCloseWithdrawModal = () => {
    setShowWithdrawModal(false);
    setSelectedSaving(null);
    setWithdrawAmount('');
    setOperationError('');
  };

  if (loading) {
    return <div className="text-center py-8">Carregando...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Cofrinhos</h1>
          {currentCDI && (
            <p className="text-sm text-gray-600 mt-1">
              CDI atual: <span className="font-semibold text-green-600">{currentCDI}% a.a.</span>
            </p>
          )}
        </div>
        <div className="flex space-x-2">
          {savings.some(s => s.cdi_percentage && s.cdi_percentage > 0 && s.current_amount > 0) && (
            <button
              onClick={handleCalculateAllYields}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              <span>Atualizar Rendimentos</span>
            </button>
          )}
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
          >
            <Plus className="w-5 h-5" />
            <span>Novo Cofrinho</span>
          </button>
        </div>
      </div>

      {showForm && (
        <div ref={formRef} className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            {editingSavings ? 'Editar Cofrinho' : 'Novo Cofrinho'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Meta</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={formData.goal_amount}
                  onChange={(e) => {
                    const processed = handleInputChange(e.target.value);
                    setFormData({ ...formData, goal_amount: processed });
                  }}
                  placeholder="0,00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Use vírgula para decimais (ex: 10.000,00)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Instituição</label>
                <select
                  value={formData.institution}
                  onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="">Selecione...</option>
                  <option value="Inter">Inter</option>
                  <option value="Itaú">Itaú</option>
                  <option value="Rico">Rico</option>
                  <option value="Nubank">Nubank</option>
                  <option value="XP">XP Investimentos</option>
                  <option value="BTG">BTG Pactual</option>
                  <option value="Outro">Outro</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  % do CDI
                </label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={formData.cdi_percentage}
                  onChange={(e) => {
                    const processed = handleInputChange(e.target.value);
                    setFormData({ ...formData, cdi_percentage: processed });
                  }}
                  placeholder="114,12"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Ex: 114.12 = 114,12% do CDI
                  {currentCDI && formData.cdi_percentage && (
                    <span className="block mt-1 text-green-600">
                      CDI atual: {currentCDI}% a.a. | Seu rendimento: {((currentCDI * parseFloat(formData.cdi_percentage.replace(',', '.'))) / 100).toFixed(2)}% a.a.
                    </span>
                  )}
                </p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows={3}
                />
              </div>
            </div>

            <div className="flex space-x-2">
              <button
                type="submit"
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
              >
                {editingSavings ? 'Atualizar' : 'Salvar'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {savings.map((saving) => {
          const progressPercentage = getProgressPercentage(saving);
          const remaining = saving.goal_amount - saving.current_amount;

          return (
            <div key={saving.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold text-gray-800">{saving.name}</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEdit(saving)}
                    className="text-primary-600 hover:text-primary-900"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(saving.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {saving.description && (
                <p className="text-sm text-gray-600 mb-2">{saving.description}</p>
              )}

              {saving.institution && (
                <div className="mb-2">
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {saving.institution}
                  </span>
                </div>
              )}

              {saving.cdi_percentage && currentCDI && (
                <div className="mb-2 text-xs text-gray-600">
                  <span className="font-semibold">{saving.cdi_percentage}% do CDI</span>
                  <span className="text-green-600 ml-2">
                    ({(currentCDI * saving.cdi_percentage / 100).toFixed(2)}% a.a.)
                  </span>
                </div>
              )}

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progresso</span>
                    <span>{progressPercentage.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-primary-600 h-3 rounded-full transition-all"
                      style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-200 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Atual:</span>
                    <span className="font-semibold text-gray-800">
                      {formatCurrency(saving.current_amount)}
                    </span>
                  </div>
                  {yieldSummaries[saving.id] && yieldSummaries[saving.id].total_yields > 0 && (
                    <>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Depositado:</span>
                        <span className="text-gray-700">
                          {formatCurrency(yieldSummaries[saving.id].total_deposits)}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Rendido:</span>
                        <span className="font-semibold text-green-600">
                          +{formatCurrency(yieldSummaries[saving.id].total_yields)}
                        </span>
                      </div>
                    </>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Meta:</span>
                    <span className="font-semibold text-gray-800">
                      {formatCurrency(saving.goal_amount)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Restante:</span>
                    <span className="font-semibold text-primary-600">
                      {formatCurrency(remaining)}
                    </span>
                  </div>
                  
                  {saving.cdi_percentage && saving.cdi_percentage > 0 && saving.current_amount > 0 && (
                    <div className="mt-2">
                      <button
                        onClick={() => handleCalculateYield(saving.id)}
                        className="w-full bg-purple-600 text-white px-3 py-2 rounded-lg hover:bg-purple-700 flex items-center justify-center space-x-1 text-sm"
                      >
                        <span>💰 Calcular Rendimento</span>
                      </button>
                    </div>
                  )}
                  
                  <div className="flex space-x-2 mt-3">
                    <button
                      onClick={() => handleDeposit(saving)}
                      className="flex-1 bg-green-600 text-white px-3 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center space-x-1 text-sm"
                    >
                      <ArrowDown className="w-4 h-4" />
                      <span>Depositar</span>
                    </button>
                    {saving.current_amount > 0 && (
                      <button
                        onClick={() => handleWithdraw(saving)}
                        className="flex-1 bg-orange-600 text-white px-3 py-2 rounded-lg hover:bg-orange-700 flex items-center justify-center space-x-1 text-sm"
                      >
                        <ArrowUp className="w-4 h-4" />
                        <span>Retirar</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {savings.length === 0 && (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Nenhum cofrinho cadastrado
        </div>
      )}

      {/* Modal de Depósito */}
      {showDepositModal && selectedSaving && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleCloseDepositModal}
        >
          <div 
            className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              Depositar no Cofrinho
            </h2>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Cofrinho:</p>
              <p className="font-semibold text-gray-800">{selectedSaving.name}</p>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Valor Atual:</p>
              <p className="text-lg font-bold text-gray-800">
                {formatCurrency(selectedSaving.current_amount)}
              </p>
            </div>

            {availableBalance !== null && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-gray-600 mb-1">Saldo Disponível:</p>
                <p className={`text-lg font-bold ${availableBalance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(availableBalance)}
                </p>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valor a Depositar
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={depositAmount}
                onChange={(e) => {
                  const processed = handleInputChange(e.target.value);
                  setDepositAmount(processed);
                  setOperationError('');
                }}
                placeholder="0,00"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSubmitDeposit();
                  } else if (e.key === 'Escape') {
                    handleCloseDepositModal();
                  }
                }}
              />
              <p className="text-xs text-gray-500 mt-1">Use vírgula para decimais (ex: 500,00)</p>
              {operationError && (
                <p className="text-xs text-red-600 mt-1">{operationError}</p>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                onClick={handleSubmitDeposit}
                className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Confirmar
              </button>
              <button
                onClick={handleCloseDepositModal}
                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Retirada */}
      {showWithdrawModal && selectedSaving && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleCloseWithdrawModal}
        >
          <div 
            className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              Retirar do Cofrinho
            </h2>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Cofrinho:</p>
              <p className="font-semibold text-gray-800">{selectedSaving.name}</p>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Valor Disponível:</p>
              <p className="text-lg font-bold text-gray-800">
                {formatCurrency(selectedSaving.current_amount)}
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valor a Retirar
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={withdrawAmount}
                onChange={(e) => {
                  const processed = handleInputChange(e.target.value);
                  setWithdrawAmount(processed);
                  setOperationError('');
                }}
                placeholder="0,00"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-orange-500"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSubmitWithdraw();
                  } else if (e.key === 'Escape') {
                    handleCloseWithdrawModal();
                  }
                }}
              />
              <p className="text-xs text-gray-500 mt-1">Use vírgula para decimais (ex: 500,00)</p>
              {operationError && (
                <p className="text-xs text-red-600 mt-1">{operationError}</p>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                onClick={handleSubmitWithdraw}
                className="flex-1 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
              >
                Confirmar
              </button>
              <button
                onClick={handleCloseWithdrawModal}
                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mensagem de Sucesso */}
      {showSuccessMessage && (
        <div className="fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center space-x-2">
          <ArrowDown className="w-5 h-5" />
          <span>Operação realizada com sucesso!</span>
        </div>
      )}
    </div>
  );
}


