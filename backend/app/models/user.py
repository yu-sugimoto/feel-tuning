# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Baseクラスをインポート
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

# Userモデルの定義
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    nickname = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(JST))

    swipes = relationship("SwipeHistory", back_populates="user")
    playlists = relationship("Playlist", back_populates="user")