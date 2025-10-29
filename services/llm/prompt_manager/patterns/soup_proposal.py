#!/usr/bin/env python3
"""
汁物提案プロンプトビルダー
"""

from ..utils import build_base_prompt


def build_soup_proposal_prompt(user_request: str, user_id: str, used_ingredients: list = None, menu_category: str = "japanese") -> str:
    """汁物提案用のプロンプトを構築"""
    base = build_base_prompt()
    
    used_ingredients_str = ", ".join(used_ingredients) if used_ingredients else "なし"
    category_name = {"japanese": "和食", "western": "洋食", "chinese": "中華"}.get(menu_category, "和食")
    
    return f"""
{base}

ユーザー要求: "{user_request}"

主菜・副菜で使った食材: {used_ingredients_str}
献立カテゴリ: {category_name} ({menu_category})

**汁物提案の4段階タスク構成**:

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `history_service.history_get_recent_titles(user_id, "soup", 14)` を呼び出し、14日間の汁物履歴を取得する。
   - user_id: "{user_id}"

c. **task3**: `recipe_service.generate_proposals(category="soup")` を呼び出す。その際:
   - `inventory_items`: "task1.result"
   - `excluded_recipes`: "task2.result.data"
   - `category`: "soup"
   - `used_ingredients`: {used_ingredients if used_ingredients else "[]"}
   - `menu_category`: "{menu_category}"
   - `user_id`: "{user_id}"

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際:
   - `recipe_titles`: "task3.result.data.candidates"

**依存関係**: task1 → task2 → task3 → task4 (直列実行が必須)

**重要**: task3はtask2の結果（`excluded_recipes`）に依存するため、task2の完了後に実行してください。
task2のdependenciesは["task1"]、task3のdependenciesは["task1", "task2"]、task4のdependenciesは["task3"]を指定してください。
"""

