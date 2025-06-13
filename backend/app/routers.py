from fastapi import APIRouter, Depends, FastAPI, Request

# APIRouterインスタンスを作成（ルーティングを管理する）
router = APIRouter()

# ホーム
@router.get("/")
def get_root():
    return {"message": "Hello World"}