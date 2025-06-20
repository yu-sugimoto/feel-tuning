# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Baseクラスをインポート
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

# Userモデルの定義
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    nickname = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション（One-to-Many）
    swipes = relationship("SwipeHistory", back_populates="user")
    playlists = relationship("PlaylistHistory", back_populates="user")