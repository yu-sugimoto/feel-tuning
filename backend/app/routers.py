# FastAPIのルーティングを定義するファイル
from fastapi import APIRouter, Depends, FastAPI, Request, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from typing import List
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
import logging
from PIL import Image
import io
import re
import difflib
from uuid import uuid4
import os

logger = logging.getLogger(__name__)

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
    """画像のバイナリデータからムードを推定する関数。
    OpenAIのAPIを使って画像の雰囲気を一つだけ選ぶ。
    Args:
        image_bytes (bytes): 画像のバイナリデータ。
    Returns:
        str: 推定されたムード（雰囲気）。
    Raises:
        HTTPException: OpenAI APIの呼び出しに失敗した場合は500エラー。
    """
    # 画像データが空の場合は400エラーを返す
    if not image_bytes:
        raise HTTPException(status_code=400, detail="画像データが空です")
    # JPEGに変換
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgb_image = img.convert("RGB")  # JPEGはRGB形式が必要
            output = io.BytesIO()
            rgb_image.save(output, format="JPEG")
            image_bytes = output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"画像の読み込みまたは変換に失敗しました: {str(e)}")

    # Base64エンコードして Data URL を作成（prefixはここだけ）
    try:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像データのエンコードに失敗しました: {str(e)}")

    # OpenAI APIを使ってムードを推定
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "次の画像を見て、以下の選択肢の中から、最もふさわしいムードを1つだけ選び、その単語だけを小文字で出力してください。理由や説明は不要です。選択肢：" + ", ".join(MOOD_SIMILARITY.keys()) + "出力形式の例：calm"},
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]
                }
            ],
            max_tokens=20,
        )
        mood = response.choices[0].message.content.strip().lower()
        mood = re.sub(r"[^a-z]", "", mood)
        return mood
    except Exception as e:
        logger.error(f"OpenAI APIの呼び出しに失敗しました: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OpenAI APIの呼び出しに失敗しました: {str(e)}")

