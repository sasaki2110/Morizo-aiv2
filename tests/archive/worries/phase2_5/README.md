# Phase 2.5 バックエンド回帰テスト

## 概要

Phase 2.5 の各パターンが正しく動作することを確認するためのHTTPベースの自動回帰テストです。

破壊的活動（デグレード）の早期発見のため、Phase 2.5 実装前後で同じ結果が得られることを確認します。

## 前提条件

1. **サーバーを起動**
   ```bash
   python main.py
   ```

2. **環境変数を設定**（`.env`ファイル）
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SUPABASE_EMAIL=tonkati2001@gmail.com
   SUPABASE_PASSWORD=Kpgc1001!
   ```

## 実行方法

### 全テストを実行

```bash
# ディレクトリに移動
cd tests/phase2_5

# テストを実行
python test_backend_regression.py
```

### 特定のテストケースのみ実行

現時点では全テストケースを実行します。特定のテストケースのみ実行する場合は、コード内の `TEST_CASES` リストを編集してください。

## テストケース

### パターン1: 在庫操作

1. **在庫追加** (`TEST_CASE_1_1`)
   - メッセージ: 「牛乳を2本追加して」
   - 期待されるタスク: `add_inventory` のみ

2. **在庫削除（曖昧性あり）** (`TEST_CASE_1_2`)
   - メッセージ: 「牛乳を削除して」
   - 前提: 複数の牛乳を登録済み
   - 期待される動作: 曖昧性検出 → 確認質問

### パターン2: 献立生成

- **献立生成** (未実装)
  - メッセージ: 「献立を教えて」
  - 期待されるタスク: `get_inventory`, `generate_menu_plan`, `search_menu_from_rag`, `search_recipes_from_web`

### パターン3: 主菜提案

1. **主菜提案（食材指定）** (`TEST_CASE_3_1`)
   - メッセージ: 「レンコンの主菜を5件提案して」
   - 期待されるタスク: `get_inventory`, `history_get_recent_titles`, `generate_proposals`, `search_recipes_from_web`

## Supabase認証

このテストは **Supabase認証で動的にJWTトークンを取得** します。

### メリット

- テスト実行時に毎回新しいJWTトークンを取得
- トークンの賞味期限切れの心配がない
- 長時間のテストでも安定動作

### 実装

`IntegrationTestClient` が初期化時に自動的にSupabaseにログインしてJWTトークンを取得します。

```python
class IntegrationTestClient:
    def __init__(self, base_url="http://localhost:8000"):
        # Supabase認証でJWTトークンを動的に取得
        auth_util = AuthUtil()
        self.jwt_token = auth_util.get_auth_token()
        
        self.session.headers.update({
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        })
```

## トラブルシューティング

### サーバーが起動していない

```
⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。
```

**解決方法**: ターミナルで `python main.py` を実行

### Supabase認証エラー

```
❌ Supabase認証に失敗しました
💡 SUPABASE_URL, SUPABASE_KEY, SUPABASE_EMAIL, SUPABASE_PASSWORD を .env に設定してください
```

**解決方法**: `.env` ファイルに必要な環境変数を設定

### HTTPリクエストエラー

```
❌ HTTPリクエストエラー: Connection refused
```

**解決方法**: サーバーのポート番号が正しいか確認（デフォルト: 8000）

## 成功基準

- 全テストケースが成功
- Phase 2.5 実装前後で同じ結果が得られる
- 曖昧性検出が正しく動作
- タスクチェーンが期待通りに生成される

## Phase 3 実装後の拡張

Phase 3 実装後は以下のテストケースも追加予定：

- パターン6: 副菜提案
- パターン7: 汁物提案
- パターン8: 副菜追加提案
- パターン9: 汁物追加提案

## 関連ドキュメント

- [Phase 2.5-1: 概要](../../plan_Phase_2.5_1_overview.md)
- [Phase 2.5-2: テスト計画](../../plan_Phase_2.5_2_testing.md)
- [Phase 2.5-3: 実装計画](../../plan_Phase_2.5_3_implementation.md)

