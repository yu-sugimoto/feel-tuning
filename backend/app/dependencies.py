# FastAPIの依存関係を定義するファイル
from typing import Generator
from app.database import SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from . import services

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# DB接続を行うジェネレータ関数
def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
   return services.decode_access_token(db, token)