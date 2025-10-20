"""
ContextManager: セッション内コンテキスト管理
"""
from typing import Dict, List, Any, Optional
from config.loggers import GenericLogger


class ContextManager:
    """コンテキスト管理クラス"""
    
    def __init__(self, sse_session_id: str):
        self.sse_session_id = sse_session_id
        self.context = {}
        self.logger = GenericLogger("core", "context_manager")
    
    def set_main_ingredient(self, ingredient: str) -> None:
        """主要食材を設定"""
        self.context["main_ingredient"] = ingredient
        self.logger.info(f"🥬 [ContextManager] Main ingredient set: {ingredient}")
    
    def get_main_ingredient(self) -> Optional[str]:
        """主要食材を取得"""
        return self.context.get("main_ingredient")
    
    def set_inventory_items(self, items: List[str]) -> None:
        """在庫食材を設定"""
        self.context["inventory_items"] = items
        self.logger.info(f"📦 [ContextManager] Inventory items set: {len(items)} items")
    
    def get_inventory_items(self) -> List[str]:
        """在庫食材を取得"""
        return self.context.get("inventory_items", [])
    
    def set_excluded_recipes(self, recipes: List[str]) -> None:
        """除外レシピを設定"""
        self.context["excluded_recipes"] = recipes
        self.logger.info(f"🚫 [ContextManager] Excluded recipes set: {len(recipes)} recipes")
    
    def get_excluded_recipes(self) -> List[str]:
        """除外レシピを取得"""
        return self.context.get("excluded_recipes", [])
    
    def clear_context(self) -> None:
        """コンテキストをクリア"""
        self.context.clear()
        self.logger.info("🧹 [ContextManager] Context cleared")
    
    def get_context(self) -> Dict[str, Any]:
        """全コンテキストを取得"""
        return self.context.copy()
