import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import CreditCards from './pages/CreditCards';
import Savings from './pages/Savings';
import { Home, DollarSign, CreditCard, PiggyBank, BarChart3 } from 'lucide-react';

// Lazy load Analytics para reduzir o bundle inicial (Recharts é muito pesado)
const Analytics = lazy(() => import('./pages/Analytics'));

function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/transactions', icon: DollarSign, label: 'Transações' },
    { path: '/credit-cards', icon: CreditCard, label: 'Cartões' },
    { path: '/savings', icon: PiggyBank, label: 'Cofrinhos' },
    { path: '/analytics', icon: BarChart3, label: 'Análises' },
  ];

  return (
    <nav className="bg-gray-800 text-white">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-8 h-8" />
            <h1 className="text-xl font-bold">Controle Financeiro</h1>
          </div>
          <div className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Suspense fallback={<div className="text-center py-8">Carregando...</div>}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/transactions" element={<Transactions />} />
              <Route path="/credit-cards" element={<CreditCards />} />
              <Route path="/savings" element={<Savings />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </Router>
  );
}

export default App;


