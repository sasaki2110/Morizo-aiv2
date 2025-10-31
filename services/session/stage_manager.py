#!/usr/bin/env python3
"""
StageManager - 段階管理マネージャー

段階的なレシピ選択の管理を担当
"""

from typing import Dict, Any
from .helpers import call_session_method, call_session_void_method


class StageManager:
    """段階管理マネージャー"""
    
    def __init__(self, session_service):
        """初期化
        
        Args:
            session_service: SessionServiceインスタンスへの参照
        """
        self.session_service = session_service
    
    async def get_current_stage(self, sse_session_id: str) -> str:
        """現在の段階を取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            str: 現在の段階
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_current_stage",
            lambda s: s.get_current_stage(),
            "main"
        )
    
    async def set_selected_recipe(
        self, 
        sse_session_id: str, 
        category: str, 
        recipe: Dict[str, Any]
    ) -> None:
        """選択したレシピを保存
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
            recipe: レシピ情報
        """
        await call_session_void_method(
            self.session_service,
            sse_session_id,
            "set_selected_recipe",
            lambda s: s.set_selected_recipe(category, recipe),
            f"✅ [SessionService] Recipe selected for {category}"
        )
    
    async def get_selected_recipes(self, sse_session_id: str) -> Dict[str, Any]:
        """選択済みレシピを取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            Dict[str, Any]: 選択済みレシピの辞書
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_selected_recipes",
            lambda s: s.get_selected_recipes(),
            {"main": None, "sub": None, "soup": None}
        )
    
    async def get_used_ingredients(self, sse_session_id: str) -> list:
        """使用済み食材を取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            list: 使用済み食材のリスト
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_used_ingredients",
            lambda s: s.get_used_ingredients(),
            []
        )
    
    async def get_menu_category(self, sse_session_id: str) -> str:
        """献立カテゴリを取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            str: 献立カテゴリ（"japanese", "western", "chinese"）
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_menu_category",
            lambda s: s.get_menu_category(),
            "japanese"
        )

