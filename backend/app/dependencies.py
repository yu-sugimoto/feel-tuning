# FastAPIの依存関係を定義するファイル
from typing import Generator
from app.database import SessionLocal

# DB接続を行うジェネレータ関数
def get_db() -> Generator:

    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()