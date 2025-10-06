#!/usr/bin/env python3
"""
05_2_test_service_integration.py

サービス層統合テスト（06_6_test_mcp_integration.pyと同等）
- 実際のToolRouter使用
- 実際のSupabase認証
- ローテーション機能付きロガー
- サービス層経由でのMCP通信テスト
- 4段階フロー: 在庫取得 → LLM推論 → RAG検索 → WEB検索
"""

import asyncio
import os
import sys
import importlib.util
from datetime import datetime
from typing import Dict, Any, List, Optional

# プロジェクトルートを取得
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# ロガー設定（後でmain()で初期化）
from config.loggers import GenericLogger

# グローバルロガー変数（main()で初期化）
logger = None

# テストユーティリティ
spec = importlib.util.spec_from_file_location("test_util", os.path.join(project_root, "tests", "00_1_test_util.py"))
test_util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_util)

# サービス層インポート
from services.tool_router import ToolRouter
from services.recipe_service import RecipeService
from services.inventory_service import InventoryService


async def get_test_user_id():
    """テスト用のユーザーIDと認証トークンを取得"""
    try:
        # 認証トークンを取得
        token = test_util.get_auth_token()
        
        # トークンを検証してユーザー情報を取得
        user_info = test_util.verify_auth_token(token)
        
        if user_info:
            user_id = user_info.get('id')
            print(f"✅ [統合テスト] ユーザーID取得成功: {user_id}")
            logger.info(f"✅ [統合テスト] ユーザーID取得成功: {user_id}")
            return user_id, token
        else:
            raise ValueError("Failed to verify auth token")
            
    except Exception as e:
        print(f"❌ [統合テスト] ユーザーID取得エラー: {e}")
        logger.error(f"❌ [統合テスト] ユーザーID取得エラー: {e}")
        return None, None


async def test_service_inventory_list():
    """サービス層経由での在庫一覧取得（06_6と同等）"""
    print("📦 [統合テスト] 在庫一覧を取得中...")
    logger.info("📦 [統合テスト] 在庫一覧を取得中...")
    
    try:
        # テスト用のユーザーIDと認証トークンを取得
        user_id, token = await get_test_user_id()
        if not user_id or not token:
            return []
        
        # ToolRouter初期化
        tool_router = ToolRouter()
        
        # InventoryService初期化
        inventory_service = InventoryService(tool_router)
        
        # サービス層経由で在庫取得
        result = await inventory_service.get_inventory(user_id, token)
        
        if result.get("success"):
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                inventory_items = tool_result.get("data", [])
                print(f"✅ [統合テスト] 在庫一覧取得成功: {len(inventory_items)}件")
                logger.info(f"✅ [統合テスト] 在庫一覧取得成功: {len(inventory_items)}件")
                
                # 在庫アイテムの表示
                for i, item in enumerate(inventory_items, 1):
                    print(f"  {i}. {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')}")
                    logger.info(f"📦 [統合テスト] 在庫アイテム {i}: {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')}")
                
                return inventory_items
            else:
                print(f"❌ [統合テスト] 在庫一覧取得失敗: {tool_result.get('error', 'Unknown error')}")
                logger.error(f"❌ [統合テスト] 在庫一覧取得失敗: {tool_result.get('error', 'Unknown error')}")
                return []
        else:
            print(f"❌ [統合テスト] サービス呼び出し失敗: {result.get('error', 'Unknown error')}")
            logger.error(f"❌ [統合テスト] サービス呼び出し失敗: {result.get('error', 'Unknown error')}")
            return []
            
    except Exception as e:
        print(f"❌ [統合テスト] 在庫一覧取得エラー: {e}")
        logger.error(f"❌ [統合テスト] 在庫一覧取得エラー: {e}")
        return []


