#!/usr/bin/env python3
"""
API層 - レスポンスモデル

Pydanticによるレスポンスデータの型定義
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any


class ChatResponse(BaseModel):
    """チャットレスポンス"""
    model_config = ConfigDict(
        ser_json_exclude_defaults=False,
        ser_json_exclude_none=False
    )
    
    response: str = Field(..., description="AIからの応答")
    success: bool = Field(..., description="処理成功フラグ")
    model_used: str = Field(..., description="使用されたモデル")
    user_id: str = Field(..., description="ユーザーID")
    processing_time: Optional[float] = Field(default=None, description="処理時間（秒）")
    requires_confirmation: Optional[bool] = Field(default=False, description="曖昧性確認が必要かどうか")
    confirmation_session_id: Optional[str] = Field(default=None, description="確認セッションID")


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="サービス状態")
    service: str = Field(..., description="サービス名")
    version: str = Field(..., description="バージョン")
    timestamp: str = Field(..., description="チェック時刻")
    services: Optional[Dict[str, Any]] = Field(None, description="各サービスの状態")


class InventoryResponse(BaseModel):
    """在庫レスポンス"""
    id: str = Field(..., description="アイテムID")
    item_name: str = Field(..., description="アイテム名")
    quantity: float = Field(..., description="数量")
    unit: str = Field(..., description="単位")
    storage_location: Optional[str] = Field(None, description="保管場所")
    expiry_date: Optional[str] = Field(None, description="消費期限")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    detail: str = Field(..., description="エラー詳細")
    status_code: int = Field(..., description="HTTPステータスコード")
    timestamp: str = Field(..., description="エラー発生時刻")
    error_type: Optional[str] = Field(None, description="エラータイプ")


class SSEEvent(BaseModel):
    """SSEイベント"""
    type: str = Field(..., description="イベントタイプ")
    data: Dict[str, Any] = Field(..., description="イベントデータ")
    timestamp: str = Field(..., description="イベント時刻")
