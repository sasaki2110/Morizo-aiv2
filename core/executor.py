"""
TaskExecutor: Task execution specialist for the core layer.

This component manages task execution, dependency resolution, and parallel processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Set
from .models import Task, TaskStatus, TaskChainManager, ExecutionResult
from .exceptions import TaskExecutionError, CircularDependencyError, AmbiguityDetected
from .service_coordinator import ServiceCoordinator
from config.loggers import GenericLogger


class TaskExecutor:
    """Executes tasks with dependency resolution and parallel processing."""
    
    def __init__(self):
        self.logger = GenericLogger("core", "executor")
        self.service_coordinator = ServiceCoordinator()
    
    async def execute(self, tasks: List[Task], user_id: str, task_chain_manager: TaskChainManager, token: str) -> ExecutionResult:
        """
        Execute a list of tasks with dependency resolution.
        
        Args:
            tasks: List of tasks to execute
            user_id: User identifier
            task_chain_manager: Task chain manager for progress tracking
            token: Authentication token
            
        Returns:
            ExecutionResult with status and outputs
        """
        try:
            self.logger.info(f"🔄 [EXECUTOR] Starting ReAct loop with {len(tasks)} tasks for user {user_id}")
            
            # Log task dependency graph
            self.logger.info(f"📊 [EXECUTOR] Task dependency graph:")
            for task in tasks:
                deps_str = f"deps: {task.dependencies}" if task.dependencies else "no dependencies"
                self.logger.info(f"  - {task.id}: {task.service}.{task.method} ({deps_str})")
            
            remaining_tasks = tasks.copy()
            all_results = {}
            iteration = 0
            
            while remaining_tasks:
                iteration += 1
                self.logger.info(f"🔄 [EXECUTOR] ReAct iteration {iteration}: {len(remaining_tasks)} tasks remaining")
                # Find executable group (tasks with resolved dependencies)
                executable_group = self._find_executable_group(remaining_tasks, all_results)
                
                if not executable_group:
                    # Check if we have remaining tasks but no executable ones
                    if remaining_tasks:
                        self.logger.error(f"❌ [EXECUTOR] Circular dependency detected in task graph")
                        raise CircularDependencyError("Circular dependency detected in task graph")
                    self.logger.info(f"✅ [EXECUTOR] All tasks completed")
                    break
                
                # Log executable group
                group_task_ids = [task.id for task in executable_group]
                self.logger.info(f"⚡ [EXECUTOR] Executing group {iteration}: {group_task_ids}")
                for task in executable_group:
                    self.logger.info(f"  - {task.id}: {task.service}.{task.method}")
                
                # Execute tasks in parallel
                group_results = await self._execute_group(executable_group, user_id, all_results, task_chain_manager, token)
                
                # Process results
                for task, result in zip(executable_group, group_results):
                    if isinstance(result, AmbiguityDetected):
                        # Ambiguity detected - interrupt execution
                        self.logger.warning(f"⚠️ [EXECUTOR] Ambiguity detected in task {task.id}: {result.message}")
                        return ExecutionResult(
                            status="needs_confirmation",
                            confirmation_context=result.context,
                            message=result.message
                        )
                    
                    if isinstance(result, Exception):
                        self.logger.error(f"❌ [EXECUTOR] Task {task.id} failed: {str(result)}")
                        task.status = TaskStatus.FAILED
                        task.error = str(result)
                        task_chain_manager.update_task_status(task.id, TaskStatus.FAILED, error=str(result))
                    else:
                        self.logger.info(f"✅ [EXECUTOR] Task {task.id} completed successfully")
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        all_results[task.id] = result
                        task_chain_manager.update_task_status(task.id, TaskStatus.COMPLETED, result)
                
                # Remove completed tasks from remaining
                completed_ids = [task.id for task in executable_group]
                remaining_tasks = [t for t in remaining_tasks if t.id not in completed_ids]
                self.logger.info(f"📊 [EXECUTOR] Completed {len(completed_ids)} tasks, {len(remaining_tasks)} remaining")
            
            self.logger.info("✅ [EXECUTOR] ReAct loop completed successfully")
            return ExecutionResult(status="success", outputs=all_results)
            
        except AmbiguityDetected as e:
            return ExecutionResult(
                status="needs_confirmation",
                confirmation_context=e.context,
                message=e.message
            )
        except Exception as e:
            self.logger.error(f"Task execution failed: {str(e)}")
            return ExecutionResult(status="error", message=str(e))
    
    def _find_executable_group(self, tasks: List[Task], completed_results: Dict[str, Any]) -> List[Task]:
        """Find tasks that can be executed (dependencies resolved)."""
        executable = []
        
        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            if self._are_dependencies_satisfied(task, completed_results):
                executable.append(task)
        
        return executable
    
    def _are_dependencies_satisfied(self, task: Task, completed_results: Dict[str, Any]) -> bool:
        """Check if all task dependencies are satisfied."""
        for dep_id in task.dependencies:
            if dep_id not in completed_results:
                return False
        return True
    
    async def _execute_group(self, tasks: List[Task], user_id: str, previous_results: Dict[str, Any], task_chain_manager: TaskChainManager, token: str) -> List[Any]:
        """Execute a group of tasks in parallel."""
        coroutines = []
        
        for task in tasks:
            task.status = TaskStatus.RUNNING
            task_chain_manager.update_task_status(task.id, TaskStatus.RUNNING)
            
            coroutine = self._execute_single_task(task, user_id, previous_results, token)
            coroutines.append(coroutine)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        return results
    
    async def _execute_single_task(self, task: Task, user_id: str, previous_results: Dict[str, Any], token: str) -> Any:
        """Execute a single task with data injection."""
        try:
            self.logger.info(f"🚀 [EXECUTOR] Starting task {task.id}: {task.service}.{task.method}")
            
            # Inject data from previous tasks
            injected_params = self._inject_data(task.parameters, previous_results)
            self.logger.info(f"📥 [EXECUTOR] Task {task.id} input parameters: {injected_params}")
            
            # Execute service method with token
            result = await self.service_coordinator.execute_service(
                task.service, task.method, injected_params, token
            )
            
            self.logger.info(f"📤 [EXECUTOR] Task {task.id} output result: {result}")
            self.logger.info(f"✅ [EXECUTOR] Task {task.id} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [EXECUTOR] Task {task.id} failed: {str(e)}")
            raise
    
    def _inject_data(self, parameters: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Inject data from previous task results into parameters."""
        injected = parameters.copy()
        
        self.logger.info(f"🔍 [EXECUTOR] Starting data injection")
        self.logger.info(f"🔍 [EXECUTOR] Parameters to inject: {parameters}")
        self.logger.info(f"🔍 [EXECUTOR] Previous results keys: {list(previous_results.keys())}")
        self.logger.info(f"🔍 [EXECUTOR] Previous results: {previous_results}")
        
        for key, value in parameters.items():
            self.logger.info(f"🔍 [EXECUTOR] Processing parameter: {key} = {value}")
            
            # task1.result 形式の処理
            if isinstance(value, str) and value.endswith(".result"):
                task_ref = value[:-7]  # "task1.result" -> "task1"
                self.logger.info(f"🔍 [EXECUTOR] Found .result reference: {task_ref}")
                
                if task_ref in previous_results:
                    self.logger.info(f"🔍 [EXECUTOR] Found task reference in previous_results: {task_ref}")
                    # 在庫データから食材名リストを抽出
                    inventory_data = previous_results[task_ref]
                    self.logger.info(f"🔍 [EXECUTOR] Inventory data: {inventory_data}")
                    
                    if isinstance(inventory_data, dict) and inventory_data.get("success"):
                        items = inventory_data.get("result", {}).get("data", [])
                        item_names = [item.get("item_name") for item in items if item.get("item_name")]
                        injected[key] = item_names
                        self.logger.info(f"🔗 [EXECUTOR] Injected {len(item_names)} items from {task_ref} to {key}")
                    else:
                        self.logger.warning(f"⚠️ [EXECUTOR] Inventory data is not successful: {inventory_data}")
                else:
                    self.logger.warning(f"⚠️ [EXECUTOR] Task reference not found in previous_results: {task_ref}")
            else:
                self.logger.info(f"🔍 [EXECUTOR] Parameter {key} does not match .result pattern")
        
        self.logger.info(f"🔍 [EXECUTOR] Final injected parameters: {injected}")
        return injected
