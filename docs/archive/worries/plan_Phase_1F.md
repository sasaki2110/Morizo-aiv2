# Phase 1F: 主菜追加提案機能（もう5件提案）

## 概要

ユーザーが提案された5件の主菜に納得できない場合、フロントエンドの「他の提案を見る」ボタンをクリックすることで追加提案を受けられる機能を実装します。セッション内で提案済みのレシピを管理し、重複を避けながら追加で5件ずつ提案します。

**既存実装の活用**:
- フロントエンド: `SelectionOptions.tsx`の「他の提案を見る」ボタン（実装済み）
- API: `/api/chat/selection`エンドポイント（実装済み）
- `selection=0`を追加提案要求として扱う（新規実装）

## 対象範囲

- セッション内での提案履歴管理
- **`selection=0`を追加提案リクエストとして認識（agent.py拡張）**
- **追加提案プロンプトの生成（agent.py拡張）**
- セッション提案履歴取得MCPツール
- 除外リストの構成（履歴14日分 + セッション内提案済み）
- 在庫情報の再利用（セッション保存）
- レスポンスフォーマットの調整
- ツールルーティングの追加
- **フロントエンド: 変更不要（既に実装済み）**

## 背景

**worries.mdの要求**:
```
主菜選定フェーズ:
- ○○を使ったメインを5件ほど提案
- ユーザーが納得できなければ、もう5件ほど提案
- ユーザーが決めるまで繰り返し
```

現状のPhase 1A-Eでは、初回の5件提案のみ実装されており、追加提案機能がありません。この機能により、ユーザーは納得するまで何度でも5件ずつ追加提案を受けられます。

## 既存実装の確認

### フロントエンド（実装済み）

**ファイル**: `/app/Morizo-web/components/SelectionOptions.tsx`

「他の提案を見る」ボタンが既に実装されています:
```typescript
const handleRequestMore = async () => {
  // バックエンドに追加提案を要求
  const response = await authenticatedFetch('/api/chat/selection', {
    method: 'POST',
    body: JSON.stringify({
      task_id: taskId,
      selection: 0,  // 0 = 追加提案要求
      sse_session_id: sseSessionId
    })
  });
};
```

### バックエンドAPI（実装済み）

**ファイル**: `/app/Morizo-aiv2/api/routes/chat.py`

`/api/chat/selection`エンドポイントが既に実装されています:
```python
@router.post("/chat/selection")
async def receive_user_selection(
    selection_request: UserSelectionRequest,
    http_request: Request
):
    # agent.process_user_selection()を呼び出し
    result = await agent.process_user_selection(
        selection_request.task_id,
        selection_request.selection,  # 0 = 追加提案要求
        selection_request.sse_session_id,
        user_id,
        token
    )
```

### エージェント（拡張が必要）

**ファイル**: `/app/Morizo-aiv2/core/agent.py`

`process_user_selection()`メソッドが既に存在しますが、`selection=0`の追加提案処理は未実装です。

## 実装計画

### 1. セッション状態管理の拡張

**修正ファイル**: `services/session_service.py`

**変更内容**:
- `Session`クラスに提案履歴管理機能を追加
- カテゴリ別（main/sub/soup）に提案済みタイトルを保存
- 提案済みタイトルの追加・取得・クリア機能

