# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from app.db.base_class import Base # Baseクラスをインポート

# Songモデルの定義
class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    preview_url = Column(String, nullable=False)
    genre = Column(String)

    features = relationship("SongFeature", uselist=False, back_populates="song")
