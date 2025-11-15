# Morizo - 開発環境

2つのリポジトリに対応したDocker開発環境

## リポジトリ構成

- **morizo-web** - Next.js 15 Webアプリ（Vercelデプロイ用）
- **morizo-mobile** - Expo モバイルアプリ（API呼び出し用）

## サービス構成

- **morizo-web** - Next.js 15環境（ポート3000）
- **morizo-mobile** - Expo環境（ポート8081, 19000-19001, 19006）

## クラウドサービス

- **Supabase PostgreSQL** - データベース（クラウド）
- **Supabase** - 認証・リアルタイム機能（クラウド）

## セットアップ

### 1. 開発環境の起動

```bash
# Docker Composeで開発環境を起動
cd docker
docker-compose up -d
```

### 2. アプリケーションの作成

#### Webアプリ（morizo-web）

```bash
# Webコンテナに接続
docker-compose exec morizo-web bash

# /app フォルダで Next.js 15アプリを作成
cd /app
npx create-next-app@latest . --typescript --tailwind --eslint --app

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

#### モバイルアプリ（morizo-mobile）

```bash
# モバイルコンテナに接続
docker-compose exec morizo-mobile bash

# /app フォルダで Expoアプリを作成
cd /app
npx create-expo-app@latest . --template blank-typescript

# 依存関係をインストール
npm install

# 開発サーバーを起動
# Expo Goで実機確認する場合（Android/iOS端末）
npx expo start --tunnel

# Webブラウザで簡易確認する場合
npx expo start --web
```

## アクセス先

- **Webアプリ**: http://localhost:3000
- **Expo DevTools**: http://localhost:19000
- **Supabase PostgreSQL**: クラウド（接続情報は環境変数で設定）
- **Supabase**: クラウド（接続情報は環境変数で設定）

## 開発コマンド

```bash
# 開発環境の起動
docker-compose up -d

# 開発環境の停止
docker-compose down

# ログの確認
docker-compose logs -f

# 特定のサービスのログ
docker-compose logs -f morizo-web
docker-compose logs -f morizo-mobile
```

## 注意事項

- WebアプリはVercelにデプロイ可能
- モバイルアプリはWebアプリのAPIを呼び出す
- 各アプリは独立したコンテナで動作
- データベースと認証はクラウドサービスを使用
- 開発環境は軽量化され、必要なサービスのみ起動