async def test_service_menu_generation(inventory_items):
    """サービス層経由でのLLM献立生成（06_6と同等）"""
    print("\n🍽️ [統合テスト] LLM献立生成中...")
    logger.info("🍽️ [統合テスト] LLM献立生成中...")
    
    try:
        # テスト用のユーザーIDと認証トークンを取得
        user_id, token = await get_test_user_id()
        if not user_id or not token:
            return {}
        
        # 在庫アイテム名のリストを作成
        item_names = [item.get('item_name', '') for item in inventory_items if item.get('item_name')]
        
        # ToolRouter初期化
        tool_router = ToolRouter()
        
        # RecipeService初期化
        recipe_service = RecipeService(tool_router)
        
        # サービス層経由で献立生成
        result = await recipe_service.generate_menu_plan(
            inventory_items=item_names,
            user_id=user_id,
            menu_type="和食",
            token=token
        )
        
        if result.get("success"):
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                menu_data = tool_result.get("data", {})
                print(f"✅ [統合テスト] LLM献立生成成功")
                logger.info(f"✅ [統合テスト] LLM献立生成成功")
                
                # 献立の表示
                main_dish = menu_data.get("main_dish", "")
                side_dish = menu_data.get("side_dish", "")
                soup = menu_data.get("soup", "")
                
                print(f"  【主菜】{main_dish}")
                print(f"  【副菜】{side_dish}")
                print(f"  【汁物】{soup}")
                
                logger.info(f"📦 [統合テスト] LLM主菜: {main_dish}")
                logger.info(f"📦 [統合テスト] LLM副菜: {side_dish}")
                logger.info(f"📦 [統合テスト] LLM汁物: {soup}")
                
                return {
                    "main_dish": main_dish,
                    "side_dish": side_dish,
                    "soup": soup
                }
            else:
                print(f"❌ [統合テスト] LLM献立生成失敗: {tool_result.get('error', 'Unknown error')}")
                logger.error(f"❌ [統合テスト] LLM献立生成失敗: {tool_result.get('error', 'Unknown error')}")
                return {}
        else:
            print(f"❌ [統合テスト] LLM献立生成サービス呼び出し失敗: {result.get('error', 'Unknown error')}")
            logger.error(f"❌ [統合テスト] LLM献立生成サービス呼び出し失敗: {result.get('error', 'Unknown error')}")
            return {}
            
    except Exception as e:
        print(f"❌ [統合テスト] LLM献立生成エラー: {e}")
        logger.error(f"❌ [統合テスト] LLM献立生成エラー: {e}")
        return {}


async def test_service_rag_menu_generation(inventory_items):
    """サービス層経由でのRAG献立検索（06_6と同等）"""
    print("\n🔍 [統合テスト] RAG検索による献立生成中...")
    logger.info("🔍 [統合テスト] RAG検索による献立生成中...")
    
    try:
        # テスト用のユーザーIDと認証トークンを取得
        user_id, token = await get_test_user_id()
        if not user_id or not token:
            return {}
        
        # 在庫アイテム名のリストを作成
        item_names = [item.get('item_name', '') for item in inventory_items if item.get('item_name')]
        
        # ToolRouter初期化
        tool_router = ToolRouter()
        
        # RecipeService初期化
        recipe_service = RecipeService(tool_router)
        
        # サービス層経由でRAG検索
        result = await recipe_service.search_menu_from_rag(
            inventory_items=item_names,
            user_id=user_id,
            menu_type="和食",
            token=token
        )
        
        if result.get("success"):
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                menu_data = tool_result.get("data", {})
                print(f"✅ [統合テスト] RAG検索による献立生成成功")
                logger.info(f"✅ [統合テスト] RAG検索による献立生成成功")
                
                # 献立の表示
                main_dish = menu_data.get("main_dish", "")
                side_dish = menu_data.get("side_dish", "")
                soup = menu_data.get("soup", "")
                
                print(f"  【主菜】{main_dish}")
                print(f"  【副菜】{side_dish}")
                print(f"  【汁物】{soup}")
                
                logger.info(f"📦 [統合テスト] RAG主菜: {main_dish}")
                logger.info(f"📦 [統合テスト] RAG副菜: {side_dish}")
                logger.info(f"📦 [統合テスト] RAG汁物: {soup}")
                
                return {
                    "main_dish": main_dish,
                    "side_dish": side_dish,
                    "soup": soup,
                    "full_data": menu_data
                }
            else:
                print(f"❌ [統合テスト] RAG検索による献立生成失敗: {tool_result.get('error', 'Unknown error')}")
                logger.error(f"❌ [統合テスト] RAG検索による献立生成失敗: {tool_result.get('error', 'Unknown error')}")
                return {}
        else:
            print(f"❌ [統合テスト] RAG検索サービス呼び出し失敗: {result.get('error', 'Unknown error')}")
            logger.error(f"❌ [統合テスト] RAG検索サービス呼び出し失敗: {result.get('error', 'Unknown error')}")
            return {}
            
    except Exception as e:
        print(f"❌ [統合テスト] RAG検索による献立生成エラー: {e}")
        logger.error(f"❌ [統合テスト] RAG検索による献立生成エラー: {e}")
        return {}


