# 💰 Controle Financeiro

Sistema completo de controle financeiro pessoal com análise de dados usando Python e interface moderna com React.

## 🚀 Funcionalidades

- **Transações**: Gerenciamento completo de receitas e despesas
- **Cartões de Crédito**: Controle de limites, faturas e vencimentos
- **Cofrinhos**: Acompanhamento de metas de poupança
- **Dashboard**: Visão geral do seu financeiro
- **Análises Avançadas**: Gráficos e estatísticas usando Python (Pandas, NumPy)

## 🛠️ Tecnologias

### Backend (Python)
- FastAPI - Framework web moderno e rápido
- SQLAlchemy - ORM para banco de dados
- Pandas - Análise de dados
- NumPy - Cálculos numéricos
- SQLite - Banco de dados (pode ser migrado para PostgreSQL)

### Frontend (React)
- React + TypeScript
- Vite - Build tool
- TailwindCSS - Estilização
- Recharts - Gráficos
- React Router - Navegação
- Axios - Comunicação com API

## 📋 Pré-requisitos

- Python 3.9+
- Node.js 18+
- npm ou yarn

## 🚀 Instalação e Início Rápido

### Instalação Completa

```bash
# 1. Instalar dependências do projeto (concurrently)
npm install

# 2. Configurar Backend (Python)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cd ..

# 3. Instalar dependências do Frontend
cd frontend
npm install
cd ..
```

### 🎯 Iniciar Aplicação (Um Único Comando!)

**Opção 1: Usando npm (Recomendado)**
```bash
npm start
```

**Opção 2: Usando Script PowerShell**
```powershell
.\start.ps1
```

**Opção 3: Usando Script Batch (Windows)**
```cmd
start.bat
```

**Opção 4: Manualmente (se necessário)**
```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 📍 URLs após iniciar:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs

## 📚 Documentação da API

Com o backend rodando, acesse:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🎯 Endpoints Principais

### Transações
- `GET /api/transactions/` - Listar transações
- `POST /api/transactions/` - Criar transação
- `GET /api/transactions/{id}` - Obter transação
- `PUT /api/transactions/{id}` - Atualizar transação
- `DELETE /api/transactions/{id}` - Excluir transação

### Cartões de Crédito
- `GET /api/credit-cards/` - Listar cartões
- `POST /api/credit-cards/` - Criar cartão
- `PUT /api/credit-cards/{id}` - Atualizar cartão
- `DELETE /api/credit-cards/{id}` - Excluir cartão

### Cofrinhos
- `GET /api/savings/` - Listar cofrinhos
- `POST /api/savings/` - Criar cofrinho
- `PUT /api/savings/{id}` - Atualizar cofrinho
- `DELETE /api/savings/{id}` - Excluir cofrinho

### Análises
- `GET /api/analytics/expenses/categories` - Gastos por categoria
- `GET /api/analytics/income/categories` - Receitas por categoria
- `GET /api/analytics/trends/monthly` - Tendências mensais
- `GET /api/analytics/chart/expenses` - Dados para gráfico de gastos
- `GET /api/analytics/chart/income` - Dados para gráfico de receitas
- `GET /api/analytics/chart/trends` - Dados para gráfico de tendências
- `GET /api/analytics/summary` - Estatísticas resumidas

## 📁 Estrutura do Projeto

```
Controle-Financeiro/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints da API
│   │   ├── models.py      # Modelos de banco de dados
│   │   ├── schemas.py     # Schemas Pydantic
│   │   ├── database.py    # Configuração do banco
│   │   └── services/      # Serviços de análise
│   ├── main.py            # Aplicação FastAPI
│   └── requirements.txt    # Dependências Python
│
├── frontend/
│   ├── src/
│   │   ├── pages/         # Páginas do app
│   │   ├── services/      # Serviços de API
│   │   ├── types/        # Tipos TypeScript
│   │   └── App.tsx       # Componente principal
│   └── package.json       # Dependências Node
│
└── README.md
```

## 🎨 Páginas do Frontend

1. **Dashboard** (`/`) - Visão geral com resumo financeiro e gráficos principais
2. **Transações** (`/transactions`) - Gerenciamento de receitas e despesas
3. **Cartões** (`/credit-cards`) - Controle de cartões de crédito
4. **Cofrinhos** (`/savings`) - Acompanhamento de metas de poupança
5. **Análises** (`/analytics`) - Gráficos detalhados e análises avançadas

## 💡 Como Usar

1. **Inicie a aplicação**: Execute `npm start` na raiz do projeto (ou use `.\start.ps1` / `start.bat`)
2. **Aguarde alguns segundos** para ambos os servidores iniciarem
3. **Acesse o app**: Abra `http://localhost:5173` no navegador
4. **Comece a usar**: Cadastre transações, cartões e cofrinhos!

**Dica**: Para parar ambos os servidores, pressione `Ctrl+C` no terminal onde executou o comando.

## 📊 Análises com Python

O backend utiliza Python para análises avançadas:
- Agrupamento por categoria usando Pandas
- Cálculos de tendências e médias
- Geração de dados para gráficos
- Análise temporal de receitas e despesas
- Estatísticas descritivas

## 🔧 Configuração Avançada

### Alterar Banco de Dados

Para usar PostgreSQL ao invés de SQLite, edite `backend/app/database.py`:

```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### Configurar CORS

Para permitir outras origens, edite `backend/main.py`:

```python
allow_origins=["http://localhost:5173", "http://seu-dominio.com"]
```

## 📝 Licença

Este projeto é open source e está disponível sob a licença MIT.

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 📧 Suporte

Para dúvidas ou problemas, abra uma issue no repositório.


