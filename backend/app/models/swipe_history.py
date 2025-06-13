# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from app.db.base_class import Base # Baseクラスをインポート

# SwipeHistoryモデルの定義
class SwipeHistory(Base):
    __tablename__ = 'swipe_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    song_id = Column(Integer, ForeignKey('songs.id'))
    action = Column(String)
    created_at = Column(DateTime)

    user = relationship("User", back_populates="swipes")
    song = relationship("Song")