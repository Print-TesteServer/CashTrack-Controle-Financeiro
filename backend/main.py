from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transactions, analytics, credit_cards, savings, ml, ai
from app.middleware import OptionalAPIKeyMiddleware
from app.rate_limit_middleware import AIRateLimitMiddleware
from app.database import engine, Base
import sqlite3
import os

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


