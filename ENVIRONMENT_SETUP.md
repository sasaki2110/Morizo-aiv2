# Morizo AI v2 - Environment Variables Setup

## 必要な環境変数

以下の環境変数を設定してください：

### Google Search API設定
```bash
GOOGLE_SEARCH_API_KEY=AIzaSy...dY9Im6Q
GOOGLE_SEARCH_ENGINE_ID=236...444f41
```

### Supabase設定
```bash
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
```

### OpenAI設定
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### ログ設定
```bash
LOG_LEVEL=INFO
LOG_FILE=morizo_ai.log
ENVIRONMENT=development
```

## Google Search APIの取得方法

1. Google Cloud Consoleにアクセス
2. プロジェクトを作成または選択
3. Custom Search APIを有効化
4. APIキーを作成
5. Custom Search Engineを作成
6. 検索対象サイトを設定（cookpad.com, kurashiru.com等）

## 設定方法

### 方法1: .envファイル
プロジェクトルートに`.env`ファイルを作成し、上記の環境変数を設定

### 方法2: システム環境変数
```bash
export GOOGLE_SEARCH_API_KEY="your_api_key"
export GOOGLE_SEARCH_ENGINE_ID="your_engine_id"
```

### 方法3: Docker環境
docker-compose.ymlまたはDockerfileで環境変数を設定
