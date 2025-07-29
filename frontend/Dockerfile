# ABDSシステム - フロントエンド Dockerfile

# ビルドステージ
FROM node:18-alpine AS builder

# 作業ディレクトリの設定
WORKDIR /app

# package.jsonとyarn.lockをコピー
COPY package*.json ./

# 依存関係のインストール
RUN npm ci --only=production

# ソースコードをコピー
COPY . .

# アプリケーションのビルド
RUN npm run build

# 本番ステージ
FROM nginx:alpine

# ビルドされたファイルをNginxにコピー
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginxの設定ファイルをコピー（オプション）
# COPY nginx.conf /etc/nginx/nginx.conf

# ポートの公開
EXPOSE 80

# Nginxの起動
CMD ["nginx", "-g", "daemon off;"]