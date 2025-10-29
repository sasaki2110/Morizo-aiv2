#!/usr/bin/env python3
"""
主菜提案プロンプトビルダー
"""

from ..utils import build_base_prompt


def build_main_proposal_prompt(user_request: str, user_id: str, main_ingredient: str = None) -> str:
    """主菜提案用のプロンプトを構築"""
    base = build_base_prompt()
    
    main_ingredient_info = f"\n主要食材: {main_ingredient}" if main_ingredient else "\n主要食材: 指定なし（在庫から提案）"
    
    return f"""
{base}

ユーザー要求: "{user_request}"
{main_ingredient_info}

**主菜提案の4段階タスク構成**:

ユーザーの要求が「主菜」「メイン」「主菜を提案して」等の主菜提案に関する場合、以下の4段階のタスク構成を使用してください。

**例**:
- 「主菜を5件提案して」→ 4段階タスク構成
- 「レンコンを使った主菜を教えて」→ 4段階タスク構成
- 「メインを提案して」→ 4段階タスク構成

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `history_service.history_get_recent_titles(user_id, "main", 14)` を呼び出し、14日間の主菜履歴を取得する。**重要**: user_idパラメータには実際のユーザーIDを設定してください。例: "{user_id}"

c. **task3**: `recipe_service.generate_proposals(category="main")` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに、ステップ2で取得した履歴タイトルを `excluded_recipes` パラメータに設定する。
      
   **重要**: excluded_recipesパラメータは必ず `"excluded_recipes": "task2.result.data"` と指定してください。`"task2.result"`ではありません。
   {f'主要食材: `"main_ingredient": "{main_ingredient}"`' if main_ingredient else '主要食材: `"main_ingredient": null`'}

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際、ステップ3で取得したレシピタイトルを `recipe_titles` パラメータに設定する。

**依存関係**: task1 → task2 → task3 → task4 (直列実行が必須)

**重要**: task3はtask2の結果（`excluded_recipes`）に依存するため、task2の完了後に実行してください。
task2のdependenciesは["task1"]、task3のdependenciesは["task1", "task2"]、task4のdependenciesは["task3"]を指定してください。
"""

