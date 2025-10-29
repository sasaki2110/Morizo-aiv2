"""
Morizo AI v2 - Recipe MCP Server

This module provides MCP server for recipe generation with LLM-based tools.
"""

import sys
import os
import asyncio
# プロジェクトルートをPythonのモジュール検索パスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from fastmcp import FastMCP

from mcp_servers.recipe_llm import RecipeLLM
from mcp_servers.recipe_rag import RecipeRAGClient
from mcp_servers.recipe_web import search_client, prioritize_recipes, filter_recipe_results
from mcp_servers.utils import get_authenticated_client
from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()

# MCPサーバー初期化
mcp = FastMCP("Recipe MCP Server")

# 処理クラスのインスタンス
llm_client = RecipeLLM()
rag_client = RecipeRAGClient()
logger = GenericLogger("mcp", "recipe_server", initialize_logging=False)

# 手動でログハンドラーを設定
from config.logging import get_logger
import logging

# ルートロガーを取得してハンドラーを設定
root_logger = logging.getLogger('morizo_ai')
if not root_logger.handlers:
    from config.logging import setup_logging
    setup_logging(initialize=False)  # ローテーションなし


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
    menu_type: str = "",
    excluded_recipes: List[str] = None,
    token: str = None
) -> Dict[str, Any]:
    """
    LLM推論による独創的な献立プラン生成（履歴考慮）
    
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
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        result = await llm_client.generate_menu_titles(inventory_items, menu_type, excluded_recipes)
        logger.info(f"✅ [RECIPE] generate_menu_plan_with_history completed successfully")
        logger.debug(f"📊 [RECIPE] Menu plan with history result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in generate_menu_plan_with_history: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_menu_from_rag_with_history(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "",
    excluded_recipes: List[str] = None,
    token: str = None
) -> Dict[str, Any]:
    """
    RAG検索による伝統的な献立タイトル生成
    
    Args:
        inventory_items: 在庫食材リスト
        user_id: ユーザーID
        menu_type: 献立のタイプ
        excluded_recipes: 除外するレシピタイトル
    
    Returns:
        {
            "candidates": [
                {
                    "main_dish": {"title": "牛乳と卵のフレンチトースト", "ingredients": ["牛乳", "卵", "パン"]},
                    "side_dish": {"title": "ほうれん草の胡麻和え", "ingredients": ["ほうれん草", "胡麻"]},
                    "soup": {"title": "白菜とハムのクリームスープ", "ingredients": ["白菜", "ハム", "牛乳"]}
                }
            ],
            "selected": {
                "main_dish": {"title": "牛乳と卵のフレンチトースト", "ingredients": ["牛乳", "卵", "パン"]},
                "side_dish": {"title": "ほうれん草の胡麻和え", "ingredients": ["ほうれん草", "胡麻"]},
                "soup": {"title": "白菜とハムのクリームスープ", "ingredients": ["白菜", "ハム", "牛乳"]}
            }
        }
    """
    logger.info(f"🔧 [RECIPE] Starting search_menu_from_rag_with_history for user: {user_id}, menu_type: {menu_type}")
    
    try:
        # 認証済みクライアントを取得（一貫性のため）
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        # RAG検索を実行（3ベクトルDB対応）
        categorized_results = await rag_client.search_recipes_by_category(
            ingredients=inventory_items,
            menu_type=menu_type,
            excluded_recipes=excluded_recipes,
            limit=10  # 多めに取得して献立構成に使用
        )
        
        logger.info(f"🔍 [RECIPE] RAG search completed, found categorized results")
        logger.info(f"🔍 [RECIPE] Main: {len(categorized_results.get('main', []))} recipes")
        logger.info(f"🔍 [RECIPE] Sub: {len(categorized_results.get('sub', []))} recipes")
        logger.info(f"🔍 [RECIPE] Soup: {len(categorized_results.get('soup', []))} recipes")
        
        # RAG検索結果を献立形式に変換（3ベクトルDB対応）
        try:
            logger.info(f"🔄 [RECIPE] Starting convert_categorized_results_to_menu_format")
            menu_result = await rag_client.convert_categorized_results_to_menu_format(
                categorized_results=categorized_results,
                inventory_items=inventory_items,
                menu_type=menu_type
            )
            logger.info(f"✅ [RECIPE] convert_categorized_results_to_menu_format completed")
        except Exception as e:
            logger.error(f"❌ [RECIPE] Error in convert_categorized_results_to_menu_format: {e}")
            logger.error(f"❌ [RECIPE] Categorized results: {categorized_results}")
            raise
        
        logger.info(f"✅ [RECIPE] search_menu_from_rag_with_history completed successfully")
        logger.debug(f"📊 [RECIPE] RAG menu result: {menu_result}")
        
        # 1件の献立のみを返す（LLM推論と合わせて計2件をユーザーに提示）
        selected_menu = menu_result.get("selected", {})
        
        # generate_menu_plan_with_historyと同じ形式に統一
        formatted_data = {
            "main_dish": selected_menu.get("main_dish", {}).get("title", ""),
            "side_dish": selected_menu.get("side_dish", {}).get("title", ""),
            "soup": selected_menu.get("soup", {}).get("title", ""),
            "ingredients_used": []
        }
        
        return {
            "success": True,
            "data": formatted_data
        }
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in search_menu_from_rag_with_history: {e}")
        return {"success": False, "error": str(e)}


def extract_recipe_titles_from_proposals(proposals_result: Dict[str, Any]) -> List[str]:
    """主菜提案結果からレシピタイトルを抽出"""
    titles = []
    
    if proposals_result.get("success") and "data" in proposals_result:
        data = proposals_result["data"]
        if "candidates" in data:
            candidates = data["candidates"]
            for candidate in candidates:
                if isinstance(candidate, dict) and "title" in candidate:
                    titles.append(candidate["title"])
                elif isinstance(candidate, str):
                    titles.append(candidate)
    
    return titles


@mcp.tool()
async def search_recipe_from_web(
    recipe_titles: List[str], 
    num_results: int = 5, 
    user_id: str = "", 
    token: str = None,
    menu_categories: List[str] = None,
    menu_source: str = "mixed"
) -> Dict[str, Any]:
    """
    Web検索によるレシピ検索（主菜提案対応・複数料理名対応・並列実行・詳細分類）
    
    Args:
        recipe_titles: 検索するレシピタイトルのリスト（主菜提案結果のcandidatesから抽出可能）
        num_results: 各料理名あたりの取得結果数
        user_id: ユーザーID（一貫性のため受け取るが使用しない）
        token: 認証トークン
        menu_categories: 料理名の分類リスト（main_dish, side_dish, soup）
        menu_source: 検索元（llm, rag, mixed）
    
    Returns:
        Dict[str, Any]: 分類された検索結果のレシピリスト（画像URL含む）
    """
    logger.info(f"🔧 [RECIPE] Starting search_recipe_from_web for {len(recipe_titles)} titles: {recipe_titles}, num_results: {num_results}")
    logger.info(f"📊 [RECIPE] Menu categories: {menu_categories}, source: {menu_source}")
    
    try:
        import asyncio
        
        async def search_single_recipe(title: str) -> Dict[str, Any]:
            """単一の料理名でレシピ検索"""
            try:
                # Web検索クライアントを使用
                recipes = await search_client.search_recipes(title, num_results)
                logger.info(f"🔍 [RECIPE] Web search completed for '{title}', found {len(recipes)} recipes")
                
                # レシピを優先順位でソート
                prioritized_recipes = prioritize_recipes(recipes)
                logger.info(f"📊 [RECIPE] Recipes prioritized for '{title}'")
                
                # 結果をフィルタリング
                filtered_recipes = filter_recipe_results(prioritized_recipes)
                logger.info(f"🔍 [RECIPE] Recipes filtered for '{title}', final count: {len(filtered_recipes)}")
                
                return {
                    "success": True,
                    "data": filtered_recipes,
                    "title": title,
                    "count": len(filtered_recipes)
                }
                
            except Exception as e:
                logger.error(f"❌ [RECIPE] Error searching for '{title}': {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "title": title,
                    "count": 0
                }
        
        # 並列実行
        tasks = [search_single_recipe(title) for title in recipe_titles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を分類別に整理
        categorized_results = {
            "llm_menu": {
                "main_dish": {"title": "", "recipes": []},
                "side_dish": {"title": "", "recipes": []},
                "soup": {"title": "", "recipes": []}
            },
            "rag_menu": {
                "main_dish": {"title": "", "recipes": []},
                "side_dish": {"title": "", "recipes": []},
                "soup": {"title": "", "recipes": []}
            }
        }
        
        successful_searches = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ [RECIPE] Search failed for '{recipe_titles[i]}': {result}")
                continue
            elif result.get("success"):
                recipes = result.get("data", [])
                successful_searches += 1
                logger.info(f"✅ [RECIPE] Found {len(recipes)} recipes for '{recipe_titles[i]}'")
                
                # 分類情報を取得
                category = "main_dish"  # デフォルト
                source = "llm_menu"     # デフォルト
                
                if menu_categories and i < len(menu_categories):
                    category = menu_categories[i]
                
                # 検索元の判定（簡易版：インデックスベース）
                if menu_source == "rag" or (menu_source == "mixed" and i >= len(recipe_titles) // 2):
                    source = "rag_menu"
                
                # 結果を分類
                categorized_results[source][category] = {
                    "title": recipe_titles[i],
                    "recipes": recipes
                }
            else:
                logger.error(f"❌ [RECIPE] Search failed for '{recipe_titles[i]}': {result.get('error')}")
        
        logger.info(f"✅ [RECIPE] Recipe search completed: {successful_searches}/{len(recipe_titles)} successful")
        
        result = {
            "success": True,
            "data": categorized_results,
            "total_count": sum(len(cat["recipes"]) for menu in categorized_results.values() for cat in menu.values()),
            "searches_completed": successful_searches,
            "total_searches": len(recipe_titles)
        }
        
        logger.info(f"✅ [RECIPE] search_recipe_from_web completed successfully")
        logger.debug(f"📊 [RECIPE] Web search result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in search_recipe_from_web: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_proposals(
    inventory_items: List[str],
    user_id: str,
    category: str = "main",  # "main", "sub", "soup"
    menu_type: str = "",
    main_ingredient: Optional[str] = None,
    used_ingredients: List[str] = None,
    excluded_recipes: List[str] = None,
    menu_category: str = "japanese",  # "japanese", "western", "chinese"
    sse_session_id: str = None,
    token: str = None
) -> Dict[str, Any]:
    """
    汎用提案メソッド（主菜・副菜・汁物対応）
    
    Args:
        category: "main", "sub", "soup"
        used_ingredients: すでに使った食材（副菜・汁物で使用）
        menu_category: 献立カテゴリ（汁物の判断に使用）
    """
    logger.info(f"🔧 [RECIPE] Starting generate_proposals")
    logger.info(f"  Category: {category}, User: {user_id}")
    logger.info(f"  Main ingredient: {main_ingredient}, Used ingredients: {used_ingredients}")
    logger.info(f"  Excluded recipes: {len(excluded_recipes or [])} recipes")
    
    try:
        # 認証済みクライアントを取得
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        # Phase 3A: セッション内の提案済みレシピは、呼び出し元でexcluded_recipesとして渡されるため
        # MCPサーバー内では追加処理は不要（プロセス分離のため）
        all_excluded = (excluded_recipes or []).copy()
        logger.info(f"📝 [RECIPE] Total excluded: {len(all_excluded)} recipes")
        
        # LLMとRAGを並列実行（汎用メソッドを使用）
        llm_task = llm_client.generate_candidates(
            inventory_items=inventory_items,
            menu_type=menu_type,
            category=category,
            main_ingredient=main_ingredient,
            used_ingredients=used_ingredients,
            excluded_recipes=all_excluded,
            count=2
        )
        rag_task = rag_client.search_candidates(
            ingredients=inventory_items,
            menu_type=menu_type,
            category=category,
            main_ingredient=main_ingredient,
            used_ingredients=used_ingredients,
            excluded_recipes=all_excluded,
            limit=3
        )
        
        # 両方の結果を待つ（並列実行）
        llm_result, rag_result = await asyncio.gather(llm_task, rag_task)
        
        # 統合
        candidates = []
        if llm_result.get("success"):
            candidates.extend(llm_result["data"]["candidates"])
        if rag_result:
            candidates.extend([{"title": r["title"], "ingredients": r.get("ingredients", [])} for r in rag_result])
        
        logger.info(f"✅ [RECIPE] generate_proposals completed: {len(candidates)} candidates")
        
        return {
            "success": True,
            "data": {
                "candidates": candidates,
                "category": category,
                "total": len(candidates),
                "main_ingredient": main_ingredient,
                "excluded_count": len(all_excluded),
                "llm_count": len(llm_result.get("data", {}).get("candidates", [])),
                "rag_count": len(rag_result)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in generate_proposals: {e}")
        return {"success": False, "error": str(e)}




if __name__ == "__main__":
    logger.info("🚀 Starting Recipe MCP Server")
    mcp.run()