**実装例**:
```python
class Session:
    def __init__(self, session_id: str, user_id: str):
        self.id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.data: Dict[str, Any] = {}
        
        # 既存: 確認コンテキスト
        self.confirmation_context: Dict[str, Any] = {
            "type": None,
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
        
        # Phase 1F: 提案履歴管理
        self.proposed_recipes: Dict[str, List[str]] = {
            "main": [],
            "sub": [],
            "soup": []
        }
        
        # Phase 1F: セッション内コンテキスト（在庫情報等）
        self.context: Dict[str, Any] = {
            "inventory_items": [],
            "main_ingredient": None,
            "menu_type": ""
        }
    
    def add_proposed_recipes(self, category: str, titles: List[str]) -> None:
        """提案済みレシピタイトルを追加
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
            titles: 提案済みタイトルのリスト
        """
        if category in self.proposed_recipes:
            self.proposed_recipes[category].extend(titles)
            self.logger.info(f"📝 [SESSION] Added {len(titles)} proposed {category} recipes")
    
    def get_proposed_recipes(self, category: str) -> List[str]:
        """提案済みレシピタイトルを取得
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            List[str]: 提案済みタイトルのリスト
        """
        return self.proposed_recipes.get(category, [])
    
    def clear_proposed_recipes(self, category: str) -> None:
        """提案済みレシピをクリア
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        """
        if category in self.proposed_recipes:
            self.proposed_recipes[category] = []
            self.logger.info(f"🧹 [SESSION] Cleared proposed {category} recipes")
    
    def set_context(self, key: str, value: Any) -> None:
        """セッションコンテキストを設定
        
        Args:
            key: コンテキストキー（"inventory_items", "main_ingredient", "menu_type"等）
            value: 値
        """
        self.context[key] = value
        self.logger.info(f"💾 [SESSION] Context set: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """セッションコンテキストを取得
        
        Args:
            key: コンテキストキー
            default: デフォルト値
        
        Returns:
            Any: コンテキスト値
        """
        return self.context.get(key, default)
```

**SessionServiceクラスの拡張**:
```python
class SessionService:
    async def add_proposed_recipes(
        self, 
        sse_session_id: str, 
        category: str, 
        titles: List[str]
    ) -> None:
        """提案済みレシピをセッションに追加"""
        session = await self.get_session(sse_session_id, user_id=None)
        if session:
            session.add_proposed_recipes(category, titles)
    
    async def get_proposed_recipes(
        self, 
        sse_session_id: str, 
        category: str
    ) -> List[str]:
        """提案済みレシピをセッションから取得"""
        session = await self.get_session(sse_session_id, user_id=None)
        if session:
            return session.get_proposed_recipes(category)
        return []
    
    async def set_session_context(
        self, 
        sse_session_id: str, 
        key: str, 
        value: Any
    ) -> None:
        """セッションコンテキストを設定"""
        session = await self.get_session(sse_session_id, user_id=None)
        if session:
            session.set_context(key, value)
    
    async def get_session_context(
        self, 
        sse_session_id: str, 
        key: str, 
        default: Any = None
    ) -> Any:
        """セッションコンテキストを取得"""
        session = await self.get_session(sse_session_id, user_id=None)
        if session:
            return session.get_context(key, default)
        return default
```

### 2. セッション提案履歴取得MCPツールの追加

**修正ファイル**: `mcp_servers/session_mcp.py`

**変更内容**:
- `session_get_proposed_titles()` ツールを追加
- セッション内で提案済みのレシピタイトルを取得
- カテゴリ（main/sub/soup）を指定

**実装例**:
```python
@mcp.tool()
async def session_get_proposed_titles(
    sse_session_id: str,
    category: str  # "main", "sub", "soup"
) -> Dict[str, Any]:
    """
    セッション内で提案済みのレシピタイトルを取得（追加提案の重複回避用）
    
    Args:
        sse_session_id: セッションID
        category: カテゴリ（"main", "sub", "soup"）
    
    Returns:
        Dict[str, Any]: {"success": bool, "data": List[str]}
    """
    logger.info(f"🔧 [SESSION] Starting session_get_proposed_titles")
    logger.info(f"  Session: {sse_session_id}, Category: {category}")
    
    try:
        # セッションサービスから提案済みタイトルを取得
        from services.session_service import session_service
        
        titles = await session_service.get_proposed_recipes(sse_session_id, category)
        
        logger.info(f"✅ [SESSION] Retrieved {len(titles)} proposed titles")
        return {"success": True, "data": titles}
        
    except Exception as e:
        logger.error(f"❌ [SESSION] Error in session_get_proposed_titles: {e}")
        return {"success": False, "error": str(e), "data": []}
```

### 3. エージェントの拡張（selection=0の処理）

**修正ファイル**: `core/agent.py`

