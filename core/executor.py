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
    
    def __init__(self, service_coordinator: ServiceCoordinator, confirmation_service=None):
        self.service_coordinator = service_coordinator
        self.confirmation_service = confirmation_service
        self.logger = GenericLogger("core", "executor")
    
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
            
            # 【新規追加】実行前に曖昧性チェック
            if self.confirmation_service:
                self.logger.info(f"🔍 [EXECUTOR] Checking for ambiguity before execution")
                
                # ConfirmationServiceで曖昧性チェック
                ambiguity_result = await self.confirmation_service.detect_ambiguity(tasks, user_id, token)
                
                if ambiguity_result.requires_confirmation:
                    self.logger.info(f"⚠️ [EXECUTOR] Ambiguity detected, requesting confirmation")
                    
                    # 最初の曖昧なタスクの情報を取得
                    first_ambiguous_task = ambiguity_result.ambiguous_tasks[0]
                    
                    return ExecutionResult(
                        status="needs_confirmation",
                        confirmation_context={
                            "ambiguity_info": first_ambiguous_task,
                            "user_response": "",
                            "original_tasks": tasks
                        },
                        outputs={},
                        message=first_ambiguous_task.details["message"]
                    )
                
                self.logger.info(f"✅ [EXECUTOR] No ambiguity detected, proceeding with execution")
            
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
                completed_count = 0
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
                        completed_count += 1
                
                # 完了したタスク数分だけ進捗を更新
                if completed_count > 0:
                    task_chain_manager.current_step += completed_count
                    
                    # 完了したタスクの情報を使用
                    completed_tasks = [task for task, result in zip(executable_group, group_results) 
                                     if not isinstance(result, Exception) and not isinstance(result, AmbiguityDetected)]
                    
                    if completed_tasks:
                        # 最初の完了タスクの情報を使用
                        first_completed_task = completed_tasks[0]
                        task_chain_manager.send_progress(first_completed_task.id, "完了", f"{completed_count}個のタスクが完了しました")
                
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
            
            coroutine = self._execute_single_task(task, user_id, previous_results, token, task_chain_manager)
            coroutines.append(coroutine)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        return results
    
    async def _execute_single_task(self, task: Task, user_id: str, previous_results: Dict[str, Any], token: str, task_chain_manager: TaskChainManager = None) -> Any:
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
        """Inject data from previous task results into parameters (辞書構造対応版)."""
        injected = parameters.copy()
        
        
        for key, value in parameters.items():
            
            if isinstance(value, str):
                # 辞書フィールド参照: "task2.result.main_dish"
                if ".result." in value and value.endswith((".main_dish", ".side_dish", ".soup")):
                    field_value = self._extract_field_from_result(value, previous_results)
                    injected[key] = field_value
                    self.logger.info(f"🔗 [EXECUTOR] Extracted field '{value}' = '{field_value}'")
                
                # 複数フィールド参照: "task2.result.main_dish,task3.result.main_dish"
                elif "," in value and ".result." in value:
                    field_values = self._extract_multiple_fields(value, previous_results)
                    injected[key] = field_values
                    self.logger.info(f"🔗 [EXECUTOR] Extracted multiple fields '{value}' = {field_values}")
                
                # 単一タスク結果参照: "task1.result"
                elif value.endswith(".result"):
                    task_ref = value[:-7]  # "task1.result" -> "task1"
                    
                    if task_ref in previous_results:
                        # 在庫データから食材名リストを抽出
                        inventory_data = previous_results[task_ref]
                        
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
                    # その他の文字列はそのまま保持
                    pass
            
            elif isinstance(value, list):
                # 🆕 リスト型パラメータの処理を追加
                resolved_list = []
                
                for item in value:
                    if isinstance(item, str):
                        # リスト内の各要素を解決
                        if ".result." in item and item.endswith((".main_dish", ".side_dish", ".soup")):
                            field_value = self._extract_field_from_result(item, previous_results)
                            resolved_list.append(field_value)
                            self.logger.info(f"🔗 [EXECUTOR] Resolved list item '{item}' = '{field_value}'")
                        elif item.endswith(".result"):
                            # 単一タスク結果参照
                            task_ref = item[:-7]
                            if task_ref in previous_results:
                                task_result = previous_results[task_ref]
                                if isinstance(task_result, dict) and task_result.get("success"):
                                    resolved_list.append(task_result.get("result", {}))
                                    self.logger.info(f"🔗 [EXECUTOR] Resolved list item '{item}' = task result")
                        else:
                            # その他の文字列はそのまま
                            resolved_list.append(item)
                    else:
                        # 文字列以外はそのまま
                        resolved_list.append(item)
                
                injected[key] = resolved_list
                self.logger.info(f"🔗 [EXECUTOR] Resolved list parameter '{key}' = {resolved_list}")
            
            else:
                # その他の型はそのまま保持
                pass
        
        return injected
    
    def _extract_field_from_result(self, value: str, previous_results: Dict[str, Any]) -> str:
        """辞書構造から特定フィールドを抽出"""
        # "task2.result.main_dish" -> task2のmain_dishフィールドを抽出
        parts = value.split(".")
        task_id = parts[0]
        field_name = parts[2]  # main_dish, side_dish, soup
        
        
        if task_id in previous_results:
            task_result = previous_results[task_id]
            
            if isinstance(task_result, dict) and task_result.get("success"):
                data = task_result.get("result", {}).get("data", {})
                field_value = data.get(field_name, "")
                self.logger.info(f"🔗 [EXECUTOR] Extracted '{field_name}' = '{field_value}'")
                return field_value
            else:
                self.logger.warning(f"⚠️ [EXECUTOR] Task result is not successful: {task_result}")
        else:
            self.logger.warning(f"⚠️ [EXECUTOR] Task '{task_id}' not found in previous_results")
        
        return ""
    
    def _extract_multiple_fields(self, value: str, previous_results: Dict[str, Any]) -> List[str]:
        """複数の辞書フィールドを抽出してリスト化"""
        field_refs = [ref.strip() for ref in value.split(",")]
        results = []
        
        
        for field_ref in field_refs:
            if ".result." in field_ref:
                field_value = self._extract_field_from_result(field_ref, previous_results)
                if field_value:  # 空文字列は除外
                    results.append(field_value)
                    self.logger.info(f"🔗 [EXECUTOR] Added field value: '{field_value}'")
                else:
                    # 空文字列の場合はスキップ
                    pass
        
        self.logger.info(f"🔗 [EXECUTOR] Final extracted values: {results}")
        return results
