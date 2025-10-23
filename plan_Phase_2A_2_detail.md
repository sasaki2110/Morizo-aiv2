# Phase 2A-2: 統合実装 - 詳細プラン

## 概要

Phase 2A-1で実装した基盤（タスクの一時停止・再開機能、コンテキスト管理機能）を活用し、エージェント層とAPI層を統合します。統合テストで全体のフローを検証します。

## 前提条件

Phase 2A-1が完了していること:
- TaskStatusに `WAITING_FOR_USER`, `PAUSED` が追加されている
- TaskChainManagerに `pause_task_for_user_selection()`, `resume_task_after_selection()` が実装されている
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
        resume_result = task_chain_manager.resume_task_after_selection(task_id, selection)
        
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
        
        # バリデーション
        if not selection_request.task_id:
            raise HTTPException(status_code=400, detail="Task ID is required")
        
        if not (1 <= selection_request.selection <= 5):
            raise HTTPException(status_code=400, detail="Selection must be between 1 and 5")
        
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
    selection: int = Field(..., ge=1, le=5, description="選択した番号（1-5）")
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
- バリデーションが正しく動作するか（不正な selection、task_id）
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

## 詳細実装手順

### Step 1: リクエストモデルの追加

**ファイル**: `api/request_models.py` (新規作成)

**実装内容**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class UserSelectionRequest(BaseModel):
    """ユーザー選択リクエストモデル"""
    task_id: str = Field(..., description="タスクID")
    selection: int = Field(..., ge=1, le=5, description="選択した番号（1-5）")
    sse_session_id: str = Field(..., description="SSEセッションID")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "main_dish_proposal_0",
                "selection": 3,
                "sse_session_id": "session_abc123"
            }
        }

class SelectionResponse(BaseModel):
    """選択結果レスポンスモデル"""
    success: bool = Field(..., description="成功フラグ")
    task_id: str = Field(..., description="タスクID")
    selection: int = Field(..., description="選択した番号")
    message: str = Field(..., description="メッセージ")
    error: Optional[str] = Field(None, description="エラーメッセージ")
```

**テスト**: `tests/phase2a2/test_00_request_models.py`
```python
import pytest
from api.request_models import UserSelectionRequest, SelectionResponse

def test_user_selection_request_valid():
    """有効なユーザー選択リクエストのテスト"""
    request = UserSelectionRequest(
        task_id="main_dish_proposal_0",
        selection=3,
        sse_session_id="session_abc123"
    )
    assert request.task_id == "main_dish_proposal_0"
    assert request.selection == 3
    assert request.sse_session_id == "session_abc123"

def test_user_selection_request_invalid_selection():
    """無効な選択番号のテスト"""
    with pytest.raises(ValueError):
        UserSelectionRequest(
            task_id="main_dish_proposal_0",
            selection=6,  # 無効な選択番号
            sse_session_id="session_abc123"
        )
```

### Step 2: レスポンスフォーマッターの拡張

**ファイル**: `services/response_formatter.py`

**実装内容**:
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

def format_selection_result(self, selection: int, task_id: str) -> dict:
    """選択結果レスポンスのフォーマット"""
    return {
        "message": f"選択肢 {selection} を受け付けました。",
        "success": True,
        "task_id": task_id,
        "selection": selection
    }
```

**テスト**: `tests/phase2a2/test_01_response_formatter.py`
```python
import pytest
from services.response_formatter import ResponseFormatter

def test_format_selection_request():
    """選択要求フォーマットのテスト"""
    formatter = ResponseFormatter()
    candidates = [
        {
            "title": "レンコンのきんぴら",
            "ingredients": ["レンコン", "ごま油", "醤油"],
            "cooking_time": "15分",
            "category": "和食"
        },
        {
            "title": "レンコンの天ぷら",
            "ingredients": ["レンコン", "天ぷら粉", "油"],
            "cooking_time": "20分",
            "category": "和食"
        }
    ]
    
    result = formatter.format_selection_request(candidates, "main_dish_proposal_0")
    
    assert result["requires_selection"] is True
    assert result["task_id"] == "main_dish_proposal_0"
    assert "以下の5件から選択してください:" in result["message"]
    assert "1. レンコンのきんぴら" in result["message"]
    assert "2. レンコンの天ぷら" in result["message"]
```

