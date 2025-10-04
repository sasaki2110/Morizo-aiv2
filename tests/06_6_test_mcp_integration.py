#!/usr/bin/env python3
"""
Morizo AI v2 - MCP Integration Test

This script tests the integration between different MCP servers.
"""

import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 環境変数の読み込み
load_dotenv()

# ロギングの初期化
from config.logging import setup_logging
setup_logging()

from config.loggers import GenericLogger

# ロガーの初期化
logger = GenericLogger("test", "mcp_integration")


async def get_test_user_id():
    """テスト用のユーザーIDを取得"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_util", os.path.join(project_root, "tests", "00_1_test_util.py"))
        test_util = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_util)
        
        # 認証トークンを取得
        token = test_util.get_auth_token()
        
        # トークンを検証してユーザー情報を取得
        user_info = test_util.verify_auth_token(token)
        
        if user_info:
            user_id = user_info.get('id')
            print(f"✅ [統合テスト] ユーザーID取得成功: {user_id}")
            logger.info(f"✅ [統合テスト] ユーザーID取得成功: {user_id}")
            return user_id
        else:
            raise ValueError("Failed to verify auth token")
            
    except Exception as e:
        print(f"❌ [統合テスト] ユーザーID取得エラー: {e}")
        logger.error(f"❌ [統合テスト] ユーザーID取得エラー: {e}")
        return None


async def test_inventory_list():
    """在庫一覧取得のテスト"""
    print("📦 [統合テスト] 在庫一覧を取得中...")
    logger.info("📦 [統合テスト] 在庫一覧を取得中...")
    
    try:
        # テスト用のユーザーIDを取得
        test_user_id = await get_test_user_id()
        if not test_user_id:
            return []
        
        # 直接CRUDクラスを使用
        from mcp_servers.inventory_crud import InventoryCRUD
        from mcp_servers.utils import get_authenticated_client
        crud = InventoryCRUD()
        
        client = get_authenticated_client(test_user_id)
        result = await crud.get_all_items(client, test_user_id)
        
        if result.get("success"):
            inventory_items = result.get("data", [])
            print(f"✅ [統合テスト] 在庫一覧取得成功: {len(inventory_items)}件")
            logger.info(f"✅ [統合テスト] 在庫一覧取得成功: {len(inventory_items)}件")
            
            # 在庫アイテムの表示
            for i, item in enumerate(inventory_items, 1):
                print(f"  {i}. {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')}")
                logger.info(f"📋 [統合テスト] 在庫アイテム {i}: {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')}")
            
            return inventory_items
        else:
            print(f"❌ [統合テスト] 在庫一覧取得失敗: {result.get('error', 'Unknown error')}")
            logger.error(f"❌ [統合テスト] 在庫一覧取得失敗: {result.get('error', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"❌ [統合テスト] 在庫一覧取得エラー: {e}")
        logger.error(f"❌ [統合テスト] 在庫一覧取得エラー: {e}")
        return []


async def test_menu_generation(inventory_items):
    """献立生成のテスト"""
    print("\n🍽️ [統合テスト] 献立生成中...")
    logger.info("🍽️ [統合テスト] 献立生成中...")
    
    try:
        # テスト用のユーザーIDを取得
        test_user_id = await get_test_user_id()
        if not test_user_id:
            return {}
        
        # 在庫アイテム名のリストを作成
        item_names = [item.get('item_name', '') for item in inventory_items if item.get('item_name')]
        
        # 直接LLMクライアントを使用
        from mcp_servers.recipe_llm import RecipeLLM
        llm_client = RecipeLLM()
        
        result = await llm_client.generate_menu_titles(
            inventory_items=item_names,
            menu_type="和食",
            excluded_recipes=[]
        )
        
        if result.get("success"):
            menu_data = result.get("data", {})
            print(f"✅ [統合テスト] 献立生成成功")
            logger.info(f"✅ [統合テスト] 献立生成成功")
            
            # 献立の表示
            main_dish = menu_data.get("main_dish", "")
            side_dish = menu_data.get("side_dish", "")
            soup = menu_data.get("soup", "")
            
            print(f"  【主菜】{main_dish}")
            print(f"  【副菜】{side_dish}")
            print(f"  【汁物】{soup}")
            
            logger.info(f"📋 [統合テスト] 主菜: {main_dish}")
            logger.info(f"📋 [統合テスト] 副菜: {side_dish}")
            logger.info(f"📋 [統合テスト] 汁物: {soup}")
            
            return {
                "main_dish": main_dish,
                "side_dish": side_dish,
                "soup": soup
            }
        else:
            print(f"❌ [統合テスト] 献立生成失敗: {result.get('error', 'Unknown error')}")
            logger.error(f"❌ [統合テスト] 献立生成失敗: {result.get('error', 'Unknown error')}")
            return {}
            
    except Exception as e:
        print(f"❌ [統合テスト] 献立生成エラー: {e}")
        logger.error(f"❌ [統合テスト] 献立生成エラー: {e}")
        return {}


async def test_recipe_search(menu_titles):
    """レシピ検索のテスト"""
    print("\n🌐 [統合テスト] レシピ検索中...")
    logger.info("🌐 [統合テスト] レシピ検索中...")
    
    try:
        # 献立タイトルのリストを作成（空文字を除外）
        recipe_titles = [title for title in menu_titles.values() if title]
        
        if not recipe_titles:
            print("⚠️ [統合テスト] 検索するレシピタイトルがありません")
            logger.warning("⚠️ [統合テスト] 検索するレシピタイトルがありません")
            return []
        
        # 直接WebSearchClientを使用
        from mcp_servers.recipe_web import GoogleSearchClient, prioritize_recipes, filter_recipe_results
        search_client = GoogleSearchClient()
        
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
        
        print(f"✅ [統合テスト] レシピ検索成功: {len(all_recipes)}件")
        logger.info(f"✅ [統合テスト] レシピ検索成功: {len(all_recipes)}件")
        
        # 検索結果の表示
        for i, recipe in enumerate(all_recipes, 1):
            print(f"\n{i}. {recipe.get('title', 'N/A')}")
            print(f"   URL: {recipe.get('url', 'N/A')}")
            print(f"   Site: {recipe.get('site', 'N/A')}")
            print(f"   Source: {recipe.get('source', 'N/A')}")
            print(f"   Search Title: {recipe.get('search_title', 'N/A')}")
            
            logger.info(f"📋 [統合テスト] レシピ {i}: {recipe.get('title', 'N/A')} from {recipe.get('source', 'N/A')}")
        
        return all_recipes
        
    except Exception as e:
        print(f"❌ [統合テスト] レシピ検索エラー: {e}")
        logger.error(f"❌ [統合テスト] レシピ検索エラー: {e}")
        return []


async def main():
    """メイン統合テスト関数"""
    print("🚀 Starting MCP Integration Tests")
    print("=" * 60)
    logger.info("🚀 [統合テスト] Starting MCP Integration Tests")
    
    # 1. 在庫一覧取得
    inventory_items = await test_inventory_list()
    
    if not inventory_items:
        print("\n⚠️ [統合テスト] 在庫一覧が取得できませんでした。テストを終了します。")
        logger.warning("⚠️ [統合テスト] 在庫一覧が取得できませんでした。テストを終了します。")
        return
    
    # 2. 献立生成
    menu_titles = await test_menu_generation(inventory_items)
    
    if not menu_titles:
        print("\n⚠️ [統合テスト] 献立が生成できませんでした。テストを終了します。")
        logger.warning("⚠️ [統合テスト] 献立が生成できませんでした。テストを終了します。")
        return
    
    # 3. レシピ検索
    recipe_results = await test_recipe_search(menu_titles)
    
    # テスト結果の要約
    print("\n" + "=" * 60)
    print("📊 Integration Test Results Summary:")
    print(f"✅ Inventory List: {len(inventory_items)} items found")
    print(f"✅ Menu Generation: {len([t for t in menu_titles.values() if t])} titles generated")
    print(f"✅ Recipe Search: {len(recipe_results)} recipes found")
    
    logger.info("📊 [統合テスト] Integration Test Results Summary:")
    logger.info(f"✅ [統合テスト] Inventory List: {len(inventory_items)} items found")
    logger.info(f"✅ [統合テスト] Menu Generation: {len([t for t in menu_titles.values() if t])} titles generated")
    logger.info(f"✅ [統合テスト] Recipe Search: {len(recipe_results)} recipes found")
    
    if inventory_items and menu_titles and recipe_results:
        print("\n🎉 All integration tests passed successfully!")
        logger.info("🎉 [統合テスト] All integration tests passed successfully!")
    else:
        print("\n⚠️ Some integration tests failed. Please check the error messages above.")
        logger.warning("⚠️ [統合テスト] Some integration tests failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
