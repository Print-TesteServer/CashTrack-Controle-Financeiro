import { useEffect, useState } from 'react';
import { transactionService, creditCardService } from '../services/api';
import type { Transaction, CreditCard } from '../types';
import { Plus, Trash2, Edit } from 'lucide-react';
import { format } from 'date-fns';
import { parseBrazilianCurrency, formatCurrency, formatForInput, handleInputChange } from '../utils/currency';

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [creditCards, setCreditCards] = useState<CreditCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);

  const [formData, setFormData] = useState({
    type: 'expense' as 'income' | 'expense',
    category: '',
    amount: '',
    description: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    payment_method: 'cash' as 'cash' | 'credit' | 'debit' | 'pix',
    credit_card_id: '',
  });

  useEffect(() => {
    loadTransactions();
    loadCreditCards();
  }, []);

  const loadTransactions = async () => {
    try {
      const data = await transactionService.getAll();
      setTransactions(data);
    } catch (error) {
      console.error('Error loading transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCreditCards = async () => {
    try {
      const cards = await creditCardService.getAll();
      setCreditCards(cards);
    } catch (error) {
      console.error('Error loading credit cards:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Converte valor do formato brasileiro para número
      const amountValue = parseBrazilianCurrency(formData.amount);
      
      // Prepara dados da transação
      const transactionData: any = {
        ...formData,
        amount: amountValue,
      };
      
      // Se não for cartão de crédito, remove credit_card_id
      if (formData.payment_method !== 'credit') {
        transactionData.credit_card_id = undefined;
      } else if (!formData.credit_card_id) {
        alert('Selecione um cartão de crédito');
        return;
      }
      
      if (editingTransaction) {
        await transactionService.update(editingTransaction.id, transactionData);
      } else {
        await transactionService.create(transactionData);
      }
      await loadTransactions();
      await loadCreditCards(); // Recarrega cartões para atualizar saldos
      resetForm();
    } catch (error) {
      console.error('Error saving transaction:', error);
      alert('Erro ao salvar transação');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Tem certeza que deseja excluir esta transação?')) return;
    try {
      await transactionService.delete(id);
      await loadTransactions();
      await loadCreditCards(); // Recarrega cartões para atualizar saldos
    } catch (error) {
      console.error('Error deleting transaction:', error);
      alert('Erro ao excluir transação');
    }
  };

  const handleEdit = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setFormData({
      type: transaction.type,
      category: transaction.category,
      amount: formatForInput(transaction.amount),
      description: transaction.description || '',
      date: format(new Date(transaction.date), 'yyyy-MM-dd'),
      payment_method: transaction.payment_method,
      credit_card_id: transaction.credit_card_id || '',
    });
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      type: 'expense',
      category: '',
      amount: '',
      description: '',
      date: format(new Date(), 'yyyy-MM-dd'),
      payment_method: 'cash',
      credit_card_id: '',
    });
    setEditingTransaction(null);
    setShowForm(false);
  };

  if (loading) {
    return <div className="text-center py-8">Carregando...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-800">Transações</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-5 h-5" />
          <span>Nova Transação</span>
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">
            {editingTransaction ? 'Editar Transação' : 'Nova Transação'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4" key={editingTransaction?.id || 'new'}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                <select
                  value={formData.type}
                  onChange={(e) =>
                    setFormData({ ...formData, type: e.target.value as 'income' | 'expense' })
                  }
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="expense">Despesa</option>
                  <option value="income">Receita</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
                <input
                  type="text"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Valor</label>
                <input
                  type="text"
                  inputMode="decimal"
                  value={formData.amount}
                  onChange={(e) => {
                    const processed = handleInputChange(e.target.value);
                    setFormData({ ...formData, amount: processed });
                  }}
                  placeholder="0,00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Use vírgula para decimais (ex: 5.111,96)</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Método de Pagamento
                </label>
                <select
                  value={formData.payment_method}
                  onChange={(e) => {
                    const newMethod = e.target.value as 'cash' | 'credit' | 'debit' | 'pix';
                    setFormData({
                      ...formData,
                      payment_method: newMethod,
                      credit_card_id: newMethod !== 'credit' ? '' : formData.credit_card_id,
                    });
                  }}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="cash">Dinheiro</option>
                  <option value="credit">Cartão de Crédito</option>
                  <option value="debit">Cartão de Débito</option>
                  <option value="pix">PIX</option>
                </select>
              </div>

              {formData.payment_method === 'credit' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cartão de Crédito
                  </label>
                  <select
                    value={formData.credit_card_id}
                    onChange={(e) => setFormData({ ...formData, credit_card_id: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    required={formData.payment_method === 'credit'}
                  >
                    <option value="">Selecione um cartão</option>
                    {creditCards.map((card) => {
                      const available = card.limit - card.current_balance;
                      return (
                        <option key={card.id} value={card.id}>
                          {card.name} - Limite: {formatCurrency(card.limit)} (Disponível: {formatCurrency(available)})
                        </option>
                      );
                    })}
                  </select>
                  {creditCards.length === 0 && (
                    <p className="text-xs text-yellow-600 mt-1">
                      Nenhum cartão cadastrado. Cadastre um cartão primeiro.
                    </p>
                  )}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>
            </div>

            <div className="flex space-x-2">
              <button
                type="submit"
                className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
              >
                {editingTransaction ? 'Atualizar' : 'Salvar'}
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

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Data
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Descrição
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Categoria
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Valor
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Método
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {format(new Date(transaction.date), 'dd/MM/yyyy')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {transaction.description || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {transaction.category}
                  </td>
                  <td
                    className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                      transaction.type === 'income' ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {transaction.type === 'income' ? '+' : '-'} {formatCurrency(transaction.amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {transaction.payment_method === 'cash' && 'Dinheiro'}
                    {transaction.payment_method === 'credit' && (
                      <span>
                        Crédito
                        {transaction.credit_card_id && creditCards.length > 0 && (
                          <span className="text-xs text-gray-400 ml-1">
                            ({creditCards.find(c => c.id === transaction.credit_card_id)?.name || 'N/A'})
                          </span>
                        )}
                      </span>
                    )}
                    {transaction.payment_method === 'debit' && 'Débito'}
                    {transaction.payment_method === 'pix' && 'PIX'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleEdit(transaction)}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(transaction.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {transactions.length === 0 && (
          <div className="text-center py-8 text-gray-500">Nenhuma transação cadastrada</div>
        )}
      </div>
    </div>
  );
}