**変更内容**:
- `process_user_selection()`メソッドに`selection=0`の処理を追加
- `selection=0`の場合、追加提案用のプロンプトを生成してプランニングループを実行
- セッションから在庫情報・主要食材を取得

**実装例**:
```python
async def process_user_selection(
    self, 
    task_id: str, 
    selection: int, 
    sse_session_id: str, 
    user_id: str, 
    token: str
) -> dict:
    """ユーザー選択結果の処理"""
    try:
        self.logger.info(f"📥 [AGENT] Processing user selection: task_id={task_id}, selection={selection}")
        
        # Phase 1F: selection=0 の場合は追加提案要求
        if selection == 0:
            self.logger.info(f"🔄 [AGENT] Additional proposal request detected (selection=0)")
            return await self._handle_additional_proposal_request(
                task_id, sse_session_id, user_id, token
            )
        
        # タスクチェーンマネージャーを初期化（SSEセッションIDから復元）
        task_chain_manager = TaskChainManager(sse_session_id)
        
        # タスクを再開
        task_chain_manager.resume_execution()
        
        self.logger.info(f"▶️ [AGENT] Task {task_id} resumed successfully")
        
        # 選択されたレシピをもとに後続処理を実行
        # （Phase 2Bで副菜・汁物の選択に進む処理を追加予定）
        
        return {
            "success": True,
            "task_id": task_id,
            "selection": selection,
            "message": f"選択肢 {selection} を受け付けました。"
        }
        
    except Exception as e:
        self.logger.error(f"❌ [AGENT] Failed to process user selection: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def _handle_additional_proposal_request(
    self, 
    task_id: str,
    sse_session_id: str, 
    user_id: str, 
    token: str
) -> dict:
    """追加提案要求の処理（selection=0の場合）"""
    try:
        self.logger.info(f"🔄 [AGENT] Handling additional proposal request")
        
        # セッションから主要食材を取得
        session = await self.session_service.get_session(sse_session_id, user_id)
        if not session:
            raise Exception("Session not found")
        
        main_ingredient = session.get_context("main_ingredient")
        
        # 追加提案用のプロンプトを生成
        if main_ingredient:
            additional_request = f"{main_ingredient}の主菜をもう5件提案して"
        else:
            additional_request = "主菜をもう5件提案して"
        
        self.logger.info(f"📝 [AGENT] Generated additional request: {additional_request}")
        
        # プランニングループを実行
        result = await self.process_request(
            additional_request, 
            user_id, 
            token, 
            sse_session_id,
            is_confirmation_response=False
        )
        
        return result
        
    except Exception as e:
        self.logger.error(f"❌ [AGENT] Failed to handle additional proposal request: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

### 4. プランナープロンプトの拡張

**修正ファイル**: `services/llm/prompt_manager.py`

**変更内容**:
- `session_get_proposed_titles` ツールの説明を追加
- 追加提案時のタスク構成ルールを追加（「もう5件」というキーワードで認識）

**追加するツール説明**:
```python
- **session_service**: セッション管理サービス
  - `session_get_proposed_titles(sse_session_id: str, category: str, ...)`: セッション内で提案済みのレシピタイトルを取得（追加提案の重複回避用）。categoryは"main"/"sub"/"soup"。
```

**追加するタスク生成ルール**:
```python
**主菜追加提案のタスク生成ルール（Phase 1F）**:

4. **主菜の追加提案の場合**: ユーザーの要求に「もう5件」「もっと」等の追加提案キーワードが含まれる場合、以下の3段階のタスク構成を使用してください：
   
   **認識パターン**:
   - 「もう5件提案して」「もう5件教えて」
   - 「もっと他の主菜」「もっと提案して」
   
   **前提条件**:
   - 「主菜」という単語が含まれる
   - セッションIDが存在する（sse_session_id）
   
   **タスク構成**:
   a. **task1**: `history_get_recent_titles(user_id, "main", 14)` を呼び出し、14日間の主菜履歴を取得する。
   b. **task2**: `session_get_proposed_titles(sse_session_id, "main")` を呼び出し、セッション内で提案済みのタイトルを取得する。
   c. **task3**: `recipe_service.generate_main_dish_proposals()` を呼び出す。その際:
      - `inventory_items`: セッションから取得（在庫取得タスクは不要）
      - `excluded_recipes`: task1.result.data + task2.result.data（履歴 + セッション提案済み）
      - `main_ingredient`: セッションから取得
      - `menu_type`: セッションから取得
   
   **重要**: 追加提案の場合、在庫取得タスクは不要です。セッション内に保存された在庫情報を再利用してください。

