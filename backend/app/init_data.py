import json
from datetime import datetime
from app.models import User, Song, SongFeature, SwipeHistory, Playlist
from app.dependencies import get_db

# DB接続
db_generator = get_db()  # ジェネレータを作成
db = next(db_generator)  # セッションを取得

try:
    if db.query(User).first() or db.query(Song).first() or db.query(SongFeature).first() or db.query(SwipeHistory).first() or db.query(Playlist).first():
        print("既にデータが存在するため、初期データ投入をスキップします。")
    else:
        with open("data/demo_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("users", []):
            db.add(User(**item))

        for item in data.get("songs", []):
            db.add(Song(**item))

        for item in data.get("song_features", []):
            db.add(SongFeature(**item))

        for item in data.get("swipe_history", []):
            item["created_at"] = datetime.fromisoformat(item["created_at"])
            db.add(SwipeHistory(**item))

        for item in data.get("playlists", []):
            item["created_at"] = datetime.fromisoformat(item["created_at"])
            db.add(Playlist(**item))

        db.commit()
        print("初期データの投入が完了しました。")
except Exception as e:
    db.rollback()
    print(f"エラーが発生しました: {e}")
finally:
    next(db_generator, None) # ジェネレータを最後まで実行してセッションをクローズ
    print("データベース接続をクローズしました。")