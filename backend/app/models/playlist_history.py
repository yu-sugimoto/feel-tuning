# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Baseクラスをインポート
from sqlalchemy.sql import func

# PlaylistHistoryモデルの定義
class PlaylistHistory(Base):
    __tablename__ = "playlist_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image_path = Column(String)
    songs_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション（Many-to-One）
    user = relationship("User", back_populates="playlists")