**パラメータ注入のルール（追加提案対応）**:
- 履歴除外リスト: `"excluded_recipes": "task1.result.data"`
- セッション提案済み除外リスト: 上記に追加で `+ task2.result.data`
- 在庫情報: セッションコンテキストから取得（タスクではなくコンテキスト参照）
- 主要食材: セッションコンテキストから取得
```

### 5. レスポンス処理の拡張

**修正ファイル**: `services/llm/response_processor.py`

**変更内容**:
- `generate_main_dish_proposals`の結果処理後に提案済みタイトルをセッションに保存
- 在庫情報もセッションに保存（初回提案時のみ）

**実装箇所**: `_process_service_method()`メソッド内
```python
elif service_method == "recipe_service.generate_main_dish_proposals":
    response_parts.extend(self.formatters.format_main_dish_proposals(data))
    
    # Phase 1F: 提案済みタイトルをセッションに保存
    if data.get("success") and sse_session_id:
        candidates = data.get("data", {}).get("candidates", [])
        titles = [c.get("title") for c in candidates if c.get("title")]
        
        # セッションに提案済みタイトルを追加
        await self.session_service.add_proposed_recipes(sse_session_id, "main", titles)
        self.logger.info(f"💾 [RESPONSE] Saved {len(titles)} proposed titles to session")
```

### 6. 在庫情報のセッション保存

**修正ファイル**: `services/llm/response_processor.py`

**変更内容**:
- `inventory_service.get_inventory`の結果処理後に在庫情報をセッションに保存

**実装箇所**: `_process_service_method()`メソッド内
```python
if service_method == "inventory_service.get_inventory":
    response_parts.extend(self.formatters.format_inventory_list(data))
    
    # Phase 1F: 在庫情報をセッションに保存（追加提案時の再利用用）
    if data.get("success") and sse_session_id:
        inventory_items = data.get("data", [])
        item_names = [item.get("name") for item in inventory_items if item.get("name")]
        
        await self.session_service.set_session_context(sse_session_id, "inventory_items", item_names)
        self.logger.info(f"💾 [RESPONSE] Saved {len(item_names)} inventory items to session")
```

### 7. 主要食材のセッション保存

**修正ファイル**: `core/agent.py`

**変更内容**:
- 主菜提案タスク実行前に主要食材をセッションに保存

**実装例**（`core/agent.py`内）:
```python
# 主菜提案タスク実行前に主要食材をセッションに保存
if task.method == "generate_main_dish_proposals":
    main_ingredient = task.parameters.get("main_ingredient")
    menu_type = task.parameters.get("menu_type", "")
    
    if sse_session_id:
        await self.session_service.set_session_context(sse_session_id, "main_ingredient", main_ingredient)
        await self.session_service.set_session_context(sse_session_id, "menu_type", menu_type)
        self.logger.info(f"💾 [AGENT] Saved main_ingredient and menu_type to session")
