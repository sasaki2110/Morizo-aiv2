# Phase 2.5-1: 概要（プロンプト肥大化問題の解決）

## 目次

- [概要](#概要)
- [問題の背景](#問題の背景)
- [解決策](#解決策)
- [現在のプロンプトのパターン分類](#現在のプロンプトのパターン分類)
- [パターン別の必要情報まとめ](#パターン別の必要情報まとめ)
- [曖昧性検出のケースまとめ](#曖昧性検出のケースまとめ)
- [関連ドキュメント](#関連ドキュメント)

---

## 概要

Phase 3B でプロンプトが肥大化して破綻した問題を解決するため、リクエスト分析基盤を実装します。
パターンマッチング方式でリクエストを事前判定し、必要なプロンプトのみを動的に構築します。

---

## 問題の背景

### 異常な状況
- プロンプトが270行以上に肥大化
- 主菜提案だけで複雑なルール（在庫操作、献立生成、主菜提案、追加提案、曖昧性解消等）が詰め込まれている
- 副菜・汁物のルールを追加すると、LLMが混乱して正しくタスク生成できない
- プロンプトのトークン数が増大し、コストとレスポンス時間が悪化

### 根本原因
1. **単一のプロンプトに全てのシナリオを詰め込んでいる**
2. **条件分岐が複雑すぎる**（9つのパターンが混在）
3. **プロンプトが静的**（リクエストの種類に応じた動的なプロンプト生成が必要）

---

## 解決策

### 方式B: パターンマッチング分岐（推奨）

**仕組み**:
1. **事前判定**: キーワードベースでパターンを判定
2. **動的プロンプト構築**: 該当パターンのプロンプトのみ構築
3. **LLM呼び出し**: 小さいプロンプトでタスクJSON生成

**メリット**:
- ✓ プロンプトがシンプル（各パターン50-80行程度）
- ✓ LLMが混乱しない（1パターンのみ提示）
- ✓ トークン消費が削減
- ✓ レスポンス時間が改善
- ✓ 保守性が高い（パターン別に管理）
- ✓ テストが容易（パターン別にテスト可能）

---

## 現在のプロンプトのパターン分類

### パターン1: 在庫操作
**キーワード**: 「追加」「削除」「更新」「変えて」「確認」  
**タスク構成**: 単一タスク
- `inventory_service.add_inventory()`
- `inventory_service.update_inventory()`
- `inventory_service.delete_inventory()`
- `inventory_service.get_inventory()`

**必要な情報**:
- 操作種別: add / update / delete / get
- アイテム名: 「牛乳」「ピーマン」等
- 数量: 5本、3個等
- strategy: by_name / by_name_all / by_name_oldest / by_name_latest
- その他属性: 保存場所、単位等

**曖昧性**: 複数の同名アイテム存在 → エージェント実行時に検出（既存機能）

---

### パターン2: 献立生成（従来の一括提案）
**キーワード**: 「献立」「メニュー」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `recipe_service.generate_menu_plan()`
3. `recipe_service.search_menu_from_rag()`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）

**曖昧性**: ほぼなし

---

### パターン3: 主菜提案（初回）
**キーワード**: 「主菜」「メイン」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `history_service.history_get_recent_titles(category="main")`
3. `recipe_service.generate_proposals(category="main")`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- category: "main"
- main_ingredient: 主要食材（オプション）

**曖昧性**: main_ingredient未指定 → 確認質問「食材を指定しますか？」（Phase 1B実装済み）

---

### パターン4: 主菜追加提案
**キーワード**: 「もう5件」「他の提案」「もっと」+ 「主菜」+ sse_session_id存在  
**タスク構成**: 4段階（在庫取得なし）
1. `history_service.history_get_recent_titles(category="main")`
2. `session_service.session_get_proposed_titles(category="main")`
3. `recipe_service.generate_proposals(category="main")` ← セッションから取得
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- sse_session_id（必須）
- category: "main"
- セッションコンテキスト: inventory_items, main_ingredient, menu_type

**曖昧性**: sse_session_id不在 → 初回提案に切り替え

---

### パターン5: 曖昧性解消後の再開（Phase 1E実装済み）
**条件**: セッションに確認待ち状態が存在  
**処理**: 元のリクエスト + ユーザー回答を統合 → パターン1-9に再分類

**必要な情報**:
- 元のリクエスト（セッションから取得）
- ユーザー回答

---

### パターン6: 副菜提案（Phase 3で追加予定）
**キーワード**: 「副菜」「サブ」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `history_service.history_get_recent_titles(category="sub")`
3. `recipe_service.generate_proposals(category="sub", used_ingredients=セッションから取得)`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- category: "sub"
- used_ingredients: 主菜で使った食材（**セッションから取得**）

**曖昧性**: used_ingredients不在（主菜未選択） → 確認質問「まず主菜を選びますか？」

---

### パターン7: 汁物提案（Phase 3で追加予定）
**キーワード**: 「汁物」「味噌汁」「スープ」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `history_service.history_get_recent_titles(category="soup")`
3. `recipe_service.generate_proposals(category="soup", used_ingredients=セッションから取得, menu_category=セッションから判定)`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- category: "soup"
- used_ingredients: 主菜・副菜で使った食材（**セッションから取得**）
- menu_category: "japanese" / "western" / "chinese"（**セッションから判定**）

**曖昧性**: used_ingredients不在（主菜・副菜未選択） → デフォルトで和食（味噌汁）提案 or 確認質問

---

### パターン8: 副菜追加提案（Phase 3で追加予定）
**キーワード**: 「もう5件」+ 「副菜」+ sse_session_id存在  
**タスク構成**: パターン4と同様（category="sub"）

**必要な情報**:
- user_id（必須）
- sse_session_id（必須）
- category: "sub"
- セッションコンテキスト: inventory_items, used_ingredients, menu_type

---

### パターン9: 汁物追加提案（Phase 3で追加予定）
**キーワード**: 「もう5件」+ 「汁物」+ sse_session_id存在  
**タスク構成**: パターン4と同様（category="soup"）

**必要な情報**:
- user_id（必須）
- sse_session_id（必須）
- category: "soup"
- セッションコンテキスト: inventory_items, used_ingredients, menu_category, menu_type

---

## パターン別の必要情報まとめ

| パターン | 必要な情報 | 抽出方法 | セッション依存 |
|---------|----------|---------|--------------|
| 1. 在庫操作 | item_name, quantity, strategy, updates | 正規表現 | なし |
| 2. 献立生成 | user_id | 固定 | なし |
| 3. 主菜提案（初回） | user_id, category="main", main_ingredient(opt) | キーワード+正規表現 | なし |
| 4. 主菜追加提案 | user_id, sse_session_id, category="main" | キーワード | **セッション必須** |
| 5. 曖昧性再開 | 元のリクエスト, ユーザー回答 | セッション | **セッション必須** |
| 6. 副菜提案 | user_id, category="sub", used_ingredients | キーワード | **セッション必須** |
| 7. 汁物提案 | user_id, category="soup", used_ingredients, menu_category | キーワード | **セッション必須** |
| 8. 副菜追加提案 | user_id, sse_session_id, category="sub" | キーワード | **セッション必須** |
| 9. 汁物追加提案 | user_id, sse_session_id, category="soup" | キーワード | **セッション必須** |

---

## 曖昧性検出のケースまとめ

| パターン | 曖昧性のケース | 検出タイミング | 確認質問 |
|---------|-------------|-------------|---------|
| 1. 在庫操作 | 複数の同名アイテム存在 | **エージェント実行時** | 「どの牛乳を削除しますか？」 |
| 3. 主菜提案 | main_ingredient未指定 | **プランナー実行前** | 「食材を指定しますか？」 |
| 4. 主菜追加提案 | sse_session_id不在 | **プランナー実行前** | N/A（初回提案に切り替え） |
| 6. 副菜提案 | used_ingredients不在（主菜未選択） | **プランナー実行前** | 「まず主菜を選びますか？」 |
| 7. 汁物提案 | used_ingredients不在（主菜・副菜未選択） | **プランナー実行前** | 「まず主菜・副菜を選びますか？」or デフォルト和食 |

**曖昧性検出の2つのタイミング**:
1. **プランナー実行前**（事前検出）: リクエスト分析時に検出
2. **エージェント実行時**（実行時検出）: タスク実行中に検出（既存）

---

## 関連ドキュメント

- [Phase 2.5-2: テスト計画（回帰テスト基盤の確立）](./plan_Phase_2.5_2_testing.md)
- [Phase 2.5-3: 実装計画（各サブフェーズの詳細）](./plan_Phase_2.5_3_implementation.md)
- [Phase 3: 副菜・汁物の段階的選択](./plan_Phase_3.md)

