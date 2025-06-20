from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.schemas.song import Song

# 最終プレイリストの出力
class PlaylistResponse(BaseModel):
    liked: List[Song]
    recommended: List[Song]

# 履歴用：保存されたプレイリストの表示
class PlaylistHistoryRead(BaseModel):
    id: int
    image_path: str
    songs_json: str
    created_at: datetime

    class Config:
        orm_mode = True