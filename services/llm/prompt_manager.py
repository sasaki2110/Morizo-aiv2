#!/usr/bin/env python3
"""
PromptManager - プロンプト管理

LLMServiceから分離したプロンプト管理専用クラス
プロンプト構築と動的プロンプト生成を担当
"""

from typing import Dict, Any
from config.loggers import GenericLogger


class PromptManager:
    """プロンプト管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.prompt")
    
    def build_planning_prompt(self, user_request: str) -> str:
        """
        タスク分解用のプロンプトを構築（サービスメソッド名対応版）
        
        Args:
            user_request: ユーザーリクエスト
        
        Returns:
            構築されたプロンプト
        """
        planning_prompt = f"""
ユーザー要求を分析し、適切なサービスクラスのメソッド呼び出しに分解してください。

ユーザー要求: "{user_request}"

利用可能なサービスと機能:

- **inventory_service**: 在庫管理サービス
  - `get_inventory()`: 現在の全在庫アイテムのリストを取得します。
  - `add_inventory(item_name: str, quantity: float, ...)`: 在庫に新しいアイテムを追加します。
  - `update_inventory(item_identifier: str, updates: dict, strategy: str)`: 在庫情報を更新します。strategyには 'by_id', 'by_name', 'by_name_oldest', 'by_name_latest' が指定可能です。
  - `delete_inventory(item_identifier: str, strategy: str)`: 在庫を削除します。strategyには 'by_id', 'by_name', 'by_name_oldest', 'by_name_latest' が指定可能です。

- **recipe_service**: レシピ・献立サービス
  - `generate_menu_plan(inventory_items: list, user_id: str, ...)`: 在庫リストに基づき、LLMによる独創的な献立提案を行います。過去の履歴も考慮します。
  - `search_menu_from_rag(query: str, user_id: str, ...)`: RAGを使用して過去の献立履歴から類似の献立を検索します。
  - `search_recipes_from_web(recipe_name: str, ...)`: 指定された料理名のレシピをWeb検索し、URLを含む詳細情報を返します。
  - `get_recipe_history(user_id: str, ...)`: 過去の料理履歴を取得します。

- **session_service**: セッション管理サービス（通常は直接呼び出し不要）

**最重要ルール: タスク生成の条件分岐**

1. **在庫操作のみの場合**: ユーザーの要求が「追加」「削除」「更新」「確認」等の在庫操作のみの場合、該当する在庫操作タスクのみを生成してください。
   
   **例**:
   - 「ピーマンを４個追加して」→ `inventory_service.add_inventory()` のみ
   - 「牛乳を削除して」→ `inventory_service.delete_inventory()` のみ  
   - 「在庫を確認して」→ `inventory_service.get_inventory()` のみ

2. **献立生成の場合**: ユーザーの要求が「献立」「レシピ」「メニュー」等の献立提案に関する場合のみ、以下の4段階のタスク構成を使用してください：
   
   **例**:
   - 「献立を教えて」→ 4段階タスク構成
   - 「レシピを提案して」→ 4段階タスク構成
   - 「在庫から作れるメニューは？」→ 4段階タスク構成

   a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。
   b. **task2**: `recipe_service.generate_menu_plan()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。
   c. **task3**: `recipe_service.search_menu_from_rag()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。
   d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際、ステップ2とステップ3の結果を適切に処理する。

**並列実行の指示**: task2とtask3は並列で実行可能です。dependenciesにtask1のみを指定してください。

**献立データの処理ルール**:
- task2とtask3の結果は辞書形式の献立データです（main_dish, side_dish, soupフィールドを含む）
- task4では、task2とtask3の両方の結果を統合してレシピ検索を行ってください：
  - `"recipe_titles": ["task2.result.main_dish", "task2.result.side_dish", "task2.result.soup", "task3.result.main_dish", "task3.result.side_dish", "task3.result.soup"]`
  - または、主菜のみ: `"recipe_titles": ["task2.result.main_dish", "task3.result.main_dish"]`

**パラメータ注入のルール**:
- 先行タスクの結果を後続タスクのパラメータに注入する場合は、必ず `"先行タスク名.result"` 形式を使用してください。
- 辞書フィールド参照の場合は `"先行タスク名.result.フィールド名"` 形式を使用してください。
- 例: task1の結果をtask2で使用する場合 → `"inventory_items": "task1.result"`
- 例: task2の主菜をtask4で使用する場合 → `"recipe_title": "task2.result.main_dish"`
- この形式により、システムが自動的に先行タスクの結果を後続タスクに注入します。

