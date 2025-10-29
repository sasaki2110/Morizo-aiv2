"""
TaskExecutor: Task execution specialist for the core layer.

This component manages task execution, dependency resolution, and parallel processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Set, Optional
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
            
            # Phase 1F: session_get_proposed_titlesのsse_session_idを実際のセッションIDで置き換え
            if task.method == "session_get_proposed_titles" and task_chain_manager and task_chain_manager.sse_session_id:
                # プランナーが生成した固定値（例: "session123"）を実際のsse_session_idで置き換え
                if "sse_session_id" in injected_params:
                    old_value = injected_params["sse_session_id"]
                    injected_params["sse_session_id"] = task_chain_manager.sse_session_id
                    self.logger.info(f"🔄 [EXECUTOR] Replaced sse_session_id: '{old_value}' → '{task_chain_manager.sse_session_id}'")
            
            self.logger.info(f"📥 [EXECUTOR] Task {task.id} input parameters: {injected_params}")
            
            # Execute service method with token
            # Phase 3A: sse_session_idをparametersに追加（generate_proposalsのみ）
            if task_chain_manager and task_chain_manager.sse_session_id and task.method == "generate_proposals":
                injected_params["sse_session_id"] = task_chain_manager.sse_session_id
            
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
            self.logger.info(f"🔍 [EXECUTOR] Processing parameter: key={key}, value={value}, type={type(value)}")
            
            # Phase 1F: セッションコンテキスト参照の処理（"session.context.xxx"形式）
            if isinstance(value, str) and value.startswith("session.context."):
                self.logger.info(f"🔍 [EXECUTOR] Detected session context reference: {value}")
                # この時点では文字列のまま保持（エージェントで実際にセッションから取得する）
                # injected[key] = value  # 既にvalueが設定されているため変更不要
                continue
            
            if isinstance(value, str):
                # 結合演算: "task1.result.data + task2.result.data"
                if " + " in value and ".result." in value:
                    self.logger.info(f"🔍 [EXECUTOR] Match: concatenation operation ({value})")
                    resolved_value = self._resolve_concatenation(value, previous_results)
                    if resolved_value is not None:
                        injected[key] = resolved_value
                        self.logger.info(f"🔗 [EXECUTOR] Resolved concatenation '{value}' = {len(resolved_value)} items")
                
                # 辞書フィールド参照: "task2.result.main_dish"
                elif ".result." in value and value.endswith((".main_dish", ".side_dish", ".soup")):
                    self.logger.info(f"🔍 [EXECUTOR] Match: dict field reference ({value})")
                    field_value = self._extract_field_from_result(value, previous_results)
                    injected[key] = field_value
                    self.logger.info(f"🔗 [EXECUTOR] Extracted field '{value}' = '{field_value}'")
                
                # 複数フィールド参照: "task2.result.main_dish,task3.result.main_dish"
                elif "," in value and ".result." in value:
                    self.logger.info(f"🔍 [EXECUTOR] Match: multiple fields reference ({value})")
                    field_values = self._extract_multiple_fields(value, previous_results)
                    injected[key] = field_values
                    self.logger.info(f"🔗 [EXECUTOR] Extracted multiple fields '{value}' = {field_values}")
                
                # ネストパス参照: "task2.result.data", "task1.result.success" など
                elif ".result." in value:
                    self.logger.info(f"🔍 [EXECUTOR] Match: nested path reference ({value})")
                    resolved_value = self._extract_nested_path(value, previous_results)
                    if resolved_value is not None:
                        injected[key] = resolved_value
                        self.logger.info(f"🔗 [EXECUTOR] Injected nested path '{value}' = {resolved_value}")
                
                # 単一タスク結果参照: "task1.result"
                elif value.endswith(".result"):
                    self.logger.info(f"🔍 [EXECUTOR] Match: single task result reference ({value})")
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
                    self.logger.info(f"🔍 [EXECUTOR] No match: keeping original value ({value})")
                    # その他の文字列はそのまま保持
                    pass
            
            elif isinstance(value, list):
                # 🆕 リスト型パラメータの処理を追加
                resolved_list = []
                
                for item in value:
                    if isinstance(item, str):
                        # リスト内の各要素を解決
                        if ".result." in item:
                            # ネストされたパス（task2.result.data.main_dishなど）の場合は_extract_nested_pathを使用
                            # シンプルなパス（task2.result.main_dish）の場合は_extract_field_from_resultを使用
                            dot_count = item.count(".")
                            if dot_count >= 3 and item.endswith((".main_dish", ".side_dish", ".soup")):
                                # ネストされたパスの場合
                                field_value = self._extract_nested_path(item, previous_results)
                                resolved_list.append(field_value if field_value is not None else "")
                                self.logger.info(f"🔗 [EXECUTOR] Resolved nested path list item '{item}' = '{field_value}'")
                            elif item.endswith((".main_dish", ".side_dish", ".soup")):
                                # シンプルなパスの場合
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
                                    resolved_list.append(item)
                            else:
                                # その他の.result.を含む文字列はネストパスとして処理
                                resolved_value = self._extract_nested_path(item, previous_results)
                                resolved_list.append(resolved_value if resolved_value is not None else item)
                                self.logger.info(f"🔗 [EXECUTOR] Resolved nested path list item '{item}' = '{resolved_value}'")
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
    
    def _extract_nested_path(self, path: str, previous_results: Dict[str, Any]) -> Any:
        """ネストされたパスを解決（任意の深さに対応: task2.result.data.candidates など）"""
        parts = path.split(".")
        if len(parts) < 2:
            self.logger.warning(f"⚠️ [EXECUTOR] Invalid nested path format: {path}")
            return None
        
        task_id = parts[0]  # "task2"
        path_after_task = parts[1:]  # ["result", "data", "candidates"]
        
        self.logger.info(f"🔍 [EXECUTOR] Extracting nested path: {path}")
        self.logger.info(f"🔍 [EXECUTOR] task_id={task_id}, nested_path={'.'.join(path_after_task)}")
        
        if task_id not in previous_results:
            self.logger.warning(f"⚠️ [EXECUTOR] Task '{task_id}' not found")
            return None
        
        task_result = previous_results[task_id]
        
        # 再帰的にパスを辿る
        current_value = task_result
        
        for key in path_after_task:
            if isinstance(current_value, dict):
                if key in current_value:
                    current_value = current_value[key]
                    self.logger.info(f"🔗 [EXECUTOR] Traversing to '{key}': found {type(current_value).__name__}")
                else:
                    self.logger.warning(f"⚠️ [EXECUTOR] Key '{key}' not found in {list(current_value.keys())}")
                    return None
            else:
                self.logger.warning(f"⚠️ [EXECUTOR] Cannot traverse '{key}' from {type(current_value).__name__}")
                return None
        
        self.logger.info(f"✅ [EXECUTOR] Successfully extracted: {type(current_value).__name__}")
        
        # Phase 3A Fix: candidatesが辞書のリストの場合、titleのリストに変換
        if isinstance(current_value, list) and len(current_value) > 0 and isinstance(current_value[0], dict):
            if "title" in current_value[0]:
                titles = [item["title"] for item in current_value if "title" in item]
                self.logger.info(f"🔧 [EXECUTOR] Converted candidates list to title list: {len(titles)} titles")
                return titles
        
        return current_value
    
    def _resolve_concatenation(self, expression: str, previous_results: Dict[str, Any]) -> Optional[list]:
        """結合演算を解決（例: "task1.result.data + task2.result.data"）"""
        try:
            parts = expression.split(" + ")
            result_list = []
            
            for part in parts:
                part = part.strip()
                # ネストパス参照として解決
                resolved_value = self._extract_nested_path(part, previous_results)
                
                if resolved_value is not None:
                    # リストの場合は拡張、それ以外は追加
                    if isinstance(resolved_value, list):
                        result_list.extend(resolved_value)
                        self.logger.info(f"🔗 [EXECUTOR] Extended {len(resolved_value)} items from {part}")
                    else:
                        result_list.append(resolved_value)
                        self.logger.info(f"🔗 [EXECUTOR] Added item from {part}")
                else:
                    self.logger.warning(f"⚠️ [EXECUTOR] Could not resolve part: {part}")
            
            self.logger.info(f"✅ [EXECUTOR] Concatenation result: {len(result_list)} items")
            return result_list
            
        except Exception as e:
            self.logger.error(f"❌ [EXECUTOR] Error in _resolve_concatenation: {e}")
            return None
