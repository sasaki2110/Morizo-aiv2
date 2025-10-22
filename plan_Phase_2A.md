# Phase 2A: バックエンド基盤の実装

## 概要

Phase 2Aでは、ユーザー選択機能のバックエンド基盤を実装します。タスクの一時停止・再開機能、選択結果受付機能、状態管理機能を追加し、フロントエンドとの連携準備を行います。

## 対象範囲

- タスクの一時停止・再開機能
- 選択結果受付機能
- 状態管理機能
- API設計の拡張
- 基本的なテスト

## 実装計画

### 1. タスク状態管理の拡張

#### 1.1 TaskStatusの拡張
**修正する場所**: `models/task.py`

**修正する内容**:
```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_USER = "waiting_for_user"  # 新規追加
    PAUSED = "paused"  # 新規追加
```

**修正の理由**: ユーザー選択待ちの状態を管理するため

**修正の影響**: 既存のタスク状態管理に影響なし

#### 1.2 タスクの一時停止機能
**修正する場所**: `services/task_chain_manager.py`

**修正する内容**:
```python
async def pause_task_for_user_selection(self, task_id: str, context: dict):
    """ユーザー選択待ちでタスクを一時停止"""
    try:
        # タスク状態を一時停止に変更
        await self.update_task_status(task_id, TaskStatus.WAITING_FOR_USER)
        
        # 再開用にコンテキストを保存
        await self.context_manager.save_context_for_resume(task_id, context)
        
        logger.info(f"Task {task_id} paused for user selection")
        return {"success": True, "task_id": task_id}
        
    except Exception as e:
        logger.error(f"Failed to pause task {task_id}: {e}")
        return {"success": False, "error": str(e)}
```

**修正の理由**: ユーザー選択待ちでタスクを一時停止するため

**修正の影響**: 既存のタスク実行フローに影響なし

#### 1.3 タスクの再開機能
**修正する場所**: `services/task_chain_manager.py`

**修正する内容**:
```python
async def resume_task_after_selection(self, task_id: str, user_selection: int):
    """ユーザー選択後にタスクを再開"""
    try:
        # 再開用のコンテキストを読み込み
        context = await self.context_manager.load_context_for_resume(task_id)
        if not context:
            raise ValueError(f"No context found for task {task_id}")
        
        # ユーザー選択をコンテキストに追加
        context['user_selection'] = user_selection
        
        # タスク状態を実行中に変更
        await self.update_task_status(task_id, TaskStatus.RUNNING)
        
        # タスクを再実行
        result = await self.execute_task(task_id, context)
        
        logger.info(f"Task {task_id} resumed with selection {user_selection}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to resume task {task_id}: {e}")
        return {"success": False, "error": str(e)}
```

**修正の理由**: ユーザー選択後にタスクを再開するため

**修正の影響**: 既存のタスク実行フローに影響なし

### 2. コンテキスト管理の拡張

#### 2.1 一時停止コンテキストの管理
**修正する場所**: `services/context_manager.py`

**修正する内容**:
```python
class ContextManager:
    def __init__(self):
        self.paused_contexts = {}  # 一時停止中のコンテキスト
        self.context_ttl = 3600  # 1時間でタイムアウト
    
    async def save_context_for_resume(self, task_id: str, context: dict):
        """再開用にコンテキストを保存"""
        try:
            # タイムスタンプを追加
            context['paused_at'] = time.time()
            
            # コンテキストを保存
            self.paused_contexts[task_id] = context
            
            logger.info(f"Context saved for task {task_id}")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Failed to save context for task {task_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def load_context_for_resume(self, task_id: str):
        """再開用のコンテキストを読み込み"""
        try:
            if task_id not in self.paused_contexts:
                return None
            
            context = self.paused_contexts.pop(task_id)
            
            # タイムアウトチェック
            if time.time() - context.get('paused_at', 0) > self.context_ttl:
                logger.warning(f"Context for task {task_id} has expired")
                return None
            
            logger.info(f"Context loaded for task {task_id}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to load context for task {task_id}: {e}")
            return None
```

**修正の理由**: 一時停止中のコンテキストを管理するため

**修正の影響**: 既存のコンテキスト管理に影響なし

### 3. エージェントの拡張

#### 3.1 ユーザー選択待ちの処理
**修正する場所**: `services/agent.py`

**修正する内容**:
```python
async def handle_user_selection_required(self, candidates: list, context: dict):
    """ユーザー選択が必要な場合の処理"""
    try:
        # タスクIDを取得
        task_id = context.get('current_task_id')
        if not task_id:
            raise ValueError("No task ID found in context")
        
        # タスクを一時停止
        pause_result = await self.task_chain_manager.pause_task_for_user_selection(
            task_id, context
        )
        
        if not pause_result["success"]:
            raise Exception(f"Failed to pause task: {pause_result['error']}")
        
        # フロントエンドに選択要求を送信
        response = {
            "success": True,
            "requires_selection": True,
            "candidates": candidates,
            "task_id": task_id,
            "message": "以下の5件から選択してください:"
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to handle user selection required: {e}")
        return {
            "success": False,
            "error": str(e),
            "requires_selection": False
        }
```

