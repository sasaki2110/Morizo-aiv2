#!/usr/bin/env python3
"""
RecipeService - レシピ関連サービス

ToolRouter経由でMCPツールに委譲するシンプルなサービス
実際の処理はMCPツールで実行されるため、ビジネスロジックは不要
"""

from typing import Dict, Any, List, Optional
from .tool_router import ToolRouter
from config.loggers import GenericLogger


class RecipeService:
    """レシピ関連サービス - ToolRouter経由でMCPツールに委譲"""
    
    def __init__(self, tool_router: ToolRouter):
        """初期化"""
        self.tool_router = tool_router
        self.logger = GenericLogger("service", "recipe")
    
    # メソッドは削除 - ToolRouterが直接MCPツールを呼び出すため不要
    # 以下のメソッドはすべてToolRouter経由でMCPツールに委譲される：
    # - generate_menu_plan_with_history
    # - search_menu_from_rag_with_history  
    # - search_recipe_from_web
    # - get_recipe_history_for_user
