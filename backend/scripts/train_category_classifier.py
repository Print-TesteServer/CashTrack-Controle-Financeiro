"""Treina o classificador de categoria a partir do banco e salva em app/ml/artifacts/."""

import os
import sys

# Diretório backend (pai de scripts/)
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app.database import SessionLocal  # noqa: E402
from app.ml.category_classifier import train_and_persist  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        meta = train_and_persist(db)
        print("Treinamento concluido:", meta)
    except ValueError as e:
        print("Erro:", e)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
