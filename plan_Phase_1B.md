# Phase 1B: プランナー・タスク設計拡張

## 概要

主菜5件提案機能を既存のタスクプランナーに統合し、動的タスク構築とコンテキスト管理機能を実装します。ユーザー要求の認識、主要食材の保存、曖昧性検出を追加します。

## 対象範囲

- プランナープロンプトの更新（新ツール認識）
- 動的タスク構築機能
- コンテキスト管理（主要食材保存）
- 曖昧性検出の拡張（主要食材未指定時）

## 実装計画

### 1. プランナープロンプトの更新

**修正ファイル**: `services/llm/prompt_manager.py`

**変更内容**:
- `build_planning_prompt()`に新ツール`generate_main_dish_proposals`の説明を追加
- ユーザー要求が「主菜を提案して」等の場合に新ツールを使用するよう指示
- **主要食材パラメータの説明を追加**

**実装箇所**: 43-47行目の`recipe_service`セクションに追加
```python
- **recipe_service**: レシピ・献立サービス
  - `generate_main_dish_proposals(inventory_items: list, user_id: str, main_ingredient: str, ...)`: 主菜5件を提案します（LLM 2件 + RAG 3件）。main_ingredientで主要食材を指定可能。主要食材が未指定の場合は曖昧性検出が発動し、ユーザーに「食材を指定する」または「指定せずに提案する」の選択肢を提示します。
  - `generate_menu_plan(inventory_items: list, user_id: str, ...)`: 在庫リストに基づき、LLMによる独創的な献立提案を行います。
  - `search_menu_from_rag(query: str, user_id: str, ...)`: RAGを使用して過去の献立履歴から類似の献立を検索します。
  - `search_recipes_from_web(recipe_name: str, ...)`: 指定された料理名のレシピをWeb検索し、URLを含む詳細情報を返します。
  - `get_recipe_history(user_id: str, ...)`: 過去の料理履歴を取得します。
```

**追加するプロンプトルール**:
```python
**主菜提案のタスク生成ルール**:

3. **主菜提案の場合**: ユーザーの要求が「主菜」「メイン」「主菜を提案して」等の主菜提案に関する場合、以下の2段階のタスク構成を使用してください：
   
   **例**:
   - 「主菜を5件提案して」→ 2段階タスク構成
   - 「レンコンを使った主菜を教えて」→ 2段階タスク構成
   - 「メインを提案して」→ 2段階タスク構成

   a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。
   b. **task2**: `recipe_service.generate_main_dish_proposals()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。

**主要食材の抽出ルール**:
- ユーザー要求に「○○を使った」「○○で」「○○を主に」等の表現がある場合、○○を `main_ingredient` パラメータに設定してください。
- 例: 「レンコンを使った主菜を提案して」→ `main_ingredient: "レンコン"`
- 例: 「キャベツでメインを作って」→ `main_ingredient: "キャベツ"`
- 例: 「主菜を提案して」→ `main_ingredient: null` (曖昧性検出が発動し、ユーザーに選択肢を提示)

