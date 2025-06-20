from pydantic import BaseModel
from typing import List
from app.schemas.song import Song

# 初期推薦（3曲）
class SwipeInitResponse(BaseModel):
    songs: List[Song]

# スワイプの送信
class SwipeRequest(BaseModel):
    song_id: int
    liked: bool

# スワイプ後の1曲推薦
class SwipeResponse(BaseModel):
    song: Song