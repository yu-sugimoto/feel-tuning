# FastAPIのルーティングを定義するファイル
from fastapi import APIRouter, Depends, FastAPI, Request, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from . import schemas
from . import services
from app.models import User, SwipeHistory, PlaylistHistory, PhotoUpload
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

# 初期楽曲を返す
@router.post("/photo", response_model=schemas.SwipeInitResponse)
def swipe_init(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    image_bytes = file.file.read()
    main_mood = estimate_mood_from_image(image_bytes)
    if main_mood not in MOOD_SIMILARITY:
        raise HTTPException(status_code=400, detail=f"'{main_mood}' は不正な雰囲気です")

    moods = MOOD_SIMILARITY.get(main_mood, [])[:3]
    selected = []
    for mood in moods:
        candidates = [s for s in SONGS if mood in s["tags"] and s["id"] not in selected]
        if candidates:
            chosen = random.choice(candidates)
            selected.append(chosen["id"])

    songs = [s for s in SONGS if s["id"] in selected]
    return {"songs": songs}

# スワイプ結果を記録・次の曲を返す
@router.post("/swipe", response_model=schemas.SwipeResponse)
def swipe(swipe: schemas.SwipeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.add(SwipeHistory(user_id=current_user.id, song_id=swipe.song_id, liked=swipe.liked))
    db.commit()

    swiped_ids = [s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id).all()]
    liked_ids = [s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id, liked=True).all()]
    liked_songs = [s for s in SONGS if s["id"] in liked_ids]

    if len(liked_songs) < 3:
        # 雰囲気探索フェーズ
        liked_moods = {tag for song in liked_songs for tag in song["tags"]}
        exclude_moods = {tag for song in SONGS if song["id"] in swiped_ids for tag in song["tags"]}
        next_moods = sorted(set(MOOD_SIMILARITY.keys()) - exclude_moods, key=lambda x: -len(MOOD_SIMILARITY.get(x, [])))
        for mood in next_moods:
            candidates = [s for s in SONGS if mood in s["tags"] and s["id"] not in swiped_ids]
            if candidates:
                return {"song": random.choice(candidates)}

    elif len(liked_songs) < 5:
        # 楽器探索フェーズ
        liked_moods = [tag for song in liked_songs for tag in song["tags"]]
        counter = {}
        for mood in liked_moods:
            for inst, score in MOOD_INST_SIMILARITY.get(mood, {}).items():
                counter[inst] = counter.get(inst, 0) + score
        sorted_instruments = sorted(counter.items(), key=lambda x: -x[1])
        top_instruments = [inst for inst, _ in sorted_instruments[:2]]
        for song in SONGS:
            if song["id"] in swiped_ids:
                continue
            if any(inst in song["tags"] for inst in top_instruments):
                return {"song": song}

    raise HTTPException(status_code=404, detail="スワイプ候補なし")

@router.get("/playlist", response_model=schemas.PlaylistResponse)
def generate_playlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    liked_ids = [s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id, liked=True).all()]
    liked_songs = [s for s in SONGS if s["id"] in liked_ids]
    if len(liked_songs) < 5:
        raise HTTPException(status_code=400, detail="まだ十分なLikeがありません")

    # 好みの雰囲気3つ、楽器2つを取得
    mood_counter = {}
    inst_counter = {}
    for s in liked_songs:
        for tag in s["tags"]:
            if tag in MOOD_SIMILARITY:
                mood_counter[tag] = mood_counter.get(tag, 0) + 1
            else:
                inst_counter[tag] = inst_counter.get(tag, 0) + 1
    top_moods = sorted(mood_counter.items(), key=lambda x: -x[1])[:3]
    top_insts = sorted(inst_counter.items(), key=lambda x: -x[1])[:2]
    mood_tags = [m[0] for m in top_moods]
    inst_tags = [i[0] for i in top_insts]

    # 推薦10曲を選定
    candidates = [s for s in SONGS if sum(1 for m in mood_tags if m in s["tags"]) >= 2 and any(i in s["tags"] for i in inst_tags) and s["id"] not in liked_ids]
    recommended = random.sample(candidates, k=min(10, len(candidates)))

    # プレイリストを保存（image_pathは仮に前回アップロードされた画像パスを使う）
    latest_upload = db.query(PhotoUpload).filter_by(user_id=current_user.id).order_by(PhotoUpload.created_at.desc()).first()
    if latest_upload:
        db.add(PlaylistHistory(
            user_id=current_user.id,
            image_path=latest_upload.image_path,
            songs_json=json.dumps(liked_songs + recommended, ensure_ascii=False)
        ))
        db.commit()

    return {"liked": liked_songs, "recommended": recommended}
