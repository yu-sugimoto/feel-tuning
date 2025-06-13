# Pydantic Schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SwipeHistoryBase(BaseModel):
    user_id: int
    song_id: int
    action: str

class SwipeHistoryCreate(SwipeHistoryBase):
    pass

class SwipeHistorySchema(SwipeHistoryBase):
    created_at: datetime

    class Config:
        orm_mode = True