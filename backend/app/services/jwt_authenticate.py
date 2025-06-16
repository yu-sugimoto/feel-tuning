import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED
from app.models import User
from app import schemas

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
 
def create_access_token(*, data: dict, expires_delta: timedelta = None):
    """JWTトークンを生成する関数。
    
    Args:
        data (dict): トークンに含めるデータ（通常はユーザーの識別情報）。
        expires_delta (timedelta, optional): トークンの有効期限。指定しない場合は15分。
    Returns:
        str: 生成されたJWTトークン。
    """
    # データのコピーを作成
    to_encode = data.copy()
    # 現在時刻（UTC）に有効期限を加える（デフォルトは15分）
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    # 有効期限（exp）をペイロードに追加
    to_encode.update({"exp": expire})
    # JWTをエンコードして返す
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(db, token):
    """JWTアクセストークンをデコードして、対応するユーザーを取得する。
    
    トークンの署名と有効期限を検証し、内部に含まれる `sub`（email） を元にデータベースからユーザー情報を取得する。
    
    Args:
        db (Session): データベースセッション。
        token (str): アクセストークン（JWT形式）。
    
    Returns:
        User: デコードされたトークンの `email` に該当するユーザーオブジェクト。
    
    Raises:
        HTTPException: トークンが不正またはユーザーが存在しない場合に401エラー。
    """
    # 認証エラー時に共通で使う例外を定義
    credentials_exception = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # JWTトークンをデコード（署名と期限を検証）
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # トークンの "sub" クレーム（＝ユーザー識別子）を取得
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # Emailの形式チェックを含む型バリデーション
        token_data = schemas.TokenData(email=email)
    except PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email ==  token_data.email).first()
    if user is None:
        raise credentials_exception
    return user