# FastAPIの依存関係を定義するファイル
from typing import Generator
from app.database import SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from . import services

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db() -> Generator:
    """DB接続を行うジェネレータ関数
    データベースセッションを生成し、使用後に閉じる。

    Returns:
        Generator: データベースセッションのジェネレータ。
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """現在のユーザーを取得するための依存関係。

    トークンをデコードして、ユーザー情報を取得する。
    トークンが無効な場合はHTTP 401エラーを返す。

    Args:
        db (Session): データベースセッション（依存性注入によって取得）。
        token (str): OAuth2トークン（依存性注入によって取得）。

    Returns:
        User: 認証されたユーザーオブジェクト。
    """
    return services.decode_access_token(db, token)