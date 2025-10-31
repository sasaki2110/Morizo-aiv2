#!/usr/bin/env python3
"""
CandidateManager - 候補情報管理マネージャー

候補情報の保存・取得を担当
"""

from .helpers import call_session_method, call_session_void_method


class CandidateManager:
    """候補情報管理マネージャー"""
    
    def __init__(self, session_service):
        """初期化
        
        Args:
            session_service: SessionServiceインスタンスへの参照
        """
        self.session_service = session_service
    
    async def set_candidates(
        self,
        sse_session_id: str,
        category: str,
        candidates: list
    ) -> None:
        """候補情報をセッションに保存（Phase 3C-3）
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
            candidates: 候補情報のリスト
        """
        await call_session_void_method(
            self.session_service,
            sse_session_id,
            "set_candidates",
            lambda s: s.set_candidates(category, candidates),
            f"✅ [SessionService] Set {len(candidates)} {category} candidates to session"
        )
    
    async def get_candidates(
        self,
        sse_session_id: str,
        category: str
    ) -> list:
        """候補情報をセッションから取得
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 候補情報のリスト
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_candidates",
            lambda s: s.get_candidates(category),
            []
        )

