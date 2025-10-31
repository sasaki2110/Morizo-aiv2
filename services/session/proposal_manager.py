#!/usr/bin/env python3
"""
ProposalManager - 提案レシピ管理マネージャー

提案済みレシピの追加・取得を担当
"""

from .helpers import call_session_method, call_session_void_method


class ProposalManager:
    """提案レシピ管理マネージャー"""
    
    def __init__(self, session_service):
        """初期化
        
        Args:
            session_service: SessionServiceインスタンスへの参照
        """
        self.session_service = session_service
    
    async def add_proposed_recipes(
        self, 
        sse_session_id: str, 
        category: str, 
        titles: list
    ) -> None:
        """提案済みレシピをセッションに追加
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
            titles: 提案済みタイトルのリスト
        """
        await call_session_void_method(
            self.session_service,
            sse_session_id,
            "add_proposed_recipes",
            lambda s: s.add_proposed_recipes(category, titles),
            f"✅ [SessionService] Added {len(titles)} proposed {category} recipes to session"
        )
    
    async def get_proposed_recipes(
        self, 
        sse_session_id: str, 
        category: str
    ) -> list:
        """提案済みレシピをセッションから取得
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 提案済みタイトルのリスト
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_proposed_recipes",
            lambda s: s.get_proposed_recipes(category),
            []
        )

