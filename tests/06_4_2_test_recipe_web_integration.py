#!/usr/bin/env python3
"""
Morizo AI v2 - Recipe Web Integration Test

This module tests the search_recipe_from_web operation through MCP client integration.
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 認証ユーティリティのインポート
sys.path.append(os.path.join(os.path.dirname(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("test_util", os.path.join(os.path.dirname(__file__), "00_1_test_util.py"))
test_util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_util)

# MCPクライアントのインポート
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_servers"))
from client import MCPClient
from config.loggers import GenericLogger
from config.logging import setup_logging


async def test_search_recipe_from_web_integration():
    """Test search_recipe_from_web operation through MCP client integration"""
    logger = GenericLogger("test", "recipe_web_integration", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe Web Search through MCP integration...")
    
    # 認証トークン取得
    token = test_util.get_auth_token()
    
    # 認証済みユーザーIDを取得
    user_info = test_util.verify_auth_token(token)
    if not user_info:
        logger.error("❌ [TEST] Failed to get user info from token")
        return False
    
    test_user_id = user_info['id']
    logger.info(f"✅ [TEST] Using authenticated user ID: {test_user_id}")
    
    # MCPクライアント作成
    mcp_client = MCPClient()
    
    try:
        # テスト用のレシピタイトルリスト
        test_recipe_titles = [
            "ハムとほうれん草のオムレツ",
            "白菜の胡麻和え", 
            "バター風味の牛乳スープ"
        ]
        
        print(f"\n🍽️ Testing Recipe Web Search for {len(test_recipe_titles)} recipes:")
        logger.info(f"🍽️ [TEST] Testing recipe web search for titles: {test_recipe_titles}")
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="search_recipe_from_web",
            parameters={
                "recipe_title": test_recipe_titles[0],  # 最初のレシピタイトルをテスト
                "num_results": 3
            },
            token=token
        )
        
        # デバッグ用：resultの型を確認
        logger.info(f"🔍 [DEBUG] Result type: {type(result)}")
        logger.info(f"🔍 [DEBUG] Result content: {result}")
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP recipe web search successful: {result}")
            print(f"✅ [TEST] MCP recipe web search successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", [])
                
                print(f"   Web Search Results:")
                print(f"   ==================")
                
                if data and len(data) > 0:
                    print(f"   📊 Found {len(data)} recipes for '{test_recipe_titles[0]}':")
                    print(f"   {'='*60}")
                    
                    for i, recipe in enumerate(data, 1):
                        print(f"   【レシピ {i}】")
                        print(f"   📝 タイトル: {recipe.get('title', 'N/A')}")
                        print(f"   🔗 URL: {recipe.get('url', 'N/A')}")
                        print(f"   📍 ソース: {recipe.get('source', 'N/A')}")
                        if recipe.get('description'):
                            desc = recipe.get('description', '')
                            if len(desc) > 100:
                                desc = desc[:100] + "..."
                            print(f"   📄 説明: {desc}")
                        print(f"   {'-'*40}")
                    
                    # ログにも整形して出力
                    logger.info(f"📊 [TEST] Retrieved {len(data)} web recipes successfully:")
                    for i, recipe in enumerate(data, 1):
                        logger.info(f"   Recipe {i}: {recipe.get('title', 'N/A')} - {recipe.get('url', 'N/A')}")
                    return True
                else:
                    print(f"   ⚠️ No recipes found for '{test_recipe_titles[0]}'")
                    logger.warning(f"⚠️ [TEST] No recipes found for '{test_recipe_titles[0]}'")
                    return False
            else:
                logger.error(f"❌ [TEST] MCP tool execution failed: {tool_result}")
                print(f"❌ [TEST] MCP tool execution failed: {tool_result}")
                return False
        else:
            logger.error(f"❌ [TEST] MCP client call failed: {result}")
            print(f"❌ [TEST] MCP client call failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [TEST] MCP integration test exception: {e}")
        print(f"❌ [TEST] MCP integration test exception: {e}")
        return False
    finally:
        # リソースのクリーンアップ
        mcp_client.cleanup()


async def test_search_multiple_recipes():
    """Test search_recipe_from_web with multiple recipe titles"""
    logger = GenericLogger("test", "recipe_web_multiple", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe Web Search with multiple recipes...")
    
    # 認証トークン取得
    token = test_util.get_auth_token()
    
    # 認証済みユーザーIDを取得
    user_info = test_util.verify_auth_token(token)
    if not user_info:
        logger.error("❌ [TEST] Failed to get user info from token")
        return False
    
    test_user_id = user_info['id']
    logger.info(f"✅ [TEST] Using authenticated user ID: {test_user_id}")
    
    # MCPクライアント作成
    mcp_client = MCPClient()
    
    try:
        # テスト用のレシピタイトルリスト
        test_recipe_titles = [
            "ハムとほうれん草のオムレツ",
            "白菜の胡麻和え", 
            "バター風味の牛乳スープ"
        ]
        
        print(f"\n🍽️ Testing Recipe Web Search for multiple recipes:")
        logger.info(f"🍽️ [TEST] Testing recipe web search for multiple titles: {test_recipe_titles}")
        
        all_results = []
        
        # 各レシピタイトルに対して検索を実行
        for recipe_title in test_recipe_titles:
            print(f"\n   🔍 Searching for: {recipe_title}")
            logger.info(f"🔍 [TEST] Searching for recipe: {recipe_title}")
            
            # MCPツール呼び出し
            result = await mcp_client.call_tool(
                tool_name="search_recipe_from_web",
                parameters={
                    "recipe_title": recipe_title,
                    "num_results": 3
                },
                token=token
            )
            
            if result.get("success"):
                tool_result = result.get("result", {})
                if tool_result.get("success"):
                    data = tool_result.get("data", [])
                    
                    print(f"   ✅ Found {len(data)} recipes for '{recipe_title}':")
                    print(f"   {'='*50}")
                    
                    for i, recipe in enumerate(data, 1):
                        print(f"   【レシピ {i}】")
                        print(f"   📝 タイトル: {recipe.get('title', 'N/A')}")
                        print(f"   🔗 URL: {recipe.get('url', 'N/A')}")
                        print(f"   📍 ソース: {recipe.get('source', 'N/A')}")
                        print(f"   {'-'*30}")
                    
                    # ログにも整形して出力
                    logger.info(f"✅ [TEST] Retrieved {len(data)} recipes for '{recipe_title}':")
                    for i, recipe in enumerate(data, 1):
                        logger.info(f"   Recipe {i}: {recipe.get('title', 'N/A')} - {recipe.get('url', 'N/A')}")
                    
                    all_results.extend(data)
                else:
                    print(f"   ❌ Search failed for '{recipe_title}': {tool_result}")
                    logger.error(f"❌ [TEST] Search failed for '{recipe_title}': {tool_result}")
            else:
                print(f"   ❌ MCP call failed for '{recipe_title}': {result}")
                logger.error(f"❌ [TEST] MCP call failed for '{recipe_title}': {result}")
        
        print(f"\n   📊 Total recipes found: {len(all_results)}")
        logger.info(f"📊 [TEST] Total recipes found across all searches: {len(all_results)}")
        
        return len(all_results) > 0
        
    except Exception as e:
        logger.error(f"❌ [TEST] Multiple recipe search exception: {e}")
        print(f"❌ [TEST] Multiple recipe search exception: {e}")
        return False
    finally:
        # リソースのクリーンアップ
        mcp_client.cleanup()


async def main():
    """メインテスト関数"""
    # ロギング設定（1回だけ実行）
    setup_logging()
    
    print("🚀 Starting Recipe Web Integration Test")
    print("=" * 60)
    
    # 1. 基本的なレシピ検索テスト
    print("\n🔍 Testing Recipe Web Search through MCP...")
    basic_success = await test_search_recipe_from_web_integration()
    
    # 2. 複数レシピ検索テスト
    print("\n🔍 Testing Recipe Web Search with multiple recipes...")
    multiple_success = await test_search_multiple_recipes()
    
    print("\n" + "=" * 60)
    if basic_success and multiple_success:
        print("🎉 Recipe Web Integration Test completed successfully!")
        print("✅ MCP client integration is working properly")
        print("✅ Recipe web search is functioning correctly")
        print("✅ Multiple recipe search works")
    else:
        print("⚠️ Recipe Web Integration Test failed. Please check the error messages above.")
        if not basic_success:
            print("❌ Basic recipe web search test failed")
        if not multiple_success:
            print("❌ Multiple recipe search test failed")


if __name__ == "__main__":
    asyncio.run(main())