async def test_service_recipe_search(menu_titles):
    """サービス層経由でのレシピ検索（06_6と同等）"""
    print("\n🌐 [統合テスト] レシピ検索中...")
    logger.info("🌐 [統合テスト] レシピ検索中...")
    
    try:
        # テスト用のユーザーIDと認証トークンを取得
        user_id, token = await get_test_user_id()
        if not user_id or not token:
            return []
        
        # 献立タイトルのリストを作成（空文字を除外）
        recipe_titles = [title for title in menu_titles.values() if title]
        
        if not recipe_titles:
            print("⚠️ [統合テスト] 検索するレシピタイトルがありません")
            logger.warning("⚠️ [統合テスト] 検索するレシピタイトルがありません")
            return []
        
        # ToolRouter初期化
        tool_router = ToolRouter()
        
        # RecipeService初期化
        recipe_service = RecipeService(tool_router)
        
        all_recipes = []
        
        # 各タイトルに対して検索を実行
        for title in recipe_titles:
            print(f"  🔍 Searching for: {title}")
            logger.info(f"🔍 [統合テスト] Searching for recipe: {title}")
            
            # サービス層経由でWeb検索
            result = await recipe_service.search_recipes_from_web(
                recipe_title=title,
                num_results=3,
                token=token
            )
            
            if result.get("success"):
                tool_result = result.get("result", {})
                if tool_result.get("success"):
                    data = tool_result.get("data", [])
                    
                    print(f"  ✅ Found {len(data)} recipes for '{title}':")
                    print(f"  {'='*50}")
                    
                    for i, recipe in enumerate(data, 1):
                        print(f"  【レシピ {i}】")
                        print(f"  📖 タイトル: {recipe.get('title', 'N/A')}")
                        print(f"  🔗 URL: {recipe.get('url', 'N/A')}")
                        print(f"  📍 ソース: {recipe.get('source', 'N/A')}")
                        print(f"  {'-'*30}")
                    
                    # ログにも整形して出力
                    logger.info(f"✅ [統合テスト] Retrieved {len(data)} recipes for '{title}':")
                    for i, recipe in enumerate(data, 1):
                        logger.info(f"   Recipe {i}: {recipe.get('title', 'N/A')} - {recipe.get('url', 'N/A')}")
                    
                    all_recipes.extend(data)
                else:
                    print(f"  ❌ Search failed for '{title}': {tool_result.get('error', 'Unknown error')}")
                    logger.error(f"❌ [統合テスト] Search failed for '{title}': {tool_result.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ Service call failed for '{title}': {result.get('error', 'Unknown error')}")
                logger.error(f"❌ [統合テスト] Service call failed for '{title}': {result.get('error', 'Unknown error')}")
        
        print(f"\n  📊 Total recipes found: {len(all_recipes)}")
        logger.info(f"📊 [統合テスト] Total recipes found across all searches: {len(all_recipes)}")
        
        return all_recipes
        
    except Exception as e:
        print(f"❌ [統合テスト] レシピ検索エラー: {e}")
        logger.error(f"❌ [統合テスト] レシピ検索エラー: {e}")
        return []


