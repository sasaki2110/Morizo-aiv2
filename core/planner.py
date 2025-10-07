"""
ActionPlanner: Task planning specialist for the core layer.

This component analyzes user requests and generates executable task lists
with proper dependency resolution.
"""

import uuid
import logging
from typing import List, Dict, Any
from .models import Task, TaskStatus
from .exceptions import PlanningError
from .service_coordinator import ServiceCoordinator
from services.llm_service import LLMService
from config.loggers import GenericLogger


class ActionPlanner:
    """Plans and decomposes user requests into executable tasks."""
    
    def __init__(self):
        self.logger = GenericLogger("core", "planner")
        self.llm_service = LLMService()
        self.service_coordinator = ServiceCoordinator()
        self.service_registry = self._build_service_registry()
    
    def _build_service_registry(self) -> Dict[str, Dict[str, Any]]:
        """Build registry of available services and their methods."""
        return {
            "RecipeService": {
                "generate_menu_plan": {
                    "description": "Generate a menu plan based on available ingredients",
                    "parameters": ["ingredients", "preferences", "dietary_restrictions"]
                },
                "search_recipes_from_web": {
                    "description": "Search for recipes from web sources",
                    "parameters": ["query", "max_results"]
                },
                "search_menu_from_rag": {
                    "description": "Search for recipes using RAG",
                    "parameters": ["query", "max_results"]
                },
                "get_recipe_history": {
                    "description": "Get user's recipe history",
                    "parameters": ["user_id", "limit"]
                }
            },
            "InventoryService": {
                "add_inventory": {
                    "description": "Add items to inventory",
                    "parameters": ["items", "user_id"]
                },
                "get_inventory": {
                    "description": "Get user's inventory",
                    "parameters": ["user_id"]
                },
                "get_inventory_by_name": {
                    "description": "Get inventory items by name",
                    "parameters": ["name", "user_id"]
                },
                "update_inventory_by_id": {
                    "description": "Update inventory item by ID",
                    "parameters": ["item_id", "updates", "user_id"]
                },
                "delete_inventory_by_id": {
                    "description": "Delete inventory item by ID",
                    "parameters": ["item_id", "user_id"]
                }
            },
            "SessionService": {
                "create_session": {
                    "description": "Create a new session",
                    "parameters": ["user_id", "session_data"]
                },
                "get_session": {
                    "description": "Get session information",
                    "parameters": ["session_id"]
                },
                "update_session": {
                    "description": "Update session data",
                    "parameters": ["session_id", "updates"]
                },
                "delete_session": {
                    "description": "Delete session",
                    "parameters": ["session_id"]
                }
            }
        }
    
    async def plan(self, user_request: str, user_id: str) -> List[Task]:
        """
        Plan tasks based on user request.
        
        Args:
            user_request: User's natural language request
            user_id: User identifier
            
        Returns:
            List of tasks with dependencies resolved
        """
        try:
            self.logger.info(f"🎯 [PLANNER] Starting task planning for user {user_id}")
            self.logger.info(f"📝 [PLANNER] User request: '{user_request}'")
            
            # Get available tools description
            tools_description = self.service_coordinator.get_available_tools_description()
            self.logger.info(f"🔧 [PLANNER] Retrieved {len(tools_description)} available tools")
            
            # Use LLM to decompose the request into tasks
            task_descriptions = await self.llm_service.decompose_tasks(
                user_request, tools_description, user_id
            )
            self.logger.info(f"🤖 [PLANNER] LLM generated {len(task_descriptions)} task descriptions")
            
            # Convert descriptions to Task objects
            tasks = self._create_tasks_from_descriptions(task_descriptions, user_id)
            self.logger.info(f"📋 [PLANNER] Created {len(tasks)} tasks from descriptions")
            
            # Log task details
            for i, task in enumerate(tasks, 1):
                self.logger.info(f"  {i}. {task.service}.{task.method} (id: {task.id}, deps: {task.dependencies})")
                self.logger.info(f"     Parameters: {task.parameters}")
            
            # Resolve dependencies
            tasks = self._resolve_dependencies(tasks)
            self.logger.info(f"🔗 [PLANNER] Dependencies resolved for {len(tasks)} tasks")
            
            # Log final task structure
            for i, task in enumerate(tasks, 1):
                self.logger.info(f"  {i}. {task.service}.{task.method} (id: {task.id}, resolved_deps: {task.dependencies})")
            
            self.logger.info(f"✅ [PLANNER] Task planning completed successfully")
            return tasks
            
        except Exception as e:
            self.logger.error(f"❌ [PLANNER] Task planning failed: {str(e)}")
            raise PlanningError(f"Failed to plan tasks: {str(e)}")
    
    def _create_tasks_from_descriptions(self, descriptions: List[Dict], user_id: str) -> List[Task]:
        """Convert task descriptions to Task objects."""
        tasks = []
        
        for desc in descriptions:
            task_id = str(uuid.uuid4())
            service = desc.get("service")
            method = desc.get("method")
            parameters = desc.get("parameters", {})
            
            # Add user_id to parameters if not present
            if "user_id" not in parameters:
                parameters["user_id"] = user_id
            
            task = Task(
                id=task_id,
                service=service,
                method=method,
                parameters=parameters,
                dependencies=desc.get("dependencies", [])
            )
            tasks.append(task)
        
        return tasks
    
    def _resolve_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Resolve task dependencies and update dependency IDs."""
        task_map = {task.id: task for task in tasks}
        
        for task in tasks:
            resolved_deps = []
            for dep_desc in task.dependencies:
                # Find task that matches the dependency description
                dep_task = self._find_dependency_task(dep_desc, tasks)
                if dep_task:
                    resolved_deps.append(dep_task.id)
            
            task.dependencies = resolved_deps
        
        return tasks
    
    def _find_dependency_task(self, dep_desc: str, tasks: List[Task]) -> Task:
        """Find task that matches dependency description."""
        # Simple matching based on service and method
        for task in tasks:
            if f"{task.service}.{task.method}" in dep_desc:
                return task
        return None
