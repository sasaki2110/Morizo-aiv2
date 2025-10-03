# Morizo AI v2 - コアアーキテクチャ設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: コア機能のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **統一されたReActエージェント**
- **シンプルかつ汎用的**: エージェント機能に特化した設計
- **サービス層依存**: サービス層を経由したビジネスロジック実行
- **動的ツール選択**: サービス層から動的に取得したツールリストから適切なツールを選択
- **疎結合**: 各サービスの内部実装に依存しない

### **責任分離の徹底**
- **TrueReactAgent**: タスク分解・制御・実行の責任のみ
- **ActionPlanner**: ユーザーリクエストを実行可能なタスクに分解
- **TaskExecutor**: タスクの順序管理と実行制御

## 🏗️ コアアーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────┐
│                        Core Layer                          │
│      (TrueReactAgent, ActionPlanner, TaskExecutor)         │
└─────────────────────┬───────────────────────────────────────┘
                      │ (Service.Method Call)
┌─────────────────────▼───────────────────────────────────────┐
│                     Service Layer                          │
│ (RecipeService, InventoryService, etc. -> MCPClient)       │
└─────────────────────┬───────────────────────────────────────┘
                      │ (Tool Name Call via MCPClient)
┌─────────────────────▼───────────────────────────────────────┐
│                        MCP Layer                           │
│      (RecipeMCP, InventoryMCP, etc.)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ (DB Access, API Call)
┌─────────────────────▼───────────────────────────────────────┐
│                     External Systems                       │
│                  (Database, 外部API)                        │
└─────────────────────────────────────────────────────────────┘
```

### **処理フロー（ReActループ）**
```
ユーザーリクエスト
    ↓
ActionPlanner（タスク分解 + 依存関係生成）
    ↓
TrueReactAgent（ReActループ開始）
    ↓
┌─────────────────────────────────────────────────────────┐
│                    ReActループ                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │ 1. 依存関係解決 + 並列実行グループ化                ││
│  │    ↓                                               ││
│  │ 2. 並列実行グループ1（asyncio.gather）              ││
│  │    ↓                                               ││
│  │ 3. データ注入（前のタスク結果を次のタスクに）      ││
│  │    ↓                                               ││
│  │ 4. Service Layer（ビジネスロジック実行）            ││
│  │    ↓                                               ││
│  │ 5. 結果評価・次のアクション決定                     ││
│  │    ↓                                               ││
│  │ 6. 完了判定 → 未完了ならループ継続                  ││
│  └─────────────────────────────────────────────────────┘│
│                    ↓                                   │
│              ループ継続/完了                            │
└─────────────────────────────────────────────────────────┘
    ↓
レスポンス生成
```

## 🔧 コアコンポーネント

### **1. TrueReactAgent（統一ReActループ）**

#### **役割**
- 全てのユーザーリクエストを統一的に処理する**シンプルかつ汎用的なエージェント**
- リクエスト受信・タスク分解・制御・実行・レスポンス生成の責任

#### **設計原則**
- **エージェント機能特化**: リクエスト受信・タスク分解・制御・実行・レスポンス生成の責任
- **サービス層依存**: サービス層を経由したビジネスロジック実行
- **動的ツール選択**: サービス層から動的に取得したツールリストから適切なツールを選択
- **疎結合**: 各サービスの内部実装に依存しない

#### **新機能**
- **依存関係解決**: タスクの実行順序を自動決定
- **データ注入**: 前のタスクの結果を次のタスクに動的に注入
- **並列実行**: 依存関係を満たしたタスクを同時実行（asyncio.gather使用）
- **エラーハンドリング**: 並列実行失敗時の個別実行フォールバック
- **ストリーミング対応**: SSEによる進捗表示とリアルタイム更新
- **確認プロセス**: 曖昧性検出とユーザー確認の処理

#### **処理フロー**
```python
async def process_request(user_request: str, user_id: str, sse_session_id: str = None) -> str:
    # 1. タスク分解
    tasks = await action_planner.decompose(user_request, user_id)
    
    # 2. 曖昧性検出
    ambiguity_result = await ambiguity_detector.detect_ambiguity(tasks, user_id)
    
    # 3. 確認プロセス（必要に応じて）
    if ambiguity_result.requires_confirmation:
        confirmation_response = await process_confirmation(
            ambiguity_result, user_id, sse_session_id
        )
        if confirmation_response.is_cancelled:
            return "操作をキャンセルしました"
        tasks = confirmation_response.updated_tasks
    
    # 4. 依存関係解決
    execution_groups = resolve_dependencies(tasks)
    
    # 5. 進捗表示開始（SSE対応）
    if sse_session_id:
        await sse_sender.send_progress(sse_session_id, 0, "処理を開始しています...")
    
    # 6. 並列実行（進捗更新付き）
    results = await execute_parallel_groups_with_progress(execution_groups, sse_session_id)
    
    # 7. レスポンス生成
    response = await generate_response(results)
    
    # 8. 完了通知
    if sse_session_id:
        await sse_sender.send_complete(sse_session_id, "処理が完了しました")
    
    return response
