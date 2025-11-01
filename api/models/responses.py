#!/usr/bin/env python3
"""
API層 - レスポンスモデル

Pydanticによるレスポンスデータの型定義
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


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
    requires_selection: Optional[bool] = Field(default=False, description="ユーザー選択が必要かどうか")
    candidates: Optional[List[Dict[str, Any]]] = Field(default=None, description="選択候補リスト")
    task_id: Optional[str] = Field(default=None, description="タスクID")
    # Phase 3D: 段階情報
    current_stage: Optional[str] = Field(default=None, description="現在の段階（main/sub/soup）")
    used_ingredients: Optional[List[str]] = Field(default=None, description="使い残し食材リスト（在庫食材 - 使用済み食材）")
    menu_category: Optional[str] = Field(default=None, description="メニューカテゴリ（japanese/western/chinese）")
    # Phase 3C-3: 自動遷移フラグ
    requires_next_stage: Optional[bool] = Field(default=False, description="次の段階の提案が必要かどうか")


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


class SavedRecipe(BaseModel):
    """保存されたレシピ"""
    title: str = Field(..., description="レシピのタイトル")
    category: str = Field(..., description="レシピのカテゴリ")
    history_id: str = Field(..., description="保存されたレシピ履歴のID")


class RecipeAdoptionResponse(BaseModel):
    """レシピ採用通知レスポンス（複数対応）"""
    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="レスポンスメッセージ")
    saved_recipes: List[SavedRecipe] = Field(..., description="保存されたレシピのリスト")
    total_saved: int = Field(..., description="保存されたレシピ数")


class SavedMenuRecipe(BaseModel):
    """保存されたレシピ情報（献立保存用）"""
    category: str = Field(..., description="カテゴリ（main, sub, soup）")
    title: str = Field(..., description="プレフィックス付きタイトル")
    history_id: str = Field(..., description="保存されたレシピ履歴のID")


class MenuSaveResponse(BaseModel):
    """献立保存レスポンス"""
    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="レスポンスメッセージ")
    saved_recipes: List[SavedMenuRecipe] = Field(..., description="保存されたレシピのリスト")
    total_saved: int = Field(..., description="保存されたレシピ数")


class HistoryRecipe(BaseModel):
    """履歴レシピ情報"""
    category: Optional[str] = Field(None, description="カテゴリ（main, sub, soup, None）")
    title: str = Field(..., description="レシピのタイトル")
    source: str = Field(..., description="レシピの出典（web, rag等）")
    url: Optional[str] = Field(None, description="レシピのURL")
    history_id: str = Field(..., description="レシピ履歴のID")


class HistoryEntry(BaseModel):
    """履歴エントリ（日付単位）"""
    date: str = Field(..., description="日付（YYYY-MM-DD形式）")
    recipes: List[HistoryRecipe] = Field(..., description="その日のレシピリスト")


class MenuHistoryResponse(BaseModel):
    """献立履歴レスポンス"""
    success: bool = Field(..., description="処理成功フラグ")
    data: List[HistoryEntry] = Field(..., description="日付別の履歴エントリリスト")
