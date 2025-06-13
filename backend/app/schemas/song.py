# Pydantic Schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SongBase(BaseModel):
    title: str
    artist: str
    preview_url: str
    genre: Optional[str]

class SongCreate(SongBase):
    pass

class SongSchema(SongBase):
    id: int

    class Config:
        orm_mode = True