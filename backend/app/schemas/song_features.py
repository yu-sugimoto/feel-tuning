# Pydantic Schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SongFeatureBase(BaseModel):
    tempo: float
    energy: float
    danceability: float
    valence: float

class SongFeatureCreate(SongFeatureBase):
    song_id: int

class SongFeatureSchema(SongFeatureBase):
    class Config:
        orm_mode = True