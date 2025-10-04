#!/usr/bin/env python3
"""
Morizo AI v2 - Recipe Web Search Test

This script tests the web search functionality for recipe retrieval.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 環境変数の読み込み
load_dotenv()

# ロギングの初期化
from config.logging import setup_logging
setup_logging()

from mcp.recipe_web import GoogleSearchClient, prioritize_recipes, filter_recipe_results
from config.loggers import GenericLogger

# ロガーの初期化
logger = GenericLogger("test", "recipe_web")


async def test_google_search_client():
    """GoogleSearchClientのテスト"""
    print("🧪 Testing GoogleSearchClient...")
    logger.info("🧪 [TEST] Testing GoogleSearchClient...")
    
    try:
        # クライアントの初期化
        client = GoogleSearchClient()
        print("✅ GoogleSearchClient initialized successfully")
        logger.info("✅ [TEST] GoogleSearchClient initialized successfully")
        
        # 検索テスト
        test_title = "フレンチトースト"
        print(f"🔍 Searching for: {test_title}")
        logger.info(f"🔍 [TEST] Searching for: {test_title}")
        
        recipes = await client.search_recipes(test_title, num_results=3)
        print(f"📊 Found {len(recipes)} recipes")
        logger.info(f"📊 [TEST] Found {len(recipes)} recipes")
        
        # 結果の表示
        for i, recipe in enumerate(recipes, 1):
            print(f"\n{i}. {recipe['title']}")
            print(f"   URL: {recipe['url']}")
            print(f"   Site: {recipe['site']}")
            print(f"   Source: {recipe['source']}")
            print(f"   Description: {recipe['description'][:100]}...")
            logger.info(f"📋 [TEST] Recipe {i}: {recipe['title']} from {recipe['source']}")
        
        return recipes
        
    except Exception as e:
        print(f"❌ Error testing GoogleSearchClient: {e}")
        logger.error(f"❌ [TEST] Error testing GoogleSearchClient: {e}")
        return []


def test_recipe_filtering():
    """レシピフィルタリングのテスト"""
    print("\n🧪 Testing recipe filtering...")
    logger.info("🧪 [TEST] Testing recipe filtering...")
    
    # テストデータ
    test_recipes = [
        {
            'title': 'フレンチトースト',
            'url': 'https://cookpad.com/recipe/123456',
            'site': 'cookpad.com',
            'source': 'Cookpad',
            'description': '美味しいフレンチトーストの作り方'
        },
        {
            'title': 'オムライス',
            'url': 'https://example.com/recipe/789',
            'site': 'other',
            'source': 'Unknown',
            'description': 'オムライスの作り方'
        },
        {
            'title': 'カレーライス',
            'url': 'https://kurashiru.com/recipe/456789',
            'site': 'kurashiru.com',
            'source': 'クラシル',
            'description': '簡単カレーライス'
        }
    ]
    
    # フィルタリングテスト
    filtered = filter_recipe_results(test_recipes)
    print(f"📊 Filtered {len(filtered)} recipes from {len(test_recipes)}")
    logger.info(f"📊 [TEST] Filtered {len(filtered)} recipes from {len(test_recipes)}")
    
    # 優先順位付けテスト
    prioritized = prioritize_recipes(filtered)
    print(f"📊 Prioritized {len(prioritized)} recipes")
    logger.info(f"📊 [TEST] Prioritized {len(prioritized)} recipes")
    
    # 結果の表示
    for i, recipe in enumerate(prioritized, 1):
        print(f"{i}. {recipe['title']} ({recipe['source']})")
        logger.info(f"📋 [TEST] Prioritized recipe {i}: {recipe['title']} ({recipe['source']})")
    
    return prioritized


async def test_mcp_integration():
    """MCP統合のテスト"""
    print("\n🧪 Testing MCP integration...")
    logger.info("🧪 [TEST] Testing MCP integration...")
    
    try:
        # 直接GoogleSearchClientを使用してテスト
        client = GoogleSearchClient()
        
        # テスト用のレシピタイトル
        test_titles = ["フレンチトースト", "オムライス"]
        
        print(f"🔍 Searching for recipes: {test_titles}")
        logger.info(f"🔍 [TEST] Searching for recipes: {test_titles}")
        
        all_recipes = []
        
        # 各タイトルに対して検索を実行
        for title in test_titles:
            recipes = await client.search_recipes(title, num_results=3)
            
            # レシピをフィルタリング・優先順位付け
            filtered_recipes = filter_recipe_results(recipes)
            prioritized_recipes = prioritize_recipes(filtered_recipes)
            
            # タイトル情報を追加
            for recipe in prioritized_recipes:
                recipe['search_title'] = title
            
            all_recipes.extend(prioritized_recipes)
        
        print(f"📊 Found {len(all_recipes)} recipes from MCP simulation")
        logger.info(f"📊 [TEST] Found {len(all_recipes)} recipes from MCP simulation")
        
        # 結果の表示
        for i, recipe in enumerate(all_recipes, 1):
            print(f"\n{i}. {recipe['title']}")
            print(f"   Search Title: {recipe.get('search_title', 'N/A')}")
            print(f"   URL: {recipe['url']}")
            print(f"   Site: {recipe['site']}")
            print(f"   Source: {recipe['source']}")
            logger.info(f"📋 [TEST] MCP Recipe {i}: {recipe['title']} from {recipe['source']}")
        
        return all_recipes
        
    except Exception as e:
        print(f"❌ Error testing MCP integration: {e}")
        logger.error(f"❌ [TEST] Error testing MCP integration: {e}")
        return []


def test_environment_variables():
    """環境変数のテスト"""
    print("\n🧪 Testing environment variables...")
    logger.info("🧪 [TEST] Testing environment variables...")
    
    required_vars = [
        'GOOGLE_SEARCH_API_KEY',
        'GOOGLE_SEARCH_ENGINE_ID',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set the required environment variables in .env file")
        logger.error(f"❌ [TEST] Missing environment variables: {missing_vars}")
        return False
    else:
        print("✅ All required environment variables are set")
        logger.info("✅ [TEST] All required environment variables are set")
        return True


async def main():
    """メインテスト関数"""
    print("🚀 Starting Recipe Web Search Tests")
    print("=" * 50)
    logger.info("🚀 [TEST] Starting Recipe Web Search Tests")
    
    # 環境変数のテスト
    env_ok = test_environment_variables()
    if not env_ok:
        print("\n⚠️  Environment variables not set. Some tests will be skipped.")
        print("Please refer to ENVIRONMENT_SETUP.md for setup instructions.")
        logger.warning("⚠️ [TEST] Environment variables not set. Some tests will be skipped.")
        return
    
    # GoogleSearchClientのテスト
    recipes = await test_google_search_client()
    
    # レシピフィルタリングのテスト
    filtered_recipes = test_recipe_filtering()
    
    # MCP統合のテスト
    mcp_recipes = await test_mcp_integration()
    
    # テスト結果の要約
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"✅ GoogleSearchClient: {len(recipes)} recipes found")
    print(f"✅ Recipe Filtering: {len(filtered_recipes)} recipes filtered")
    print(f"✅ MCP Integration: {len(mcp_recipes)} recipes from MCP")
    
    logger.info("📊 [TEST] Test Results Summary:")
    logger.info(f"✅ [TEST] GoogleSearchClient: {len(recipes)} recipes found")
    logger.info(f"✅ [TEST] Recipe Filtering: {len(filtered_recipes)} recipes filtered")
    logger.info(f"✅ [TEST] MCP Integration: {len(mcp_recipes)} recipes from MCP")
    
    if recipes and filtered_recipes and mcp_recipes:
        print("\n🎉 All tests passed successfully!")
        logger.info("🎉 [TEST] All tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
        logger.warning("⚠️ [TEST] Some tests failed. Please check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
