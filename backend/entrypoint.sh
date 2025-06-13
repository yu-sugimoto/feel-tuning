#!/bin/bash
export PYTHONPATH=/

echo "マイグレーションを実行します（初回のみ実行）..."
alembic upgrade head

echo "初期データを投入します（初回のみ実行）..."
python app/init_data.py

echo "FastAPIアプリケーションを起動します..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload