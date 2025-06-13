# FastAPI ORMモデルとPydanticスキーマ定義
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship, declarative_base
from app.db.base_class import Base # Baseクラスをインポート

# SongFeatureモデルの定義
class SongFeature(Base):
    __tablename__ = 'song_features'

    song_id = Column(Integer, ForeignKey('songs.id'), primary_key=True)
    tempo = Column(Float)
    energy = Column(Float)
    danceability = Column(Float)
    valence = Column(Float)

    song = relationship("Song", back_populates="features")