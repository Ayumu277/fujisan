# ABDSシステム

ABDSシステムは、FastAPI、React、PostgreSQL、Redisを使用したモダンなWebアプリケーションです。

## 技術スタック

### バックエンド
- **FastAPI**: Python 3.11
- **データベース**: PostgreSQL 15
- **キャッシュ**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **マイグレーション**: Alembic

### フロントエンド
- **React**: 18.x
- **TypeScript**: 5.x
- **ビルドツール**: Vite
- **スタイリング**: Tailwind CSS
- **状態管理**: Zustand
- **HTTPクライアント**: Axios
- **フォーム**: React Hook Form + Yup

### インフラ
- **コンテナ**: Docker & Docker Compose
- **Webサーバー**: Nginx (本番環境)

## プロジェクト構造

```
abds-system/
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI アプリケーションエントリーポイント
│   │   ├── api/            # API エンドポイント
│   │   ├── core/           # 設定とコアユーティリティ
│   │   ├── models/         # SQLAlchemy モデル
│   │   ├── schemas/        # Pydantic スキーマ
│   │   └── services/       # ビジネスロジック
│   ├── requirements.txt    # Python 依存関係
│   └── Dockerfile         # バックエンド Dockerfile
├── frontend/               # React フロントエンド
│   ├── src/               # ソースコード
│   ├── public/            # 静的ファイル
│   ├── package.json       # Node.js 依存関係
│   └── Dockerfile         # フロントエンド Dockerfile
├── docker-compose.yml     # サービス管理
└── .env.example          # 環境変数サンプル
```

## セットアップ

### 前提条件
- Docker
- Docker Compose

### 開発環境の起動

1. リポジトリをクローン
```bash
git clone <repository-url>
cd abds-system
```

2. 環境変数の設定
```bash
cp .env.example .env
# .env ファイルを編集して、必要な環境変数を設定
```

3. サービスの起動
```bash
docker-compose up -d
```

4. サービスの確認
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- API ドキュメント: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 開発

### バックエンド開発

```bash
# バックエンドのみ起動（開発用）
docker-compose up -d postgres redis
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### フロントエンド開発

```bash
# フロントエンドのみ開発
cd frontend
npm install
npm run dev
```

### データベースマイグレーション

```bash
# マイグレーションファイルの作成
docker-compose exec backend alembic revision --autogenerate -m "migration message"

# マイグレーションの実行
docker-compose exec backend alembic upgrade head
```

## API エンドポイント

### ヘルスチェック
- `GET /` - 基本ヘルスチェック
- `GET /health` - 詳細ヘルスチェック

### API ドキュメント
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## 環境変数

主要な環境変数については `.env.example` ファイルを参照してください。

## デプロイ

### 本番環境

```bash
# 本番用ビルド
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。