```

#### **特徴**
- シンプルな挨拶から複雑な在庫管理まで同じフロー
- LLM判断による責任分離
- 動的なレスポンス生成
- サービス層の内部実装に依存しない設計
- **真のAIエージェント**: 複雑なタスクを効率的に処理

### **2. ActionPlanner（タスク分解）**

#### **役割**
- ユーザーリクエストを、実行可能な「サービス呼び出しタスク」に分解する。
- LLMに対し、利用可能なサービスとその機能を提示し、最適なメソッド呼び出しシーケンスを計画させる。

#### **機能**
- 自然言語の理解とタスク分解。
- 利用可能サービスの動的取得。
- サービス呼び出しタスクのJSON形式での出力。
- タスク間の依存関係の生成。

#### **出力例**
```json
{
  "tasks": [
    {
      "id": "task1",
      "description": "牛乳を在庫に追加する",
      "service": "inventory_service",
      "method": "add_inventory",
      "parameters": {
        "item_name": "牛乳",
        "quantity": 1,
        "unit": "本"
      },
      "dependencies": []
    },
    {
      "id": "task2",
      "description": "最新の在庫状況を取得する",
      "service": "inventory_service",
      "method": "get_inventory",
      "parameters": {},
      "dependencies": ["task1"]
    },
    {
      "id": "task3",
      "description": "在庫から献立を生成する",
      "service": "recipe_service",
      "method": "generate_menu_plan",
      "parameters": {
        "inventory_items": [],
        "user_id": "user-123"
      },
      "dependencies": ["task2"]
    }
  ]
}
```

#### **実装方針**
```python
class ActionPlanner:
    def __init__(self, service_coordinator: ServiceCoordinator, llm_service: LLMService):
        self.service_coordinator = service_coordinator
        self.llm_service = llm_service
    
    async def decompose(self, user_request: str, user_id: str) -> List[Task]:
        # 1. 利用可能サービスの機能説明を取得
        available_services_info = await self.service_coordinator.get_services_description()
        
        # 2. LLMサービスによるタスク分解（外部委譲）
        # プロンプトにはサービス一覧とそのメソッドが渡される
        tasks = await self.llm_service.decompose_tasks(
            user_request, available_services_info, user_id
        )
        
        # 3. 依存関係の生成（コア機能の責任）
        tasks_with_deps = self._generate_dependencies(tasks)
        
        return tasks_with_deps
```

#### **LLM呼び出しの責任分離**
- **LLMService**: LLM呼び出しのコントロール専用
- **個別呼び出し**: 各責任で子ファイルに分解
  - `task_decomposer.py`: タスク分解専用
  - `response_formatter.py`: 最終回答整形専用
  - `constraint_solver.py`: 制約解決専用

### **3. TaskExecutor（タスク実行）**

#### **役割**
- タスクの順序管理と実行制御
- 依存関係管理
- 並列実行の制御

#### **機能**
- タスクの依存関係管理
- 優先度に基づく実行順序
- エラーハンドリングとリトライ
- 実行結果の収集
- **タスクIDによる検索と状態管理**

#### **並列実行戦略**
```python
class TaskExecutor:
    def __init__(self, service_coordinator: ServiceCoordinator):
        self.service_coordinator = service_coordinator
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        # 1. 依存関係の解決
        execution_groups = self._resolve_dependencies(tasks)
        
        # 2. 並列実行グループの実行
        results = {}
        for group in execution_groups:
            group_results = await asyncio.gather(
                *[self._execute_task(task) for task in group],
                return_exceptions=True
            )
            
            # 3. 結果の処理
            for task, result in zip(group, group_results):
                results[task.id] = result
        
        return results
```

#### **エラーハンドリング**
```python
async def _execute_task(self, task: Task) -> Any:
    try:
        # サービス層経由でタスク実行
        result = await self.service_coordinator.execute_service(
            task.service, task.method, task.parameters
        )
        return result
    except Exception as e:
        # エラーログ出力
        logger.error(f"Task {task.id} failed: {e}")
        
        # フォールバック処理
        if task.fallback_service:
            return await self.service_coordinator.execute_service(
                task.fallback_service, task.fallback_method, task.parameters
            )
        
        raise e