def flatten_tags(tags: dict) -> set:
    """ジャンル・楽器・ムードなどすべてのタグを1つのsetにまとめる"""
    return {tag for category in tags.values() for tag in category}

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
    """アップロードされた画像からムードを推定し、初期の楽曲リストを返すエンドポイント。
    アップロードされた画像を読み込み、OpenAIのAPIを使ってムードを推定し、
    そのムードに基づいて楽曲を選定する。
    Args:
        file (UploadFile): アップロードされた画像ファイル。
        db (Session): データベースセッション。
        current_user (User): 現在の認証ユーザー。
    Returns:
        schemas.SwipeInitResponse: 初期の楽曲リストを含むレスポンス。
    Raises:
        HTTPException: 画像のムード推定に失敗した場合や不正なムードが返された場合は400エラー。
    """
    # 画像を読み込む
    image_bytes = file.file.read()
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{uuid4().hex}_{file.filename}"
    image_path = os.path.join(upload_dir, unique_filename)

    try:
        with open(image_path, "wb") as f:
            f.write(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像の保存に失敗しました: {str(e)}")

    # DB保存処理（追加）
    photo_entry = PhotoUpload(user_id=current_user.id, image_path=image_path)
    db.add(photo_entry)
    db.commit()

    # ムードを推定
    try:
        main_mood = estimate_mood_from_image(image_bytes)
        print(f"[DEBUG] GPTから返されたムード: '{main_mood}'")
    except Exception as e:
        raise HTTPException(status_code=400, detail="画像のムード推定に失敗しました")
    # 辞書に存在しないなら補正候補を探す
    if main_mood not in MOOD_SIMILARITY:
        candidates = difflib.get_close_matches(main_mood, MOOD_SIMILARITY.keys(), n=1, cutoff=0.6)
        if not candidates:
            raise HTTPException(status_code=400, detail=f"'{main_mood}' は不正な雰囲気です")
        main_mood = candidates[0]
    # ムードに関連する楽曲を3つ選ぶ
    mood_data = MOOD_SIMILARITY.get(main_mood,{})
    moods = sorted(mood_data.items(), key=lambda x: x[1], reverse=True)[:3]
    if not moods:
        raise HTTPException(status_code=400, detail="ムードに関連する楽曲が見つかりません")
    # 選ばれたムードに基づいて楽曲をランダムに選ぶ
    selected = []
    # ムードごとに楽曲を選ぶ
    for mood, _ in moods:
        candidates = [
            s for s in SONGS 
            if mood in sum(s["tags"].values(), []) and s["id"] not in selected
        ]
        if candidates:
            chosen = random.choice(candidates)
            selected.append(chosen["id"])
    
    songs = [s for s in SONGS if s["id"] in selected]
    print(f"選ばれた楽曲: {[s['title'] for s in songs]}")
    return {"songs": songs}

# スワイプ結果を記録・次の曲を返す
@router.post("/swipe", response_model= schemas.SwipeResponse)
def swipe(
    swipe: schemas.SwipeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """スワイプ結果を記録し、次の曲を返すエンドポイント。"""
    # スワイプ履歴を保存
    db.add(SwipeHistory(user_id=current_user.id, song_id=swipe.song_id, liked=swipe.liked))
    db.commit()

    # スワイプ済みの曲ID
    swiped_ids = [
        s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id).all()
    ]
    # スワイプ済みの曲を除外した楽曲リスト
    SONGS_EXCLUDED = [s for s in SONGS if s["id"] not in swiped_ids]
    # ユーザーがLikeした曲のIDを取得
    if swipe.liked:
        # Likeした曲を履歴に追加
        db.add(SwipeHistory(user_id=current_user.id, song_id=swipe.song_id, liked=True))
        db.commit()
    else:
        # Likeしなかった曲は履歴に追加しない

        # ユーザーがLikeした曲のIDを取得
        liked_ids = [
            s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id, liked=True).all()
        ]
        liked_songs = [s for s in SONGS if s["id"] in liked_ids]
        # Likeした曲が3曲未満の場合はムード探索
        if len(liked_songs) < 3:
            liked_moods = {tag for song in liked_songs for tag in flatten_tags(song["tags"])}
            exclude_moods = {
                tag for song in SONGS_EXCLUDED if song["id"] in swiped_ids for tag in flatten_tags(song["tags"])
            }
            next_moods = sorted(
                set(MOOD_SIMILARITY.keys()) - exclude_moods,
                key=lambda x: -len(MOOD_SIMILARITY.get(x, []))
            )
            for mood in next_moods:
                candidates = [s for s in SONGS_EXCLUDED if mood in flatten_tags(s["tags"])]
                if candidates:
                    return {"song": random.choice(candidates)}
        # Likeした曲が5曲未満の場合は楽器探索
        elif len(liked_songs) < 5:
            liked_moods = [tag for song in liked_songs for tag in flatten_tags(song["tags"])]
            counter = {}
            for mood in liked_moods:
                for inst, score in MOOD_INST_SIMILARITY.get(mood, {}).items():
                    counter[inst] = counter.get(inst, 0) + score
            sorted_instruments = sorted(counter.items(), key=lambda x: -x[1])
            top_instruments = [inst for inst, _ in sorted_instruments[:2]]

            for song in SONGS_EXCLUDED:
                if any(inst in flatten_tags(song["tags"]) for inst in top_instruments):
                    return {"song": song}
    # スワイプ済みの曲がすべてLikeされている場合は、次の曲をランダムに選ぶ
    if not SONGS_EXCLUDED:
        raise HTTPException(status_code=404, detail="スワイプ候補なし")
    next_song = random.choice(SONGS_EXCLUDED)
    return {"song": next_song}
    # # Likeした曲のIDと詳細を取得
    # liked_ids = [
    #     s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id, liked=True).all()
    # ]
    # liked_songs = [s for s in SONGS if s["id"] in liked_ids]

    # # 3曲未満：ムード探索
    # if len(liked_songs) < 3:
    #     liked_moods = {tag for song in liked_songs for tag in flatten_tags(song["tags"])}
    #     exclude_moods = {
    #         tag for song in SONGS if song["id"] in swiped_ids for tag in flatten_tags(song["tags"])
    #     }
    #     next_moods = sorted(
    #         set(MOOD_SIMILARITY.keys()) - exclude_moods,
    #         key=lambda x: -len(MOOD_SIMILARITY.get(x, []))
    #     )
    #     for mood in next_moods:
    #         candidates = [s for s in SONGS if mood in flatten_tags(s["tags"]) and s["id"] not in swiped_ids]
    #         if candidates:
    #             return {"song": random.choice(candidates)}

    # # 5曲未満：楽器探索
    # elif len(liked_songs) < 5:
    #     liked_moods = [tag for song in liked_songs for tag in flatten_tags(song["tags"])]
    #     counter = {}
    #     for mood in liked_moods:
    #         for inst, score in MOOD_INST_SIMILARITY.get(mood, {}).items():
    #             counter[inst] = counter.get(inst, 0) + score
    #     sorted_instruments = sorted(counter.items(), key=lambda x: -x[1])
    #     top_instruments = [inst for inst, _ in sorted_instruments[:2]]

    #     for song in SONGS:
    #         if song["id"] in swiped_ids:
    #             continue
    #         if any(inst in flatten_tags(song["tags"]) for inst in top_instruments):
    #             return {"song": song}

    # # 該当曲なし
    # raise HTTPException(status_code=404, detail="スワイプ候補なし")

