"""
TrueReactAgent: Main orchestrator for the core layer.

This component coordinates the entire ReAct loop, orchestrating:
- Task planning (via ActionPlanner)
- Task execution (via TaskExecutor)
- Confirmation handling (via ConfirmationHandler)
- User selection processing (via SelectionHandler)
- Stage management (via StageManager)
- Response formatting (via ResponseFormatter)
"""

from typing import Optional, Dict, Any
from .models import TaskChainManager, ExecutionResult
from .planner import ActionPlanner
from .executor import TaskExecutor
from .service_coordinator import ServiceCoordinator
from .response_formatter import ResponseFormatter
from .handlers.confirmation_handler import ConfirmationHandler
from .handlers.selection_handler import SelectionHandler
from .handlers.stage_manager import StageManager
from services.confirmation_service import ConfirmationService
from config.loggers import GenericLogger


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
        from services.session_service import SessionService
        self.session_service = SessionService()
        
        # Handler initialization
        # Note: Callbacks are set later to avoid circular references
        self.confirmation_handler = ConfirmationHandler(
            session_service=self.session_service,
            confirmation_service=self.confirmation_service,
            task_executor=self.task_executor,
            response_formatter=self.response_formatter,
            process_request_callback=None
        )
        self.stage_manager = StageManager(session_service=self.session_service)
        self.selection_handler = SelectionHandler(
            session_service=self.session_service,
            process_request_callback=None,
            stage_manager=self.stage_manager
        )
    
    def _set_confirmation_handler_callback(self):
        """Set ConfirmationHandler callback (called after initialization to avoid circular references)"""
        self.confirmation_handler.process_request_callback = self.process_request
    
    def _set_selection_handler_callbacks(self):
        """Set SelectionHandler callback (called after initialization to avoid circular references)"""
        self.selection_handler.process_request_callback = self.process_request
    
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
        # Set callbacks on first invocation (to avoid circular references)
        if self.confirmation_handler.process_request_callback is None:
            self._set_confirmation_handler_callback()
        if self.selection_handler.process_request_callback is None:
            self._set_selection_handler_callbacks()
        
        try:
            self.logger.info(f"🎯 [AGENT] Starting request processing for user {user_id}")
            self.logger.info(f"📝 [AGENT] User request: '{user_request}'")
            self.logger.info(f"🔄 [AGENT] Is confirmation response: {is_confirmation_response}")
            
            # Handle confirmation response if needed
            if is_confirmation_response and sse_session_id:
                saved_state = await self.session_service.get_confirmation_state(sse_session_id)
                if saved_state:
                    self.logger.info(f"🔄 [AGENT] Resuming from confirmation")
                    return await self.confirmation_handler.resume_from_confirmation(
                        saved_state, user_request, user_id, token, sse_session_id
                    )
                else:
                    self.logger.warning(f"⚠️ [AGENT] Confirmation response but no saved state found for session: {sse_session_id}")
            
            # Initialize task chain manager
            task_chain_manager = TaskChainManager(sse_session_id)
            self.logger.info(f"🔗 [AGENT] TaskChainManager initialized")
            
            # Step 1: Planning - Generate task list
            self.logger.info(f"📋 [AGENT] Starting planning phase...")
            tasks = await self.action_planner.plan(user_request, user_id, sse_session_id)
            
            # Inject session context for additional proposals
            if sse_session_id and any(t.parameters.get("inventory_items", "").startswith("session.context.") for t in tasks):
                self.logger.info(f"🔄 [AGENT] Detected session context references, injecting values")
                for task in tasks:
                    for key, value in task.parameters.items():
                        if isinstance(value, str) and value.startswith("session.context."):
                            context_key = value.replace("session.context.", "")
                            context_value = await self.session_service.get_session_context(
                                sse_session_id, context_key, None
                            )
                            task.parameters[key] = context_value
                            self.logger.info(f"💾 [AGENT] Injected session context: {context_key} = {context_value}")
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
                confirmation_result = await self.confirmation_handler.handle_confirmation(
                    execution_result, user_id, task_chain_manager, token, user_request
                )
                
                if confirmation_result.get("requires_confirmation"):
                    task_chain_manager.send_complete(
                        confirmation_result["response"],
                        confirmation_data={
                            "requires_confirmation": True,
                            "confirmation_session_id": confirmation_result["confirmation_session_id"]
                        }
                    )
                    return confirmation_result
                else:
                    return confirmation_result["response"]
            
            # Step 4: Format final response
            if execution_result.status == "success":
                self.logger.info(f"📄 [AGENT] Starting response formatting...")
                final_response, menu_data = await self.response_formatter.format(execution_result.outputs, sse_session_id)
                self.logger.info(f"🔍 [AGENT] Menu data received: {menu_data is not None}")
                if menu_data:
                    self.logger.info(f"📊 [AGENT] Menu data size: {len(str(menu_data))} characters")
                task_chain_manager.send_complete(final_response, menu_data)
                self.logger.info(f"✅ [AGENT] Response formatting completed")
                self.logger.info(f"🎉 [AGENT] Request processing completed successfully")
                
                # Return selection UI data if needed
                if menu_data and isinstance(menu_data, dict) and menu_data.get("requires_selection"):
                    return {
                        "response": final_response,
                        "requires_selection": menu_data.get("requires_selection", False),
                        "candidates": menu_data.get("candidates"),
                        "task_id": menu_data.get("task_id"),
                        "message": menu_data.get("message", "選択してください"),
                        "current_stage": menu_data.get("current_stage"),
                        "used_ingredients": menu_data.get("used_ingredients"),
                        "menu_category": menu_data.get("menu_category")
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
    
    async def handle_user_selection_required(self, candidates: list, context: dict, task_chain_manager: TaskChainManager) -> dict:
        """Handle user selection required (delegates to SelectionHandler)"""
        return await self.selection_handler.handle_user_selection_required(candidates, context, task_chain_manager)
    
    async def process_user_selection(self, task_id: str, selection: int, sse_session_id: str, user_id: str, token: str, old_sse_session_id: str = None) -> dict:
        """Process user selection (delegates to SelectionHandler)"""
        # Set callback on first invocation (to avoid circular references)
        if self.selection_handler.process_request_callback is None:
            self._set_selection_handler_callbacks()
        return await self.selection_handler.process_user_selection(task_id, selection, sse_session_id, user_id, token, old_sse_session_id)
    