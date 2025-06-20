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
    # 画像データをBase64エンコードしてData URL形式に変換
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    # Data URL形式の画像データを作成
    image_data_url = f"data:image/jpeg;base64,{encoded}"

    # OpenAI APIを使ってムードを推定
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI APIの呼び出しに失敗しました: {str(e)}")

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
    # ムードを推定
    try:
        main_mood = estimate_mood_from_image(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail="画像のムード推定に失敗しました")
    # ムードが不正な場合は400エラー
    if main_mood not in MOOD_SIMILARITY:
        raise HTTPException(status_code=400, detail=f"'{main_mood}' は不正な雰囲気です")
    # ムードに関連する楽曲を3つ選ぶ
    moods = MOOD_SIMILARITY.get(main_mood, [])[:3]
    if not moods:
        raise HTTPException(status_code=400, detail="ムードに関連する楽曲が見つかりません")
    # 選ばれたムードに基づいて楽曲をランダムに選ぶ
    selected = []
    # ムードごとに楽曲を選ぶ
    for mood in moods:
        # 選ばれたムードに関連する楽曲をランダムに選ぶ
        # 選ばれた楽曲のIDを除外して候補を作成
        candidates = [s for s in SONGS if mood in s["tags"] and s["id"] not in selected]
        if candidates:
            chosen = random.choice(candidates)
            selected.append(chosen["id"])
    
    songs = [s for s in SONGS if s["id"] in selected]
    return {"songs": songs}

# スワイプ結果を記録・次の曲を返す
@router.post("/swipe", response_model=schemas.SwipeResponse)
def swipe(swipe: schemas.SwipeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """スワイプ結果を記録し、次の曲を返すエンドポイント。
    ユーザーが曲をスワイプした結果（liked=True/False）をデータベースに保存し、
    ユーザーの好みに基づいて次の曲を選定する。
    Args:
        swipe (schemas.SwipeRequest): スワイプ結果（song_id, liked）。
        db (Session): データベースセッション。
        current_user (User): 現在の認証ユーザー。
    Returns:
        schemas.SwipeResponse: 次の曲の情報を含むレスポンス。
    Raises:
        HTTPException: スワイプ候補がない場合は404エラー。
    """
    # スワイプ履歴を保存
    db.add(SwipeHistory(user_id=current_user.id, song_id=swipe.song_id, liked=swipe.liked))
    db.commit()
    # スワイプした曲が存在しない場合は404エラー
    song = db.query(SwipeHistory).filter_by(user_id=current_user.id, song_id=swipe.song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="スワイプした曲が見つかりません")
    # すでにスワイプした曲のIDを取得
    swiped_ids = [s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id).all()]
    # ユーザーがLikeした曲のIDを取得
    liked_ids = [s.song_id for s in db.query(SwipeHistory).filter_by(user_id=current_user.id, liked=True).all()]
    # すでにLikeした曲を取得
    liked_songs = [s for s in SONGS if s["id"] in liked_ids]

    # ユーザーがLikeした曲が3曲未満の場合は、雰囲気探索フェーズ
    if len(liked_songs) < 3:
        # 雰囲気探索フェーズ
        liked_moods = {tag for song in liked_songs for tag in song["tags"]}
        # すでにスワイプした曲のムードを除外
        exclude_moods = {tag for song in SONGS if song["id"] in swiped_ids for tag in song["tags"]}
        # ムードの候補を取得（スワイプした曲のムードを除外）
        next_moods = sorted(set(MOOD_SIMILARITY.keys()) - exclude_moods, key=lambda x: -len(MOOD_SIMILARITY.get(x, [])))
        for mood in next_moods:
            candidates = [s for s in SONGS if mood in s["tags"] and s["id"] not in swiped_ids]
            if candidates:
                return {"song": random.choice(candidates)}

    # ユーザーがLikeした曲が5曲以上の場合は、楽器探索フェーズ
    elif len(liked_songs) < 5:
        # 楽器探索フェーズ
        liked_moods = [tag for song in liked_songs for tag in song["tags"]]
        counter = {}
        # ユーザーがLikeした曲のムードに関連する楽器を集計
        for mood in liked_moods:
            for inst, score in MOOD_INST_SIMILARITY.get(mood, {}).items():
                counter[inst] = counter.get(inst, 0) + score
        # 除外された楽器を除いて、スコアの高い楽器を選ぶ
        sorted_instruments = sorted(counter.items(), key=lambda x: -x[1])
        # 上位2つの楽器を選ぶ
        top_instruments = [inst for inst, _ in sorted_instruments[:2]]
        # スワイプした曲の楽器を除外
        for song in SONGS:
            if song["id"] in swiped_ids:
                continue
            if any(inst in song["tags"] for inst in top_instruments):
                return {"song": song}
    raise HTTPException(status_code=404, detail="スワイプ候補なし")

# プレイリスト生成
@router.get("/playlist", response_model=schemas.PlaylistResponse)
def generate_playlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ユーザーのLike履歴からプレイリストを生成するエンドポイント。
    ユーザーがLikeした曲を元に、好みの雰囲気と楽器を分析し、10曲の推薦リストを生成する。
    Args:
        db (Session): データベースセッション。
        current_user (User): 現在の認証ユーザー。
    Returns:
        schemas.PlaylistResponse: ユーザーのLikeした曲と推薦曲のリストを含むレスポンス。
    Raises:
        HTTPException: ユーザーのLike履歴が十分でない場合は400エラー。
    """
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

@router.get("/playlist/history", response_model=List[schemas.PlaylistHistoryRead])
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