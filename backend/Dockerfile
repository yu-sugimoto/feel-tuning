# ベースイメージ
FROM python:3.13-slim

# 作業ディレクトリの設定
WORKDIR /

# 必要なシステムパッケージのインストール
RUN rm -rf /var/lib/apt/lists/* && apt-get update && apt-get install -y --no-install-recommends curl && apt-get clean

# requirements.txt のコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードのコピー
COPY . .

# FastAPIアプリの起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]