# プレイリスト生成
@router.get("/playlist", response_model=schemas.PlaylistResponse)
def generate_playlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    liked_ids = [
        s.song_id for s in db.query(SwipeHistory)
        .filter_by(user_id=current_user.id, liked=True).all()
    ]
    liked_songs = [s for s in SONGS if s["id"] in liked_ids]

    # --- フォールバック①：Like数が足りない場合 ---
    if len(liked_songs) < 3:
        liked_songs = random.sample([s for s in SONGS if s["id"] not in liked_ids], k=3)

    # --- タグカウント ---
    mood_counter = {}
    inst_counter = {}
    for song in liked_songs:
        tags = flatten_tags(song["tags"])
        for tag in tags:
            if tag in MOOD_SIMILARITY:
                mood_counter[tag] = mood_counter.get(tag, 0) + 1
            else:
                inst_counter[tag] = inst_counter.get(tag, 0) + 1

    mood_tags = [m[0] for m in sorted(mood_counter.items(), key=lambda x: -x[1])[:3]]
    inst_tags = [i[0] for i in sorted(inst_counter.items(), key=lambda x: -x[1])[:2]]

    # --- 推薦抽出 ---
    candidates = [
        s for s in SONGS
        if s["id"] not in liked_ids
        and len(set(mood_tags) & flatten_tags(s["tags"])) >= 2
        and len(set(inst_tags) & flatten_tags(s["tags"])) >= 1
    ]

    # --- フォールバック②：推薦がゼロならランダム推薦 ---
    if not candidates:
        candidates = [s for s in SONGS if s["id"] not in liked_ids]

    recommended = random.sample(candidates, k=min(10, len(candidates)))

    # --- プレイリスト履歴保存 ---
    latest_upload = db.query(PhotoUpload)\
        .filter_by(user_id=current_user.id)\
        .order_by(PhotoUpload.created_at.desc()).first()

    if latest_upload:
        playlist = PlaylistHistory(
            user_id=current_user.id,
            image_path=latest_upload.image_path,
            songs_json=json.dumps(liked_songs + recommended, ensure_ascii=False),
        )
        db.add(playlist)
        db.commit()

    return {
        "liked": liked_songs,
        "recommended": recommended
    }



@router.get("/history", response_model=List[schemas.PlaylistHistoryRead])
def get_playlist_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """現在のユーザーのプレイリスト履歴を取得する
    ユーザーが過去に生成したプレイリストの履歴を取得し、最新のものから順に返す。
    Args:
        db (Session): データベースセッション。
        current_user (User): 現在の認証ユーザー。
    Returns:
        List[schemas.PlaylistHistoryRead]: ユーザーのプレイリスト履歴のリスト。
    """
    history = db.query(PlaylistHistory).filter(PlaylistHistory.user_id == current_user.id).order_by(PlaylistHistory.created_at.desc()).all()
    return history