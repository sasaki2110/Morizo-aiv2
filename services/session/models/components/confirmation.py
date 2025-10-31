#!/usr/bin/env python3
"""
ConfirmationComponent - 確認管理コンポーネント

確認コンテキストの管理を担当
"""

from typing import Dict, Any, Optional
from datetime import datetime
from config.loggers import GenericLogger


class ConfirmationComponent:
    """確認管理コンポーネント"""
    
    def __init__(self, logger: GenericLogger):
        """初期化
        
        Args:
            logger: ロガーインスタンス
        """
        self.logger = logger
        self.confirmation_context: Dict[str, Any] = {
            "type": None,  # "inventory_operation" | "ambiguity_resolution"
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
    
    def is_waiting(self) -> bool:
        """確認待ち状態かどうか"""
        return self.confirmation_context.get("type") is not None
    
    def set_ambiguity_confirmation(
        self, 
        original_request: str, 
        question: str,
        ambiguity_details: Dict[str, Any]
    ):
        """曖昧性解消の確認状態を設定"""
        self.confirmation_context = {
            "type": "ambiguity_resolution",
            "original_request": original_request,
            "clarification_question": question,
            "detected_ambiguity": ambiguity_details,
            "timestamp": datetime.now()
        }
    
    def clear(self):
        """確認コンテキストをクリア"""
        self.confirmation_context = {
            "type": None,
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
    
    def get_type(self) -> Optional[str]:
        """確認タイプを取得"""
        return self.confirmation_context.get("type")

