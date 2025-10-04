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

### **1. TrueReactAgent（タスクオーケストレーター）**

#### **役割**
- ユーザー要求から最終的な応答を生成するまでの一連の処理フローを制御する、トップレベルの**調整役（Orchestrator）**。
- 各専門コンポーネント（`ActionPlanner`, `TaskExecutor`など）を適切な順序で呼び出すことに専念する。

#### **アーキテクチャ図（処理フローの概念）**
```
ユーザーリクエスト
    │
    ▼
ActionPlanner.plan()      # 1. 思考：タスクリストを一度だけ計画
    │
    ▼
TaskExecutor.execute()    # 2. 行動：タスクリストを実行
    │
    ├─ (実行中に曖昧性を検出) ─▶ 中断し、確認要求を返す
    │       │
    │       ▼
    │ ConfirmationService     # 3a. ユーザーに確認
    │       │
    │       ▼
    └─ TaskExecutor.execute()  # 3b. 新しいタスクで再実行
    │
    ▼
ResponseFormatter.format()# 4. 応答：最終結果を整形
    │
    ▼
レスポンス
```

具体的な実装フローは、以下の`TrueReactAgent`クラスの擬似コードを参照してください。

#### **実装方針（擬似コード）**
```python
class TrueReactAgent:
    # ... (init) ...

    async def process_request(self, user_request: str, user_id: str, sse_session_id: str = None) -> str:
        task_chain_manager = TaskChainManager(sse_session_id)

        # 1. 思考 (Initial Plan) - 一度だけ実行
        tasks = await self.action_planner.plan(user_request, user_id)
        task_chain_manager.set_tasks(tasks)

        # 2. 行動 (Execution) - TaskExecutorに完全実行を委譲
        # TaskExecutorは、実行中に曖昧性を検出すると、処理を中断し、
        # status='needs_confirmation' を含むExecutionResultを返す。
        execution_result = await self.task_executor.execute(
            tasks, user_id, task_chain_manager
        )

        # 3. 曖昧性の処理
        if execution_result.status == "needs_confirmation":
            task_chain_manager.pause_for_confirmation()
            user_choice = await self.confirmation_service.ask_user(execution_result.confirmation_context)
            
            if user_choice.is_cancelled:
                return "操作はキャンセルされました。"
            
            # ユーザーの選択に基づき、更新されたタスクで再度TaskExecutorを実行
            final_results = await self.task_executor.execute(
                user_choice.updated_tasks, user_id, task_chain_manager
            )
        else:
            final_results = execution_result.outputs

        # 4. 最終レスポンスの生成
        final_response = await self.response_formatter.format(final_results)
        task_chain_manager.send_complete(final_response)

        return final_response
```

### **2. ActionPlanner（初期計画の専門家）**

#### **役割**
- ユーザー要求を分析し、実行すべき**タスクリスト（行動計画）を最初に一度だけ**生成する。

### **3. TaskExecutor（タスク実行の専門家）**

#### **役割**
- `TrueReactAgent`から渡されたタスクリストの実行に関する全責任を負う、タスク実行の心臓部。

#### **機能**
- **内部ループによるタスクリストの反復処理**: 与えられたタスクリストがすべて完了するまで、内部でループ処理を実行する。
- **依存関係の解決と循環依存の検出**: 実行順序を決定し、循環依存を検出する。
- **並列実行**: **依存している先行タスクがすべて完了した**、実行可能なタスクグループを並列に実行する。
- **曖昧性の検出と処理の中断**: 下位のサービスが曖昧性を検出した場合、後続のタスク実行を中断し、確認が必要であることを示す結果を返す。
- **データ注入**: 先行タスクの結果を後続タスクのパラメータに注入する。
- **進捗報告**: `TaskChainManager`に実行状況を報告する。

#### **実装方針（擬似コード）**
```python
class TaskExecutor:
    # ... (init) ...

    async def execute(self, tasks: List[Task], user_id: str, task_chain_manager: TaskChainManager) -> ExecutionResult:
        remaining_tasks = tasks
        all_results = {}

        while remaining_tasks:
            try:
                executable_group = self._find_executable_group(remaining_tasks, all_results)
            except ValueError as e: # 循環依存を検出
                return ExecutionResult(status="error", message=str(e))

            if not executable_group: break

            coroutines = [self._execute_single_task(task, user_id, all_results) for task in executable_group]
            group_results = await asyncio.gather(*coroutines, return_exceptions=True)

            # 実行結果を評価
            for task, result in zip(executable_group, group_results):
                # 曖昧性検出のチェック
                if isinstance(result, AmbiguityDetected):
                    # 曖昧性が検出されたら、即座に処理を中断して結果を返す
                    return ExecutionResult(status="needs_confirmation", confirmation_context=result.context)
                
                if isinstance(result, Exception):
                    # ... エラーハンドリング ...
                
                all_results[task.id] = result

            remaining_tasks = [t for t in remaining_tasks if t.id not in [task.id for task in executable_group]]

        return ExecutionResult(status="success", outputs=all_results)

    async def _execute_single_task(self, task: Task, user_id: str, previous_results: dict) -> Any:
        # ... データ注入ロジック ...
        injected_params = self._inject_data(task.parameters, previous_results)
        
        # ServiceCoordinator経由でサービスを呼び出す
        # サービスは曖昧性を検出すると、AmbiguityDetectedオブジェクトを返す場合がある
        return await self.service_coordinator.execute_service(
            task.service, task.method, injected_params
        )
```

### **4. TaskChainManager（状態管理と通知のハブ）**

#### **役割**
- タスク実行プロセス全体の状態を一元管理し、外部（特にSSE）との通信を担うハブ。

#### **機能**
- **タスクチェーンの状態管理**: 全タスクリスト、実行済みタスク、結果などを管理する。
- **進捗通知のディスパッチ**: `TaskExecutor`からの進捗報告を受け取り、接続されている全てのSSEクライアントに配信する。
- **中断と再開の管理**: 曖昧性確認などによるタスクチェーンの一時停止・再開の内部状態を管理する。

### **5. ResponseFormatter（最終応答生成の専門家）**

#### **役割**
- `TaskExecutor`から渡された最終的なタスク実行結果（構造化データ）を受け取り、これをユーザーにとって自然で分かりやすい応答文に整形する責務を持つ。

#### **設計思想**
- これは、正規表現やテンプレート置換を駆使した静的な文字列処理ではない。
- `ResponseFormatter`は、最終結果を元に、**LLMに対して要約や対話生成を依頼するための専用プロンプトを構築**し、その結果をユーザーへの最終応答とする。これにより、一連のタスク実行の文脈を汲んだ、より自然で知的な応答が実現される。
