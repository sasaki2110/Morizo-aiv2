#!/usr/bin/env python3
"""
ConfirmationService - 確認プロセスサービス

曖昧性検出と確認プロセスのビジネスロジックを提供
タスクチェーン保持機能を実装
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from config.loggers import GenericLogger
from .tool_name_converter import ToolNameConverter
from .confirmation.models import AmbiguityInfo, AmbiguityResult, ConfirmationResult
from .confirmation.response_parser import UserResponseParser

if TYPE_CHECKING:
    from core.models import Task


class ConfirmationService:
    """確認プロセスサービス"""
    
    def __init__(self, tool_router=None):
        """初期化"""
        self.tool_router = tool_router
        self.logger = GenericLogger("service", "confirmation")
        self.response_parser = UserResponseParser()
    
    async def detect_ambiguity(
        self, 
        tasks: List[Any], 
        user_id: str,
        token: str = ""
    ) -> AmbiguityResult:
        """
        曖昧性検出
        
        Args:
            tasks: タスクリスト（Taskオブジェクト）
            user_id: ユーザーID
        
        Returns:
            曖昧性検出結果
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Detecting ambiguity for user: {user_id}")
            
            ambiguous_tasks = []
            
            # 各タスクの曖昧性チェック
            for task in tasks:
                # Taskオブジェクトの場合のみ処理
                if hasattr(task, 'service') and hasattr(task, 'method'):
                    tool_name = f"{task.service}_{task.method}"
                    
                    if tool_name.startswith("inventory_"):
                        # 在庫操作の曖昧性チェック
                        ambiguity_info = await self._check_inventory_ambiguity(task, user_id, token)
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
        context: Dict[str, Any],
        original_tasks: List['Task'] = None
    ) -> ConfirmationResult:
        """
        確認プロセス処理
        
        Args:
            ambiguity_info: 曖昧性情報
            user_response: ユーザー応答
            context: コンテキスト
            original_tasks: 元のタスクリスト
        
        Returns:
            確認プロセス結果
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Processing confirmation for task: {ambiguity_info.task_id}")
            
            # ユーザー応答の解析
            parsed_response = self.response_parser.parse_response(user_response)
            
            # タスクの更新 - 元のタスク情報を渡す
            updated_tasks = await self._update_tasks([ambiguity_info], parsed_response, original_tasks)
            
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
        original_tasks: List[Any],
        confirmation_result: ConfirmationResult
    ) -> List['Task']:
        """
        タスクチェーン維持（文脈補完実装）
        
        Args:
            original_tasks: 元のタスクリスト
            confirmation_result: 確認プロセス結果
        
        Returns:
            更新されたタスクリスト（Taskオブジェクトのリスト）
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Maintaining task chain for {len(original_tasks)} tasks")
            
            if confirmation_result.is_cancelled:
                self.logger.info(f"⚠️ [ConfirmationService] Task chain cancelled by user")
                return []
            
            # 文脈補完：元のタスク情報とユーザーの回答を統合
            updated_tasks = []
            
            # 循環インポートを避けるため、関数内でインポート
            from core.models import Task
            
            # 確認結果から更新されたタスクを取得
            confirmation_tasks = confirmation_result.updated_tasks
            
            for i, confirmation_task in enumerate(confirmation_tasks):
                # 元のタスク情報を取得
                original_task = None
                if i < len(original_tasks):
                    original_task = original_tasks[i]
                
                # 文脈補完：元のタスクのパラメータを保持しつつ、戦略を更新
                if original_task:
                    # 元のパラメータをコピー
                    updated_parameters = original_task.parameters.copy()
                    
                    # 確認結果の戦略を適用
                    if hasattr(confirmation_task, 'parameters') and confirmation_task.parameters:
                        strategy = confirmation_task.parameters.get('strategy')
                        if strategy:
                            updated_parameters['strategy'] = strategy
                    
                    # 文脈補完されたタスクを作成
                    updated_task = Task(
                        id=confirmation_task.id,
                        service=confirmation_task.service,
                        method=confirmation_task.method,
                        parameters=updated_parameters,
                        dependencies=confirmation_task.dependencies
                    )
                else:
                    # 元のタスクがない場合は確認結果をそのまま使用
                    updated_task = confirmation_task
                
                updated_tasks.append(updated_task)
            
            self.logger.info(f"✅ [ConfirmationService] Task chain maintained successfully: {len(updated_tasks)} tasks")
            
            return updated_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in maintain_task_chain: {e}")
            return original_tasks
    
    async def _check_inventory_ambiguity(
        self, 
        task: Any, 
        user_id: str,
        token: str = ""
    ) -> Optional[AmbiguityInfo]:
        """
        在庫操作の曖昧性チェック（MCPツール経由）
        
        Args:
            task: タスク（Taskオブジェクト）
            user_id: ユーザーID
        
        Returns:
            曖昧性情報（曖昧でない場合はNone）
        """
        try:
            # Taskオブジェクトの場合のみ処理
            if hasattr(task, 'service') and hasattr(task, 'method'):
                tool_name = f"{task.service}_{task.method}"
                parameters = task.parameters.copy()  # コピーを作成
                
                # 【重要】user_idパラメータを確実に含める
                if "user_id" not in parameters:
                    parameters["user_id"] = user_id
                task_id = task.id
                
                # 在庫更新・削除で名前指定の場合の曖昧性チェック
                if task.service == "inventory_service" and task.method in ["update_inventory", "delete_inventory"]:
                    item_name = parameters.get("item_identifier", "")
                    strategy = parameters.get("strategy", "")
                    
                    # by_name戦略（曖昧性あり）の場合のみ曖昧性チェック
                    if item_name and strategy == "by_name" and self.tool_router:
                        # MCPツール経由でデータを取得
                        result = await self.tool_router.route_tool(
                            "inventory_list_by_name",
                            {"item_name": item_name, "user_id": user_id},
                            token
                        )
                        
                        # Service層で曖昧性を判定
                        self.logger.info(f"🔍 [ConfirmationService] Checking ambiguity for {item_name}: result={result}")
                        if result.get("success") and len(result.get("result", {}).get("data", [])) > 1:
                            items = result.get("result", {}).get("data", [])
                            self.logger.info(f"⚠️ [ConfirmationService] Ambiguity detected: {len(items)} items found")
                            return AmbiguityInfo(
                                task_id=task_id,
                                tool_name=tool_name,
                                ambiguity_type="multiple_items",
                                details={
                                    "item_name": item_name,
                                    "items": items,
                                    "count": len(items),
                                    "message": self._generate_confirmation_message(item_name, items)
                                },
                                original_parameters=parameters  # user_idを含むパラメータ
                            )
                        else:
                            self.logger.info(f"✅ [ConfirmationService] No ambiguity: success={result.get('success')}, data_count={len(result.get('result', {}).get('data', []))}")
                    elif item_name and strategy not in ["by_name"]:
                        # 明確な戦略の場合は曖昧性チェックをスキップ
                        self.logger.info(f"✅ [ConfirmationService] Skipping ambiguity check for strategy: {strategy}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in _check_inventory_ambiguity: {e}")
            return None
    
    def _generate_confirmation_message(self, item_name: str, items: List[Dict[str, Any]]) -> str:
        """確認メッセージを生成"""
        message = f"「{item_name}」が{len(items)}件見つかりました。\n\n"
        
        for i, item in enumerate(items, 1):
            message += f"アイテム{i}:\n"
            message += f"  数量: {item['quantity']} {item['unit']}\n"
            message += f"  保存場所: {item['storage_location']}\n"
            if item.get('expiry_date'):
                message += f"  期限: {item['expiry_date']}\n"
            message += f"  追加日: {item['created_at']}\n\n"
        
        message += "以下のいずれかを選択してください：\n"
        message += "- 「最新の」または「新しい」: 最も最近追加されたもの\n"
        message += "- 「古い」または「古いの」: 最も古いもの\n"
        message += "- 「全部」または「すべて」: 全てのアイテム\n"
        message += "- 「キャンセル」: 操作を中止"
        
        return message
    
    async def _update_tasks(
        self, 
        ambiguous_tasks: List[AmbiguityInfo], 
        parsed_response: Dict[str, Any],
        original_tasks: List['Task'] = None
    ) -> List['Task']:
        """
        タスクの更新
        
        Args:
            ambiguous_tasks: 曖昧なタスクリスト
            parsed_response: 解析された応答
            original_tasks: 元のタスクリスト
        
        Returns:
            更新されたタスクリスト（Taskオブジェクトのリスト）
        """
        try:
            self.logger.info(f"🔧 [ConfirmationService] Updating tasks")
            
            # 循環インポートを避けるため、関数内でインポート
            from core.models import Task
            
            updated_tasks = []
            strategy = parsed_response.get("strategy", "by_id")
            
            for task_info in ambiguous_tasks:
                # 戦略に応じてツール名を変更
                original_tool = task_info.tool_name
                if strategy == "by_name_latest":
                    new_tool = original_tool.replace("_by_name", "_by_name_latest")
                elif strategy == "by_name_oldest":
                    new_tool = original_tool.replace("_by_name", "_by_name_oldest")
                elif strategy == "by_name_all":
                    new_tool = original_tool.replace("_by_name", "_by_name_all")
                elif strategy == "by_id":
                    new_tool = original_tool.replace("_by_name", "_by_id")
                else:
                    new_tool = original_tool
                
                # 元のタスクからパラメータを取得
                original_task = None
                if original_tasks:
                    for task in original_tasks:
                        if task.id == task_info.task_id:
                            original_task = task
                            break
                
                # 戦略を反映したパラメータを作成
                if original_task:
                    updated_parameters = original_task.parameters.copy()
                    updated_parameters["strategy"] = strategy
                else:
                    updated_parameters = task_info.original_parameters.copy()
                    updated_parameters["strategy"] = strategy
                
                # Taskオブジェクトを作成
                updated_task = Task(
                    id=task_info.task_id,
                    service=ToolNameConverter.get_service_from_tool(new_tool),
                    method=ToolNameConverter.get_method_from_tool(new_tool),
                    parameters=updated_parameters,
                    dependencies=[]
                )
                updated_tasks.append(updated_task)
            
            self.logger.info(f"✅ [ConfirmationService] Tasks updated successfully: {len(updated_tasks)} tasks")
            
            return updated_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [ConfirmationService] Error in _update_tasks: {e}")
            return []
