# Morizo AI v2 - サービス層設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: サービス層のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **サービス層の役割**
- **ビジネスロジックの実装**: 各ドメインのビジネスロジックを実装
- **MCP Client経由のツール呼び出し**: FastMCP Clientを使用したツール通信
- **データ変換**: コア層とMCP層の間でのデータ変換
- **バリデーション**: 入力データの検証
- **エラーハンドリング**: サービス固有のエラー処理

### **責任分離の徹底**
- **RecipeService**: レシピ関連のビジネスロジック
- **InventoryService**: 在庫管理のビジネスロジック
- **RecipeHistoryService**: レシピ履歴のビジネスロジック
- **SessionService**: セッション管理のビジネスロジック
- **LLMService**: LLM呼び出しのコントロール専用
- **ConfirmationService**: 確認プロセスのビジネスロジック

## 🏗️ サービス層アーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                           │
├─────────────────┬─────────────────┬─────────────────────────┤
│  RecipeService  │ InventoryService│    SessionService       │
│  LLMService     │ RecipeHistorySvc│    ConfirmationService  │
│                 │                 │                         │
│ • レシピ生成    │ • 在庫管理      │ • セッション管理        │
│ • レシピ検索    │ • 在庫検索      │ • ユーザー管理          │
│ • 履歴管理      │ • 在庫更新      │ • 認証管理              │
│ • 重複回避      │ • 在庫削除      │ • 権限管理              │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### **データフロー**
```
Core Layer (TrueReactAgent)
    ↓ (Service.Method Call)
Service Layer (各サービスがToolRouterを利用)
    ↓ (Tool Name Call)
ToolRouter (ツール名からMCPサーバーへルーティング)
    ↓ (MCPClient.call_tool)
MCPClient (既存のFastMCPクライアント)
    ↓ (stdio接続)
MCP Layer (各MCPツール)
    ↓ (DB Access, API Call)
External Systems (DB, API, etc.)
```

## 🛠️ ToolRouter統合

**重要: ToolRouterコンポーネントの設計思想**

`ToolRouter`は、`FastMCP`ライブラリが提供する汎用的なクライアント機能のことでは**ありません**。これは、本プロジェクトで**自前で実装する、非常に重要なカスタムコンポーネント**です。

このクラスは「サービスロケータ」あるいは「ルータ」としての役割を担い、サービス層とMCP層を疎結合に保つための要（かなめ）となります。

**責務と動作:**
1.  **ルーティング情報の一元管理:** `ToolRouter`は、どのツール（例: `generate_menu_*`）がどのMCPサーバー（例: `recipe`）に属しているかという対応表（`tool_server_mapping`）を唯一の知識として保持します。
2.  **統一インターフェースの提供:** すべてのサービスクラス（`RecipeService`など）は、具体的なMCPサーバー（`RecipeMCPServer`など）の存在を意識しません。代わりに、この`ToolRouter`のインスタンスを一つだけ受け取り、汎用的な `route_tool("ツール名", ...)` メソッドのみを呼び出します。
3.  **処理の振り分け:** `route_tool`が呼び出されると、`ToolRouter`は内部の対応表に基づき、リクエストを適切なMCPサーバーへ自動的に振り分けます。

この設計により、将来MCPサーバーの構成が変更（例: ツールの移動、サーバーの分割）されたとしても、修正箇所は`ToolRouter`内部の対応表のみに限定され、サービス層のコードには一切影響が及びません。将来のAIは、この設計意図を理解し、`ToolRouter`を上記の責務を持つカスタムクラスとして実装する必要があります。

### **ToolRouterの使用方法**
```python
from mcp_servers.client import MCPClient

class ToolRouter:
    def __init__(self):
        self.mcp_client = MCPClient()  # 既存のMCPクライアントを使用
        self.tool_server_mapping = {
            "inventory_*": "inventory",
            "recipes_*": "recipe_history",
            "generate_menu_*": "recipe",
            "search_recipe_*": "recipe"
        }
    
    async def route_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        token: str
    ) -> Any:
        """ツールを適切なMCPサーバーにルーティング"""
        # 1. 適切なサーバーを選択
        server_name = self._select_server(tool_name)
        
        if not server_name:
            raise ToolNotFoundError(f"Tool {tool_name} not found")
        
        # 2. 既存のMCPクライアントに処理を委譲
        return await self.mcp_client.call_tool(tool_name, parameters, token)
    
    def _select_server(self, tool_name: str) -> str:
        """ツール名に基づいて適切なサーバー名を選択"""
        for pattern, server_name in self.tool_server_mapping.items():
            if fnmatch.fnmatch(tool_name, pattern):
                return server_name
        return None
```

