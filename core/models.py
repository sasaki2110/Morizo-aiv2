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
        # TODO: Implement SSE communication
        pass
    
    def send_complete(self, final_response: str) -> None:
        """Send completion notification via SSE."""
        # TODO: Implement SSE communication
        pass
    
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