```

### 8. レスポンスフォーマットの調整

**修正ファイル**: `services/llm/response_formatters.py`

**変更内容**:
- 追加提案の場合、提案済み件数を表示
- セッション情報から提案済み件数を取得

**実装例**:
```python
def format_main_dish_proposals(
    self, 
    data: Dict[str, Any], 
    sse_session_id: str = None
) -> List[str]:
    """主菜5件提案のフォーマット（追加提案対応）"""
    response_parts = []
    
    try:
        if data.get("success"):
            candidates = data.get("data", {}).get("candidates", [])
            main_ingredient = data.get("data", {}).get("main_ingredient")
            llm_count = data.get("data", {}).get("llm_count", 0)
            rag_count = data.get("data", {}).get("rag_count", 0)
            
            # Phase 1F: セッションから提案済み件数を取得
            total_proposed = 0
            if sse_session_id:
                from services.session_service import session_service
                proposed_titles = await session_service.get_proposed_recipes(sse_session_id, "main")
                total_proposed = len(proposed_titles)
            
            # 主要食材の表示
            if main_ingredient:
                if total_proposed > 0:
                    response_parts.append(f"🍽️ **主菜の追加提案（5件）- {main_ingredient}使用**")
                    response_parts.append(f"これまでに{total_proposed}件提案済みです。さらに5件提案します。")
                else:
                    response_parts.append(f"🍽️ **主菜の提案（5件）- {main_ingredient}使用**")
            else:
                if total_proposed > 0:
                    response_parts.append("🍽️ **主菜の追加提案（5件）**")
                    response_parts.append(f"これまでに{total_proposed}件提案済みです。さらに5件提案します。")
                else:
                    response_parts.append("🍽️ **主菜の提案（5件）**")
            response_parts.append("")
            
            # LLM提案（最初の2件）
            if llm_count > 0:
                response_parts.append("💡 **斬新な提案（LLM推論）**")
                for i, candidate in enumerate(candidates[:llm_count], 1):
                    title = candidate.get("title", "")
                    ingredients = ", ".join(candidate.get("ingredients", []))
                    response_parts.append(f"{i}. {title}")
                    response_parts.append(f"   使用食材: {ingredients}")
                    response_parts.append("")
            
            # RAG提案（残りの3件）
            if rag_count > 0:
                response_parts.append("📚 **伝統的な提案（RAG検索）**")
                start_idx = llm_count
                for i, candidate in enumerate(candidates[start_idx:], start_idx + 1):
                    title = candidate.get("title", "")
                    ingredients = ", ".join(candidate.get("ingredients", []))
                    response_parts.append(f"{i}. {title}")
                    response_parts.append(f"   使用食材: {ingredients}")
                    response_parts.append("")
            
            # Phase 1F: 追加提案の案内
            if total_proposed > 0:
                response_parts.append("💬 さらに他の選択肢をご覧になりたい場合は「もう5件提案して」とお伝えください。")
                response_parts.append("")
        else:
            # エラー時の表示
            error_msg = data.get("error", "不明なエラー")
            response_parts.append("❌ **主菜提案の取得に失敗しました**")
            response_parts.append("")
            response_parts.append(f"エラー: {error_msg}")
            response_parts.append("")
            response_parts.append("もう一度お試しください。")
            
    except Exception as e:
        self.logger.error(f"❌ [ResponseFormatters] Error in format_main_dish_proposals: {e}")
        response_parts.append("主菜提案の処理中にエラーが発生しました。")
    
    return response_parts
```

### 9. ToolRouterの更新

**修正ファイル**: `services/tool_router.py`

**変更内容**:
- `service_method_mapping`に新しいマッピングを追加
- `session_get_proposed_titles`ツールをマッピング

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
            ("recipe_service", "generate_main_dish_proposals"): "generate_main_dish_proposals",
            
            # RecipeHistoryService のマッピング（重複回避用）
            ("history_service", "history_get_recent_titles"): "history_get_recent_titles",
            
            # Phase 1F: SessionService のマッピング（追加提案用）
            ("session_service", "session_get_proposed_titles"): "session_get_proposed_titles",
        }
        
        self.logger = GenericLogger("service", "tool_router")
```

### 10. プランナーのコンテキスト参照機能

**修正ファイル**: `services/llm/planner.py`または`core/agent.py`

**変更内容**:
- タスク生成時にセッションコンテキストを参照できるようにする
- 追加提案時に在庫情報をセッションから取得

