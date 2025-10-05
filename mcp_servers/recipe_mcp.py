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

# 手動でログハンドラーを設定
from config.logging import get_logger
import logging

# ルートロガーを取得してハンドラーを設定
root_logger = logging.getLogger('morizo_ai')
if not root_logger.handlers:
    from config.logging import setup_logging
    setup_logging(initialize=False)  # ローテーションなし


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
        Dict[str, Any]: 生成された献立情報
    """
    logger.info(f"🔧 [RECIPE] Starting generate_menu_with_llm_constraints for user: {user_id}, menu_type: {menu_type}")
    
    try:
        client = get_authenticated_client(user_id)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        result = await llm_client.generate_menu_with_constraints(client, inventory_items, user_id, menu_type, excluded_recipes)
        logger.info(f"✅ [RECIPE] generate_menu_with_llm_constraints completed successfully")
        logger.debug(f"📊 [RECIPE] LLM constraints result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in generate_menu_with_llm_constraints: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def get_recipe_history_for_user(user_id: str, token: str = None) -> Dict[str, Any]:
    """
    ユーザーのレシピ履歴を取得
    
    Args:
        user_id: ユーザーID
        token: 認証トークン
    
    Returns:
        Dict[str, Any]: レシピ履歴のリスト
    """
    logger.info(f"🔧 [RECIPE] Starting get_recipe_history_for_user for user: {user_id}")
    
    try:
        client = get_authenticated_client(user_id)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        result = await llm_client.get_recipe_history(client, user_id)
        logger.info(f"✅ [RECIPE] get_recipe_history_for_user completed successfully")
        logger.debug(f"📊 [RECIPE] Recipe history result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in get_recipe_history_for_user: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_menu_plan_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "和食",
    excluded_recipes: List[str] = None,
    token: str = None
) -> Dict[str, Any]:
    """
    履歴を考慮した献立プラン生成
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID
        menu_type: 献立のタイプ（和食・洋食・中華）
        excluded_recipes: 除外するレシピタイトル
        token: 認証トークン
    
    Returns:
        Dict[str, Any]: 生成された献立プラン
    """
    logger.info(f"🔧 [RECIPE] Starting generate_menu_plan_with_history for user: {user_id}, menu_type: {menu_type}")
    
    try:
        client = get_authenticated_client(user_id)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        result = await llm_client.generate_menu_titles(inventory_items, menu_type, excluded_recipes)
        logger.info(f"✅ [RECIPE] generate_menu_plan_with_history completed successfully")
        logger.debug(f"📊 [RECIPE] Menu plan with history result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in generate_menu_plan_with_history: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_recipe_from_web(recipe_title: str, num_results: int = 5, token: str = None) -> Dict[str, Any]:
    """
    Web検索によるレシピ検索
    
    Args:
        recipe_title: 検索するレシピタイトル
        num_results: 取得する結果数
        token: 認証トークン
    
    Returns:
        Dict[str, Any]: 検索結果のレシピリスト
    """
    logger.info(f"🔧 [RECIPE] Starting search_recipe_from_web for title: {recipe_title}, num_results: {num_results}")
    
    try:
        # Web検索クライアントを使用
        recipes = await search_client.search_recipes(recipe_title, num_results)
        logger.info(f"🔍 [RECIPE] Web search completed, found {len(recipes)} recipes")
        
        # レシピを優先順位でソート
        prioritized_recipes = prioritize_recipes(recipes)
        logger.info(f"📊 [RECIPE] Recipes prioritized")
        
        # 結果をフィルタリング
        filtered_recipes = filter_recipe_results(prioritized_recipes)
        logger.info(f"🔍 [RECIPE] Recipes filtered, final count: {len(filtered_recipes)}")
        
        result = {
            "success": True,
            "data": filtered_recipes,
            "total_count": len(filtered_recipes)
        }
        
        logger.info(f"✅ [RECIPE] search_recipe_from_web completed successfully")
        logger.debug(f"📊 [RECIPE] Web search result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in search_recipe_from_web: {e}")
        return {"success": False, "error": str(e)}



if __name__ == "__main__":
    logger.info("🚀 Starting Recipe MCP Server")
    mcp.run()
