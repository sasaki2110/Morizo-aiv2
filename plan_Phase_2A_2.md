# Phase 2A-2: 統合実装

## 概要

Phase 2A-1で実装した基盤（タスクの一時停止・再開機能、コンテキスト管理機能）を活用し、エージェント層とAPI層を統合します。統合テストで全体のフローを検証します。

## 前提条件

Phase 2A-1が完了していること:
- TaskStatusに `WAITING_FOR_USER`, `PAUSED` が追加されている
- TaskChainManagerに `pause_for_confirmation()`, `resume_execution()` が実装されている
- ContextManagerに `save_context_for_resume()`, `load_context_for_resume()` が実装されている
- Phase 2A-1の単体テストがすべて成功している

## 対象範囲

- TrueReactAgentの拡張（ユーザー選択待ち・選択結果処理）
- API拡張（選択結果受付エンドポイント）
- リクエストモデルの追加
- レスポンスフォーマッターの拡張
- 統合テスト（全体フローの検証）

## 実装計画

### 1. TrueReactAgentの拡張

**修正する場所**: `core/agent.py` (TrueReactAgentクラス)

**修正する内容**:

#### 1.1 ユーザー選択待ちの処理
```python
async def handle_user_selection_required(self, candidates: list, context: dict, task_chain_manager: TaskChainManager) -> dict:
    """ユーザー選択が必要な場合の処理"""
    try:
        # タスクIDを取得
        task_id = context.get('current_task_id')
        if not task_id:
            raise ValueError("No task ID found in context")
        
        # タスクを一時停止
        pause_result = task_chain_manager.pause_task_for_user_selection(task_id, context)
        
        if not pause_result["success"]:
            raise Exception(f"Failed to pause task: {pause_result['error']}")
        
        self.logger.info(f"⏸️ [AGENT] Task {task_id} paused for user selection")
        
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
        self.logger.error(f"❌ [AGENT] Failed to handle user selection required: {e}")
        return {
            "success": False,
            "error": str(e),
            "requires_selection": False
        }
```

**修正の理由**: ユーザー選択待ちの処理を統合するため

**修正の影響**: 既存のエージェント処理に影響なし（新規メソッド追加）

#### 1.2 選択結果の処理
```python
async def process_user_selection(self, task_id: str, selection: int, sse_session_id: str, user_id: str, token: str) -> dict:
    """ユーザー選択結果の処理"""
    try:
        self.logger.info(f"📥 [AGENT] Processing user selection: task_id={task_id}, selection={selection}")
        
        # タスクチェーンマネージャーを初期化（SSEセッションIDから復元）
        task_chain_manager = TaskChainManager(sse_session_id)
        
        # タスクを再開
        resume_result = task_chain_manager.resume_execution()
        
        if not resume_result["success"]:
            raise Exception(f"Failed to resume task: {resume_result['error']}")
        
        # 再開後のコンテキストを取得
        context = resume_result.get("context", {})
        
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
```

**修正の理由**: ユーザー選択結果を処理し、タスクを再開するため

**修正の影響**: 既存のエージェント処理に影響なし（新規メソッド追加）

### 2. API拡張

**修正する場所**: `api/chat.py`

**修正する内容**:

#### 2.1 選択結果受付エンドポイント
```python
@router.post("/chat/selection")
async def receive_user_selection(
    selection_request: UserSelectionRequest,
    token: str = Depends(verify_token)
):
    """ユーザーの選択結果を受信"""
    try:
        user_id = get_user_id_from_token(token)
        
        # バリデーション（基本的な必須項目のみ）
        if not selection_request.task_id:
            raise HTTPException(status_code=400, detail="Task ID is required")
        
        if not selection_request.sse_session_id:
            raise HTTPException(status_code=400, detail="SSE session ID is required")
        
        logger.info(f"📥 [API] Received user selection: task_id={selection_request.task_id}, selection={selection_request.selection}")
        
        # エージェントで選択結果を処理
        result = await agent.process_user_selection(
            selection_request.task_id,
            selection_request.selection,
            selection_request.sse_session_id,
            user_id,
            token
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Failed to receive user selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**修正の理由**: ユーザー選択結果を受信するため

**修正の影響**: 既存のAPIに影響なし（新規エンドポイント追加）

### 3. リクエストモデルの追加

**修正する場所**: `api/models.py` または新規ファイル `api/request_models.py`

**修正する内容**:
```python
from pydantic import BaseModel, Field