async def main():
    """メインテスト実行（06_6_test_mcp_integration.pyと同等の統合フロー）"""
    print("🚀 Starting Service Layer Integration Tests")
    print("=" * 60)
    
    # ログ設定の初期化（ローテーション）
    from config.logging import setup_logging
    setup_logging(initialize=True)
    
    # グローバルロガーの初期化
    global logger
    logger = GenericLogger("test", "service_integration", initialize_logging=False)
    logger.info("🚀 [統合テスト] Starting Service Layer Integration Tests")
    
    # 1. 在庫一覧取得（サービス層経由）
    inventory_items = await test_service_inventory_list()
    
    if not inventory_items:
        print("\n⚠️ [統合テスト] 在庫一覧が取得できませんでした。テストを終了します。")
        logger.warning("⚠️ [統合テスト] 在庫一覧が取得できませんでした。テストを終了します。")
        return
    
    # 2. LLM推論による献立生成（サービス層経由）
    llm_menu = await test_service_menu_generation(inventory_items)
    
    if not llm_menu:
        print("\n⚠️ [統合テスト] LLM推論による献立が生成できませんでした。")
        logger.warning("⚠️ [統合テスト] LLM推論による献立が生成できませんでした。")
        llm_menu = {}
    
    # 3. RAG検索による献立生成（サービス層経由）
    rag_menu = await test_service_rag_menu_generation(inventory_items)
    
    if not rag_menu:
        print("\n⚠️ [統合テスト] RAG検索による献立が生成できませんでした。")
        logger.warning("⚠️ [統合テスト] RAG検索による献立が生成できませんでした。")
        rag_menu = {}
    
    # 4. WEB検索（LLMとRAGの両方のタイトルで検索）
    all_titles = {}
    
    # LLM推論結果のタイトルを追加
    if llm_menu:
        all_titles.update({
            "llm_main": llm_menu.get("main_dish", ""),
            "llm_side": llm_menu.get("side_dish", ""),
            "llm_soup": llm_menu.get("soup", "")
        })
    
    # RAG検索結果のタイトルを追加
    if rag_menu:
        all_titles.update({
            "rag_main": rag_menu.get("main_dish", ""),
            "rag_side": rag_menu.get("side_dish", ""),
            "rag_soup": rag_menu.get("soup", "")
        })
    
    recipe_results = await test_service_recipe_search(all_titles)
    
    # テスト結果の要約
    print("\n" + "=" * 60)
    print("📊 Service Layer Integration Test Results Summary:")
    print(f"✅ Inventory List: {len(inventory_items)} items found")
    
    # LLM推論結果の表示
    llm_titles_count = len([t for t in [llm_menu.get("main_dish", ""), llm_menu.get("side_dish", ""), llm_menu.get("soup", "")] if t])
    print(f"✅ LLM Menu Generation: {llm_titles_count} titles generated")
    
    # RAG検索結果の表示
    rag_titles_count = len([t for t in [rag_menu.get("main_dish", ""), rag_menu.get("side_dish", ""), rag_menu.get("soup", "")] if t])
    print(f"✅ RAG Menu Generation: {rag_titles_count} titles generated")
    
    print(f"✅ Recipe Search: {len(recipe_results)} recipes found")
    
    # LLMとRAGの比較表示
    if llm_menu and rag_menu:
        print("\n" + "=" * 60)
        print("🔄 LLM vs RAG Comparison:")
        print(f"  【主菜】LLM: {llm_menu.get('main_dish', 'N/A')} | RAG: {rag_menu.get('main_dish', 'N/A')}")
        print(f"  【副菜】LLM: {llm_menu.get('side_dish', 'N/A')} | RAG: {rag_menu.get('side_dish', 'N/A')}")
        print(f"  【汁物】LLM: {llm_menu.get('soup', 'N/A')} | RAG: {rag_menu.get('soup', 'N/A')}")
    
    logger.info("📊 [統合テスト] Service Layer Integration Test Results Summary:")
    logger.info(f"✅ [統合テスト] Inventory List: {len(inventory_items)} items found")
    logger.info(f"✅ [統合テスト] LLM Menu Generation: {llm_titles_count} titles generated")
    logger.info(f"✅ [統合テスト] RAG Menu Generation: {rag_titles_count} titles generated")
    logger.info(f"✅ [統合テスト] Recipe Search: {len(recipe_results)} recipes found")
    
    # 成功判定
    success_count = 0
    total_tests = 4
    
    if inventory_items:
        success_count += 1
    if llm_menu:
        success_count += 1
    if rag_menu:
        success_count += 1
    if recipe_results:
        success_count += 1
    
    print(f"\n📈 Test Success Rate: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("\n🎉 All service layer integration tests passed successfully!")
        logger.info("🎉 [統合テスト] All service layer integration tests passed successfully!")
    elif success_count >= 3:
        print("\n✅ Most service layer integration tests passed successfully!")
        logger.info("✅ [統合テスト] Most service layer integration tests passed successfully!")
    else:
        print("\n⚠️ Some service layer integration tests failed. Please check the error messages above.")
        logger.warning("⚠️ [統合テスト] Some service layer integration tests failed. Please check the error messages above.")
    
    return success_count == total_tests


if __name__ == "__main__":
    # ローテーション機能付きロガーでテスト実行
    asyncio.run(main())
