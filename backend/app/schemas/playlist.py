# Pydantic Schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .song import SongSchema

class PlaylistBase(BaseModel):
    name: str
    display_order: Optional[int]
    created_at: datetime

class PlaylistCreate(PlaylistBase):
    song_id: int
    user_id: int

class PlaylistSchema(PlaylistBase):
    song: SongSchema

    class Config:
        orm_mode = True