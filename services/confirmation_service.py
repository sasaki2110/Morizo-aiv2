#!/usr/bin/env python3
"""
ConfirmationService - 確認プロセスサービス

曖昧性検出と確認プロセスのビジネスロジックを提供
タスクチェーン保持機能を実装
"""

from typing import Dict, Any, List, Optional
from config.loggers import GenericLogger


class AmbiguityInfo:
    """曖昧性情報クラス"""
    
    def __init__(self, task_id: str, tool_name: str, ambiguity_type: str, details: Dict[str, Any]):
        self.task_id = task_id
        self.tool_name = tool_name
        self.ambiguity_type = ambiguity_type
        self.details = details
        self.is_ambiguous = True


class AmbiguityResult:
    """曖昧性検出結果クラス"""
    
    def __init__(self, requires_confirmation: bool, ambiguous_tasks: List[AmbiguityInfo]):
        self.requires_confirmation = requires_confirmation
        self.ambiguous_tasks = ambiguous_tasks


class ConfirmationResult:
    """確認プロセス結果クラス"""
    
    def __init__(self, is_cancelled: bool, updated_tasks: List[Dict[str, Any]], confirmation_context: Dict[str, Any]):
        self.is_cancelled = is_cancelled
        self.updated_tasks = updated_tasks
        self.confirmation_context = confirmation_context


class ConfirmationService:
    """確認プロセスサービス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "confirmation")
    
    async def detect_ambiguity(
        self, 
        tasks: List[Dict[str, Any]], 
        user_id: str
    ) -> AmbiguityResult:
        """
        曖昧性検出
        
        Args:
            tasks: タスクリスト
            user_id: ユーザーID
        
        Returns:
            曖昧性検出結果
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Detecting ambiguity for user: {user_id}")
            
            ambiguous_tasks = []
            
            # 各タスクの曖昧性チェック
            for task in tasks:
                if task.get("tool", "").startswith("inventory_"):
                    # 在庫操作の曖昧性チェック
                    ambiguity_info = await self._check_inventory_ambiguity(task, user_id)
                    if ambiguity_info and ambiguity_info.is_ambiguous:
                        ambiguous_tasks.append(ambiguity_info)
            
            requires_confirmation = len(ambiguous_tasks) > 0
            
            result = AmbiguityResult(
                requires_confirmation=requires_confirmation,
                ambiguous_tasks=ambiguous_tasks
            )
            
            self.logger.info(f"✅ [ConfirmationService] Ambiguity detection completed: {len(ambiguous_tasks)} ambiguous tasks")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in detect_ambiguity: {e}")
            return AmbiguityResult(requires_confirmation=False, ambiguous_tasks=[])
    
    async def process_confirmation(
        self, 
        ambiguity_info: AmbiguityInfo,
        user_response: str,
        context: Dict[str, Any]
    ) -> ConfirmationResult:
        """
        確認プロセス処理
        
        Args:
            ambiguity_info: 曖昧性情報
            user_response: ユーザー応答
            context: コンテキスト
        
        Returns:
            確認プロセス結果
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Processing confirmation for task: {ambiguity_info.task_id}")
            
            # ユーザー応答の解析
            parsed_response = await self._parse_user_response(user_response, ambiguity_info)
            
            # タスクの更新
            updated_tasks = await self._update_tasks([ambiguity_info], parsed_response)
            
            result = ConfirmationResult(
                is_cancelled=parsed_response.get("is_cancelled", False),
                updated_tasks=updated_tasks,
                confirmation_context=context
            )
            
            self.logger.info(f"✅ [ConfirmationService] Confirmation processed successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in process_confirmation: {e}")
            return ConfirmationResult(is_cancelled=True, updated_tasks=[], confirmation_context={})
    
    async def maintain_task_chain(
        self, 
        original_tasks: List[Dict[str, Any]],
        confirmation_result: ConfirmationResult
    ) -> List[Dict[str, Any]]:
        """
        タスクチェーン保持
        
        Args:
            original_tasks: 元のタスクリスト
            confirmation_result: 確認プロセス結果
        
        Returns:
            更新されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Maintaining task chain for {len(original_tasks)} tasks")
            
            if confirmation_result.is_cancelled:
                self.logger.info(f"⚠️ [ConfirmationService] Task chain cancelled by user")
                return []
            
            # 確認結果に基づいてタスクを更新
            updated_tasks = confirmation_result.updated_tasks
            
            self.logger.info(f"✅ [ConfirmationService] Task chain maintained successfully: {len(updated_tasks)} tasks")
            
            return updated_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in maintain_task_chain: {e}")
            return original_tasks
    
    async def _check_inventory_ambiguity(
        self, 
        task: Dict[str, Any], 
        user_id: str
    ) -> Optional[AmbiguityInfo]:
        """
        在庫操作の曖昧性チェック
        
        Args:
            task: タスク
            user_id: ユーザーID
        
        Returns:
            曖昧性情報（曖昧でない場合はNone）
        """
        try:
            tool_name = task.get("tool", "")
            parameters = task.get("parameters", {})
            
            # 在庫更新・削除で名前指定の場合の曖昧性チェック
            if tool_name in ["inventory_update_by_name", "inventory_delete_by_name"]:
                item_name = parameters.get("item_name", "")
                if item_name:
                    # TODO: 実際の曖昧性チェックロジックを実装
                    # 現在は基本的な実装
                    return AmbiguityInfo(
                        task_id=task.get("id", ""),
                        tool_name=tool_name,
                        ambiguity_type="multiple_items",
                        details={"item_name": item_name, "message": "同名のアイテムが複数存在します"}
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in _check_inventory_ambiguity: {e}")
            return None
    
    async def _parse_user_response(
        self, 
        user_response: str, 
        ambiguity_info: AmbiguityInfo
    ) -> Dict[str, Any]:
        """
        ユーザー応答の解析
        
        Args:
            user_response: ユーザー応答
            ambiguity_info: 曖昧性情報
        
        Returns:
            解析結果
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Parsing user response")
            
            # TODO: 実際の応答解析ロジックを実装
            # 現在は基本的な実装
            parsed_response = {
                "is_cancelled": "キャンセル" in user_response or "やめる" in user_response,
                "strategy": "by_id" if "ID" in user_response else "by_name",
                "raw_response": user_response
            }
            
            self.logger.info(f"✅ [ConfirmationService] User response parsed successfully")
            
            return parsed_response
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in _parse_user_response: {e}")
            return {"is_cancelled": True, "strategy": "by_id", "raw_response": user_response}
    
    async def _update_tasks(
        self, 
        ambiguous_tasks: List[AmbiguityInfo], 
        parsed_response: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        タスクの更新
        
        Args:
            ambiguous_tasks: 曖昧なタスクリスト
            parsed_response: 解析された応答
        
        Returns:
            更新されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Updating tasks")
            
            # TODO: 実際のタスク更新ロジックを実装
            # 現在は基本的な実装
            updated_tasks = []
            
            for task_info in ambiguous_tasks:
                updated_task = {
                    "id": task_info.task_id,
                    "tool": task_info.tool_name,
                    "parameters": task_info.details,
                    "strategy": parsed_response.get("strategy", "by_id")
                }
                updated_tasks.append(updated_task)
            
            self.logger.info(f"✅ [ConfirmationService] Tasks updated successfully: {len(updated_tasks)} tasks")
            
            return updated_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in _update_tasks: {e}")
            return []
