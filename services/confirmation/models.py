#!/usr/bin/env python3
"""
Confirmation Service のデータモデル

曖昧性検出と確認プロセスで使用されるデータクラス
"""

from typing import Dict, Any, List


class AmbiguityInfo:
    """曖昧性情報クラス"""
    
    def __init__(self, task_id: str, tool_name: str, ambiguity_type: str, details: Dict[str, Any], original_parameters: Dict[str, Any] = None):
        self.task_id = task_id
        self.tool_name = tool_name
        self.ambiguity_type = ambiguity_type
        self.details = details
        self.original_parameters = original_parameters or {}
        self.is_ambiguous = True


class AmbiguityResult:
    """曖昧性検出結果クラス"""
    
    def __init__(self, requires_confirmation: bool, ambiguous_tasks: List[AmbiguityInfo]):
        self.requires_confirmation = requires_confirmation
        self.ambiguous_tasks = ambiguous_tasks


class ConfirmationResult:
    """確認プロセス結果クラス"""
    
    def __init__(self, is_cancelled: bool, updated_tasks: List[Any], confirmation_context: Dict[str, Any]):
        self.is_cancelled = is_cancelled
        self.updated_tasks = updated_tasks
        self.confirmation_context = confirmation_context