```

### **4. TaskChainManager（タスクチェーン管理）**

#### **役割**
- タスクチェーン全体の状態管理（実行待ち、実行中、完了）。
- SSE（Server-Sent Events）と連携し、外部にリアルタイムの進捗を通知する。
- ユーザーの確認が必要な場合にタスクチェーンを一時停止し、応答に応じて再開する。

#### **実装方針**
```python
class TaskChainManager:
    def __init__(self, sse_session_id: Optional[str] = None):
        self.tasks: List[Task] = []
        self.executed_tasks: List[Task] = []
        self.sse_sender: Optional[SSESender] = get_sse_sender(sse_session_id) if sse_session_id else None

    def set_tasks(self, tasks: List[Task]):
        """実行するタスクチェーン全体を設定"""
        self.tasks = tasks
        if self.sse_sender:
            self.sse_sender.send_start(total_tasks=len(tasks))

    def on_task_progress(self, task_id: str, status: str):
        """個々のタスクの進捗を更新し、SSEで通知"""
        # ... progress calculation logic ...
        progress_info = self.get_progress_info()
        if self.sse_sender:
            self.sse_sender.send_progress(progress_info)

    def on_chain_complete(self, final_result: Dict[str, Any]):
        """タスクチェーン全体の完了を通知"""
        if self.sse_sender:
            self.sse_sender.send_complete(final_result)

    def pause_for_confirmation(self, context: Dict[str, Any]):
        """ユーザー確認のためにチェーンを一時停止"""
        # ... pausing logic ...

    def resume_with_new_tasks(self, new_tasks: List[Task]):
        """ユーザーの応答に基づき、新しいタスクでチェーンを再開"""
        # ... resuming logic ...
```

## 🛠️ ServiceCoordinator（サービス調整）

### **役割**
- サービス層の統一インターフェース
- サービス間の調整と制御
- 利用可能サービスの管理

### **実装**
```python
class ServiceCoordinator:
    def __init__(self):
        self.services = {
            "recipe": RecipeService(),
            "inventory": InventoryService(),
            "recipe_history": RecipeHistoryService(),
            "confirmation": ConfirmationService(),
            "llm": LLMService()
        }
    
    async def get_available_services(self) -> List[str]:
        """利用可能なサービス一覧を取得"""
        return list(self.services.keys())
    
    async def execute_service(
        self, 
        service_name: str, 
        method_name: str, 
        parameters: Dict[str, Any]
    ) -> Any:
        """サービスを実行"""
        service = self.services.get(service_name)
        if not service:
            raise ServiceNotFoundError(f"Service {service_name} not found")
        
        method = getattr(service, method_name)
        return await method(**parameters)
```

## 🔄 依存関係解決アルゴリズム

### **依存関係グラフ構築**
```python
def build_dependency_graph(tasks: List[Task]) -> Dict[str, List[str]]:
    """タスクの依存関係グラフを構築"""
    graph = {}
    for task in tasks:
        graph[task.id] = task.dependencies
    return graph
```

### **トポロジカルソート**
```python
def topological_sort(graph: Dict[str, List[str]]) -> List[List[str]]:
    """依存関係を満たす実行順序を決定"""
    execution_groups = []
    remaining_tasks = set(graph.keys())
    
    while remaining_tasks:
        # 依存関係を満たしたタスクを特定
        ready_tasks = [
            task for task in remaining_tasks
            if all(dep not in remaining_tasks for dep in graph[task])
        ]
        
        if not ready_tasks:
            raise ValueError("Circular dependency detected")
        
        execution_groups.append(ready_tasks)
        remaining_tasks -= set(ready_tasks)
    
    return execution_groups
```

## 🚀 実装戦略

### **Phase 1: 基本構造**
1. **TrueReactAgent**: 基本的なReActループ
2. **ActionPlanner**: シンプルなタスク分解
3. **TaskExecutor**: 基本的なタスク実行

### **Phase 2: 高度な機能**
1. **依存関係解決**: トポロジカルソートの実装
2. **並列実行**: asyncio.gatherによる並列処理
3. **エラーハンドリング**: フォールバック処理の実装

### **Phase 3: 最適化**
1. **パフォーマンス最適化**: 実行時間の短縮
2. **メモリ最適化**: メモリ使用量の削減
3. **ログ最適化**: ログ出力の最適化

## 📊 成功基準

### **機能面**
- [ ] 統一されたReActエージェントの動作確認
- [ ] タスク分解機能の動作確認
- [ ] 依存関係解決機能の動作確認
- [ ] 並列実行機能の動作確認
- [ ] エラーハンドリング機能の動作確認

### **技術面**
- [ ] 全ファイルが150行以下
- [ ] 循環依存の排除
- [ ] 並列実行の正常動作
- [ ] 保守性の確認

---

**このドキュメントは、Morizo AI v2のコアアーキテクチャ設計を定義します。**
**すべてのコア機能は、この設計に基づいて実装されます。**