**在庫操作のstrategy判定について**:
- ユーザーが「古い方」「最新」「全部」などを明示しない限り、`update_inventory` や `delete_inventory` の `strategy` パラメータは `'by_name_with_ambiguity_check'` を指定してください。これにより、サービス層でユーザーへの確認プロセスが起動します。

**strategy判定の重要ルール**:
1. **「全部」「すべて」の判定**: ユーザー要求に「全部」「すべて」が含まれている場合、語順に関係なく `strategy='by_name'` を指定してください。
2. **「古い」「最新」の判定**: ユーザー要求に「古い」「最新」が含まれている場合、該当するstrategyを指定してください。
3. **曖昧性の判定**: 上記のキーワードが含まれていない場合のみ `strategy='by_name_with_ambiguity_check'` を指定してください。

**判定例**:
- 「牛乳を全部１本に変えて」→ 「全部」が含まれている → `strategy='by_name'`
- 「全部の牛乳を１本にして」→ 「全部」が含まれている → `strategy='by_name'`
- 「牛乳をすべて削除して」→ 「すべて」が含まれている → `strategy='by_name'`
- 「牛乳を１本に変えて」→ キーワードなし → `strategy='by_name_with_ambiguity_check'`

**⚠️ 重要: 「変えて」の認識ルール**:
- 「変えて」「変更して」「修正して」等のキーワードは**必ず更新操作**として認識してください
- 「変えて」要求に対して**削除+追加の組み合わせは絶対に生成しないでください**
- 「変えて」は既存アイテムの数量や属性を変更する操作であり、新しいアイテムの追加ではありません

**strategy判定の例**:
- 「牛乳を更新/削除して」 → `strategy='by_name_with_ambiguity_check'` (曖昧)
- 「古い牛乳を更新/削除して」 → `strategy='by_name_oldest'` (最古)
- 「最新の牛乳を更新/削除して」 → `strategy='by_name_latest'` (最新)
- 「全部の牛乳を更新/削除して」 → `strategy='by_name'` (全部)

**「変えて」の具体例（更新操作）**:
- 「最新の牛乳を5本に変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'quantity': 5}}, strategy='by_name_latest')`
- 「一番古いピーマンを3個に変えて」 → `inventory_service.update_inventory(item_identifier='ピーマン', updates={{'quantity': 3}}, strategy='by_name_oldest')`
- 「牛乳の保存場所を冷凍庫に変えて」 → `inventory_service.update_inventory(item_identifier='牛乳', updates={{'storage_location': '冷凍庫'}}, strategy='by_name_with_ambiguity_check')`
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
            "parameters": {{ "inventory_items": "task1.result", "user_id": "user123" }},
            "dependencies": ["task1"]
        }},
        {{
            "id": "task3",
            "description": "在庫リストに基づき、RAGを使用して過去の献立履歴から類似献立を検索する",
            "service": "recipe_service",
            "method": "search_menu_from_rag",
            "parameters": {{ "inventory_items": "task1.result", "user_id": "user123" }},
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
                "menu_source": "mixed"
            }},
            "dependencies": ["task2", "task3"]
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
        return planning_prompt
    
    def create_dynamic_prompt(
        self, 
        base_prompt: str, 
        tool_descriptions: str,
        user_context: Dict[str, Any]
    ) -> str:
        """
        動的プロンプト生成
        
        Args:
            base_prompt: ベースプロンプト
            tool_descriptions: ツール説明
            user_context: ユーザーコンテキスト
        
        Returns:
            動的プロンプト
        """
        try:
            self.logger.info(f"🔧 [PromptManager] Creating dynamic prompt")
            
            # 動的プロンプトを生成
            dynamic_prompt = f"""
{base_prompt}

{tool_descriptions}

ユーザーコンテキスト:
- ユーザーID: {user_context.get('user_id', 'N/A')}
- セッションID: {user_context.get('session_id', 'N/A')}
- リクエスト時刻: {user_context.get('timestamp', 'N/A')}
"""
            
            self.logger.info(f"✅ [PromptManager] Dynamic prompt created successfully")
            
            return dynamic_prompt
            
        except Exception as e:
            self.logger.error(f"❌ [PromptManager] Error in create_dynamic_prompt: {e}")
            return base_prompt
