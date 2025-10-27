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

## 期待される効果

- プランナーが副菜・汁物のタスクを生成できるようになる
- 段階的選択システムの基盤が完成