**実装例**:
```python
# タスク生成時にセッションコンテキストを取得
if sse_session_id and is_additional_proposal:
    inventory_items = await self.session_service.get_session_context(
        sse_session_id, "inventory_items", []
    )
    main_ingredient = await self.session_service.get_session_context(
        sse_session_id, "main_ingredient", None
    )
    menu_type = await self.session_service.get_session_context(
        sse_session_id, "menu_type", ""
    )
    
    # これらをタスクパラメータに設定
    task.parameters["inventory_items"] = inventory_items
    task.parameters["main_ingredient"] = main_ingredient
    task.parameters["menu_type"] = menu_type
```

## データフロー

### 初回提案
```
1. ユーザー: 「レンコンの主菜を教えて」

2. プランナー: 3タスク構成
   - task1: inventory_get() → ["レンコン", "人参", "玉ねぎ", ...]
   - task2: history_get_recent_titles("main", 14) → ["過去レシピA", "過去レシピB", ...]
   - task3: generate_main_dish_proposals(
       inventory_items=task1.result,
       excluded_recipes=task2.result.data,
       main_ingredient="レンコン"
     )

3. 実行結果: ["レシピA", "レシピB", "レシピC", "レシピD", "レシピE"]

4. セッションに保存:
   - proposed_recipes["main"] = ["レシピA", "レシピB", "レシピC", "レシピD", "レシピE"]
   - context["inventory_items"] = ["レンコン", "人参", "玉ねぎ", ...]
   - context["main_ingredient"] = "レンコン"
   - context["menu_type"] = ""
```

### 追加提案（1回目）- ボタンクリック
```
1. フロントエンド: ユーザーが「他の提案を見る」ボタンをクリック
   → POST /api/chat/selection { task_id, selection: 0, sse_session_id }

2. API: agent.process_user_selection(task_id, selection=0, sse_session_id, user_id, token)

3. Agent: selection=0を検出 → _handle_additional_proposal_request()
   - セッションから主要食材を取得: "レンコン"
   - 追加提案プロンプトを生成: "レンコンの主菜をもう5件提案して"
   - process_request()を呼び出し（プランニングループ実行）

4. プランナー: 「もう5件」キーワードを検出 → 3タスク構成（在庫取得なし）
   - task1: history_get_recent_titles("main", 14) → ["過去レシピA", "過去レシピB", ...]
   - task2: session_get_proposed_titles("main") → ["レシピA", "レシピB", "レシピC", "レシピD", "レシピE"]
   - task3: generate_main_dish_proposals(
       inventory_items=session.context["inventory_items"],  # セッションから取得
       excluded_recipes=task1.result.data + task2.result.data,  # 履歴 + セッション提案済み
       main_ingredient=session.context["main_ingredient"]  # セッションから取得
     )

5. 実行結果: ["レシピF", "レシピG", "レシピH", "レシピI", "レシピJ"]

6. セッションに追加:
   - proposed_recipes["main"] = ["レシピA", "レシピB", "レシピC", "レシピD", "レシピE", 
                                  "レシピF", "レシピG", "レシピH", "レシピI", "レシピJ"]

7. フロントエンド: 新しい5件が SelectionOptions として表示される
```

### 追加提案（2回目）- ボタンクリック
```
1. フロントエンド: ユーザーが再度「他の提案を見る」ボタンをクリック
   → POST /api/chat/selection { task_id, selection: 0, sse_session_id }

2. Agent: 追加提案プロンプトを生成: "レンコンの主菜をもう5件提案して"

3. 除外リスト = 履歴14日分 + セッション提案済み10件

4. 実行結果: ["レシピK", "レシピL", "レシピM", "レシピN", "レシピO"]

5. セッションに追加:
   - proposed_recipes["main"] = [過去10件 + "レシピK", "レシピL", "レシピM", "レシピN", "レシピO"]

6. フロントエンド: 新しい5件が SelectionOptions として表示される
```

## テスト計画

### 単体テスト

1. **セッション状態管理のテスト**
   - `add_proposed_recipes()`が正しくタイトルを追加
   - `get_proposed_recipes()`が正しくタイトルを取得
   - `clear_proposed_recipes()`が正しくクリア
   - `set_context()`/`get_context()`が正しく動作

2. **MCPツールのテスト**
   - `session_get_proposed_titles()`が正しくセッションからタイトルを取得

