#!/usr/bin/env python3
"""
API層 - リクエストモデル

Pydanticによるリクエストデータの型定義とバリデーション
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """チャットリクエスト"""
    model_config = {"populate_by_name": True}  # Pydantic v2
    
    message: str = Field(..., description="ユーザーメッセージ", min_length=1, max_length=1000)
    token: Optional[str] = Field(None, description="認証トークン")
    sse_session_id: Optional[str] = Field(None, description="SSEセッションID", alias="sseSessionId")
    confirm: bool = Field(
        default=False, 
        description="曖昧性解決の回答かどうか"
    )
    
    @field_validator('confirm', mode='before')
    @classmethod
    def validate_confirm(cls, v):
        """confirmのバリデーション（デバッグ用）"""
        from config.loggers import GenericLogger
        logger = GenericLogger("api", "pydantic")
        logger.info(f"🔍 [Pydantic] confirm validator called with value: {v} (type: {type(v)})")
        return v


class ProgressUpdate(BaseModel):
    """進捗更新"""
    type: str = Field(..., description="更新タイプ: progress, complete, error")
    progress: int = Field(..., description="進捗率（0-100）", ge=0, le=100)
    message: str = Field(..., description="進捗メッセージ")
    timestamp: str = Field(..., description="タイムスタンプ")


class InventoryRequest(BaseModel):
    """在庫リクエスト"""
    item_name: str = Field(..., description="アイテム名", min_length=1, max_length=100)
    quantity: float = Field(..., description="数量", gt=0)
    unit: str = Field(..., description="単位", min_length=1, max_length=20)
    storage_location: Optional[str] = Field(None, description="保管場所", max_length=50)
    expiry_date: Optional[str] = Field(None, description="消費期限")


class HealthRequest(BaseModel):
    """ヘルスチェックリクエスト"""
    check_services: Optional[bool] = Field(False, description="サービス状態の確認")


class RecipeItem(BaseModel):
    """個別レシピアイテム"""
    title: str = Field(
        ..., 
        description="レシピのタイトル", 
        min_length=1, 
        max_length=255
    )
    category: str = Field(
        ..., 
        description="レシピのカテゴリ",
        pattern="^(main_dish|side_dish|soup)$"
    )
    menu_source: str = Field(
        ..., 
        description="メニューの出典",
        pattern="^(llm_menu|rag_menu|manual)$"
    )
    url: Optional[str] = Field(
        None, 
        description="レシピのURL（Web検索から採用した場合）"
    )


class RecipeAdoptionRequest(BaseModel):
    """レシピ採用通知リクエスト（複数対応）"""
    recipes: List[RecipeItem] = Field(
        ..., 
        description="採用されたレシピのリスト",
        min_length=1,
        max_length=3  # 主菜・副菜・汁物の最大3つ
    )
    token: Optional[str] = Field(
        None, 
        description="認証トークン（ヘッダーからも取得可能）"
    )


class MenuSaveRequest(BaseModel):
    """献立保存リクエスト"""
    sse_session_id: Optional[str] = Field(None, description="SSEセッションID（後方互換性のためオプショナル）")
    recipes: Optional[Dict[str, Any]] = Field(None, description="選択済みレシピ（main, sub, soup）。指定された場合はセッションIDよりも優先される")
