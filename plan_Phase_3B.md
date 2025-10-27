# Phase 3B: プランナーの拡張

## 概要

プランナープロンプトに副菜・汁物提案のタスク生成ルールを追加します。

## 対象範囲

- `services/llm/prompt_manager.py`

## 実装計画

### プランナープロンプトの拡張

**修正する場所**: `services/llm/prompt_manager.py` - `build_planning_prompt()`メソッド

**修正する内容**:

```python
- **recipe_service**: レシピ・献立サービス
  - `generate_main_dish_proposals(...)`: 主菜5件を提案（既存）
  - `generate_proposals(category="main", ...)`: 主菜5件を提案（新規・汎用）
  - `generate_proposals(category="sub", used_ingredients=..., ...)`: 副菜5件を提案（新規）
  - `generate_proposals(category="soup", used_ingredients=..., menu_category=..., ...)`: 汁物5件を提案（新規）

- **session_service**: セッション管理サービス（Phase 1Fで実装済み）
  - `session_get_proposed_titles(sse_session_id: str, category: str, ...)`: セッション内で提案済みのレシピタイトルを取得（追加提案の重複回避用）。categoryは"main"/"sub"/"soup"。

**主菜提案（Phase 2で実装済み）**:
- 4段階タスク構成（在庫取得→履歴取得→主菜提案→Web検索）
- ユーザーが主菜を選択

**副菜提案（Phase 3で新規実装）**:
- ユーザーが主菜を選択した後に実行
- 主菜で使った食材を`used_ingredients`として指定
- 4段階タスク構成を使用
  a. task1: 在庫取得
  b. task2: 副菜履歴取得（category="sub", days=14）
  c. task3: 副菜提案（category="sub", used_ingredients=主菜の食材）
  d. task4: Web検索

**汁物提案（Phase 3で新規実装）**:
- ユーザーが副菜を選択した後に実行
- 主菜・副菜で使った食材を`used_ingredients`として指定
- 献立カテゴリ（和食/洋食/中華）を判定して汁物タイプを決定
- 4段階タスク構成を使用
  a. task1: 在庫取得
  b. task2: 汁物履歴取得（category="soup", days=14）
  c. task3: 汁物提案（category="soup", used_ingredients=主菜+副菜の食材, menu_category=判定結果）
  d. task4: Web検索
```

**修正の理由**: 副菜・汁物提案を認識させるため

**修正の影響**: 既存の主菜提案には影響なし（追加のみ）

---

## テスト

### 単体試験

#### プランナープロンプトのテスト
**テストファイル**: `tests/phase3b/test_01_planner_prompt.py`

**テスト項目**:
- 副菜提案のリクエストで副菜タスクが生成されること
- 汁物提案のリクエストで汁物タスクが生成されること
- 4段階タスク構成が正しく生成されること
- used_ingredientsパラメータが正しく設定されること

**テスト例**:
```python
async def test_planner_sub_dish_request():
    """副菜提案リクエストテスト"""
    request = "主菜で使っていない食材で副菜を5件提案して"
    tasks = await action_planner.plan(request, user_id)
    
    # 4段階タスク構成
    assert len(tasks) == 4
    assert tasks[0].method == "get_inventory"
    assert tasks[1].method == "history_get_recent_titles"
    assert tasks[1].parameters["category"] == "sub"
    assert tasks[2].method == "generate_proposals"
    assert tasks[2].parameters["category"] == "sub"
    assert "used_ingredients" in tasks[2].parameters
    assert tasks[3].method == "search_recipes_from_web"

async def test_planner_soup_request():
    """汁物提案リクエストテスト"""
    request = "味噌汁を5件提案して"
    tasks = await action_planner.plan(request, user_id)
    
    # 4段階タスク構成
    assert len(tasks) == 4
    assert tasks[2].method == "generate_proposals"
    assert tasks[2].parameters["category"] == "soup"
    assert "menu_category" in tasks[2].parameters
```

### 結合試験

#### プランナー + エージェントの結合テスト
**テストファイル**: `tests/phase3b/test_02_planner_agent_integration.py`

**テストシナリオ**:
1. 副菜提案リクエストを送信
2. プランナーが4段階タスクを生成
3. タスクが順次実行される
4. 副菜候補が5件返される
5. Web検索結果が含まれる

---

## 期待される効果

- プランナーが副菜・汁物のタスクを生成できるようになる
- 段階的選択システムの基盤が完成