### Step 3: TrueReactAgentの拡張

**ファイル**: `core/agent.py`

**実装内容**:
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

async def process_user_selection(self, task_id: str, selection: int, sse_session_id: str, user_id: str, token: str) -> dict:
    """ユーザー選択結果の処理"""
    try:
        self.logger.info(f"📥 [AGENT] Processing user selection: task_id={task_id}, selection={selection}")
        
        # タスクチェーンマネージャーを初期化（SSEセッションIDから復元）
        task_chain_manager = TaskChainManager(sse_session_id)
        
        # タスクを再開
        resume_result = task_chain_manager.resume_task_after_selection(task_id, selection)
        
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

**テスト**: `tests/phase2a2/test_02_agent_selection_flow.py`
```python
import pytest
from unittest.mock import Mock, AsyncMock
from core.agent import TrueReactAgent
from core.task_chain_manager import TaskChainManager

@pytest.mark.asyncio
async def test_handle_user_selection_required():
    """ユーザー選択要求処理のテスト"""
    agent = TrueReactAgent()
    task_chain_manager = Mock(spec=TaskChainManager)
    task_chain_manager.pause_task_for_user_selection.return_value = {"success": True}
    
    candidates = [
        {"title": "レンコンのきんぴら", "ingredients": ["レンコン", "ごま油"]},
        {"title": "レンコンの天ぷら", "ingredients": ["レンコン", "天ぷら粉"]}
    ]
    context = {"current_task_id": "main_dish_proposal_0"}
    
    result = await agent.handle_user_selection_required(candidates, context, task_chain_manager)
    
    assert result["success"] is True
    assert result["requires_selection"] is True
    assert result["task_id"] == "main_dish_proposal_0"
    assert len(result["candidates"]) == 2

@pytest.mark.asyncio
async def test_process_user_selection():
    """ユーザー選択結果処理のテスト"""
    agent = TrueReactAgent()
    
    # モックの設定
    with patch('core.agent.TaskChainManager') as mock_task_manager_class:
        mock_task_manager = Mock()
        mock_task_manager_class.return_value = mock_task_manager
        mock_task_manager.resume_task_after_selection.return_value = {
            "success": True,
            "context": {"selected_recipe": "レンコンのきんぴら"}
        }
        
        result = await agent.process_user_selection(
            "main_dish_proposal_0", 3, "session_abc123", "user_123", "token_123"
        )
        
        assert result["success"] is True
        assert result["task_id"] == "main_dish_proposal_0"
        assert result["selection"] == 3
```

### Step 4: API拡張

**ファイル**: `api/chat.py`

**実装内容**:
```python
from api.request_models import UserSelectionRequest
from core.agent import agent

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

**テスト**: `tests/phase2a2/test_03_selection_api_integration.py`
```python
import pytest
from fastapi.testclient import TestClient
from api.request_models import UserSelectionRequest