class UserSelectionRequest(BaseModel):
    """ユーザー選択リクエストモデル"""
    task_id: str = Field(..., description="タスクID")
    selection: int = Field(..., description="選択した番号")
    sse_session_id: str = Field(..., description="SSEセッションID")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "main_dish_proposal_0",
                "selection": 3,
                "sse_session_id": "session_abc123"
            }
        }
```

**修正の理由**: ユーザー選択リクエストの型定義のため

**修正の影響**: 既存のモデルに影響なし（新規モデル追加）

### 4. レスポンスフォーマッターの拡張

**修正する場所**: `services/response_formatter.py` または既存のフォーマッター

**修正する内容**:
```python
def format_selection_request(self, candidates: list, task_id: str) -> dict:
    """選択要求レスポンスのフォーマット"""
    formatted = "以下の5件から選択してください:\n\n"
    
    for i, candidate in enumerate(candidates, 1):
        formatted += f"{i}. {candidate.get('title', '不明なレシピ')}\n"
        
        # 食材リスト
        ingredients = candidate.get('ingredients', [])
        if ingredients:
            formatted += f"   食材: {', '.join(ingredients)}\n"
        
        # 調理時間
        cooking_time = candidate.get('cooking_time')
        if cooking_time:
            formatted += f"   調理時間: {cooking_time}\n"
        
        # カテゴリ
        category = candidate.get('category')
        if category:
            formatted += f"   カテゴリ: {category}\n"
        
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

**修正の影響**: 既存のレスポンスフォーマットに影響なし（新規メソッド追加）

## テスト計画

### 1. エージェント統合テスト

**テストファイル**: `tests/phase2a2/test_01_agent_selection_flow.py`

**テストケース**:
- `handle_user_selection_required()`: 選択要求が正しく処理されるか
- `process_user_selection()`: 選択結果が正しく処理されるか
- Phase 2A-1の機能と正しく連携できるか
- エラーハンドリングが正しく動作するか

### 2. API統合テスト

**テストファイル**: `tests/phase2a2/test_02_selection_api_integration.py`

**テストケース**:
- `POST /chat/selection`: エンドポイントが正しく動作するか
- バリデーションが正しく動作するか（不正な task_id）
- 認証が正しく動作するか
- エラーハンドリングが正しく動作するか

### 3. エンドツーエンドテスト

**テストファイル**: `tests/phase2a2/test_03_end_to_end_selection.py`

**テストケース**:
- ユーザーリクエスト → 5件提案 → 選択 → 再開の全体フロー
- タスクチェーン全体が正しく動作するか
- コンテキストが正しく保持されるか
- SSEセッションとの連携が正しく動作するか

### 4. 回帰テスト

**テストファイル**: Phase 2A-1のテストをすべて再実行

**目的**: Phase 2A-2の実装がPhase 2A-1の機能を破壊していないか確認

## 実装順序

1. リクエストモデルの追加（型定義）
2. レスポンスフォーマッターの拡張（表示機能）
3. TrueReactAgentの拡張（ビジネスロジック）
4. API拡張（外部インターフェース）
5. 統合テスト実装（3ファイル）
6. テスト実行・検証
7. 回帰テスト実行

## 期待される効果

- ユーザー選択機能のバックエンドが完成
- フロントエンドとの連携準備が整う
- Phase 2Bでのフロントエンド実装が容易になる
- エンドツーエンドで選択機能が動作する

## 制約事項

- フロントエンドの修正は含まない（Phase 2Bで実施）
- 副菜・汁物の段階的選択は含まない（Phase 3で実施）
- タスクチェーンのロールバックは含まない（Phase 4で実施）
- Phase 1の機能を破壊しない

## 成功基準

- すべての統合テストが成功
- Phase 2A-1の単体テストが引き続き成功（回帰テストOK）
- エンドツーエンドでユーザー選択フローが動作
- APIエンドポイントが正常に動作
- エラーハンドリングが適切に動作

## 次のステップ

Phase 2A-2完了後、Phase 2B（フロントエンド連携の実装）に進みます。

