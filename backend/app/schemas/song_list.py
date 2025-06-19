from pydantic import BaseModel
from .song import SongRead

class SongList(BaseModel):
    similar: list[SongRead]
    dissimilar: list[SongRead]