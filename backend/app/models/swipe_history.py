# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Baseクラスをインポート
from sqlalchemy.sql import func
from sqlalchemy.types import Boolean

# SwipeHistoryモデルの定義
class SwipeHistory(Base):
    __tablename__ = 'swipe_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    song_id = Column(Integer)
    liked = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション（Many-to-One）
    user = relationship("User", back_populates="swipes")