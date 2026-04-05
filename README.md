# 💰 Controle Financeiro

Sistema completo de controle financeiro pessoal com análise de dados usando Python e interface moderna com React.

## 🚀 Funcionalidades

- **Transações**: Gerenciamento completo de receitas e despesas
- **Cartões de Crédito**: Controle de limites, faturas e vencimentos
- **Cofrinhos**: Acompanhamento de metas de poupança
- **Dashboard**: Visão geral do seu financeiro
- **Análises Avançadas**: Gráficos e estatísticas (Pandas, NumPy)
- **ML aplicado**: previsão de gastos com comparação de modelos (média móvel, tendência linear, **ARIMA**), validação holdout com **MAE/RMSE**
- **Classificação de categorias**: TF-IDF + regressão logística (treino com despesas + descrição), endpoint de inferência
- **Anomalias**: regras com z-score e **Isolation Forest** (sklearn) em agregados mensais por categoria
- **IA generativa**: explicação do panorama financeiro e **consultas em linguagem natural** → plano JSON seguro (sem SQL livre), via **Google Gemini** (API REST)

## 🛠️ Tecnologias

### Backend (Python)
- FastAPI - Framework web moderno e rápido
- SQLAlchemy - ORM para banco de dados
- Pandas - Análise de dados
- NumPy - Cálculos numéricos
- statsmodels - Séries temporais (ARIMA)
- scikit-learn - Classificação de texto e Isolation Forest
- httpx - Chamadas HTTP ao modelo de linguagem (Gemini / Google AI)
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

# Na raiz (usa o Python do venv em backend — recomendado após clonar ou atualizar deps)
npm run install:backend

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
- `GET /api/analytics/forecast-expenses` - Previsão de gastos (modelos + métricas quando há histórico suficiente)
- `GET /api/analytics/anomalies` - Anomalias (`method=zscore` \| `isolation_forest` \| `both`)

### Machine learning (`/api/ml`)
- `POST /api/ml/predict-category` - Sugestão de categoria a partir da descrição (requer modelo treinado)
- `POST /api/ml/train-category-classifier` - Treina e salva o classificador em `app/ml/artifacts/`
- `GET /api/ml/category-model` - Metadados do modelo (accuracy, macro F1, etc.)

### IA (`/api/ai`) — chave só no servidor
- `POST /api/ai/explain` - Texto explicativo com base em **resumos agregados** (totais, categorias, previsão, anomalias)
- `POST /api/ai/query` - Pergunta em PT-BR → JSON estruturado (intents whitelisted) → resposta numérica / ranking

## 🧠 Inteligência aplicada (resumo)

| Área | O que faz | Onde ver |
|------|-----------|----------|
| Séries temporais | Benchmark MA / linear / ARIMA com holdout (12+ meses), MAE/RMSE | `GET .../forecast-expenses`, UI Análises |
| Classificação | Pipeline sklearn (TF-IDF + LogisticRegression), `joblib` | `POST /api/ml/*`, script `backend/scripts/train_category_classifier.py` |
| Anomalias | Z-score + Isolation Forest sobre totais mensais por categoria | `GET .../anomalies?method=...` |
| LLM | Explicação e NL→plano seguro; **não** envia lista de transações brutas ao modelo | `POST /api/ai/explain`, `POST /api/ai/query` |

**Treinar classificador de categorias (CLI):** com despesas com descrição no banco, a partir de `backend/`:

```bash
venv\Scripts\python.exe scripts\train_category_classifier.py
```

Artefatos gerados ficam em `backend/app/ml/artifacts/` (ignorados pelo git por padrão).

## 📁 Estrutura do Projeto

