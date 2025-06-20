import json
from datetime import datetime
from app.models import User
from app.dependencies import get_db

# DB接続
db_generator = get_db()  # ジェネレータを作成
db = next(db_generator)  # セッションを取得

# 初期データ投入（ユーザーのみ）
try:
    if db.query(User).first():
        print("既にユーザーデータが存在するため、初期データ投入をスキップします。")
    else:
        with open("data/demo_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("users", []):
            db.add(User(**item))

        db.commit()
        print("初期データの投入が完了しました。")
except Exception as e:
    db.rollback()
    print(f"エラーが発生しました: {e}")
finally:
    next(db_generator, None) # ジェネレータを最後まで実行してセッションをクローズ
    print("データベース接続をクローズしました。")