#!/usr/bin/env python3
"""
献立生成プロンプトビルダー
"""

from ..utils import build_base_prompt


def build_menu_prompt(user_request: str, user_id: str) -> str:
    """献立生成用のプロンプトを構築"""
    base = build_base_prompt()
    
    return f"""
{base}

ユーザー要求: "{user_request}"

**献立生成の4段階タスク構成**:

ユーザーの要求が「献立」「レシピ」「メニュー」等の献立提案に関する場合のみ、以下の4段階のタスク構成を使用してください。

**例**:
- 「献立を教えて」→ 4段階タスク構成
- 「レシピを提案して」→ 4段階タスク構成
- 「在庫から作れるメニューは？」→ 4段階タスク構成

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `recipe_service.generate_menu_plan()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。

c. **task3**: `recipe_service.search_menu_from_rag()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際、ステップ2とステップ3の結果を適切に処理する。

**献立データの処理ルール**:
- task2とtask3の結果は辞書形式の献立データです（main_dish, side_dish, soupフィールドを含む）
- task4では、task2とtask3の両方の結果を統合してレシピ検索を行ってください：
  - `"recipe_titles": ["task2.result.main_dish", "task2.result.side_dish", "task2.result.soup", "task3.result.main_dish", "task3.result.side_dish", "task3.result.soup"]`
  - または、主菜のみ: `"recipe_titles": ["task2.result.main_dish", "task3.result.main_dish"]`

**献立生成の具体例（サービスメソッド名対応）**:
{{
    "tasks": [
        {{
            "id": "task1",
            "description": "現在の全在庫アイテムのリストを取得する",
            "service": "inventory_service",
            "method": "get_inventory",
            "parameters": {{}},
            "dependencies": []
        }},
        {{
            "id": "task2",
            "description": "在庫リストに基づき、LLMによる独創的な献立を提案する",
            "service": "recipe_service",
            "method": "generate_menu_plan",
            "parameters": {{ "inventory_items": "task1.result", "user_id": "{user_id}" }},
            "dependencies": ["task1"]
        }},
        {{
            "id": "task3",
            "description": "在庫リストに基づき、RAGを使用して過去の献立履歴から類似献立を検索する",
            "service": "recipe_service",
            "method": "search_menu_from_rag",
            "parameters": {{ "inventory_items": "task1.result", "user_id": "{user_id}" }},
            "dependencies": ["task1"]
        }},
        {{
            "id": "task4",
            "description": "提案された献立のレシピをWeb検索して詳細情報を取得する",
            "service": "recipe_service",
            "method": "search_recipes_from_web",
            "parameters": {{ 
                "recipe_titles": ["task2.result.main_dish", "task2.result.side_dish", "task2.result.soup", "task3.result.main_dish", "task3.result.side_dish", "task3.result.soup"],
                "menu_categories": ["main_dish", "side_dish", "soup", "main_dish", "side_dish", "soup"],
                "menu_source": "mixed",
                "num_results": 3
            }},
            "dependencies": ["task2", "task3"]
        }}
    ]
}}
"""