### **サービス層でのToolRouter使用**
```python
class RecipeService:
    def __init__(self, tool_router: ToolRouter):
        self.tool_router = tool_router
    
    async def search_recipes(self, title: str, token: str) -> List[Recipe]:
        """レシピを検索"""
        # ToolRouter経由でツール呼び出し
        result = await self.tool_router.route_tool(
            "search_recipe_from_web",
            {"recipe_titles": [title]},
            token
        )
        return result
```

## 🔧 サービスコンポーネント

### **1. ConfirmationService（確認プロセスサービス）**

#### **役割**
- 曖昧性検出と確認プロセスのビジネスロジック
- タスクチェーン保持

#### **主要機能**
```python
class ConfirmationService:
    async def detect_ambiguity(
        self, 
        tasks: List[Task], 
        user_id: str
    ) -> AmbiguityResult:
        """曖昧性検出"""
        
    async def process_confirmation(
        self, 
        ambiguity_info: AmbiguityInfo,
        user_response: str,
        context: dict
    ) -> ConfirmationResult:
        """確認プロセス処理"""
        
    async def maintain_task_chain(
        self, 
        original_tasks: List[Task],
        confirmation_result: ConfirmationResult
    ) -> List[Task]:
        """タスクチェーン保持"""
```

#### **実装方針**
```python
class ConfirmationService:
    def __init__(self, ambiguity_detector: AmbiguityDetector, confirmation_processor: ConfirmationProcessor):
        self.ambiguity_detector = ambiguity_detector
        self.confirmation_processor = confirmation_processor
    
    async def detect_ambiguity(
        self, 
        tasks: List[Task], 
        user_id: str
    ) -> AmbiguityResult:
        """曖昧性検出"""
        # 1. 各タスクの曖昧性チェック
        ambiguous_tasks = []
        
        for task in tasks:
            if task.tool.startswith("inventory_"):
                # 在庫操作の曖昧性チェック
                ambiguity_info = await self.ambiguity_detector.check_inventory_ambiguity(
                    task, user_id
                )
                if ambiguity_info.is_ambiguous:
                    ambiguous_tasks.append(ambiguity_info)
        
        return AmbiguityResult(
            requires_confirmation=len(ambiguous_tasks) > 0,
            ambiguous_tasks=ambiguous_tasks
        )
    
    async def process_confirmation(
        self, 
        ambiguity_info: AmbiguityInfo,
        user_response: str,
        context: dict
    ) -> ConfirmationResult:
        """確認プロセス処理"""
        # 1. ユーザー応答の解析
        parsed_response = await self.confirmation_processor.parse_user_response(
            user_response, ambiguity_info
        )
        
        # 2. タスクの更新
        updated_tasks = await self.confirmation_processor.update_tasks(
            ambiguity_info.original_tasks, parsed_response
        )
        
        return ConfirmationResult(
            is_cancelled=parsed_response.is_cancelled,
            updated_tasks=updated_tasks,
            confirmation_context=context
        )
```

### **2. RecipeService（レシピ関連サービス）**

#### **主要機能**
```python
class RecipeService:
    async def generate_menu_plan(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食"
    ) -> MenuPlan:
        """在庫食材から献立構成を生成"""
        # ToolRouter経由でRecipeMCPツールを呼び出し
        result = await self.tool_router.route_tool(
            "generate_menu_plan_with_history",
            {
                "inventory_items": inventory_items,
                "user_id": user_id,
                "menu_type": menu_type
            },
            token
        )
        return result
    
    async def search_recipes(
        self, 
        dish_type: str, 
        title: str,
        available_ingredients: List[str]
    ) -> List[Recipe]:
        """レシピを検索"""
        # ToolRouter経由でRecipeMCPツールを呼び出し
        result = await self.tool_router.route_tool(
            "search_recipe_from_web",
            {"recipe_titles": [title]},
            token
        )
        return result
    
    async def check_cooking_history(
        self, 
        user_id: str, 
        recipe_titles: List[str],
        exclusion_days: int = 14
    ) -> CookingHistory:
        """過去の調理履歴をチェック"""
        # ToolRouter経由でRecipeHistoryMCPツールを呼び出し
        result = await self.tool_router.route_tool(
            "history_list",
            {
                "user_id": user_id
            },
            token
        )
        return result
```