**修正の理由**: ユーザー選択待ちの処理を統合するため

**修正の影響**: 既存のエージェント処理に影響なし

#### 3.2 選択結果の処理
**修正する場所**: `services/agent.py`

**修正する内容**:
```python
async def process_user_selection(self, task_id: str, selection: int):
    """ユーザー選択結果の処理"""
    try:
        # タスクを再開
        result = await self.task_chain_manager.resume_task_after_selection(
            task_id, selection
        )
        
        if not result["success"]:
            raise Exception(f"Failed to resume task: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to process user selection: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

**修正の理由**: ユーザー選択結果を処理するため

**修正の影響**: 既存のエージェント処理に影響なし

### 4. API設計の拡張

#### 4.1 選択結果受付エンドポイント
**修正する場所**: `api/chat.py`

**修正する内容**:
```python
@router.post("/chat/selection")
async def receive_user_selection(
    selection_request: UserSelectionRequest,
    token: str = Depends(verify_token)
):
    """ユーザーの選択結果を受信"""
    try:
        user_id = get_user_id_from_token(token)
        
        # バリデーション
        if not selection_request.task_id:
            raise HTTPException(status_code=400, detail="Task ID is required")
        
        if not (1 <= selection_request.selection <= 5):
            raise HTTPException(status_code=400, detail="Selection must be between 1 and 5")
        
        # エージェントで選択結果を処理
        result = await agent.process_user_selection(
            selection_request.task_id,
            selection_request.selection
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to receive user selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**修正の理由**: ユーザー選択結果を受信するため

**修正の影響**: 既存のAPIに影響なし

#### 4.2 リクエストモデルの追加
**修正する場所**: `models/requests.py`

**修正する内容**:
```python
class UserSelectionRequest(BaseModel):
    task_id: str
    selection: int
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "task_123",
                "selection": 3
            }
        }
```

**修正の理由**: ユーザー選択リクエストの型定義のため

**修正の影響**: 既存のモデルに影響なし

### 5. レスポンスフォーマッターの拡張

#### 5.1 選択要求レスポンスのフォーマット
**修正する場所**: `services/response_formatter.py`

**修正する内容**:
```python
def format_selection_request(self, candidates: list, task_id: str):
    """選択要求レスポンスのフォーマット"""
    formatted = "以下の5件から選択してください:\n\n"
    
    for i, candidate in enumerate(candidates, 1):
        formatted += f"{i}. {candidate['title']}\n"
        formatted += f"   食材: {', '.join(candidate['ingredients'])}\n"
        if 'cooking_time' in candidate:
            formatted += f"   調理時間: {candidate['cooking_time']}\n"
        formatted += "\n"
    
    formatted += "番号を選択してください（1-5）:"
    
    return {
        "message": formatted,
        "requires_selection": True,
        "candidates": candidates,
        "task_id": task_id
    }
```

**修正の理由**: 選択要求のレスポンスをフォーマットするため

**修正の影響**: 既存のレスポンスフォーマットに影響なし

## テスト計画

### 1. 単体テスト

#### 1.1 タスク状態管理テスト
**テストケース**: `test_task_status_management()`
- タスクの一時停止機能
- タスクの再開機能
- 状態遷移の確認

#### 1.2 コンテキスト管理テスト
**テストケース**: `test_context_management()`
- コンテキストの保存・読み込み
- タイムアウト処理
- エラーハンドリング

#### 1.3 エージェント機能テスト
**テストケース**: `test_agent_selection_handling()`
- ユーザー選択待ちの処理
- 選択結果の処理
- エラーハンドリング

### 2. 統合テスト

#### 2.1 API統合テスト
**テストケース**: `test_selection_api_integration()`
- 選択結果受付エンドポイント
- バリデーション
- エラーハンドリング

#### 2.2 タスクチェーン統合テスト
**テストケース**: `test_task_chain_with_selection()`
- タスクの一時停止・再開
- コンテキストの保持
- 状態管理の整合性

## 実装順序

1. **TaskStatusの拡張** → 基本状態管理
2. **タスクの一時停止・再開機能** → 核心機能
3. **コンテキスト管理の拡張** → 状態保持
4. **エージェントの拡張** → 統合処理
5. **API設計の拡張** → 外部インターフェース
6. **レスポンスフォーマッターの拡張** → 表示機能
7. **テスト実装** → 品質保証

## 期待される効果

- ユーザー選択機能のバックエンド基盤が完成
- フロントエンドとの連携準備が整う
- Phase 2Bでのフロントエンド実装が容易になる
- タスクの一時停止・再開機能が利用可能

## 制約事項

- フロントエンドの修正は含まない
- 既存のAPI構造を維持
- Phase 1の機能を破壊しない
- セッション管理は簡易実装

## 成功基準

- すべての単体テストが成功
- 統合テストが成功
- タスクの一時停止・再開が正常に動作
- コンテキスト管理が正常に動作
- APIエンドポイントが正常に動作

## 次のステップ

Phase 2A完了後、Phase 2B（フロントエンド連携の実装）に進みます。