```
Controle-Financeiro/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints da API
│   │   ├── models.py      # Modelos de banco de dados
│   │   ├── schemas.py     # Schemas Pydantic
│   │   ├── database.py    # Configuração do banco
│   │   ├── ml/            # Métricas, previsão, classificador, artefatos (joblib)
│   │   └── services/      # Analytics, ai_insights, nl_query
│   ├── scripts/           # Ex.: treino do classificador de categorias
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

## 📊 Análises e ML com Python

O backend combina analytics clássico (Pandas/NumPy) com:
- Agrupamentos, tendências, gráficos e estatísticas descritivas
- Previsão de gastos com **seleção automática de modelo** e métricas no JSON quando há histórico longo
- Modelos sklearn (classificação de texto, Isolation Forest) e **statsmodels** (ARIMA)
- Camada de IA no servidor: apenas agregados e intents validados entram no prompt ou no plano estruturado

## ⚙️ Variáveis de ambiente

### Backend (`backend/.env` ou variáveis do sistema)

Copie `backend/.env.example` para `backend/.env` se quiser usar arquivo local. O `main.py` carrega `backend/.env` automaticamente ao iniciar (via `python-dotenv`).

| Variável | Descrição |
|----------|-----------|
| `API_KEY` | Opcional. Se definida (não vazia), todas as rotas `/api/*` exigem o header `X-API-Key` com o mesmo valor. |
| `GEMINI_API_KEY` | Opcional. Necessária para `POST /api/ai/explain` e `POST /api/ai/query` (Google AI / Gemini). **Nunca** commite no repositório. Gere em [Google AI Studio](https://aistudio.google.com/apikey). |
| `GEMINI_MODEL` | Opcional. Ex.: `gemini-2.0-flash` (padrão no código). |
| `GEMINI_TIMEOUT_SECONDS` | Opcional. Timeout HTTP para o modelo (padrão 60). |
| `ALLOW_TRAINING_WITHOUT_API_KEY` | Opcional. Padrão `true` (dev): permite `POST /api/ml/train-category-classifier` sem `API_KEY` no servidor. Em produção use `false` e defina `API_KEY` para exigir `X-API-Key`. |
| `AI_RATE_LIMIT_PER_MINUTE` | Opcional. Limite de requisições por IP nas rotas `/api/ai/*` (padrão 40). |
| `AI_RATE_LIMIT_ENABLED` | Opcional. `true`/`false` — ativa o limite acima (padrão `true`). |

### Frontend (`frontend/.env` ou `frontend/.env.local`)

Copie `frontend/.env.example` e ajuste:

| Variável | Descrição |
|----------|-----------|
| `VITE_API_URL` | **Deixe vazio** para desenvolvimento e preview locais: o app chama `/api/...` na mesma origem e o Vite encaminha para o backend. **Defina URL completa** (ex. `https://api.seudominio.com`) quando publicar o front em hospedagem estática **sem** proxy — aí o navegador fala direto com o backend. |
| `VITE_API_KEY` | Opcional. Igual ao `API_KEY` do backend, se você ativou proteção por chave. |
| `VITE_API_PROXY_TARGET` | Opcional. Para onde o Vite envia `/api` no **dev** e no **`vite preview`** (padrão `http://localhost:8000`). Use se o FastAPI não estiver na porta 8000. |

**Resumo:** com backend em `http://localhost:8000` e `npm run dev` (ou `npm run preview` após o build), não precisa configurar `VITE_API_URL`. Se as requisições falharem, confira se o backend está no ar e se `VITE_API_PROXY_TARGET` aponta para ele.

## 🧪 Testes

```bash
cd backend
venv\Scripts\python.exe -m pip install pytest -q   # uma vez, se ainda nao tiver
venv\Scripts\python.exe -m pytest tests/ -q
```

Ou com unittest:

```bash
cd backend
python -m unittest discover -s tests -p "test_*.py" -v
```

Na raiz do projeto também:

```bash
npm run test:backend
```

Relatório estruturado (JSON + TXT em `backend/`):

```bash
cd backend
python tests/run_tests.py
```

## 🔄 CI (GitHub Actions)

O workflow `.github/workflows/ci.yml` roda em push/PR para `main`/`master`: testes Python no `backend` e `npm ci` + `npm run build` no `frontend`.

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


