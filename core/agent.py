"""
TrueReactAgent: Main orchestrator for the core layer.

This component coordinates the entire ReAct loop, managing task planning,
execution, and response generation.
"""

import logging
from typing import Optional, Dict, Any
from .models import TaskChainManager, ExecutionResult
from .planner import ActionPlanner
from .executor import TaskExecutor
from .service_coordinator import ServiceCoordinator
from .exceptions import CoreError
from services.confirmation_service import ConfirmationService
from services.llm_service import LLMService
from config.loggers import GenericLogger


class ResponseFormatter:
    """Formats final responses using LLM."""
    
    def __init__(self):
        self.logger = GenericLogger("core", "response_formatter")
        self.llm_service = LLMService()
    
    async def format(self, execution_results: dict) -> tuple[str, Optional[Dict[str, Any]]]:
        """Format execution results into natural language response."""
        try:
            # Use LLM service to format the response
            response, menu_data = await self.llm_service.format_response(execution_results)
            self.logger.info(f"🔍 [ResponseFormatter] Menu data received: {menu_data is not None}")
            if menu_data:
                self.logger.info(f"📊 [ResponseFormatter] Menu data size: {len(str(menu_data))} characters")
            return response, menu_data
        except Exception as e:
            logger = GenericLogger("core", "response_formatter")
            logger.error(f"Response formatting failed: {str(e)}")
            return f"タスクが完了しましたが、レスポンスの生成に失敗しました: {str(e)}", None


