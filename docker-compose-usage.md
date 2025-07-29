# Docker Compose 使用ガイド

## 概要

ABDSシステムは、以下のサービスで構成されています：

1. **backend**: FastAPI アプリケーション (ポート8000)
2. **frontend**: React アプリケーション (ポート3000)
3. **postgres**: PostgreSQL データベース (ポート5432)
4. **redis**: Redis キャッシュ (ポート6379)
5. **pgadmin**: データベース管理ツール (ポート5050) ※オプション
6. **nginx**: リバースプロキシ (ポート80/443) ※本番環境用

## セットアップ

### 1. 環境変数の設定

```bash
# env.example を .env にコピー
cp env.example .env

# .env ファイルを編集して、必要な値を設定
nano .env
```

### 2. 基本的な起動

```bash
# すべてのサービスを起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# 特定のサービスのログを確認
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. サービス個別操作

```bash
# 特定のサービスのみ起動
docker-compose up -d postgres redis
docker-compose up -d backend
docker-compose up -d frontend

# サービス停止
docker-compose stop backend
docker-compose stop frontend

# サービス再起動
docker-compose restart backend
```

## 開発用コマンド

### pgAdmin を使用（データベース管理）

```bash
# pgAdmin を含めて起動
docker-compose --profile tools up -d

# アクセス: http://localhost:5050
# ログイン: admin@example.com / admin123
```

### 本番環境用起動

```bash
# Nginx を含めて起動
docker-compose --profile production up -d
```

### ホットリロード開発

```bash
# 開発モードで起動（ファイル変更時に自動リロード）
docker-compose up -d

# コードを編集すると自動的に反映されます
# - backend: ./backend/app/ ディレクトリ
# - frontend: ./frontend/src/ ディレクトリ
```

## アクセス URL

| サービス | URL | 説明 |
|----------|-----|------|
| フロントエンド | http://localhost:3000 | React アプリケーション |
| バックエンドAPI | http://localhost:8000 | FastAPI サーバー |
| API ドキュメント | http://localhost:8000/docs | Swagger UI |
| API ドキュメント | http://localhost:8000/redoc | ReDoc |
| pgAdmin | http://localhost:5050 | データベース管理 |
| PostgreSQL | localhost:5432 | データベース直接接続 |
| Redis | localhost:6379 | Redis 直接接続 |

## トラブルシューティング

### 1. ポート競合エラー

```bash
# 使用中のポートを確認
lsof -i :8000
lsof -i :3000
lsof -i :5432

# .env ファイルでポートを変更
BACKEND_PORT=8001
FRONTEND_PORT=3001
POSTGRES_PORT=5433
```

### 2. データベース接続エラー

```bash
# PostgreSQL の状態確認
docker-compose ps postgres
docker-compose logs postgres

# データベースの再初期化
docker-compose down -v
docker-compose up -d postgres
```

### 3. フロントエンドビルドエラー

```bash
# node_modules を削除して再インストール
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install

# または、イメージを再ビルド
docker-compose build --no-cache frontend
```

### 4. バックエンド依存関係エラー

```bash
# Python パッケージの再インストール
docker-compose exec backend pip install -r requirements.txt

# または、イメージを再ビルド
docker-compose build --no-cache backend
```

## データ管理

### バックアップ

```bash
# データベースバックアップ
docker-compose exec postgres pg_dump -U postgres abds_db > backup.sql

# Redis データバックアップ
docker-compose exec redis redis-cli save
docker cp $(docker-compose ps -q redis):/data/dump.rdb ./redis-backup.rdb
```

### リストア

```bash
# データベースリストア
docker-compose exec -T postgres psql -U postgres abds_db < backup.sql

# Redis データリストア
docker cp ./redis-backup.rdb $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis
```

### データ削除

```bash
# すべてのデータを削除（注意！）
docker-compose down -v

# 特定のボリュームのみ削除
docker volume rm abds_postgres_data
docker volume rm abds_redis_data
```

## パフォーマンス最適化

### 開発環境

```bash
# ファイル変更監視の除外設定（大きなnode_modulesなど）
# docker-compose.yml の volumes 設定で調整済み
```

### 本番環境

```bash
# 本番用環境変数を設定
echo "DEBUG=false" >> .env
echo "ENVIRONMENT=production" >> .env

# 最適化されたイメージでビルド
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## モニタリング

### リソース使用量確認

```bash
# コンテナのリソース使用量
docker stats

# ディスク使用量
docker system df

# ログサイズ確認
docker-compose exec backend du -sh /var/log
```

### ヘルスチェック

```bash
# すべてのサービスの状態確認
docker-compose ps

# ヘルスチェック詳細
docker inspect $(docker-compose ps -q backend) | grep -A 5 Health
docker inspect $(docker-compose ps -q frontend) | grep -A 5 Health
```