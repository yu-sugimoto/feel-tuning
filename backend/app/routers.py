# FastAPIのルーティングを定義するファイル
from fastapi import APIRouter, Depends, FastAPI, Request, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from . import schemas
from . import services
from app.models import User, Song, SwipeHistory
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.status import HTTP_401_UNAUTHORIZED
from datetime import timedelta
import random

# APIRouterインスタンスを作成（ルーティングを管理する）
router = APIRouter()

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

# ホーム（スワイプ画面）
@router.get("/swipe" , response_model=schemas.SongRead)
def swipe(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """スワイプ用の推薦楽曲を1件返す。

    ユーザーが過去にスワイプした曲を除外し、ランダムに1曲を推薦する。（本来は推薦アルゴリズムを使用）
    スワイプ可能な曲がない場合は404エラーを返す。
    
    Args:
        request (Request): リクエストオブジェクト。
        db (Session): データベースセッション（依存性注入によって取得）。
        current_user (User): 現在の認証ユーザー（依存性注入によって取得）。
    Returns:
        schemas.SwipeResponse: 推薦楽曲の情報を含むレスポンスモデル。
    Raises:
        HTTPException: スワイプ可能な曲がない場合は404エラー。
    """
    # 過去にスワイプした曲のIDを取得
    swiped_song_ids = db.query(SwipeHistory.song_id).filter(SwipeHistory.user_id == current_user.id).all()
    swiped_song_ids = [row[0] for row in swiped_song_ids]

    # スワイプしていない曲を取得
    candidate_songs = db.query(Song).filter(~Song.id.in_(swiped_song_ids)).all()

    if not candidate_songs:
        raise HTTPException(status_code=404, detail="スワイプ可能な曲がありません")

    # ランダムに1曲推薦（本来は推薦アルゴリズムを使用）
    song = random.choice(candidate_songs)

    return schemas.SongRead(
        id=song.id,
        title=song.title,
        artist=song.artist,
        preview_url=song.preview_url,
        genre=song.genre
    )