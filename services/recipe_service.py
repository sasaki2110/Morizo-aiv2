#!/usr/bin/env python3
"""
RecipeService - レシピ関連サービス

レシピ生成・検索・履歴管理のビジネスロジックを提供
ToolRouter経由でMCPツールを呼び出し
"""

from typing import Dict, Any, List, Optional
from .tool_router import ToolRouter
from config.loggers import GenericLogger


class RecipeService:
    """レシピ関連サービス"""
    
    def __init__(self, tool_router: ToolRouter):
        """初期化"""
        self.tool_router = tool_router
        self.logger = GenericLogger("service", "recipe")
    
    async def generate_menu_plan(
        self, 
        inventory_items: List[str], 
        user_id: str,
        menu_type: str = "和食",
        excluded_recipes: List[str] = None,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        在庫食材から献立構成を生成
        
        Args:
            inventory_items: 在庫食材リスト
            user_id: ユーザーID
            menu_type: 献立のタイプ
            excluded_recipes: 除外するレシピタイトル
            token: 認証トークン
        
        Returns:
            生成された献立プラン
        """
        try:
            self.logger.info(f"🔧 [RecipeService] Generating menu plan for user: {user_id}")
            
            # ToolRouter経由でRecipeMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "generate_menu_plan_with_history",
                {
                    "inventory_items": inventory_items,
                    "user_id": user_id,
                    "menu_type": menu_type,
                    "excluded_recipes": excluded_recipes or []
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [RecipeService] Menu plan generated successfully")
            else:
                self.logger.error(f"❌ [RecipeService] Menu plan generation failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [RecipeService] Error in generate_menu_plan: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_recipes_from_web(
        self, 
        recipe_titles: List[str],
        num_results: int = 5,
        user_id: str = "",
        token: str = "",
        menu_categories: List[str] = None,
        menu_source: str = "mixed"
    ) -> Dict[str, Any]:
        """
        Web検索によるレシピ検索（複数料理名対応・並列実行・詳細分類）
        
        Args:
            recipe_titles: 検索するレシピタイトルのリスト
            num_results: 各料理名あたりの取得結果数
            user_id: ユーザーID（一貫性のため受け取るが使用しない）
            token: 認証トークン
            menu_categories: 料理名の分類リスト（main_dish, side_dish, soup）
            menu_source: 検索元（llm, rag, mixed）
        
        Returns:
            分類された検索結果のレシピリスト
        """
        try:
            self.logger.info(f"🔧 [RecipeService] Searching recipes for {len(recipe_titles)} titles: {recipe_titles}")
            self.logger.info(f"📊 [RecipeService] Menu categories: {menu_categories}, source: {menu_source}")
            
            # ToolRouter経由でRecipeMCPツールを呼び出し（詳細分類対応）
            result = await self.tool_router.route_tool(
                "search_recipe_from_web",
                {
                    "recipe_titles": recipe_titles,
                    "num_results": num_results,
                    "menu_categories": menu_categories,
                    "menu_source": menu_source
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [RecipeService] Recipe search completed successfully: {result.get('total_count', 0)} recipes found")
            else:
                self.logger.error(f"❌ [RecipeService] Recipe search failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [RecipeService] Error in search_recipes_from_web: {e}")
            return {"success": False, "error": str(e)}
    
    async def search_menu_from_rag(
        self,
        inventory_items: List[str],
        user_id: str,
        menu_type: str = "和食",
        excluded_recipes: List[str] = None,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        RAG検索による献立タイトル生成
        
        Args:
            inventory_items: 在庫食材リスト
            user_id: ユーザーID
            menu_type: 献立のタイプ
            excluded_recipes: 除外するレシピタイトル
            token: 認証トークン
        
        Returns:
            RAG検索による献立結果
        """
        try:
            self.logger.info(f"🔧 [RecipeService] Searching menu from RAG for user: {user_id}")
            
            # ToolRouter経由でRecipeMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "search_menu_from_rag_with_history",
                {
                    "inventory_items": inventory_items,
                    "user_id": user_id,
                    "menu_type": menu_type,
                    "excluded_recipes": excluded_recipes or []
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [RecipeService] RAG menu search completed successfully")
            else:
                self.logger.error(f"❌ [RecipeService] RAG menu search failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [RecipeService] Error in search_menu_from_rag: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_recipe_history(
        self, 
        user_id: str,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        ユーザーのレシピ履歴を取得
        
        Args:
            user_id: ユーザーID
            token: 認証トークン
        
        Returns:
            レシピ履歴のリスト
        """
        try:
            self.logger.info(f"🔧 [RecipeService] Getting recipe history for user: {user_id}")
            
            # ToolRouter経由でRecipeMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "get_recipe_history_for_user",
                {
                    "user_id": user_id
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [RecipeService] Recipe history retrieved successfully")
            else:
                self.logger.error(f"❌ [RecipeService] Recipe history retrieval failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [RecipeService] Error in get_recipe_history: {e}")
            return {"success": False, "error": str(e)}
