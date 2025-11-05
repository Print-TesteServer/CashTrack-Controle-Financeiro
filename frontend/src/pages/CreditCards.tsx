import { useEffect, useState } from 'react';
import { creditCardService } from '../services/api';
import type { CreditCard } from '../types';
import { Plus, Trash2, Edit, DollarSign, RefreshCw } from 'lucide-react';
import { parseBrazilianCurrency, formatCurrency, formatForInput, handleInputChange } from '../utils/currency';

export default function CreditCards() {
  const [cards, setCards] = useState<CreditCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingCard, setEditingCard] = useState<CreditCard | null>(null);
  const [showPayModal, setShowPayModal] = useState(false);
  const [payingCard, setPayingCard] = useState<CreditCard | null>(null);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentError, setPaymentError] = useState('');
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    limit: '',
    due_date: '',
    closing_date: '',
  });

  useEffect(() => {
    loadCards();
  }, []);

  const loadCards = async () => {
    try {
      const data = await creditCardService.getAll();
      setCards(data);
    } catch (error) {
      console.error('Error loading credit cards:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const limitValue = parseBrazilianCurrency(formData.limit);
      
      if (editingCard) {
        await creditCardService.update(editingCard.id, {
          ...formData,
          limit: limitValue,
          due_date: parseInt(formData.due_date),
          closing_date: parseInt(formData.closing_date),
        });
      } else {
        await creditCardService.create({
          ...formData,
          limit: limitValue,
          due_date: parseInt(formData.due_date),
          closing_date: parseInt(formData.closing_date),
        });
      }
      await loadCards();
      resetForm();
    } catch (error) {
      console.error('Error saving credit card:', error);
      alert('Erro ao salvar cartão');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir este cartão?')) return;
    try {
      await creditCardService.delete(id);
      await loadCards();
    } catch (error) {
      console.error('Error deleting credit card:', error);
      alert('Erro ao excluir cartão');
    }
  };

  const handleEdit = (card: CreditCard) => {
    setEditingCard(card);
    setFormData({
      name: card.name,
      limit: formatForInput(card.limit),
      due_date: card.due_date.toString(),
      closing_date: card.closing_date.toString(),
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      limit: '',
      due_date: '',
      closing_date: '',
    });
    setEditingCard(null);
    setShowForm(false);
  };

  const getUsagePercentage = (card: CreditCard) => {
    return (card.current_balance / card.limit) * 100;
  };

  const handlePayBill = (card: CreditCard) => {
    setPayingCard(card);
    setPaymentAmount('');
    setPaymentError('');
    setShowPayModal(true);
  };

  const handleSubmitPayment = async () => {
    if (!payingCard) return;
    
    setPaymentError('');
    
    if (!paymentAmount || paymentAmount.trim() === '') {
      setPaymentError('Por favor, informe o valor pago');
      return;
    }
    
    try {
      const amount = parseBrazilianCurrency(paymentAmount);
      if (amount <= 0) {
        setPaymentError('Valor deve ser maior que zero');
        return;
      }
      
      if (amount > payingCard.current_balance) {
        setPaymentError('Valor não pode ser maior que o saldo atual');
        return;
      }
      
      await creditCardService.payBill(payingCard.id, amount);
      await loadCards();
      setShowPayModal(false);
      setShowSuccessMessage(true);
      setTimeout(() => setShowSuccessMessage(false), 3000);
    } catch (error) {
      console.error('Error paying bill:', error);
      setPaymentError('Erro ao registrar pagamento. Tente novamente.');
    }
  };

  const handleClosePayModal = () => {
    setShowPayModal(false);
    setPayingCard(null);
    setPaymentAmount('');
    setPaymentError('');
  };

  const handleRecalculateBalance = async (cardId: string) => {
    if (!confirm('Recalcular o saldo baseado em todas as transações deste cartão?')) return;
    
    try {
      await creditCardService.recalculateBalance(cardId);
      await loadCards();
      alert('Saldo recalculado com sucesso!');
    } catch (error) {
      console.error('Error recalculating balance:', error);
      alert('Erro ao recalcular saldo');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Carregando...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Cartões de Crédito</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          <span>Novo Cartão</span>
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            {editingCard ? 'Editar Cartão' : 'Novo Cartão'}
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Limite</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={formData.limit}
                  onChange={(e) => {
                    const processed = handleInputChange(e.target.value);
                    setFormData({ ...formData, limit: processed });
                  }}
                  placeholder="0,00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Use vírgula para decimais (ex: 5.000,00)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dia de Vencimento
                </label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dia de Fechamento
                </label>
                <input
                  type="number"
                  min="1"
                  max="31"
                  value={formData.closing_date}
                  onChange={(e) => setFormData({ ...formData, closing_date: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>
            </div>

            <div className="flex space-x-2">
              <button
                type="submit"
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
              >
                {editingCard ? 'Atualizar' : 'Salvar'}
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
        {cards.map((card) => {
          const usagePercentage = getUsagePercentage(card);
          const available = card.limit - card.current_balance;

          return (
            <div key={card.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold text-gray-800">{card.name}</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleEdit(card)}
                    className="text-primary-600 hover:text-primary-900"
                    title="Editar cartão"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(card.id)}
                    className="text-red-600 hover:text-red-900"
                    title="Excluir cartão"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleRecalculateBalance(card.id)}
                    className="text-blue-600 hover:text-blue-900"
                    title="Recalcular saldo"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Limite</span>
                    <span>{formatCurrency(card.limit)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        usagePercentage >= 90
                          ? 'bg-red-600'
                          : usagePercentage >= 70
                          ? 'bg-yellow-500'
                          : 'bg-green-600'
                      }`}
                      style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>Usado: {usagePercentage.toFixed(1)}%</span>
                    <span>Disponível: {formatCurrency(available)}</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Saldo Atual:</span>
                    <span className="font-semibold text-gray-800">
                      {formatCurrency(card.current_balance)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-gray-600">Vencimento:</span>
                    <span className="text-gray-800">Dia {card.due_date}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-2">
                    <span className="text-gray-600">Fechamento:</span>
                    <span className="text-gray-800">Dia {card.closing_date}</span>
                  </div>
                  {card.current_balance > 0 && (
                    <button
                      onClick={() => handlePayBill(card)}
                      className="w-full mt-3 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center justify-center space-x-2"
                    >
                      <DollarSign className="w-4 h-4" />
                      <span>Registrar Pagamento</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {cards.length === 0 && (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          Nenhum cartão cadastrado
        </div>
      )}

      {/* Modal de Registro de Pagamento */}
      {showPayModal && payingCard && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleClosePayModal}
        >
          <div 
            className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-gray-800 mb-4">
              Registrar Pagamento
            </h2>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Cartão:</p>
              <p className="font-semibold text-gray-800">{payingCard.name}</p>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">Saldo Atual:</p>
              <p className="text-lg font-bold text-gray-800">
                {formatCurrency(payingCard.current_balance)}
              </p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valor Pago
              </label>
              <input
                type="text"
                inputMode="decimal"
                value={paymentAmount}
                onChange={(e) => {
                  const processed = handleInputChange(e.target.value);
                  setPaymentAmount(processed);
                  setPaymentError('');
                }}
                placeholder="0,00"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSubmitPayment();
                  } else if (e.key === 'Escape') {
                    handleClosePayModal();
                  }
                }}
              />
              <p className="text-xs text-gray-500 mt-1">Use vírgula para decimais (ex: 500,00)</p>
              {paymentError && (
                <p className="text-xs text-red-600 mt-1">{paymentError}</p>
              )}
            </div>

            <div className="flex space-x-2">
              <button
                onClick={handleSubmitPayment}
                className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
              >
                Confirmar
              </button>
              <button
                onClick={handleClosePayModal}
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
          <DollarSign className="w-5 h-5" />
          <span>Pagamento registrado com sucesso!</span>
        </div>
      )}
    </div>
  );
}


