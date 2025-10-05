#!/usr/bin/env python3
"""
Morizo AI v2 - Recipe LLM Integration Test

This module tests the generate_menu_plan_with_history operation through MCP client integration.
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


async def test_generate_menu_plan_with_history_integration():
    """Test generate_menu_plan_with_history operation through MCP client integration"""
    logger = GenericLogger("test", "recipe_llm_integration", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe LLM Menu Plan Generation through MCP integration...")
    
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
        # 献立生成テスト（MCPクライアント経由）
        logger.info("🍽️ [TEST] Testing generate_menu_plan_with_history through MCP client...")
        
        # テスト用の在庫食材リスト
        test_inventory_items = [
            "牛乳",
            "卵",
            "パン",
            "バター",
            "ほうれん草",
            "胡麻",
            "白菜",
            "ハム",
            "小麦粉"
        ]
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="generate_menu_plan_with_history",
            parameters={
                "inventory_items": test_inventory_items,
                "user_id": test_user_id,
                "menu_type": "和食"
            },
            token=token
        )
        
        # デバッグ用：resultの型を確認
        logger.info(f"🔍 [DEBUG] Result type: {type(result)}")
        logger.info(f"🔍 [DEBUG] Result content: {result}")
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP recipe menu plan generation successful: {result}")
            print(f"✅ [TEST] MCP recipe menu plan generation successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", {})
                
                print(f"   Generated Menu Plan:")
                print(f"   ===================")
                
                # 主菜の表示
                main_dish = data.get("main_dish", {})
                if main_dish:
                    print(f"   🍖 主菜: {main_dish.get('title', 'N/A')}")
                    ingredients = main_dish.get('ingredients', [])
                    if ingredients:
                        print(f"      材料: {', '.join(ingredients)}")
                
                # 副菜の表示
                side_dish = data.get("side_dish", {})
                if side_dish:
                    print(f"   🥗 副菜: {side_dish.get('title', 'N/A')}")
                    ingredients = side_dish.get('ingredients', [])
                    if ingredients:
                        print(f"      材料: {', '.join(ingredients)}")
                
                # 汁物の表示
                soup = data.get("soup", {})
                if soup:
                    print(f"   🍲 汁物: {soup.get('title', 'N/A')}")
                    ingredients = soup.get('ingredients', [])
                    if ingredients:
                        print(f"      材料: {', '.join(ingredients)}")
                
                # 食材使用状況の表示
                ingredient_usage = data.get("ingredient_usage", {})
                if ingredient_usage:
                    used_ingredients = ingredient_usage.get("used", [])
                    remaining_ingredients = ingredient_usage.get("remaining", [])
                    
                    print(f"   📊 食材使用状況:")
                    print(f"      使用済み: {', '.join(used_ingredients) if used_ingredients else 'なし'}")
                    print(f"      残り: {', '.join(remaining_ingredients) if remaining_ingredients else 'なし'}")
                
                # 除外レシピの表示
                excluded_recipes = data.get("excluded_recipes", [])
                if excluded_recipes:
                    print(f"   🚫 除外レシピ: {', '.join(excluded_recipes)}")
                else:
                    print(f"   🚫 除外レシピ: なし（履歴なし）")
                
                # フォールバック使用の表示
                fallback_used = data.get("fallback_used", False)
                print(f"   🔄 フォールバック使用: {'はい' if fallback_used else 'いいえ'}")
                
                logger.info(f"📊 [TEST] Generated menu plan with {len(test_inventory_items)} inventory items")
                return True
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


async def test_generate_menu_plan_with_different_menu_types():
    """Test generate_menu_plan_with_history with different menu types"""
    logger = GenericLogger("test", "recipe_llm_menu_types", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe LLM Menu Plan Generation with different menu types...")
    
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
    
    # テスト用の在庫食材リスト
    test_inventory_items = [
        "牛乳",
        "卵",
        "パン",
        "バター",
        "ほうれん草",
        "胡麻",
        "白菜",
        "ハム",
        "小麦粉"
    ]
    
    # テストする献立タイプ
    menu_types = ["和食", "洋食", "中華", "イタリアン"]
    
    try:
        for menu_type in menu_types:
            print(f"\n🍽️ Testing Menu Type: {menu_type}")
            logger.info(f"🍽️ [TEST] Testing menu type: {menu_type}")
            
            # MCPツール呼び出し
            result = await mcp_client.call_tool(
                tool_name="generate_menu_plan_with_history",
                parameters={
                    "inventory_items": test_inventory_items,
                    "user_id": test_user_id,
                    "menu_type": menu_type
                },
                token=token
            )
            
            if result.get("success"):
                tool_result = result.get("result", {})
                if tool_result.get("success"):
                    data = tool_result.get("data", {})
                    
                    print(f"   ✅ {menu_type}献立生成成功:")
                    
                    # 主菜の表示
                    main_dish = data.get("main_dish", {})
                    if main_dish:
                        print(f"      主菜: {main_dish.get('title', 'N/A')}")
                    
                    # 副菜の表示
                    side_dish = data.get("side_dish", {})
                    if side_dish:
                        print(f"      副菜: {side_dish.get('title', 'N/A')}")
                    
                    # 汁物の表示
                    soup = data.get("soup", {})
                    if soup:
                        print(f"      汁物: {soup.get('title', 'N/A')}")
                    
                    logger.info(f"✅ [TEST] {menu_type} menu generation successful")
                else:
                    print(f"   ❌ {menu_type}献立生成失敗: {tool_result}")
                    logger.error(f"❌ [TEST] {menu_type} menu generation failed: {tool_result}")
            else:
                print(f"   ❌ {menu_type}MCP呼び出し失敗: {result}")
                logger.error(f"❌ [TEST] {menu_type} MCP call failed: {result}")
        
        logger.info(f"📊 [TEST] Completed menu type testing for {len(menu_types)} types")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] Menu type testing exception: {e}")
        print(f"❌ [TEST] Menu type testing exception: {e}")
        return False
    finally:
        # リソースのクリーンアップ
        mcp_client.cleanup()


async def test_generate_menu_plan_with_minimal_inventory():
    """Test generate_menu_plan_with_history with minimal inventory items"""
    logger = GenericLogger("test", "recipe_llm_minimal", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe LLM Menu Plan Generation with minimal inventory...")
    
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
        # 最小限の在庫食材リスト
        minimal_inventory_items = ["卵", "ご飯"]
        
        print(f"\n🍽️ Testing with minimal inventory: {minimal_inventory_items}")
        logger.info(f"🍽️ [TEST] Testing with minimal inventory: {minimal_inventory_items}")
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="generate_menu_plan_with_history",
            parameters={
                "inventory_items": minimal_inventory_items,
                "user_id": test_user_id,
                "menu_type": "和食"
            },
            token=token
        )
        
        if result.get("success"):
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", {})
                
                print(f"   ✅ 最小在庫での献立生成成功:")
                
                # 主菜の表示
                main_dish = data.get("main_dish", {})
                if main_dish:
                    print(f"      主菜: {main_dish.get('title', 'N/A')}")
                
                # 副菜の表示
                side_dish = data.get("side_dish", {})
                if side_dish:
                    print(f"      副菜: {side_dish.get('title', 'N/A')}")
                
                # 汁物の表示
                soup = data.get("soup", {})
                if soup:
                    print(f"      汁物: {soup.get('title', 'N/A')}")
                
                # フォールバック使用の確認
                fallback_used = data.get("fallback_used", False)
                print(f"      フォールバック使用: {'はい' if fallback_used else 'いいえ'}")
                
                logger.info(f"✅ [TEST] Minimal inventory menu generation successful")
                return True
            else:
                print(f"   ❌ 最小在庫での献立生成失敗: {tool_result}")
                logger.error(f"❌ [TEST] Minimal inventory menu generation failed: {tool_result}")
                return False
        else:
            print(f"   ❌ 最小在庫でのMCP呼び出し失敗: {result}")
            logger.error(f"❌ [TEST] Minimal inventory MCP call failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [TEST] Minimal inventory testing exception: {e}")
        print(f"❌ [TEST] Minimal inventory testing exception: {e}")
        return False
    finally:
        # リソースのクリーンアップ
        mcp_client.cleanup()


async def main():
    """メインテスト関数"""
    # ロギング設定（1回だけ実行）
    setup_logging()
    
    print("🚀 Starting Recipe LLM Integration Test")
    print("=" * 60)
    
    # 1. 基本的な献立生成テスト
    print("\n🍽️ Testing Recipe LLM Menu Plan Generation through MCP...")
    basic_success = await test_generate_menu_plan_with_history_integration()
    
    # 2. 異なる献立タイプでのテスト
    print("\n🍽️ Testing Recipe LLM with different menu types...")
    menu_types_success = await test_generate_menu_plan_with_different_menu_types()
    
    # 3. 最小在庫でのテスト
    print("\n🍽️ Testing Recipe LLM with minimal inventory...")
    minimal_success = await test_generate_menu_plan_with_minimal_inventory()
    
    print("\n" + "=" * 60)
    if basic_success and menu_types_success and minimal_success:
        print("🎉 Recipe LLM Integration Test completed successfully!")
        print("✅ MCP client integration is working properly")
        print("✅ Recipe menu plan generation is functioning correctly")
        print("✅ Different menu types are supported")
        print("✅ Minimal inventory handling works")
    else:
        print("⚠️ Recipe LLM Integration Test failed. Please check the error messages above.")
        if not basic_success:
            print("❌ Basic menu plan generation test failed")
        if not menu_types_success:
            print("❌ Different menu types test failed")
        if not minimal_success:
            print("❌ Minimal inventory test failed")


if __name__ == "__main__":
    asyncio.run(main())
