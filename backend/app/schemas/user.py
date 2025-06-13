# Pydantic Schemas
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: str
    nickname: str

class UserCreate(UserBase):
    password: str

class UserSchema(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True