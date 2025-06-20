from pydantic import BaseModel
from typing import List

# 楽曲データの構造
class Song(BaseModel):
    id: int
    title: str
    artist: str
    tags: List[str]