def test_receive_user_selection_success(client: TestClient, auth_headers: dict):
    """選択結果受信の成功テスト"""
    request_data = {
        "task_id": "main_dish_proposal_0",
        "selection": 3,
        "sse_session_id": "session_abc123"
    }
    
    response = client.post(
        "/chat/selection",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["task_id"] == "main_dish_proposal_0"
    assert data["selection"] == 3

def test_receive_user_selection_invalid_selection(client: TestClient, auth_headers: dict):
    """無効な選択番号のテスト"""
    request_data = {
        "task_id": "main_dish_proposal_0",
        "selection": 6,  # 無効な選択番号
        "sse_session_id": "session_abc123"
    }
    
    response = client.post(
        "/chat/selection",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Selection must be between 1 and 5" in response.json()["detail"]

def test_receive_user_selection_missing_task_id(client: TestClient, auth_headers: dict):
    """タスクID未指定のテスト"""
    request_data = {
        "selection": 3,
        "sse_session_id": "session_abc123"
    }
    
    response = client.post(
        "/chat/selection",
        json=request_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Task ID is required" in response.json()["detail"]
```

### Step 5: エンドツーエンドテスト

**ファイル**: `tests/phase2a2/test_04_end_to_end_selection.py`

**実装内容**:
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

@pytest.mark.asyncio
async def test_complete_selection_flow(client: TestClient, auth_headers: dict):
    """完全な選択フローのテスト"""
    # 1. ユーザーリクエスト（レンコンを使ったメインを提案して）
    chat_request = {
        "message": "レンコンを使ったメインを提案して",
        "sse_session_id": "session_abc123"
    }
    
    # 2. チャットリクエストを送信
    response = client.post(
        "/chat",
        json=chat_request,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    chat_data = response.json()
    assert chat_data["success"] is True
    
    # 3. 選択要求が返されることを確認
    assert chat_data["requires_selection"] is True
    assert "candidates" in chat_data
    assert "task_id" in chat_data
    assert len(chat_data["candidates"]) == 5
    
    task_id = chat_data["task_id"]
    
    # 4. ユーザー選択を送信
    selection_request = {
        "task_id": task_id,
        "selection": 3,
        "sse_session_id": "session_abc123"
    }
    
    selection_response = client.post(
        "/chat/selection",
        json=selection_request,
        headers=auth_headers
    )
    
    assert selection_response.status_code == 200
    selection_data = selection_response.json()
    assert selection_data["success"] is True
    assert selection_data["task_id"] == task_id
    assert selection_data["selection"] == 3

@pytest.mark.asyncio
async def test_selection_flow_with_invalid_selection(client: TestClient, auth_headers: dict):
    """無効な選択でのフローテスト"""
    # 1. ユーザーリクエスト
    chat_request = {
        "message": "レンコンを使ったメインを提案して",
        "sse_session_id": "session_abc123"
    }
    
    response = client.post(
        "/chat",
        json=chat_request,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    chat_data = response.json()
    task_id = chat_data["task_id"]
    
    # 2. 無効な選択を送信
    selection_request = {
        "task_id": task_id,
        "selection": 6,  # 無効な選択番号
        "sse_session_id": "session_abc123"
    }
    
    selection_response = client.post(
        "/chat/selection",
        json=selection_request,
        headers=auth_headers
    )
    
    assert selection_response.status_code == 400
    assert "Selection must be between 1 and 5" in selection_response.json()["detail"]
```

### Step 6: 回帰テスト

**ファイル**: `tests/phase2a2/test_05_regression.py`

**実装内容**:
```python
import pytest
from tests.phase2a1.test_01_task_status import TestTaskStatus
from tests.phase2a1.test_02_task_chain_manager import TestTaskChainManager
from tests.phase2a1.test_03_context_manager import TestContextManager

class TestPhase2A2Regression:
    """Phase 2A-2の回帰テスト"""
    
    def test_phase2a1_task_status_regression(self):
        """Phase 2A-1のTaskStatusテストを再実行"""
        test_instance = TestTaskStatus()
        test_instance.test_task_status_enum()
        test_instance.test_task_status_transitions()
    
    def test_phase2a1_task_chain_manager_regression(self):
        """Phase 2A-1のTaskChainManagerテストを再実行"""
        test_instance = TestTaskChainManager()
        test_instance.test_pause_task_for_user_selection()
        test_instance.test_resume_task_after_selection()
        test_instance.test_task_status_updates()
    
    def test_phase2a1_context_manager_regression(self):
        """Phase 2A-1のContextManagerテストを再実行"""
        test_instance = TestContextManager()
        test_instance.test_save_context_for_resume()
        test_instance.test_load_context_for_resume()
        test_instance.test_context_persistence()
```

## 実装チェックリスト

### Phase 2A-2 実装チェックリスト

- [ ] **Step 1: リクエストモデルの追加**
  - [ ] `api/request_models.py` ファイル作成
  - [ ] `UserSelectionRequest` クラス実装
  - [ ] `SelectionResponse` クラス実装
  - [ ] バリデーション設定
  - [ ] テストケース実装

- [ ] **Step 2: レスポンスフォーマッターの拡張**
  - [ ] `format_selection_request()` メソッド実装
  - [ ] `format_selection_result()` メソッド実装
  - [ ] フォーマットロジックのテスト
  - [ ] エラーハンドリングのテスト

- [ ] **Step 3: TrueReactAgentの拡張**
  - [ ] `handle_user_selection_required()` メソッド実装
  - [ ] `process_user_selection()` メソッド実装
  - [ ] エラーハンドリング実装
  - [ ] ログ出力実装
  - [ ] 単体テスト実装

- [ ] **Step 4: API拡張**
  - [ ] `POST /chat/selection` エンドポイント実装
  - [ ] バリデーション実装
  - [ ] 認証実装
  - [ ] エラーハンドリング実装
  - [ ] APIテスト実装

- [ ] **Step 5: 統合テスト実装**
  - [ ] エージェント統合テスト
  - [ ] API統合テスト
  - [ ] エンドツーエンドテスト
  - [ ] 回帰テスト

- [ ] **Step 6: テスト実行・検証**
  - [ ] 全テストの実行
  - [ ] テスト結果の確認
  - [ ] エラーの修正
  - [ ] パフォーマンステスト

- [ ] **Step 7: ドキュメント更新**
  - [ ] API仕様書の更新
  - [ ] 実装ガイドの更新
  - [ ] テストガイドの更新

## トラブルシューティング

### よくある問題と解決方法

#### 1. タスクIDが見つからないエラー
**問題**: `No task ID found in context`
**原因**: コンテキストにタスクIDが正しく設定されていない
**解決方法**: 
- タスクチェーンマネージャーでタスクIDを正しく設定
- コンテキストの保存・復元を確認

#### 2. 選択番号のバリデーションエラー
**問題**: `Selection must be between 1 and 5`
**原因**: フロントエンドから無効な選択番号が送信される
**解決方法**:
- フロントエンドでのバリデーション強化
- バックエンドでのバリデーション確認

#### 3. SSEセッションIDの不一致
**問題**: `SSE session ID is required`
**原因**: セッションIDが正しく送信されていない
**解決方法**:
- フロントエンドでのセッションID管理確認
- バックエンドでのセッションID検証確認

#### 4. タスクの一時停止・再開エラー
**問題**: `Failed to pause/resume task`
**原因**: Phase 2A-1の機能が正しく実装されていない
**解決方法**:
- Phase 2A-1のテストを再実行
- タスクチェーンマネージャーの実装確認

## パフォーマンス考慮事項

### 1. メモリ使用量
- 選択候補のデータサイズを最小限に抑制
- コンテキストの適切なクリーンアップ

### 2. レスポンス時間
- 選択結果処理の最適化
- データベースアクセスの最小化

### 3. 同時接続数
- セッション管理の最適化
- リソースの適切な解放

## セキュリティ考慮事項

### 1. 認証・認可
- トークンベースの認証
- ユーザーIDの検証

### 2. 入力検証
- 選択番号の範囲チェック
- タスクIDの形式チェック

### 3. セッション管理
- セッションIDの適切な管理
- セッションの有効期限管理

## 次のフェーズへの準備

### Phase 2B への準備
- フロントエンドとの連携インターフェースの完成
- リアルタイム通信の基盤整備
- ユーザー体験の向上準備

### Phase 3 への準備
- 副菜・汁物選択の基盤
- 段階的選択システムの拡張準備
- タスクチェーンの動的構築準備

この詳細プランに従って実装を進めることで、Phase 2A-2の統合実装が確実に完了します。
