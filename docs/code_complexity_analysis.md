# コード複雑度分析レポート - ダイエット候補特定

## サマリー

- **総行数**: 約13,588行（テストファイル除く）
- **主要ディレクトリ別行数**:
  - `services`: 4,937行
  - `mcp_servers`: 3,806行
  - `core`: 2,419行
  - `api`: 1,441行

## 🔴 最優先ダイエット候補（600行以上）

| ファイル | 行数 | クラス | 関数 | メソッド | 合計シンボル | 優先度 |
|---------|------|--------|------|----------|--------------|--------|
| `services/session/service.py` | 614 | 1 | 2 | 2 | 5 | 🔴 高 |
| `services/llm/response_processor.py` | 569 | 1 | 9 | 9 | 19 | 🔴 高 |
| `services/llm/response_formatters.py` | 545 | 1 | 20 | 20 | 41 | 🔴 高 |

## 🟡 高優先度ダイエット候補（400-600行）

| ファイル | 行数 | クラス | 関数 | メソッド | 合計シンボル | 優先度 |
|---------|------|--------|------|----------|--------------|--------|
| `core/executor.py` | 461 | 1 | 8 | 8 | 17 | 🟡 中 |
| `mcp_servers/recipe_mcp.py` | 439 | 0 | 1 | 0 | 1 | 🟡 中 |
| `mcp_servers/recipe_llm.py` | 433 | 1 | 7 | 7 | 15 | 🟡 中 |
| `api/routes/chat.py` | 388 | 0 | 1 | 0 | 1 | 🟡 中 |
| `services/tool_router.py` | 372 | 3 | 6 | 6 | 15 | 🟡 中 |

## 🟢 中優先度ダイエット候補（300-400行）

| ファイル | 行数 | クラス | 関数 | メソッド | 合計シンボル | 優先度 |
|---------|------|--------|------|----------|--------------|--------|
| `core/handlers/confirmation_handler.py` | 360 | 1 | 4 | 4 | 9 | 🟢 低 |
| `mcp_servers/recipe_rag/menu_format.py` | 360 | - | - | - | - | 🟢 低 |
| `core/handlers/selection_handler.py` | 353 | 1 | 1 | 1 | 3 | 🟢 低 |
| `services/session/models.py` | 345 | 1 | 22 | 21 | 44 | 🟢 低（複雑度高） |

## 📊 ディレクトリ別詳細分析

### services/ (4,937行)
- `services/session/`: 973行
  - `service.py`: 614行 ⚠️ 最大
  - `models.py`: 345行（メソッド21個）⚠️ 複雑度高
- `services/llm/`: 1,883行
  - `response_processor.py`: 569行 ⚠️ 最大
  - `response_formatters.py`: 545行（メソッド20個）⚠️ 複雑度最高
  - `prompt_manager/`: 307行
    - `patterns/`: 361行

### core/ (2,419行)
- `core/handlers/`: 917行
  - `confirmation_handler.py`: 360行
  - `selection_handler.py`: 353行
- `core/executor.py`: 461行 ⚠️ 最大

### mcp_servers/ (3,806行)
- `recipe_rag/`: 1,162行
  - `menu_format.py`: 360行
  - `client.py`: 332行
  - `search.py`: 326行
- `recipe_mcp.py`: 439行 ⚠️ 最大
- `recipe_llm.py`: 433行

### api/ (1,441行)
- `routes/`: 645行
  - `chat.py`: 388行 ⚠️ 最大

## 🎯 推奨リファクタリング戦略

### 1. `services/session/service.py` (614行)
**問題点**: 
- 単一クラスに多くの機能が集中
- メソッドが少ない（2個）のに行数が多い = メソッドが長すぎる可能性

**推奨アクション**:
- セッション操作メソッドをグループ化（提案管理、確認状態管理、コンテキスト管理など）
- 各グループを別のクラスまたはモジュールに分離

### 2. `services/llm/response_formatters.py` (545行, メソッド20個)
**問題点**:
- メソッドが20個と多い = 単一責任の原則違反の可能性

**推奨アクション**:
- フォーマッターをカテゴリ別に分割
  - `MenuFormatter` (献立フォーマット)
  - `InventoryFormatter` (在庫フォーマット)
  - `RecipeFormatter` (レシピフォーマット)
  - など

### 3. `services/llm/response_processor.py` (569行, メソッド9個)
**問題点**:
- レスポンス処理のロジックが集中しすぎている

**推奨アクション**:
- レスポンス処理のステップを分離
  - データ変換
  - フォーマット処理
  - エラーハンドリング

### 4. `services/session/models.py` (345行, メソッド21個)
**問題点**:
- モデルクラスにビジネスロジックが多すぎる

**推奨アクション**:
- ビジネスロジックをモデルから分離
- ヘルパー関数を別モジュールに移動

### 5. `core/executor.py` (461行)
**問題点**:
- タスク実行ロジックが集中

**推奨アクション**:
- 実行前処理、実行中処理、実行後処理を分離
- エラーハンドリングを別モジュールに

### 6. `mcp_servers/recipe_mcp.py` (439行, 関数1個)
**問題点**:
- 単一のファイルに複数のMCPツールが定義されている
- 関数が1個しかカウントされていない = デコレータで定義されている可能性

**推奨アクション**:
- MCPツールを機能別に分割
  - `recipe_generation.py`
  - `recipe_search.py`
  - `recipe_history.py`

### 7. `api/routes/chat.py` (388行)
**問題点**:
- ルートハンドラーが大きい

**推奨アクション**:
- エンドポイントごとにファイル分割
- ビジネスロジックをサービス層に移動

## 📈 複雑度指標

### 複雑度が高いファイル（シンボル数が多い順）
1. `services/session/models.py`: 44シンボル（メソッド21個）
2. `services/llm/response_formatters.py`: 41シンボル（メソッド20個）
3. `services/llm/response_processor.py`: 19シンボル（メソッド9個）
4. `core/executor.py`: 17シンボル（メソッド8個）
5. `mcp_servers/recipe_llm.py`: 15シンボル（メソッド7個）

## 🔍 追加調査推奨項目

1. **重複コードの検出**: 類似のメソッドが複数ファイルに存在しないか
2. **循環依存の確認**: 特に`services/`と`core/`の間
3. **テストカバレッジ**: 大きいファイルのテストが十分か
4. **インポート依存関係**: モジュール間の依存度が高すぎないか

## ✅ 次のステップ

1. **Phase 1**: `services/session/service.py`の分割
2. **Phase 2**: `services/llm/response_formatters.py`の分割
3. **Phase 3**: `services/llm/response_processor.py`のリファクタリング
4. **Phase 4**: `mcp_servers/recipe_mcp.py`の分割

