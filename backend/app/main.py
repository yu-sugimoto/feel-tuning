# FastAPI アプリケーションのエントリーポイントを定義するファイル
from fastapi import FastAPI
from .routers import router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# FastAPIのインスタンスを作成（アプリケーション全体を管理する）
app = FastAPI()

# CORS を許可（Expoとの接続は未テスト）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# アップロードフォルダを公開
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# routers.pyで作成したルーティングを読み込む
app.include_router(router)
