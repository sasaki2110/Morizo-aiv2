from pydantic import BaseModel, Field
from typing import Optional

class UserSelectionRequest(BaseModel):
    """ユーザー選択リクエストモデル"""
    task_id: str = Field(..., description="タスクID")
    selection: int = Field(..., description="選択した番号")
    sse_session_id: str = Field(..., description="SSEセッションID")
    old_sse_session_id: Optional[str] = Field(None, description="旧SSEセッションID（追加提案時のコンテキスト復元用）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "main_dish_proposal_0",
                "selection": 3,
                "sse_session_id": "session_abc123",
                "old_sse_session_id": "old_session_xyz789"
            }
        }

class SelectionResponse(BaseModel):
    """選択結果レスポンスモデル"""
    success: bool = Field(..., description="成功フラグ")
    task_id: str = Field(..., description="タスクID")
    selection: int = Field(..., description="選択した番号")
    message: str = Field(..., description="メッセージ")
    error: Optional[str] = Field(None, description="エラーメッセージ")
