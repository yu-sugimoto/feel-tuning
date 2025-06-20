# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Baseクラスをインポート
from sqlalchemy.sql import func

class PhotoUpload(Base):
    __tablename__ = 'photo_uploads'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーション（Many-to-One）
    user = relationship("User", back_populates="photo_uploads")
