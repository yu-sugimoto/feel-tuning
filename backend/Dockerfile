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

# Entrypoint スクリプトをコピーし実行権限付与
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Entrypointの実行（マイグレーション → 初期データ投入 → アプリ起動）
CMD ["/entrypoint.sh"]