#### **実装方針**
```python
class RecipeService:
    def __init__(self, tool_router: ToolRouter):
        self.tool_router = tool_router
    
    # 各メソッドはToolRouter経由でツール呼び出し
    # ビジネスロジックはMCP層で実装
    # データ変換・バリデーションはサービス層で実装
```


### **3. InventoryService（在庫管理サービス）**

#### **役割**
- 在庫管理のビジネスロジック
- FIFO原則による在庫操作
- 在庫検索・更新・削除の制御

#### **主要機能**
```python
class InventoryService:
    async def add_inventory(
        self, 
        user_id: str, 
        item: InventoryItem
    ) -> str:
        """在庫を追加"""
        # ToolRouter経由でInventoryMCPツールを呼び出し
        result = await self.tool_router.route_tool(
            "inventory_add",
            {
                "user_id": user_id,
                "item_name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "storage_location": item.storage_location,
                "expiry_date": item.expiry_date
            },
            token
        )
        return result
        
    async def get_inventory(
        self, 
        user_id: str
    ) -> List[InventoryItem]:
        """在庫一覧を取得"""
        # ToolRouter経由でInventoryMCPツールを呼び出し
        result = await self.tool_router.route_tool(
            "inventory_list",
            {"user_id": user_id},
            token
        )
        return result
        
    async def update_inventory(
        self, 
        user_id: str, 
        item_identifier: str,  # ID または 名前
        updates: Dict[str, Any],
        strategy: str = None  # "by_id", "by_name", "by_name_oldest", "by_name_latest"
    ) -> bool:
        """在庫を更新（呼び出し元で曖昧性解決済み）"""
        # 戦略に基づいて適切なToolRouterツールを呼び出し
        if strategy == "by_id":
            result = await self.tool_router.route_tool(
                "inventory_update_by_id",
                {"user_id": user_id, "item_id": item_identifier, **updates},
                token
            )
        elif strategy == "by_name":
            result = await self.tool_router.route_tool(
                "inventory_update_by_name",
                {"user_id": user_id, "item_name": item_identifier, **updates},
                token
            )
        elif strategy == "by_name_oldest":
            result = await self.tool_router.route_tool(
                "inventory_update_by_name_oldest",
                {"user_id": user_id, "item_name": item_identifier, **updates},
                token
            )
        elif strategy == "by_name_latest":
            result = await self.tool_router.route_tool(
                "inventory_update_by_name_latest",
                {"user_id": user_id, "item_name": item_identifier, **updates},
                token
            )
        else:
            # デフォルト：IDとして扱う
            result = await self.tool_router.route_tool(
                "inventory_update_by_id",
                {"user_id": user_id, "item_id": item_identifier, **updates},
                token
            )
        return result
        
    async def delete_inventory(
        self, 
        user_id: str, 
        item_identifier: str,  # ID または 名前
        strategy: str = None  # "by_id", "by_name", "by_name_oldest", "by_name_latest"
    ) -> bool:
        """在庫を削除（呼び出し元で曖昧性解決済み）"""
        # 戦略に基づいて適切なToolRouterツールを呼び出し
        if strategy == "by_id":
            result = await self.tool_router.route_tool(
                "inventory_delete_by_id",
                {"user_id": user_id, "item_id": item_identifier},
                token
            )
        elif strategy == "by_name":
            result = await self.tool_router.route_tool(
                "inventory_delete_by_name",
                {"user_id": user_id, "item_name": item_identifier},
                token
            )
        elif strategy == "by_name_oldest":
            result = await self.tool_router.route_tool(
                "inventory_delete_by_name_oldest",
                {"user_id": user_id, "item_name": item_identifier},
                token
            )
        elif strategy == "by_name_latest":
            result = await self.tool_router.route_tool(
                "inventory_delete_by_name_latest",
                {"user_id": user_id, "item_name": item_identifier},
                token
            )
        else:
            # デフォルト：IDとして扱う
            result = await self.tool_router.route_tool(
                "inventory_delete_by_id",
                {"user_id": user_id, "item_id": item_identifier},
                token
            )
        return result
```