3. **レスポンス処理のテスト**
   - 提案済みタイトルが正しくセッションに保存される
   - 在庫情報が正しくセッションに保存される

### 統合テスト

**テスト1: 初回提案→追加提案（ボタンクリック1回）**
```
入力1: 「レンコンの主菜を教えて」
期待1: 5件提案（A, B, C, D, E）、SelectionOptionsに表示、セッションに保存

入力2: フロントエンドで「他の提案を見る」ボタンをクリック (selection=0)
期待2: 5件追加提案（F, G, H, I, J）、A-Eは除外、セッションに追加保存
期待3: SelectionOptionsが新しい5件で更新される
```

**テスト2: 初回提案→追加提案（ボタンクリック複数回）**
```
入力1: 「主菜を教えて」
期待1: 5件提案、SelectionOptionsに表示、セッションに保存

入力2: 「他の提案を見る」ボタンクリック
期待2: 5件追加提案（1回目の5件を除外）

入力3: 「他の提案を見る」ボタンクリック
期待3: 5件追加提案（1-2回目の10件を除外）

入力4: 「他の提案を見る」ボタンクリック
期待4: 5件追加提案（1-3回目の15件を除外）
```

**テスト3: 主要食材の保持**
```
入力1: 「レンコンの主菜を教えて」
期待1: レンコンを使った5件提案

入力2: 「もう5件」
期待2: レンコンを使った追加5件提案（主要食材が保持される）
```

**テスト4: 重複回避の確認**
```
前提: 履歴14日分に「過去レシピX」「過去レシピY」が存在

入力1: 「主菜を教えて」
期待1: 5件提案（過去レシピX, Yは含まれない）

入力2: 「もう5件」
期待2: 5件追加提案（過去レシピX, Y + 1回目の5件は含まれない）
```

**テスト5: セッションなしのエラーハンドリング**
```
入力: 「もう5件提案して」（セッションIDなし）
期待: エラーメッセージまたはセッションが必要な旨の通知
```

### エンドツーエンドテスト

1. **正常フロー（初回→追加→追加）**
   - ユーザーが初回提案を受ける
   - 納得できず追加提案を要求
   - さらに納得できず追加提案を要求
   - すべて重複なく提案される

2. **セッション永続性**
   - 提案済みタイトルがセッションに保存される
   - 在庫情報がセッションに保存される
   - 追加提案時にセッション情報が正しく利用される

3. **除外リストの統合**
   - 履歴14日分 + セッション提案済みが正しく統合される
   - 重複が完全に排除される

## 修正ファイル一覧

### バックエンド（修正が必要）
1. `services/session_service.py` - セッション状態管理の拡張
2. `mcp_servers/session_mcp.py` - `session_get_proposed_titles()` ツール追加
3. `core/agent.py` - `process_user_selection()`に`selection=0`の処理追加、主要食材のセッション保存
4. `services/llm/prompt_manager.py` - プランナープロンプトに追加提案ルール追加
5. `services/llm/response_processor.py` - 提案結果と在庫情報のセッション保存
6. `services/llm/response_formatters.py` - 追加提案時の表示調整
7. `services/tool_router.py` - 新ツールのマッピング追加

### フロントエンド（修正不要）
- `/app/Morizo-web/components/SelectionOptions.tsx` - **既に実装済み**（変更不要）
- `/app/Morizo-aiv2/api/routes/chat.py` - **既に実装済み**（変更不要）

## 制約事項

1. **セッション依存**: セッションIDが必須（sse_session_idがない場合は追加提案不可）
2. **在庫不変の前提**: セッション内で在庫は変わらない前提（在庫が変わった場合は初回提案からやり直し）
3. **Phase 1A-Eの完成**: 基本機能が完成している必要がある
4. **Phase 2との独立性**: ユーザー選択機能（Phase 2）とは独立して動作
5. **Phase 4との独立性**: ロールバック機能（Phase 4）とは独立して動作

## 期待される効果

