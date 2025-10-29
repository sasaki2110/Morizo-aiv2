#!/usr/bin/env python3
"""
PromptManager Utils - 共通ユーティリティ

共通のベースプロンプトやヘルパー関数を提供
"""

def build_base_prompt() -> str:
    """共通ベースプロンプトを構築"""
    return """
ユーザー要求を分析し、適切なサービスクラスのメソッド呼び出しに分解してください。

利用可能なサービスと機能:

- **inventory_service**: 在庫管理サービス
  - `get_inventory()`: 現在の全在庫アイテムのリストを取得します。
  - `add_inventory(item_name: str, quantity: float, ...)`: 在庫に新しいアイテムを追加します。
  - `update_inventory(item_identifier: str, updates: dict, strategy: str)`: 在庫情報を更新します。strategyには 'by_id', 'by_name', 'by_name_all', 'by_name_oldest', 'by_name_latest' が指定可能です。
  - `delete_inventory(item_identifier: str, strategy: str)`: 在庫を削除します。strategyには 'by_id', 'by_name', 'by_name_all', 'by_name_oldest', 'by_name_latest' が指定可能です。

- **recipe_service**: レシピ・献立サービス
  - `generate_proposals(inventory_items: list, user_id: str, category: str, main_ingredient: str, excluded_recipes: list, ...)`: 主菜・副菜・汁物5件を提案します（LLM 2件 + RAG 3件）。categoryで"main"/"sub"/"soup"を指定。main_ingredientで主要食材を指定可能。excluded_recipesで重複回避対象のレシピタイトルを指定。
  - `generate_menu_plan(inventory_items: list, user_id: str, ...)`: 在庫リストに基づき、LLMによる独創的な献立提案を行います。過去の履歴も考慮します。
  - `search_menu_from_rag(query: str, user_id: str, ...)`: RAGを使用して過去の献立履歴から類似の献立を検索します。
  - `search_recipes_from_web(recipe_name: str, ...)`: 指定された料理名のレシピをWeb検索し、URLを含む詳細情報を返します。
  - `get_recipe_history(user_id: str, ...)`: 過去の料理履歴を取得します。

- **history_service**: レシピ履歴サービス
  - `history_get_recent_titles(user_id: str, category: str, days: int, ...)`: 指定期間内のレシピタイトルを取得（重複回避用）。categoryは"main"/"sub"/"soup"、daysは日数。

- **session_service**: セッション管理サービス
  - `session_get_proposed_titles(sse_session_id: str, category: str, ...)`: セッション内で提案済みのレシピタイトルを取得（追加提案の重複回避用）。categoryは"main"/"sub"/"soup"。

**パラメータ注入のルール**:
- task1の結果をtask3で使用する場合 → `"inventory_items": "task1.result"`
- task2の結果をtask3で使用する場合 → **必ず** `"excluded_recipes": "task2.result.data"` **を使用してください**（重要: task2.resultではなくtask2.result.dataと指定）
- task3の結果をtask4で使用する場合 → **必ず** `"recipe_titles": "task3.result.data.candidates"` **を使用してください**（重要: recipe_nameではなくrecipe_titlesと指定）
- 主要食材がある場合 → `"main_ingredient": "抽出された食材名"`
- 主要食材がない場合 → `"main_ingredient": null`
- 先行タスクの結果を後続タスクのパラメータに注入する場合は、必ず `"先行タスク名.result"` 形式を使用してください。
- 辞書フィールド参照の場合は `"先行タスク名.result.フィールド名"` 形式を使用してください。
- 例: task1の結果をtask2で使用する場合 → `"inventory_items": "task1.result"`
- 例: task2の主菜をtask4で使用する場合 → `"recipe_title": "task2.result.main_dish"`
- 例: task3の候補をtask4で使用する場合 → `"recipe_titles": "task3.result.data.candidates"`（注意: recipe_nameではなくrecipe_titles）

**在庫操作のstrategy判定について**:
- ユーザーが「古い方」「最新」「全部」などを明示しない限り、`update_inventory` や `delete_inventory` の `strategy` パラメータは `'by_name'` を指定してください。

**strategy判定の重要ルール**:
1. **「全部」「すべて」の判定**: ユーザー要求に「全部」「すべて」が含まれている場合、語順に関係なく `strategy='by_name_all'` を指定してください。
2. **「古い」「最新」の判定**: ユーザー要求に「古い」「最新」が含まれている場合、該当するstrategyを指定してください。
3. **曖昧性の判定**: 上記のキーワードが含まれていない場合は `strategy='by_name'` を指定し、システムが自動的に曖昧性を検知します。

**判定例**:
- 「牛乳を全部１本に変えて」→ 「全部」が含まれている → `strategy='by_name_all'`
- 「全部の牛乳を１本にして」→ 「全部」が含まれている → `strategy='by_name_all'`
- 「牛乳をすべて削除して」→ 「すべて」が含まれている → `strategy='by_name_all'`
- 「牛乳を１本に変えて」→ キーワードなし → `strategy='by_name'` (システムが曖昧性を検知)

**⚠️ 重要: 「変えて」の認識ルール**:
- 「変えて」「変更して」「修正して」等のキーワードは**必ず更新操作**として認識してください
- 「変えて」要求に対して**削除+追加の組み合わせは絶対に生成しないでください**
- 「変えて」は既存アイテムの数量や属性を変更する操作であり、新しいアイテムの追加ではありません

**strategy判定の例**:
- 「牛乳を更新/削除して」 → `strategy='by_name'` (システムが曖昧性を検知)
- 「古い牛乳を更新/削除して」 → `strategy='by_name_oldest'` (最古)
- 「最新の牛乳を更新/削除して」 → `strategy='by_name_latest'` (最新)
- 「全部の牛乳を更新/削除して」 → `strategy='by_name_all'` (全部)

**「変えて」の具体例（更新操作）**:
- 「最新の牛乳を5本に変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'quantity': 5}}, strategy='by_name_latest')`
- 「一番古いピーマンを3個に変えて」 → `inventory_service.update_inventory(item_identifier='ピーマン', updates={{'quantity': 3}}, strategy='by_name_oldest')`
- 「牛乳の保存場所を冷凍庫に変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'storage_location': '冷凍庫'}}, strategy='by_name')`
- 「古い牛乳の単位をパックに変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'unit': 'パック'}}, strategy='by_name_oldest')`

**❌ 禁止パターン（「変えて」要求に対して）**:
- 「変えて」要求で `delete_inventory` + `add_inventory` の組み合わせは絶対に生成しない
- 「変えて」要求で複数タスクに分解しない（必ず1つの `update_inventory` タスクのみ）

**出力形式**: 必ず以下のJSON形式で回答してください（コメントは禁止）：

{{
    "tasks": [
        {{
            "id": "task1",
            "description": "タスクの自然言語での説明",
            "service": "呼び出すサービス名",
            "method": "呼び出すメソッド名",
            "parameters": {{ "key": "value" }},
            "dependencies": []
        }}
    ]
}}

**依存関係のルール**:
- 各タスクには一意のID（task1, task2, ...）を付与してください。
- `dependencies` には、実行前に完了しているべきタスクのIDをリストで指定してください。
- 依存関係がない場合は空配列 `[]` を指定してください。

**挨拶や一般的な会話の場合**:
- タスクは生成せず、空の配列 `{{"tasks": []}}` を返してください。
"""

def build_task_chain_description(tasks: list) -> str:
    """タスクチェーンの説明を構築"""
    lines = []
    for i, task in enumerate(tasks, 1):
        lines.append(f"   {i}. **{task['id']}**: {task['description']}")
    return "\n".join(lines)