class TrueReactAgent:
    """
    Main orchestrator for the unified ReAct agent.
    
    This component coordinates the entire process from user request
    to final response, managing task planning, execution, and confirmation.
    """
    
    def __init__(self):
        self.logger = GenericLogger("core", "agent")
        self.action_planner = ActionPlanner()
        self.service_coordinator = ServiceCoordinator()
        self.confirmation_service = ConfirmationService(self.service_coordinator.tool_router)
        self.task_executor = TaskExecutor(self.service_coordinator, self.confirmation_service)
        self.response_formatter = ResponseFormatter()
        # SessionServiceのインポートと初期化を追加
        from services.session_service import SessionService
        self.session_service = SessionService()
    
    async def process_request(self, user_request: str, user_id: str, token: str, sse_session_id: Optional[str] = None, is_confirmation_response: bool = False) -> Dict[str, Any]:
        """
        Process user request through the complete ReAct loop.
        
        Args:
            user_request: User's natural language request
            user_id: User identifier
            token: Authentication token
            sse_session_id: Optional SSE session ID for progress tracking
            is_confirmation_response: Whether this is a response to confirmation request
            
        Returns:
            Final response string
        """
        try:
            self.logger.info(f"🎯 [AGENT] Starting request processing for user {user_id}")
            self.logger.info(f"📝 [AGENT] User request: '{user_request}'")
            self.logger.info(f"🔄 [AGENT] Is confirmation response: {is_confirmation_response}")
            
            # 曖昧性解決の回答かチェック
            if is_confirmation_response and sse_session_id:
                saved_state = await self.session_service.get_confirmation_state(sse_session_id)
                if saved_state:
                    self.logger.info(f"🔄 [AGENT] Resuming from confirmation")
                    # ActionPlannerをスキップして、保存された状態から再開
                    return await self._resume_from_confirmation(
                        saved_state, user_request, user_id, token, sse_session_id
                    )
                else:
                    self.logger.warning(f"⚠️ [AGENT] Confirmation response but no saved state found for session: {sse_session_id}")
            
            # 新しいリクエストの場合の通常処理
            
            # Initialize task chain manager
            task_chain_manager = TaskChainManager(sse_session_id)
            self.logger.info(f"🔗 [AGENT] TaskChainManager initialized")
            
            # Step 1: Planning - Generate task list
            self.logger.info(f"📋 [AGENT] Starting planning phase...")
            tasks = await self.action_planner.plan(user_request, user_id)
            task_chain_manager.set_tasks(tasks)
            self.logger.info(f"✅ [AGENT] Planning phase completed: {len(tasks)} tasks generated")
            
            # Step 2: Execution - Execute tasks
            self.logger.info(f"⚙️ [AGENT] Starting execution phase...")
            execution_result = await self.task_executor.execute(
                tasks, user_id, task_chain_manager, token
            )
            self.logger.info(f"✅ [AGENT] Execution phase completed: status={execution_result.status}")
            
            # Step 3: Handle confirmation if needed
            if execution_result.status == "needs_confirmation":
                self.logger.info(f"⚠️ [AGENT] Confirmation required, handling user interaction...")
                confirmation_result = await self._handle_confirmation(
                    execution_result, user_id, task_chain_manager, token, user_request
                )
                
                # 確認が必要な場合は辞書を返す
                if confirmation_result.get("requires_confirmation"):
                    # SSE経由で確認情報を送信
                    task_chain_manager.send_complete(
                        confirmation_result["response"],
                        confirmation_data={
                            "requires_confirmation": True,
                            "confirmation_session_id": confirmation_result["confirmation_session_id"]
                        }
                    )
                    return confirmation_result
                else:
                    # 確認応答が処理された後の通常レスポンス
                    return confirmation_result["response"]
            
            # Step 4: Format final response
            if execution_result.status == "success":
                self.logger.info(f"📄 [AGENT] Starting response formatting...")
                final_response, menu_data = await self.response_formatter.format(execution_result.outputs)
                self.logger.info(f"🔍 [TrueReactAgent] Menu data received: {menu_data is not None}")
                if menu_data:
                    self.logger.info(f"📊 [TrueReactAgent] Menu data size: {len(str(menu_data))} characters")
                task_chain_manager.send_complete(final_response, menu_data)
                self.logger.info(f"✅ [AGENT] Response formatting completed")
                self.logger.info(f"🎉 [AGENT] Request processing completed successfully")
                
                # 選択UI用のデータがある場合は辞書形式で返す
                if menu_data and isinstance(menu_data, dict) and menu_data.get("requires_selection"):
                    return {
                        "response": final_response,
                        "requires_selection": menu_data.get("requires_selection", False),
                        "candidates": menu_data.get("candidates"),
                        "task_id": menu_data.get("task_id"),
                        "message": menu_data.get("message", "選択してください")
                    }
                else:
                    return {"response": final_response}
            else:
                error_msg = f"タスクの実行中にエラーが発生しました: {execution_result.message}"
                self.logger.error(f"❌ [AGENT] Execution failed: {execution_result.message}")
                return {"response": error_msg}
                
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Request processing failed: {str(e)}")
            return {"response": f"リクエストの処理中にエラーが発生しました: {str(e)}"}
    
    async def _handle_confirmation(self, execution_result: ExecutionResult, user_id: str, task_chain_manager: TaskChainManager, token: str, user_request: str) -> dict:
        """Handle confirmation process when ambiguity is detected."""
        try:
            self.logger.info(f"🤝 [AGENT] Starting confirmation handling for user {user_id}")
            
            # Pause execution for confirmation
            task_chain_manager.pause_for_confirmation()
            self.logger.info(f"⏸️ [AGENT] Execution paused for user confirmation")
            
            # Process confirmation with user
            confirmation_context = execution_result.confirmation_context
            if not confirmation_context:
                self.logger.error(f"❌ [AGENT] Confirmation context is missing")
                return {
                    "response": "確認情報が不足しています。",
                    "requires_confirmation": False
                }
            
            # 元のタスク情報を保持
            ambiguity_info = confirmation_context.get("ambiguity_info")
            original_tasks = confirmation_context.get("original_tasks", [])
            
            # Phase 1E: セッションに確認コンテキストを保存
            if task_chain_manager.sse_session_id:
                session = await self.session_service.get_session(task_chain_manager.sse_session_id, user_id)
                if not session:
                    # セッションが存在しない場合は作成
                    session = await self.session_service.create_session(user_id)
                    # 新しく作成したセッションをtask_chain_managerのセッションIDで保存
                    if user_id not in self.session_service.user_sessions:
                        self.session_service.user_sessions[user_id] = {}
                    self.session_service.user_sessions[user_id][task_chain_manager.sse_session_id] = session
                    # セッションIDを更新
                    session.id = task_chain_manager.sse_session_id
                
                confirmation_message = execution_result.message if hasattr(execution_result, 'message') else ""
                session.set_ambiguity_confirmation(
                    original_request=user_request,  # 元のユーザーリクエスト
                    question=confirmation_message,  # 確認質問
                    ambiguity_details=ambiguity_info.details if hasattr(ambiguity_info, 'details') else {}
                )
                self.logger.info(f"💾 [AGENT] Confirmation context saved to session")
            
            # 状態を保存
            from datetime import datetime
            state_data = {
                'task_chain_manager': task_chain_manager,
                'execution_result': execution_result,
                'original_tasks': original_tasks,
                'ambiguity_info': ambiguity_info,
                'created_at': datetime.now(),
                'user_id': user_id,
                'token': token
            }
            
            await self.session_service.save_confirmation_state(
                task_chain_manager.sse_session_id,
                user_id,
                state_data
            )
            self.logger.info(f"💾 [AGENT] Confirmation state saved for session: {task_chain_manager.sse_session_id}")
            
            # ユーザーに確認メッセージを返す（次のリクエストで再開）
            # 曖昧性のタイプに応じて適切なメソッドを呼び出す
            if hasattr(ambiguity_info, 'details') and ambiguity_info.details.get("type") == "main_ingredient_optional_selection":
                confirmation_message = self._create_menu_confirmation_message(ambiguity_info)
            else:
                confirmation_message = self._create_confirmation_message(ambiguity_info)
            
            # デバッグログ: ambiguity_infoの詳細を出力
            self.logger.info(f"🔍 [AGENT] Ambiguity info details: {ambiguity_info.details if hasattr(ambiguity_info, 'details') else 'No details'}")
            self.logger.info(f"📝 [AGENT] Confirmation message: {confirmation_message}")
            
            result_dict = {
                "response": confirmation_message,
                "requires_confirmation": True,
                "confirmation_session_id": task_chain_manager.sse_session_id
            }
            
            # デバッグログ: 戻り値の辞書を出力
            self.logger.info(f"📤 [AGENT] Returning confirmation result: {result_dict}")
            
            return result_dict
                
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Confirmation handling failed: {str(e)}")
            return {
                "response": f"確認処理中にエラーが発生しました: {str(e)}",
                "requires_confirmation": False
            }
    
    async def _resume_from_confirmation(
        self,
        saved_state: Dict[str, Any],
        user_response: str,
        user_id: str,
        token: str,
        sse_session_id: str
    ) -> str:
        """
        保存された状態から曖昧性解決を再開
        
        Args:
            saved_state: 保存された状態
            user_response: ユーザーの回答（例：「最新のでお願い」）
            user_id: ユーザーID
            token: 認証トークン
            sse_session_id: SSEセッションID
        """
        try:
            self.logger.info(f"🔄 [AGENT] Resuming from confirmation for session: {sse_session_id}")
            
            # 保存された状態を復元
            task_chain_manager = saved_state['task_chain_manager']
            original_tasks = saved_state['original_tasks']
            ambiguity_info = saved_state['ambiguity_info']
            
            # Phase 1E: 曖昧性解消の場合は、コンテキスト統合を行う
            if hasattr(ambiguity_info, 'details') and ambiguity_info.details.get("type") == "main_ingredient_optional_selection":
                # 元のユーザーリクエストを取得（セッションから）
                session = await self.session_service.get_session(sse_session_id, user_id)
                if session and session.confirmation_context.get("original_request"):
                    original_request = session.confirmation_context.get("original_request")
                    
                    # コンテキスト統合
                    integrated_request = await self._integrate_confirmation_response(
                        original_request,
                        user_response,
                        ambiguity_info.details
                    )
                    
                    # 確認コンテキストをクリア
                    session.clear_confirmation_context()
                    
                    # 統合されたリクエストで通常のプランニングループを実行
                    self.logger.info(f"▶️ [AGENT] Resuming planning loop with integrated request: {integrated_request}")
                    result = await self.process_request(integrated_request, user_id, token, sse_session_id, False)
                    return result
            
            # 既存の処理（在庫操作確認等）
            confirmation_context = {
                'ambiguity_info': ambiguity_info,
                'user_response': user_response,
                'original_tasks': original_tasks
            }
            
            confirmation_result = await self.confirmation_service.process_confirmation(
                ambiguity_info, user_response, confirmation_context, original_tasks
            )
            
            if confirmation_result.is_cancelled:
                await self.session_service.clear_confirmation_state(sse_session_id)
                return "操作はキャンセルされました。"
            
            # タスクを更新
            updated_tasks = await self.confirmation_service.maintain_task_chain(
                original_tasks, confirmation_result
            )
            
            # 実行再開
            task_chain_manager.resume_execution()
            task_chain_manager.set_tasks(updated_tasks)
            
            # ★ここでTaskExecutor再実行（ActionPlannerはスキップ）
            final_execution_result = await self.task_executor.execute(
                updated_tasks, user_id, task_chain_manager, token
            )
            
            # 状態をクリア
            await self.session_service.clear_confirmation_state(sse_session_id)
            
            # 最終レスポンス生成
            if final_execution_result.status == "success":
                final_response, menu_data = await self.response_formatter.format(final_execution_result.outputs)
                task_chain_manager.send_complete(final_response, menu_data)
                return final_response
            else:
                return f"確認後のタスク実行中にエラーが発生しました: {final_execution_result.message}"
        
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Resume from confirmation failed: {e}")
            await self.session_service.clear_confirmation_state(sse_session_id)
            return f"確認処理の再開中にエラーが発生しました: {str(e)}"
    
    def _create_confirmation_message(self, ambiguity_info) -> str:
        """
        曖昧性情報から確認メッセージを生成
        
        Args:
            ambiguity_info: 曖昧性情報
            
        Returns:
            確認メッセージ
        """
        try:
            if not ambiguity_info:
                return "複数の選択肢があります。どちらを選択しますか？"
            
            # 曖昧性の詳細を取得
            details = ambiguity_info.details if hasattr(ambiguity_info, 'details') else {}
            tool_name = ambiguity_info.tool_name if hasattr(ambiguity_info, 'tool_name') else "操作"
            
            # 在庫操作の場合の確認メッセージ
            if tool_name.startswith("inventory_"):
                if 'items' in details:
                    items = details['items']
                    if len(items) > 1:
                        item_name = items[0].get('item_name', 'アイテム')
                        operation = "削除" if "delete" in tool_name else "更新"
                        
                        message = f"「{item_name}」が{len(items)}件見つかりました。\n\n"
                        for i, item in enumerate(items, 1):
                            message += f"アイテム{i}:\n"
                            if 'quantity' in item:
                                message += f"  数量: {item['quantity']} {item.get('unit', '')}\n"
                            if 'storage_location' in item and item['storage_location']:
                                message += f"  保存場所: {item['storage_location']}\n"
                            if 'expiry_date' in item and item['expiry_date']:
                                message += f"  期限: {item['expiry_date']}\n"
                            if 'created_at' in item:
                                message += f"  追加日: {item['created_at']}\n"
                            message += "\n"
                        
                        message += "以下のいずれかを選択してください：\n"
                        message += "- 「最新の」または「新しい」: 最も最近追加されたもの\n"
                        message += "- 「古い」または「古いの」: 最も古いもの\n"
                        message += "- 「全部」または「すべて」: 全てのアイテム\n"
                        message += "- 「キャンセル」: 操作を中止"
                        return message
                
                # itemsがない場合のフォールバック
                return f"複数のアイテムが見つかりました。どれを{tool_name.replace('inventory_', '').replace('_', ' ')}しますか？"
            
            # デフォルトメッセージ
            return "複数の選択肢があります。どちらを選択しますか？"
            
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Error creating confirmation message: {e}")
            return "複数の選択肢があります。どちらを選択しますか？"
    
    def _create_menu_confirmation_message(self, ambiguity_info) -> str:
        """
        献立提案の曖昧性情報から確認メッセージを生成
        
        Args:
            ambiguity_info: 曖昧性情報
            
        Returns:
            確認メッセージ
        """
        details = ambiguity_info.details if hasattr(ambiguity_info, 'details') else {}
        return details.get("message", "複数の選択肢があります。どちらを選択しますか？")
    
    async def handle_user_selection_required(self, candidates: list, context: dict, task_chain_manager: TaskChainManager) -> dict:
        """ユーザー選択が必要な場合の処理"""
        try:
            # タスクIDを取得
            task_id = context.get('current_task_id')
            if not task_id:
                raise ValueError("No task ID found in context")
            
            # タスクを一時停止
            pause_result = task_chain_manager.pause_task_for_user_selection(task_id, context)
            
            if not pause_result["success"]:
                raise Exception(f"Failed to pause task: {pause_result['error']}")
            
            self.logger.info(f"⏸️ [AGENT] Task {task_id} paused for user selection")
            
            # フロントエンドに選択要求を送信
            response = {
                "success": True,
                "requires_selection": True,
                "candidates": candidates,
                "task_id": task_id,
                "message": "以下の5件から選択してください:"
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Failed to handle user selection required: {e}")
            return {
                "success": False,
                "error": str(e),
                "requires_selection": False
            }
    
    async def process_user_selection(self, task_id: str, selection: int, sse_session_id: str, user_id: str, token: str) -> dict:
        """ユーザー選択結果の処理"""
        try:
            self.logger.info(f"📥 [AGENT] Processing user selection: task_id={task_id}, selection={selection}")
            
            # タスクチェーンマネージャーを初期化（SSEセッションIDから復元）
            task_chain_manager = TaskChainManager(sse_session_id)
            
            # タスクを再開
            task_chain_manager.resume_execution()
            
            self.logger.info(f"▶️ [AGENT] Task {task_id} resumed successfully")
            
            # 選択されたレシピをもとに後続処理を実行
            # （Phase 2Bで副菜・汁物の選択に進む処理を追加予定）
            
            return {
                "success": True,
                "task_id": task_id,
                "selection": selection,
                "message": f"選択肢 {selection} を受け付けました。"
            }
            
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Failed to process user selection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _integrate_confirmation_response(
        self, 
        original_request: str,  # 「主菜を教えて」
        user_response: str,     # 「レンコンでお願い」
        confirmation_context: Dict[str, Any]  # 確認時のコンテキスト
    ) -> str:
        """
        元のリクエストとユーザー回答を統合して、
        完全なリクエストを生成する
        
        例:
        - 元: 「主菜を教えて」
        - 回答: 「レンコンでお願い」
        - 結果: 「レンコンの主菜を教えて」
        """
        
        self.logger.info(f"🔗 [AGENT] Integrating request")
        self.logger.info(f"  Original: {original_request}")
        self.logger.info(f"  Response: {user_response}")
        
        # パターン1: 「指定しない」系の回答
        proceed_keywords = ["いいえ", "そのまま", "提案して", "在庫から", "このまま", "進めて", "指定しない", "2"]
        if any(keyword in user_response for keyword in proceed_keywords):
            # 元のリクエストをそのまま使用
            integrated_request = original_request
            self.logger.info(f"✅ [AGENT] Integrated (proceed): {integrated_request}")
            return integrated_request
        
        # パターン2: 食材名が含まれている
        # 簡易的な統合（LLMを使わない方式）
        # 「レンコン」「レンコンで」「レンコンを使って」等を抽出
        ingredient = self._extract_ingredient_simple(user_response)
        
        if ingredient:
            # 元のリクエストに食材を追加
            # 「主菜を教えて」→「レンコンの主菜を教えて」
            if "主菜" in original_request or "メイン" in original_request:
                integrated_request = f"{ingredient}の主菜を教えて"
            elif "料理" in original_request:
                integrated_request = f"{ingredient}の料理を教えて"
            else:
                integrated_request = f"{ingredient}を使って{original_request}"
            
            self.logger.info(f"✅ [AGENT] Integrated (ingredient): {integrated_request}")
            return integrated_request
        
        # パターン3: 統合できない場合は元のリクエストを返す
        self.logger.warning(f"⚠️ [AGENT] Could not integrate, using original request")
        return original_request
    
    def _extract_ingredient_simple(self, user_response: str) -> Optional[str]:
        """ユーザー応答から食材名を簡易抽出"""
        
        # 助詞を除去
        cleaned = user_response.replace("で", "").replace("を", "").replace("が", "")
        cleaned = cleaned.replace("使って", "").replace("お願い", "").replace("ください", "")
        cleaned = cleaned.strip()
        
        # 空でなければ食材名として扱う
        if cleaned and len(cleaned) > 0:
            return cleaned
        
        return None