1. **ユーザー満足度の向上**: 5件で満足できない場合に追加提案可能
2. **重複回避の強化**: 履歴14日分 + セッション提案済みを完全に除外
3. **効率化**: 在庫取得を再実行せず、セッション情報を再利用
4. **worries.md対応**: 「納得できなければもう5件ほど提案 ⇒ ユーザーが決めるまで繰り返し」を実現
5. **ユーザー体験の向上**: 選択肢を見る楽しみ、自分で決める楽しみを提供

## worries.mdとの対応関係

### 実現できること
- ✅ 主菜を5件ほど提案
- ✅ ユーザーが納得できなければ、もう5件ほど提案
- ✅ ユーザーが決めるまで繰り返し
- ✅ 2週間重複回避（履歴14日分 + セッション提案済み）
- ✅ いろいろな候補を見る楽しみ
- ✅ 自分で決める楽しみ

### Phase 2以降で実現予定
- ❌ **ユーザーが5件から選択する機能**: Phase 2で実装予定
- ❌ **副菜・汁物の段階的選択**: Phase 3で実装予定
- ❌ **前段階へのロールバック**: Phase 4で実装予定

## 実装の優先度

**優先度: 高**
- worries.mdの核心的要求を実現
- Phase 1の完成に必須
- Phase 2（ユーザー選択機能）の前提条件

## 実装規模

- **中規模**
- 新規ファイル: 0個
- 修正ファイル: 7個
- 新規MCPツール: 1個
- テストファイル: 2-3個

## 実装時間の目安

- セッション管理拡張: 2-3時間
- MCPツール追加: 1時間
- プランナー拡張: 2-3時間
- レスポンス処理拡張: 1-2時間
- テスト: 2-3時間
- 合計: 8-12時間

## To-dos

### セッション管理拡張
- [ ] Sessionクラスに提案履歴管理機能を追加（services/session_service.py）
  - `proposed_recipes` 属性追加
  - `add_proposed_recipes()`, `get_proposed_recipes()`, `clear_proposed_recipes()` メソッド
  - `context` 属性と `set_context()`, `get_context()` メソッド
- [ ] SessionServiceクラスに提案履歴操作メソッドを追加（services/session_service.py）
  - `add_proposed_recipes()`, `get_proposed_recipes()`
  - `set_session_context()`, `get_session_context()`

### MCPツール追加
- [ ] session_get_proposed_titles() MCPツールを追加（mcp_servers/session_mcp.py）
- [ ] ToolRouterにsession_get_proposed_titlesのマッピングを追加（services/tool_router.py）

### エージェント拡張（selection=0処理）
- [ ] process_user_selection()にselection=0の処理を追加（core/agent.py）
- [ ] _handle_additional_proposal_request()メソッドを追加（core/agent.py）
  - セッションから主要食材を取得
  - 追加提案プロンプトを生成（「〇〇の主菜をもう5件提案して」）
  - process_request()を呼び出し
- [ ] 主要食材のセッション保存処理を追加（core/agent.py）

### プランナー拡張
- [ ] プランナープロンプトにsession_get_proposed_titlesツール説明を追加（services/llm/prompt_manager.py）
- [ ] プランナープロンプトに追加提案認識ルールを追加（services/llm/prompt_manager.py）
  - 「もう5件」「もっと」等のキーワード認識
  - 3タスク構成（履歴取得→セッション取得→LLM+RAG）

### レスポンス処理拡張
- [ ] レスポンス処理に提案済みタイトルのセッション保存を追加（services/llm/response_processor.py）
- [ ] レスポンス処理に在庫情報のセッション保存を追加（services/llm/response_processor.py）
- [ ] レスポンスフォーマットに追加提案時の表示調整を追加（services/llm/response_formatters.py）
  - 提案済み件数の表示
  - 「これまでにN件提案済みです」メッセージ

### テスト
- [ ] Phase 1Fの単体テスト: セッション管理、MCPツール、selection=0処理
- [ ] Phase 1Fの統合テスト: ボタンクリックによる追加提案、重複回避
- [ ] Phase 1Fのエンドツーエンドテスト: 複数回の追加提案、セッション永続性、フロントエンド連携

