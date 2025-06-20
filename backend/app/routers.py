# FastAPIのルーティングを定義するファイル
from fastapi import APIRouter, Depends, FastAPI, Request, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from . import schemas
from . import services
from app.models import User, SwipeHistory, PlaylistHistory
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.status import HTTP_401_UNAUTHORIZED
from datetime import timedelta
import random, json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
from app.core.config import settings
from openai import OpenAI

# OpenAIクライアント
openai_client = OpenAI(api_key=settings.API_KEY)

# APIRouterインスタンスを作成（ルーティングを管理する）
router = APIRouter()

# データ読み込み（起動時一度だけ）
with open("data/filtered_songs_4_or_more_tags.json", encoding="utf-8") as f:
    SONGS = json.load(f)
with open("data/mood_similarity.json", encoding="utf-8") as f:
    MOOD_SIMILARITY = json.load(f)
with open("data/mood_instrument_similarity.json", encoding="utf-8") as f:
    MOOD_INST_SIMILARITY = json.load(f)

# 画像からムードを推定する関数
def estimate_mood_from_image(image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:image/jpeg;base64,{encoded}"

    response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像の雰囲気を一つだけ選んで。選択肢：" + ", ".join(MOOD_SIMILARITY.keys())},
                    {"type": "image_url", "image_url": {"url": image_data_url}}
                ]
            }
        ],
        max_tokens=20,
    )
    return response.choices[0].message.content.strip().lower()

# ルート
@router.get("/")
def get_root():
    return {"message": "接続成功"}

# サインアップ
@router.post("/signup", response_model=schemas.Token)
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """新しいユーザーを作成して登録するエンドポイント。

    指定されたメールアドレスが既に登録されている場合は、409 Conflict エラーを返す。
    そうでなければパスワードをハッシュ化し、データベースに新しいユーザーを保存する。
    登録成功後、JWTトークンを発行して返却。

    Args:
        user_data (schemas.UserCreate): リクエストボディで受け取るユーザー情報（email, password）。
        db (Session): データベースセッション（依存性注入によって取得）。

    Returns:
        dict: access_token と token_type を含む辞書。
    """

    user = db.query(User).filter(User.email == user_data.email).first()
    # ユーザーが既に存在する場合は409エラーを返す
    if user:
        raise HTTPException(status_code=409, detail="メールアドレスは既に使用されています")
    # パスワードをハッシュ化してUserインスタンス作成
    signedup_user = User(
        email=user_data.email,
        hashed_password=services.get_password_hash(user_data.password)
    )
    # DBに保存
    db.add(signedup_user)
    db.commit()
    db.refresh(signedup_user)
   
    # トークンの有効期限を15分に設定
    access_token_expires = timedelta(minutes=15)
    # JWTトークンを生成（"sub"クレームにemailを含める）
    access_token = services.create_access_token(
        data={"sub": signedup_user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ログイン
@router.post("/login", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """ログイン処理を行い、有効なクレデンシャルに対してJWTトークンを発行する。

    フォームから送信されたユーザー名（email）とパスワードを検証し、
    有効な場合は15分間有効なアクセストークン（JWT）を返す。

    Args:
        db (Session): データベースセッション。
        form_data (OAuth2PasswordRequestForm): フォームデータ（username, password）。

    Returns:
        dict: アクセストークンとトークンタイプ（bearer）を含む辞書。

    Raises:
        HTTPException: 認証に失敗した場合は401エラー。
    """
    # ユーザー名（メール）とパスワードを使って認証
    print("form_data.username:", form_data.username)
    user = services.authenticate_user(db, form_data.username, form_data.password)
    print("DBから取得したuser:", user)
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # トークンの有効期限を15分に設定
    access_token_expires = timedelta(minutes=15)
    # JWTトークンを生成（"sub"クレームにemailを含める）
    access_token = services.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

