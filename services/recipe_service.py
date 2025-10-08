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
        token: str = ""
    ) -> Dict[str, Any]:
        """
        Web検索によるレシピ検索（複数料理名対応・並列実行）
        
        Args:
            recipe_titles: 検索するレシピタイトルのリスト
            num_results: 各料理名あたりの取得結果数
            user_id: ユーザーID（一貫性のため受け取るが使用しない）
            token: 認証トークン
        
        Returns:
            統合された検索結果のレシピリスト
        """
        try:
            self.logger.info(f"🔧 [RecipeService] Searching recipes for {len(recipe_titles)} titles: {recipe_titles}")
            
            # 並列でMCPツールを呼び出し
            import asyncio
            
            async def search_single_recipe(title: str) -> Dict[str, Any]:
                """単一の料理名でレシピ検索"""
                return await self.tool_router.route_tool(
                    "search_recipe_from_web",
                    {
                        "recipe_title": title,
                        "num_results": num_results
                    },
                    token
                )
            
            # 並列実行
            tasks = [search_single_recipe(title) for title in recipe_titles]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果を統合
            all_recipes = []
            successful_searches = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ [RecipeService] Search failed for '{recipe_titles[i]}': {result}")
                elif result.get("success"):
                    recipes = result.get("data", [])
                    all_recipes.extend(recipes)
                    successful_searches += 1
                    self.logger.info(f"✅ [RecipeService] Found {len(recipes)} recipes for '{recipe_titles[i]}'")
                else:
                    self.logger.error(f"❌ [RecipeService] Search failed for '{recipe_titles[i]}': {result.get('error')}")
            
            # 重複を除去（URLベース）
            unique_recipes = []
            seen_urls = set()
            for recipe in all_recipes:
                if recipe.get("url") not in seen_urls:
                    unique_recipes.append(recipe)
                    seen_urls.add(recipe.get("url"))
            
            self.logger.info(f"✅ [RecipeService] Recipe search completed: {successful_searches}/{len(recipe_titles)} successful, {len(unique_recipes)} unique recipes")
            
            return {
                "success": True,
                "data": unique_recipes,
                "total_count": len(unique_recipes),
                "searches_completed": successful_searches,
                "total_searches": len(recipe_titles)
            }
            
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