#### **実装方針**
```python
class InventoryService:
    def __init__(self, tool_router: ToolRouter):
        self.tool_router = tool_router
    
    # 各メソッドはToolRouter経由でツール呼び出し
    # ビジネスロジックはMCP層で実装
    # 戦略パターンによる適切なツール選択はサービス層で実装
```

### **4. LLMService（LLM呼び出しサービス）**

#### **役割**
- LLM呼び出しのコントロール
- プロンプト設計・管理
- 動的ツール取得・プロンプト動的埋め込み
- 個別呼び出しの子ファイル管理
- プロンプト肥大化の防止

#### **主要機能**
```python
class LLMService:
    def __init__(self):
        self.task_decomposer = TaskDecomposer()
        self.response_formatter = ResponseFormatter()
        self.constraint_solver = ConstraintSolver()
    
    async def decompose_tasks(
        self, 
        user_request: str, 
        available_tools: List[str], 
        user_id: str
    ) -> List[Task]:
        """タスク分解（子ファイル委譲）"""
        return await self.task_decomposer.decompose(
            user_request, available_tools, user_id
        )
    
    async def format_response(
        self, 
        results: List[TaskResult]
    ) -> str:
        """最終回答整形（子ファイル委譲）"""
        return await self.response_formatter.format(results)
    
    async def solve_constraints(
        self, 
        candidates: List[Dict], 
        constraints: Dict
    ) -> Dict:
        """制約解決（子ファイル委譲）"""
        return await self.constraint_solver.solve(candidates, constraints)
```

### **5. SessionService（セッション管理サービス）**

#### **役割**
- セッション管理のビジネスロジック
- セッション状態の管理

#### **主要機能**
```python
class SessionService:
    async def create_session(
        self, 
        user_id: str
    ) -> Session:
        """セッションを作成（認証はAPI層で完了済み）"""
        
    async def get_session(
        self, 
        session_id: str
    ) -> Optional[Session]:
        """セッションを取得"""
        
    async def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """セッションを更新"""
        
    async def delete_session(
        self, 
        session_id: str
    ) -> bool:
        """セッションを削除"""
```

#### **実装方針**
```python
class SessionService:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
    
    async def create_session(
        self, 
        user_id: str
    ) -> Session:
        # 1. セッションの作成（認証はAPI層で完了済み）
        session = Session(
            id=generate_session_id(),
            user_id=user_id,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )
        
        # 2. セッションの保存
        self.sessions[session.id] = session
        
        return session
    
    async def get_session(
        self, 
        session_id: str
    ) -> Optional[Session]:
        session = self.sessions.get(session_id)
        
        if session:
            # 最終アクセス時刻の更新
            session.last_accessed = datetime.now()
        
        return session
```

## 🚀 実装戦略

### **Phase 1: 基本サービス**
1. **RecipeService**: 基本的なレシピ生成・検索
2. **InventoryService**: 基本的な在庫管理
3. **SessionService**: 基本的なセッション管理

### **Phase 2: 最適化**
1. **パフォーマンス最適化**: 処理時間の短縮
2. **メモリ最適化**: メモリ使用量の削減
3. **エラーハンドリング**: エラー処理の強化

## 📊 成功基準

### **機能面**
- [ ] RecipeServiceの動作確認
- [ ] InventoryServiceの動作確認
- [ ] SessionServiceの動作確認

### **技術面**
- [ ] 全ファイルが100行以下
- [ ] LLMServiceのコントロール専用設計
- [ ] 個別LLM呼び出しの子ファイル分解
- [ ] 保守性の確認

---

**このドキュメントは、Morizo AI v2のサービス層設計を定義します。**
**すべてのサービスは、この設計に基づいて実装されます。**
