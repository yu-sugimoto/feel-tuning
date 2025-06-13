# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from app.db.base_class import Base # Baseクラスをインポート

# Userモデルの定義
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    nickname = Column(String, nullable=False)

    swipes = relationship("SwipeHistory", back_populates="user")
    playlists = relationship("Playlist", back_populates="user")