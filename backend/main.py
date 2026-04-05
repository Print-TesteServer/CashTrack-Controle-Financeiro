"""API Controle Financeiro — carrega .env antes de qualquer uso de variáveis de ambiente."""
import os
import shutil
import sqlite3
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _BACKEND_DIR.parent

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def _ensure_backend_env_file() -> None:
    """Cria backend/.env a partir do exemplo se ainda não existir (facilita configurar GEMINI_API_KEY)."""
    env_path = _BACKEND_DIR / ".env"
    example = _BACKEND_DIR / ".env.example"
    if env_path.exists():
        return
    if not example.exists():
        return
    try:
        shutil.copyfile(example, env_path)
        print(
            "[INFO] Criado backend/.env a partir de .env.example. "
            "Abra esse arquivo, preencha GEMINI_API_KEY e reinicie o servidor para usar /api/ai/*."
        )
    except OSError as exc:
        print(f"[AVISO] Nao foi possivel criar backend/.env: {exc}")


def _load_env_files() -> None:
    if load_dotenv is None:
        print("[AVISO] Pacote python-dotenv nao encontrado. Execute: pip install -r requirements.txt")
        return
    # Raiz do monorepo (alguns ambientes colocam .env na pasta do repositório)
    load_dotenv(_ROOT_DIR / ".env", override=False, encoding="utf-8")
    # Preferência: backend/.env sobrescreve chaves vindas da raiz
    load_dotenv(_BACKEND_DIR / ".env", override=True, encoding="utf-8")


_ensure_backend_env_file()
_load_env_files()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, analytics, credit_cards, ml, savings, transactions
from app.database import Base, engine
from app.middleware import OptionalAPIKeyMiddleware
from app.rate_limit_middleware import AIRateLimitMiddleware

# Criar tabelas
Base.metadata.create_all(bind=engine)

# Migrações: adicionar colunas se não existirem
DB_PATH = "./finance.db"
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Migração: adicionar coluna credit_card_id na tabela transactions
        try:
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'credit_card_id' not in columns:
                print("Adicionando coluna credit_card_id à tabela transactions...")
                cursor.execute("ALTER TABLE transactions ADD COLUMN credit_card_id TEXT")
                conn.commit()
                print("[OK] Coluna credit_card_id adicionada com sucesso!")
        except Exception as e:
            print(f"Erro ao adicionar credit_card_id: {e}")
        
        # Migração: adicionar colunas na tabela savings
        try:
            cursor.execute("PRAGMA table_info(savings)")
            savings_columns = [column[1] for column in cursor.fetchall()]
            print(f"Colunas existentes na tabela savings: {savings_columns}")
            
            if 'institution' not in savings_columns:
                print("Adicionando coluna institution à tabela savings...")
                cursor.execute("ALTER TABLE savings ADD COLUMN institution TEXT")
                conn.commit()
                print("[OK] Coluna institution adicionada com sucesso!")
            else:
                print("[OK] Coluna institution já existe")
            
            if 'cdi_percentage' not in savings_columns:
                print("Adicionando coluna cdi_percentage à tabela savings...")
                cursor.execute("ALTER TABLE savings ADD COLUMN cdi_percentage REAL")
                conn.commit()
                print("[OK] Coluna cdi_percentage adicionada com sucesso!")
            else:
                print("[OK] Coluna cdi_percentage já existe")
            
            if 'last_yield_calculation' not in savings_columns:
                print("Adicionando coluna last_yield_calculation à tabela savings...")
                cursor.execute("ALTER TABLE savings ADD COLUMN last_yield_calculation DATETIME")
                conn.commit()
                print("[OK] Coluna last_yield_calculation adicionada com sucesso!")
            else:
                print("[OK] Coluna last_yield_calculation já existe")
        except Exception as e:
            print(f"Erro ao adicionar colunas na tabela savings: {e}")
            import traceback
            traceback.print_exc()
        
        conn.close()
        print("Migrações concluídas!")
    except Exception as e:
        print(f"Erro ao executar migração: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Banco de dados não encontrado em {DB_PATH}. Será criado automaticamente.")

app = FastAPI(title="Controle Financeiro API", version="1.0.0")

if not os.getenv("GEMINI_API_KEY", "").strip():
    print(
        "[AVISO] GEMINI_API_KEY vazia ou ausente — POST /api/ai/* retornara 503 ate configurar.\n"
        f"         Edite: {_BACKEND_DIR / '.env'}  (cole sua chave apos GEMINI_API_KEY= e salve; reinicie o backend.)"
    )

# CORS
# API key primeiro (inner), CORS por último (outermost) — preflight e headers corretos
app.add_middleware(OptionalAPIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Ultimo adicionado = mais externo: limita /api/ai antes de outras camadas
app.add_middleware(AIRateLimitMiddleware)

# Rotas
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(credit_cards.router, prefix="/api/credit-cards", tags=["credit-cards"])
app.include_router(savings.router, prefix="/api/savings", tags=["savings"])
app.include_router(ml.router, prefix="/api/ml", tags=["ml"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

@app.get("/")
def root():
    return {"message": "Controle Financeiro API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


