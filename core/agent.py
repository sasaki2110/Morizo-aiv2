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
        self.task_executor = TaskExecutor()
        self.confirmation_service = ConfirmationService()
        self.response_formatter = ResponseFormatter()
    
    async def process_request(self, user_request: str, user_id: str, token: str, sse_session_id: Optional[str] = None) -> str:
        """
        Process user request through the complete ReAct loop.
        
        Args:
            user_request: User's natural language request
            user_id: User identifier
            token: Authentication token
            sse_session_id: Optional SSE session ID for progress tracking
            
        Returns:
            Final response string
        """
        try:
            self.logger.info(f"🎯 [AGENT] Starting request processing for user {user_id}")
            self.logger.info(f"📝 [AGENT] User request: '{user_request}'")
            if sse_session_id:
                self.logger.info(f"📡 [AGENT] SSE session ID: {sse_session_id}")
            
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
                return await self._handle_confirmation(
                    execution_result, user_id, task_chain_manager
                )
            
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
                return final_response
            else:
                error_msg = f"タスクの実行中にエラーが発生しました: {execution_result.message}"
                self.logger.error(f"❌ [AGENT] Execution failed: {execution_result.message}")
                return error_msg
                
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Request processing failed: {str(e)}")
            return f"リクエストの処理中にエラーが発生しました: {str(e)}"
    
    async def _handle_confirmation(self, execution_result: ExecutionResult, user_id: str, task_chain_manager: TaskChainManager) -> str:
        """Handle confirmation process when ambiguity is detected."""
        try:
            self.logger.info(f"🤝 [AGENT] Starting confirmation handling for user {user_id}")
            
            # Pause execution for confirmation
            task_chain_manager.pause_for_confirmation()
            self.logger.info(f"⏸️ [AGENT] Execution paused for user confirmation")
            
            # Process confirmation with user
            confirmation_result = await self.confirmation_service.process_confirmation(
                execution_result.confirmation_context, user_id
            )
            self.logger.info(f"📝 [AGENT] Confirmation result: {confirmation_result}")
            
            if confirmation_result.get("cancelled", False):
                self.logger.info(f"❌ [AGENT] User cancelled the operation")
                return "操作はキャンセルされました。"
            
            # Update tasks based on user choice
            updated_tasks = self.confirmation_service._update_tasks(
                confirmation_result.get("updated_tasks", []), user_id
            )
            self.logger.info(f"🔄 [AGENT] Updated tasks based on user choice: {len(updated_tasks)} tasks")
            
            # Resume execution with updated tasks
            task_chain_manager.resume_execution()
            task_chain_manager.set_tasks(updated_tasks)
            self.logger.info(f"▶️ [AGENT] Execution resumed with updated tasks")
            
            # Execute updated tasks
            final_execution_result = await self.task_executor.execute(
                updated_tasks, user_id, task_chain_manager
            )
            self.logger.info(f"✅ [AGENT] Updated task execution completed: status={final_execution_result.status}")
            
            if final_execution_result.status == "success":
                final_response, menu_data = await self.response_formatter.format(final_execution_result.outputs)
                self.logger.info(f"🔍 [TrueReactAgent] Confirmation Menu data received: {menu_data is not None}")
                if menu_data:
                    self.logger.info(f"📊 [TrueReactAgent] Confirmation Menu data size: {len(str(menu_data))} characters")
                task_chain_manager.send_complete(final_response, menu_data)
                self.logger.info(f"🎉 [AGENT] Confirmation handling completed successfully")
                return final_response
            else:
                error_msg = f"確認後のタスク実行中にエラーが発生しました: {final_execution_result.message}"
                self.logger.error(f"❌ [AGENT] Post-confirmation execution failed: {final_execution_result.message}")
                return error_msg
                
        except Exception as e:
            self.logger.error(f"❌ [AGENT] Confirmation handling failed: {str(e)}")
            return f"確認処理中にエラーが発生しました: {str(e)}"
