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
        """選択済みレシピを取得（親セッションからも集約）
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            Dict[str, Any]: 選択済みレシピの辞書（親セッションからも集約）
        """
        # 現在のセッションから選択済みレシピを取得
        current_recipes = await call_session_method(
            self.session_service,
            sse_session_id,
            "get_selected_recipes",
            lambda s: s.get_selected_recipes(),
            {"main": None, "sub": None, "soup": None}
        )
        
        # 親セッションIDを取得して再帰的に集約
        # 無限ループ防止のため、訪問済みセッションIDを追跡（最大10階層まで）
        return await self._get_selected_recipes_recursive(sse_session_id, current_recipes, visited=set(), max_depth=10)
    
    async def _get_selected_recipes_recursive(
        self, 
        sse_session_id: str, 
        current_recipes: Dict[str, Any],
        visited: set,
        max_depth: int
    ) -> Dict[str, Any]:
        """再帰的に選択済みレシピを集約（内部メソッド）"""
        # 無限ループ防止
        if sse_session_id in visited or max_depth <= 0:
            return current_recipes
        
        visited.add(sse_session_id)
        
        try:
            session = await self.session_service.get_session(sse_session_id, user_id=None)
            if session:
                parent_session_id = session.get_context("parent_session_id")
                if parent_session_id:
                    # 親セッションからも選択済みレシピを取得（再帰）
                    parent_recipes = await self._get_selected_recipes_recursive(
                        parent_session_id,
                        {"main": None, "sub": None, "soup": None},
                        visited,
                        max_depth - 1
                    )
                    
                    # 現在のセッションの選択済みレシピで親セッションのものを上書き
                    # （最新の選択が優先される、Noneチェックを明示的に行う）
                    merged_recipes = {
                        "main": current_recipes.get("main") if current_recipes.get("main") is not None else parent_recipes.get("main"),
                        "sub": current_recipes.get("sub") if current_recipes.get("sub") is not None else parent_recipes.get("sub"),
                        "soup": current_recipes.get("soup") if current_recipes.get("soup") is not None else parent_recipes.get("soup")
                    }
                    return merged_recipes
        except Exception as e:
            # 親セッションの取得に失敗した場合は、現在のセッションの結果を返す
            import logging
            logging.warning(f"⚠️ [StageManager] Failed to get parent session recipes: {e}")
        
        return current_recipes
    
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

