# ABDSシステム - バックエンド Dockerfile
# マルチステージビルド（開発・本番対応）

# ベースイメージ
FROM python:3.11-slim as base

# 環境変数設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 作業ディレクトリの設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 開発ステージ
FROM base as development

# 開発用の追加パッケージ
RUN apt-get update && apt-get install -y \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# アプリケーションコードをコピー
COPY ./app ./app

# 開発用ポートの公開
EXPOSE 8000

# 開発用の起動コマンド（ホットリロード有効）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 本番ステージ
FROM base as production

# Python依存関係のインストール（本番用最適化）
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-dev -r requirements.txt

# 非rootユーザーの作成
RUN groupadd -r appuser && useradd -r -g appuser appuser

# アプリケーションコードをコピー
COPY ./app ./app

# uploadsディレクトリの作成とパーミッション設定
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

# 非rootユーザーに切り替え
USER appuser

# 本番用ポートの公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 本番用の起動コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]