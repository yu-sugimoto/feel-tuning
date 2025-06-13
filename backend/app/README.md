# backend 環境構築

## 手順
**下記コマンドで、マイグレーション → 初期データ投入 → アプリ起動までを提供する**
```
$ docker-compose up --build
```
→ app / db コンテナが起動し、http://localhost:8000/ にアクセスできることを確認

※ 成功コマンド
```
Attaching to app, db
db   | 
db   | PostgreSQL Database directory appears to contain a database; Skipping initialization
db   | 
db   | 2025-06-13 17:19:12.491 UTC [1] LOG:  starting PostgreSQL 17.5 (Debian 17.5-1.pgdg120+1) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
db   | 2025-06-13 17:19:12.491 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
db   | 2025-06-13 17:19:12.491 UTC [1] LOG:  listening on IPv6 address "::", port 5432
db   | 2025-06-13 17:19:12.493 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
db   | 2025-06-13 17:19:12.494 UTC [29] LOG:  database system was shut down at 2025-06-13 17:16:50 UTC
db   | 2025-06-13 17:19:12.497 UTC [1] LOG:  database system is ready to accept connections
app  | マイグレーションを実行します（初回のみ実行）...
app  | INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
app  | INFO  [alembic.runtime.migration] Will assume transactional DDL.
app  | INFO  [alembic.runtime.migration] Running upgrade  -> 8ea9a73f83b5, initial migration
app  | 初期データを投入します（初回のみ実行）...
app  | Using database at postgresql://music_swipe:music_swipe@db:5432/music_swipe
app  | 初期データの投入が完了しました。
app  | データベース接続をクローズしました。
app  | FastAPIアプリケーションを起動します...
app  | INFO:     Will watch for changes in these directories: ['/']
app  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app  | INFO:     Started reloader process [1] using StatReload
app  | INFO:     Started server process [10]
app  | INFO:     Waiting for application startup.
app  | INFO:     Application startup complete.
```

## ディレクトリ構造
```
.
├── alembic/                 # Alembic によるマイグレーション関連フォルダ
│   ├── README               
│   ├── __pycache__          
│   ├── env.py               # Alembicのマイグレーション処理ファイル
│   ├── script.py.mako       
│   └── versions/            # マイグレーションファイルが格納されるフォルダ
├── alembic.ini              # Alembic の設定ファイル
├── app/                     
│   ├── README.md            
│   ├── __init__.py          
│   ├── __pycache__          
│   ├── core/                # 設定・共通処理を格納するフォルダ
│   ├── database.py          # SQLAlchemy セッションや DB 接続処理を定義するファイル
│   ├── db/                  # DB関連の初期処理関連フォルダ
│   ├── dependencies.py      # FastAPI の 依存関係注入を定義するファイル
│   ├── init_data.py         # 初期データ（シード）投入処理のスクリプト
│   ├── main.py              # FastAPI アプリのエントリーポイントを定義するファイル
│   ├── models/              # SQLAlchemy による ORM モデルを格納するフォルダ
│   ├── routers.py           # APIルーティングのエントリーポイントを定義するファイル
│   ├── schemas/             # Pydantic によるデータ検証スキーマを定義するフォルダ
│   └── services/            # ビジネスロジック層を定義するフォルダ
├── data/
│   └── demo_data.json       # 初期投入用のデモデータ
├── Dockerfile               # FastAPI アプリ用の Docker ビルド定義ファイル
├── docker-compose.yml       # API/DB を一括で起動する設定ファイル
├── entrypoint.sh            # コンテナ起動時に実行されるスクリプト
└── requirements.txt         # pip でインストールすべき Python パッケージの一覧
```