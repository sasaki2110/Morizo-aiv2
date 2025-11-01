# Phase 5.1 テスト手順書

## 概要

Phase 5.1で実装した`source`フィールド追加機能が正しく動作していることを確認するためのテスト手順です。

## テストシナリオ

### テストケース1: 主菜選択フロー

**手順**:
1. フロントエンドから「レンコンの主菜を提案して」とリクエスト
2. 主菜候補5件が表示される
3. いずれかの候補を選択して確定
4. 副菜提案に自動遷移

**確認ポイント**:
- ログで各候補の`source`フィールドが正しく設定されているか
- 選択されたレシピの`source`フィールドが保持されているか

## ログ確認箇所

### 1. 候補生成時（`generate_proposals`）

**ログ検索キーワード**: `generate_proposals completed`

**確認内容**:
```
✅ [RECIPE] generate_proposals completed: 5 candidates (LLM: 2, RAG: 3)
🔍 [RECIPE] Candidate 1: title='レンコンのきんぴら', source='llm'
🔍 [RECIPE] Candidate 2: title='レンコンの天ぷら', source='llm'
🔍 [RECIPE] Candidate 3: title='レンコンの筑前煮', source='rag'
🔍 [RECIPE] Candidate 4: title='レンコンのサラダ', source='rag'
🔍 [RECIPE] Candidate 5: title='レンコンの炒め物', source='rag'
```

**期待される結果**:
- 最初の2件が`source='llm'`
- 残りの3件が`source='rag'`

### 2. URL統合時（`web_integrator.integrate`）

**ログ検索キーワード**: `Integrated URLs for candidate`

**確認内容**:
```
🔗 [WebSearchResultIntegrator] Integrated URLs for candidate 0: [...], source: llm
🔗 [WebSearchResultIntegrator] Integrated URLs for candidate 1: [...], source: llm
🔗 [WebSearchResultIntegrator] Integrated URLs for candidate 2: [...], source: rag
```

**期待される結果**:
- 各候補の`source`が正しく保持されている
- URLが統合されても`source`が変更されない

### 3. セッション保存時（`set_candidates`）

**ログ検索キーワード**: `Saving candidate` または `Saved.*candidates to session`

**確認内容**:
```
🔍 [RecipeServiceHandler] Saving candidate 1: title='レンコンのきんぴら', source='llm'
🔍 [RecipeServiceHandler] Saving candidate 2: title='レンコンの天ぷら', source='llm'
🔍 [RecipeServiceHandler] Saving candidate 3: title='レンコンの筑前煮', source='rag'
💾 [RecipeServiceHandler] Saved 5 main candidates to session
```

**期待される結果**:
- 各候補の`source`が正しく保存されている

### 4. レシピ選択時（`get_selected_recipe_from_task`）

**ログ検索キーワード**: `Selected recipe`

**確認内容**:
```
✅ [STAGE] Selected recipe: title='レンコンのきんぴら', source='llm'
```

**期待される結果**:
- 選択されたレシピの`source`が正しく取得されている

### 5. セッション保存時（`set_selected_recipe`）

**ログ検索キーワード**: `Recipe selected for`

**確認内容**:
```
✅ [SESSION] Recipe selected for main: title='レンコンのきんぴら', source='llm'
```

**期待される結果**:
- 選択されたレシピの`source`が正しくセッションに保存されている

## ログファイルの場所

- バックエンドログ: `/app/Morizo-aiv2/morizo_ai.log`
- または、リアルタイムでログを確認: `tail -f /app/Morizo-aiv2/morizo_ai.log`

## ログレベルについて

- `logger.info()`: 通常のログ（常に出力される）
- `logger.debug()`: デバッグログ（詳細情報。ログレベル設定により出力されない場合がある）

**注意**: `logger.debug()`のログが表示されない場合は、ログレベルを調整してください。

## 期待される動作

### 正常系

1. **主菜提案時**:
   - LLM候補（2件）: `source='llm'`
   - RAG候補（3件）: `source='rag'`
   - 合計5件の候補が生成される

2. **レシピ選択時**:
   - 選択されたレシピの`source`が保持される
   - セッションに`source`が保存される

3. **副菜提案時**:
   - 同様に`source`フィールドが設定される
   - 主菜で使った食材を除外した候補が生成される

### 異常系

もし`source='N/A'`と表示された場合は、`source`フィールドが設定されていないことを示します。これは以下の原因が考えられます：

1. 古いコードが実行されている（修正が反映されていない）
2. 予期しない処理フローで候補が生成されている
3. ログレベル設定の問題（デバッグログが出力されていない）

## トラブルシューティング

### デバッグログが表示されない場合

ログレベルを確認してください：
```python
# config/loggers.py などでログレベルを確認
```

### source='N/A'が表示される場合

1. 修正したコードが正しく反映されているか確認
2. サーバーを再起動して最新のコードを読み込んでいるか確認
3. 候補生成のフローを確認（`generate_proposals`が呼ばれているか）

## 次のステップ

Phase 5.1のテストが完了したら、Phase 5A（`/api/menu/save`エンドポイント実装）に進みます。

Phase 5Aでは、`get_selected_recipes()`で取得したレシピの`source`フィールドをDBに保存する処理を実装します。

