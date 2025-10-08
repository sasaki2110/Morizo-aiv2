"""
Data models for the core layer.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a single task to be executed."""
    
    id: str
    service: str  # "RecipeService", "InventoryService", etc.
    method: str    # "generate_menu_plan", "add_inventory", etc.
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None


@dataclass
class ExecutionResult:
    """Result of task execution."""
    
    status: str  # "success", "needs_confirmation", "error"
    outputs: Dict[str, Any] = field(default_factory=dict)
    confirmation_context: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class TaskChainManager:
    """Manages task chain state and SSE communication."""
    
    def __init__(self, sse_session_id: Optional[str] = None):
        self.sse_session_id = sse_session_id
        self.tasks: List[Task] = []
        self.results: Dict[str, Any] = {}
        self.is_paused = False
        self.current_step = 0
        self.total_steps = 0
    
    def set_tasks(self, tasks: List[Task]) -> None:
        """Set the task list for execution."""
        self.tasks = tasks
        self.total_steps = len(tasks)
        self.current_step = 0
        self.results = {}
    
    def pause_for_confirmation(self) -> None:
        """Pause execution for user confirmation."""
        self.is_paused = True
    
    def resume_execution(self) -> None:
        """Resume execution after confirmation."""
        self.is_paused = False
    
    def send_progress(self, task_id: str, status: str, message: str = "") -> None:
        """Send progress update via SSE."""
        if self.sse_session_id:
            try:
                # SSE送信者を取得して進捗を送信
                from api.utils.sse_manager import get_sse_sender
                sse_sender = get_sse_sender()
                
                # 進捗率を計算（現在のステップ / 総ステップ数）
                progress_percentage = int((self.current_step / self.total_steps) * 100) if self.total_steps > 0 else 0
                
                # 進捗メッセージを送信
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 既にイベントループが実行中の場合は、タスクを作成
                    asyncio.create_task(sse_sender.send_progress(
                        self.sse_session_id, 
                        progress_percentage, 
                        f"タスク {task_id}: {message}"
                    ))
                else:
                    # イベントループが実行されていない場合は、同期的に実行
                    loop.run_until_complete(sse_sender.send_progress(
                        self.sse_session_id, 
                        progress_percentage, 
                        f"タスク {task_id}: {message}"
                    ))
            except Exception as e:
                # SSE送信エラーはログに記録するが、処理は継続
                import logging
                logger = logging.getLogger("core.models")
                logger.error(f"❌ [TaskChainManager] SSE progress send failed: {e}")
    
    def send_complete(self, final_response: str) -> None:
        """Send completion notification via SSE."""
        if self.sse_session_id:
            try:
                # SSE送信者を取得して完了通知を送信
                from api.utils.sse_manager import get_sse_sender
                sse_sender = get_sse_sender()
                
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 既にイベントループが実行中の場合は、タスクを作成
                    asyncio.create_task(sse_sender.send_complete(
                        self.sse_session_id, 
                        "すべてのタスクが完了しました"
                    ))
                else:
                    # イベントループが実行されていない場合は、同期的に実行
                    loop.run_until_complete(sse_sender.send_complete(
                        self.sse_session_id, 
                        "すべてのタスクが完了しました"
                    ))
            except Exception as e:
                # SSE送信エラーはログに記録するが、処理は継続
                import logging
                logger = logging.getLogger("core.models")
                logger.error(f"❌ [TaskChainManager] SSE complete send failed: {e}")
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: str = None) -> None:
        """Update task status and result."""
        for task in self.tasks:
            if task.id == task_id:
                task.status = status
                task.result = result
                task.error = error
                if status == TaskStatus.COMPLETED:
                    self.results[task_id] = result
                break
