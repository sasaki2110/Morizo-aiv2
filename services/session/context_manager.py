#!/usr/bin/env python3
"""
ContextManager - セッションコンテキスト管理マネージャー

セッションコンテキストの設定・取得を担当
"""

from typing import Any
from .helpers import call_session_method, call_session_void_method


class ContextManager:
    """セッションコンテキスト管理マネージャー"""
    
    def __init__(self, session_service):
        """初期化
        
        Args:
            session_service: SessionServiceインスタンスへの参照
        """
        self.session_service = session_service
    
    async def set_session_context(
        self, 
        sse_session_id: str, 
        key: str, 
        value: Any
    ) -> None:
        """セッションコンテキストを設定
        
        Args:
            sse_session_id: SSEセッションID
            key: コンテキストキー
            value: 値
        """
        await call_session_void_method(
            self.session_service,
            sse_session_id,
            "set_session_context",
            lambda s: s.set_context(key, value),
            f"✅ [SessionService] Set session context: {key}"
        )
    
    async def get_session_context(
        self, 
        sse_session_id: str, 
        key: str, 
        default: Any = None
    ) -> Any:
        """セッションコンテキストを取得
        
        Args:
            sse_session_id: SSEセッションID
            key: コンテキストキー
            default: デフォルト値
        
        Returns:
            Any: コンテキスト値
        """
        return await call_session_method(
            self.session_service,
            sse_session_id,
            "get_session_context",
            lambda s: s.get_context(key, default),
            default
        )

