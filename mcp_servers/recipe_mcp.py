"""
Morizo AI v2 - Recipe MCP Server

This module provides MCP server for recipe generation with LLM-based tools.
"""

import sys
import os
# プロジェクトルートをPythonのモジュール検索パスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from fastmcp import FastMCP

from mcp_servers.recipe_llm import RecipeLLM
from mcp_servers.recipe_web import search_client, prioritize_recipes, filter_recipe_results
from mcp_servers.utils import get_authenticated_client
from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()

# MCPサーバー初期化
mcp = FastMCP("Recipe MCP Server")

# 処理クラスのインスタンス
llm_client = RecipeLLM()
logger = GenericLogger("mcp", "recipe_server", initialize_logging=False)


# LLM推論ツール
@mcp.tool()
async def generate_menu_with_llm_constraints(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食",
    excluded_recipes: List[str] = None
) -> Dict[str, Any]:
    """
    LLM推論による独創的な献立タイトル生成
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID
        menu_type: 献立のタイプ（和食・洋食・中華）
        excluded_recipes: 除外するレシピタイトル
    
    Returns:
        生成された献立タイトルの候補
    
    TODO: 複数提案機能の実装
    - 食材重複抑止のため、複数の献立候補を生成する必要がある
    - 現在は1つの献立のみ生成しているが、3-5個の候補を生成すべき
    - 各候補は主菜・副菜・汁物の3品構成で、食材の重複を避ける
    """
    logger.info(f"🧠 [MCP] Generating LLM menu for user: {user_id}")
    
    try:
        result = await llm_client.generate_menu_titles(
            inventory_items=inventory_items,
            menu_type=menu_type,
            excluded_recipes=excluded_recipes
        )
        
        if result["success"]:
            logger.info(f"✅ [MCP] LLM menu generation successful")
            return result
        else:
            logger.error(f"❌ [MCP] LLM menu generation failed: {result['error']}")
            return result
            
    except Exception as e:
        logger.error(f"❌ [MCP] LLM menu generation exception: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_recipe_history_for_user(
    user_id: str,
    days: int = 14,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    ユーザーのレシピ履歴を取得（除外レシピ用）
    
    Args:
        user_id: ユーザーID
        days: 取得する日数（デフォルト14日）
    
    Returns:
        レシピ履歴のリスト
    """
    logger.info(f"📋 [MCP] Getting recipe history for user: {user_id} (last {days} days)")
    
    try:
        client = get_authenticated_client(user_id, token)
        
        # レシピ履歴を取得（簡易実装）
        result = client.table("recipe_historys").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if result.data:
            # 指定日数以内のレシピのみフィルタリング
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_recipes = []
            for recipe in result.data:
                created_at = datetime.fromisoformat(recipe['created_at'].replace('Z', '+00:00'))
                if created_at >= cutoff_date:
                    recent_recipes.append(recipe['title'])
            
            logger.info(f"✅ [MCP] Found {len(recent_recipes)} recent recipes")
            return {"success": True, "data": recent_recipes}
        else:
            logger.info(f"✅ [MCP] No recipe history found")
            return {"success": True, "data": []}
            
    except Exception as e:
        logger.error(f"❌ [MCP] Failed to get recipe history: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_menu_plan_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食",
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    在庫食材から献立構成を生成（過去履歴を考慮）
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID
        menu_type: 献立のタイプ
    
    Returns:
        生成された献立構成
    
    TODO: 食材重複抑止機能の実装
    - LLMまたはRAGから複数提案された献立から、食材が重複しない組み合わせを推論する機能
    - AI制約解決エンジンによる最適選択機能
    - 複数候補から食材重複を避ける最適な組み合わせを選択
    - 在庫食材を最大限活用し、バランスの良い献立構成を実現
    """
    logger.info(f"🍽️ [MCP] Generating menu plan with history for user: {user_id}")
    
    try:
        # 1. 過去のレシピ履歴を取得
        history_result = await get_recipe_history_for_user(user_id, days=14, token=token)
        
        excluded_recipes = []
        if history_result["success"]:
            excluded_recipes = history_result["data"]
        
        # 2. LLM推論で献立を生成
        menu_result = await generate_menu_with_llm_constraints(
            inventory_items=inventory_items,
            user_id=user_id,
            menu_type=menu_type,
            excluded_recipes=excluded_recipes
        )
        
        if menu_result["success"]:
            # 3. 結果を整形
            menu_data = menu_result["data"]
            
            result = {
                "main_dish": {
                    "title": menu_data.get("main_dish", ""),
                    "ingredients": menu_data.get("ingredients_used", [])
                },
                "side_dish": {
                    "title": menu_data.get("side_dish", ""),
                    "ingredients": []
                },
                "soup": {
                    "title": menu_data.get("soup", ""),
                    "ingredients": []
                },
                "ingredient_usage": {
                    "used": menu_data.get("ingredients_used", []),
                    "remaining": []
                },
                "excluded_recipes": excluded_recipes,
                "fallback_used": False
            }
            
            logger.info(f"✅ [MCP] Menu plan generation successful")
            return {"success": True, "data": result}
        else:
            logger.error(f"❌ [MCP] Menu plan generation failed: {menu_result['error']}")
            return menu_result
            
    except Exception as e:
        logger.error(f"❌ [MCP] Menu plan generation exception: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_recipe_from_web(
    recipe_titles: List[str]
) -> List[Dict[str, Any]]:
    """
    Web検索による具体的レシピ取得
    
    Args:
        recipe_titles: 検索するレシピタイトルリスト
    
    Returns:
        検索されたレシピのリスト（URL、説明、サイト情報を含む）
    """
    logger.info(f"🌐 [MCP] Searching recipes from web: {recipe_titles}")
    
    try:
        all_recipes = []
        
        # 各タイトルに対して検索を実行
        for title in recipe_titles:
            recipes = await search_client.search_recipes(title, num_results=3)
            
            # レシピをフィルタリング・優先順位付け
            filtered_recipes = filter_recipe_results(recipes)
            prioritized_recipes = prioritize_recipes(filtered_recipes)
            
            # タイトル情報を追加
            for recipe in prioritized_recipes:
                recipe['search_title'] = title
            
            all_recipes.extend(prioritized_recipes)
        
        logger.info(f"✅ [MCP] Found {len(all_recipes)} recipes from web search")
        return all_recipes
        
    except Exception as e:
        logger.error(f"❌ [MCP] Web search failed: {e}")
        return []


class RecipeMCP:
    """Recipe MCPクラス（MCPClient用のラッパー）"""

    def __init__(self):
        self.llm_client = RecipeLLM()
        self.logger = GenericLogger("mcp", "recipe_mcp_class")

    async def execute(self, tool_name: str, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """MCPツールを実行"""
        try:
            # ツール名に基づいて適切なメソッドを呼び出し
            if tool_name == "generate_menu_with_llm_constraints":
                return await self._execute_generate_menu_with_llm_constraints(parameters)
            elif tool_name == "get_recipe_history_for_user":
                return await self._execute_get_recipe_history_for_user(parameters, token)
            elif tool_name == "generate_menu_plan_with_history":
                return await self._execute_generate_menu_plan_with_history(parameters, token)
            elif tool_name == "search_recipe_from_web":
                return await self._execute_search_recipe_from_web(parameters)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"❌ [RecipeMCP] Tool {tool_name} failed: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_generate_menu_with_llm_constraints(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """LLM推論による献立生成を実行"""
        return await self.llm_client.generate_menu_titles(
            inventory_items=parameters["inventory_items"],
            menu_type=parameters.get("menu_type", "和食"),
            excluded_recipes=parameters.get("excluded_recipes")
        )

    async def _execute_get_recipe_history_for_user(self, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """レシピ履歴取得を実行"""
        try:
            client = get_authenticated_client(parameters["user_id"], token)
            
            # レシピ履歴を取得（簡易実装）
            result = client.table("recipe_historys").select("*").eq("user_id", parameters["user_id"]).order("created_at", desc=True).execute()
            
            if result.data:
                # 指定日数以内のレシピのみフィルタリング
                from datetime import datetime, timedelta
                days = parameters.get("days", 14)
                cutoff_date = datetime.now() - timedelta(days=days)
                
                recent_recipes = []
                for recipe in result.data:
                    created_at = datetime.fromisoformat(recipe['created_at'].replace('Z', '+00:00'))
                    if created_at >= cutoff_date:
                        recent_recipes.append(recipe['title'])
                
                return {"success": True, "data": recent_recipes}
            else:
                return {"success": True, "data": []}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_generate_menu_plan_with_history(self, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """履歴を考慮した献立計画生成を実行"""
        try:
            # 1. 過去のレシピ履歴を取得
            history_result = await self._execute_get_recipe_history_for_user(parameters, token)
            
            excluded_recipes = []
            if history_result["success"]:
                excluded_recipes = history_result["data"]
            
            # 2. LLM推論で献立を生成
            menu_result = await self._execute_generate_menu_with_llm_constraints({
                "inventory_items": parameters["inventory_items"],
                "menu_type": parameters.get("menu_type", "和食"),
                "excluded_recipes": excluded_recipes
            })
            
            if menu_result["success"]:
                # 3. 結果を整形
                menu_data = menu_result["data"]
                
                result = {
                    "main_dish": {
                        "title": menu_data.get("main_dish", ""),
                        "ingredients": menu_data.get("ingredients_used", [])
                    },
                    "side_dish": {
                        "title": menu_data.get("side_dish", ""),
                        "ingredients": []
                    },
                    "soup": {
                        "title": menu_data.get("soup", ""),
                        "ingredients": []
                    },
                    "ingredient_usage": {
                        "used": menu_data.get("ingredients_used", []),
                        "remaining": []
                    },
                    "excluded_recipes": excluded_recipes,
                    "fallback_used": False
                }
                
                return {"success": True, "data": result}
            else:
                return menu_result
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_search_recipe_from_web(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Web検索によるレシピ取得を実行"""
        try:
            all_recipes = []
            recipe_titles = parameters["recipe_titles"]
            
            # 各タイトルに対して検索を実行
            for title in recipe_titles:
                recipes = await search_client.search_recipes(title, num_results=3)
                
                # レシピをフィルタリング・優先順位付け
                filtered_recipes = filter_recipe_results(recipes)
                prioritized_recipes = prioritize_recipes(filtered_recipes)
                
                # タイトル情報を追加
                for recipe in prioritized_recipes:
                    recipe['search_title'] = title
                
                all_recipes.extend(prioritized_recipes)
            
            return {"success": True, "data": all_recipes}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    logger.info("🚀 Starting Recipe MCP Server")
    mcp.run()
