# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from app.db.base_class import Base # Baseクラスをインポート

# Playlistモデルの定義
class Playlist(Base):
    __tablename__ = 'playlists'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    song_id = Column(Integer, ForeignKey('songs.id'))
    name = Column(String)
    display_order = Column(Integer)
    created_at = Column(DateTime)

    user = relationship("User", back_populates="playlists")
    song = relationship("Song")