**パラメータ注入のルール**:
- task1の結果をtask2で使用する場合 → `"inventory_items": "task1.result"`
- 主要食材がある場合 → `"main_ingredient": "抽出された食材名"`
- 主要食材がない場合 → `"main_ingredient": null`
```

### 2. 動的タスク構築機能

**新規ファイル**: `core/dynamic_task_builder.py`

**変更内容**:
- ユーザー反応に応じてタスクを動的に追加・変更する機能
- 主要食材のコンテキスト管理
- タスクチェーンの状態管理

**実装例**:
```python
class DynamicTaskBuilder:
    """動的タスク構築クラス"""
    
    def __init__(self, task_chain_manager: TaskChainManager):
        self.task_chain_manager = task_chain_manager
        self.context = {}  # コンテキスト管理
        self.logger = GenericLogger("core", "dynamic_task_builder")
    
    def set_context(self, key: str, value: Any) -> None:
        """コンテキストを設定"""
        self.context[key] = value
        self.logger.info(f"📝 [DynamicTaskBuilder] Context set: {key} = {value}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """コンテキストを取得"""
        return self.context.get(key, default)
    
    def add_main_dish_proposal_task(
        self, 
        inventory_items: List[str], 
        user_id: str,
        main_ingredient: str = None,
        menu_type: str = "",
        excluded_recipes: List[str] = None
    ) -> Task:
        """主菜提案タスクを追加"""
        
        # 主要食材をコンテキストに保存
        if main_ingredient:
            self.set_context("main_ingredient", main_ingredient)
        
        task = Task(
            id=f"main_dish_proposal_{len(self.task_chain_manager.tasks)}",
            service="recipe_service",
            method="generate_main_dish_proposals",
            parameters={
                "inventory_items": inventory_items,
                "user_id": user_id,
                "main_ingredient": main_ingredient,
                "menu_type": menu_type,
                "excluded_recipes": excluded_recipes
            },
            dependencies=[],
            status=TaskStatus.PENDING
        )
        
        self.logger.info(f"➕ [DynamicTaskBuilder] Added main dish proposal task: {task.id}")
        return task
    
    def add_inventory_task(self, user_id: str) -> Task:
        """在庫取得タスクを追加"""
        task = Task(
            id=f"inventory_get_{len(self.task_chain_manager.tasks)}",
            service="inventory_service",
            method="get_inventory",
            parameters={"user_id": user_id},
            dependencies=[],
            status=TaskStatus.PENDING
        )
        
        self.logger.info(f"➕ [DynamicTaskBuilder] Added inventory task: {task.id}")
        return task
```

### 3. コンテキスト管理機能

**新規ファイル**: `core/context_manager.py`

**変更内容**:
- セッション内でのコンテキスト管理
- 主要食材の保存と取得
- タスク間でのデータ共有

**実装例**:
```python
class ContextManager:
    """コンテキスト管理クラス"""
    
    def __init__(self, sse_session_id: str):
        self.sse_session_id = sse_session_id
        self.context = {}
        self.logger = GenericLogger("core", "context_manager")
    
    def set_main_ingredient(self, ingredient: str) -> None:
        """主要食材を設定"""
        self.context["main_ingredient"] = ingredient
        self.logger.info(f"🥬 [ContextManager] Main ingredient set: {ingredient}")
    
    def get_main_ingredient(self) -> Optional[str]:
        """主要食材を取得"""
        return self.context.get("main_ingredient")
    
    def set_inventory_items(self, items: List[str]) -> None:
        """在庫食材を設定"""
        self.context["inventory_items"] = items
        self.logger.info(f"📦 [ContextManager] Inventory items set: {len(items)} items")
    
    def get_inventory_items(self) -> List[str]:
        """在庫食材を取得"""
        return self.context.get("inventory_items", [])
    
    def clear_context(self) -> None:
        """コンテキストをクリア"""
        self.context.clear()
        self.logger.info("🧹 [ContextManager] Context cleared")
    
    def get_context(self) -> Dict[str, Any]:
        """全コンテキストを取得"""
        return self.context.copy()
```

### 4. 曖昧性検出の拡張

**修正ファイル**: `services/confirmation/ambiguity_detector.py`

**変更内容**:
- 主菜提案要求で主要食材が未指定の場合の曖昧性検出を追加
- 在庫食材から主要食材候補を提示

**実装例**:
```python
async def check_main_dish_ambiguity(
    self, 
    task: Any, 
    user_id: str,
    token: str = ""
) -> Optional[AmbiguityInfo]:
    """主菜提案の曖昧性チェック（主要食材未指定時の柔軟な選択肢提示）"""
    
    if task.method == "generate_main_dish_proposals":
        # 主要食材が指定されていない場合
        main_ingredient = task.parameters.get("main_ingredient")
        if not main_ingredient:
            return AmbiguityInfo(
                is_ambiguous=True,
                task_id=task.id,
                details={
                    "message": "なにか主な食材を指定しますか？それとも今の在庫から作れる主菜を提案しましょうか？",
                    "type": "main_ingredient_optional_selection",
                    "options": [
                        {"value": "specify", "label": "食材を指定する"},
                        {"value": "proceed", "label": "指定せずに提案してもらう"}
                    ],
                    "task_type": "main_dish_proposal"
                }
            )
    
    return None
```

### 5. 確認プロセス処理の拡張

**修正ファイル**: `services/confirmation/response_parser.py`

**変更内容**:
- 主要食材選択の確認プロセス処理を柔軟な選択肢対応に変更
- 「指定せずに進める」パターンの処理を追加
- ユーザー選択に基づくタスク更新

**実装例**:
```python
async def process_main_ingredient_confirmation(
    self,
    ambiguity_info: AmbiguityInfo,
    user_response: str,
    context: Dict[str, Any]
) -> ConfirmationResult:
    """主要食材選択の確認プロセス処理（柔軟な選択肢対応）"""
    
    # パターン1: 指定せずに進める
    proceed_keywords = ["いいえ", "そのまま", "提案して", "在庫から", "このまま", "進めて", "指定しない", "2"]
    if any(keyword in user_response for keyword in proceed_keywords):
        return ConfirmationResult(
            is_confirmed=True,
            updated_tasks=context.get("original_tasks", []),  # main_ingredient: null のまま
            message="在庫から作れる主菜を提案します。"
        )
    
    # パターン2: 食材を指定する
    # 食材名を抽出（既存の食材認識ロジックを活用）
    specified_ingredient = self._extract_ingredient_from_response(user_response)
    if specified_ingredient:
        updated_tasks = self._update_task_with_main_ingredient(
            context.get("original_tasks", []),
            ambiguity_info.task_id,
            specified_ingredient
        )
        return ConfirmationResult(
            is_confirmed=True,
            updated_tasks=updated_tasks,
            message=f"主要食材を「{specified_ingredient}」に設定しました。"
        )
    
    # パターン3: 認識できない応答
    return ConfirmationResult(
        is_confirmed=False,
        updated_tasks=[],
        message="すみません、理解できませんでした。食材名を指定するか、「そのまま提案して」とお答えください。"
    )

def _extract_ingredient_from_response(self, user_response: str) -> Optional[str]:
    """ユーザー応答から食材名を抽出"""
    # 既存の食材認識ロジックを活用
    # 例: "サバで"、"レンコンを使って"、"キャベツ" など
    # この実装は既存の食材認識機能に依存
    return None  # 実装は既存機能に依存

def _update_task_with_main_ingredient(
    self, 
    tasks: List[Task], 
    task_id: str, 
    main_ingredient: str
) -> List[Task]:
    """主要食材を設定してタスクを更新"""
    updated_tasks = []
    
    for task in tasks:
        if task.id == task_id:
            # 主要食材を設定
            task.parameters["main_ingredient"] = main_ingredient
            updated_tasks.append(task)
        else:
            updated_tasks.append(task)
    
    return updated_tasks
```

### 7. ToolRouterの更新

**修正ファイル**: `services/tool_router.py`

**変更内容**:
- `service_method_mapping`に新しいマッピングを追加
- Phase 1Aで追加された`generate_main_dish_proposals`ツールを`recipe_service`のメソッドとしてマッピング

**実装例**:
```python
class ToolRouter:
    def __init__(self):
        # 既存のMCPクライアントを使用
        self.mcp_client = MCPClient()
        
        # MCP Clientのマッピングを参照
        self.tool_server_mapping = self.mcp_client.tool_server_mapping
        
        # サービス名・メソッド名からMCPツール名へのマッピング
        self.service_method_mapping = {
            # InventoryService のマッピング
            ("inventory_service", "get_inventory"): "inventory_list",
            ("inventory_service", "add_inventory"): "inventory_add",
            ("inventory_service", "update_inventory"): "inventory_update_by_id",
            ("inventory_service", "delete_inventory"): "inventory_delete_by_id",
            
            # RecipeService のマッピング
            ("recipe_service", "generate_menu_plan"): "generate_menu_plan_with_history",
            ("recipe_service", "search_menu_from_rag"): "search_menu_from_rag_with_history",
            ("recipe_service", "search_recipes_from_web"): "search_recipe_from_web",
            ("recipe_service", "get_recipe_history"): "get_recipe_history_for_user",
            
            # Phase 1Aで追加された新ツールのマッピング
            ("recipe_service", "generate_main_dish_proposals"): "generate_main_dish_proposals",
        }
        
        self.logger = GenericLogger("service", "tool_router")
```

**重要**: このマッピングにより、Core LayerからのタスクでService.Method形式（`recipe_service.generate_main_dish_proposals`）で呼び出された際に、ToolRouterが適切にMCPツール名（`generate_main_dish_proposals`）に変換してMCP層にルーティングします。

**データフローの確認**:
```
1. Core Layer: Task(service="recipe_service", method="generate_main_dish_proposals", ...)
   ↓
2. ServiceCoordinator: execute_service("recipe_service", "generate_main_dish_proposals", ...)
   ↓
3. ToolRouter: route_service_method("recipe_service", "generate_main_dish_proposals", ...)
   ↓ (service_method_mapping でツール名に変換)
4. ToolRouter: route_tool("generate_main_dish_proposals", ...)
   ↓
5. MCPClient: call_tool("generate_main_dish_proposals", ...)
   ↓
6. MCP Layer: recipe_mcp.py の generate_main_dish_proposals() ツール実行
```


## テスト計画

### 単体テスト
1. プランナープロンプトが正しく更新されることを確認
2. 動的タスク構築機能が正しく動作することを確認
3. コンテキスト管理機能が正しく動作することを確認
4. 曖昧性検出が正しく動作することを確認

### 統合テスト
1. ユーザー要求「主菜を5件提案して」で正しくタスクが生成されることを確認
2. ユーザー要求「レンコンを使った主菜を提案して」で主要食材が正しく抽出されることを確認
3. 主要食材未指定時の曖昧性検出が正しく動作することを確認
4. 確認プロセス後のタスク更新が正しく動作することを確認

## 制約事項
- Phase 1Aの基本機能が完成している必要がある
- 既存のタスク実行フローとの整合性を保つ
- セッション管理との連携が必要

## 期待される効果
- ユーザー要求の認識精度が向上
- 主要食材を考慮した提案が可能
- 曖昧性検出によりユーザー体験が向上
- 動的タスク構築の基盤が完成

### To-dos

- [ ] プランナープロンプトに新ツールの説明を追加（prompt_manager.py）
- [ ] 動的タスク構築機能を core/dynamic_task_builder.py に実装
- [ ] コンテキスト管理機能を core/context_manager.py に実装
- [ ] 主菜提案の曖昧性検出機能を ambiguity_detector.py に追加
- [ ] 主要食材選択の確認プロセス処理を response_parser.py に追加
- [ ] TrueReactAgentに動的タスク構築機能を統合（agent.py）
- [ ] ToolRouterのservice_method_mappingに新ツールマッピングを追加（tool_router.py）
- [ ] Phase 1Bの統合テスト: プランナー・タスク設計拡張の動作確認
