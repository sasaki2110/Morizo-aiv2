#!/usr/bin/env python3
"""
Morizo AI v2 - Inventory Add Integration Test

This module tests the inventory_add operation through MCP client integration.
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
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp"))
from client import MCPClient
from config.loggers import GenericLogger
from config.logging import setup_logging


async def test_inventory_add_integration():
    """Test inventory_add operation through MCP client integration"""
    # ロギング設定
    setup_logging()
    logger = GenericLogger("test", "inventory_add_integration")
    
    logger.info("🧪 [TEST] Testing Inventory Add operation through MCP integration...")
    
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
        # 在庫追加テスト（MCPクライアント経由）
        logger.info("📦 [TEST] Testing inventory_add through MCP client...")
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="inventory_add",
            parameters={
                "user_id": test_user_id,
                "item_name": "テスト用牛乳（MCP統合）",
                "quantity": 1.0,
                "unit": "本",
                "storage_location": "冷蔵庫",
                "expiry_date": "2025-01-15"
            },
            token=token
        )
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP inventory add successful: {result}")
            print(f"✅ [TEST] MCP inventory add successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", {})
                print(f"   Item ID: {data.get('id', 'N/A')}")
                print(f"   Item Name: {data.get('item_name', 'N/A')}")
                print(f"   Quantity: {data.get('quantity', 'N/A')}")
                print(f"   Unit: {data.get('unit', 'N/A')}")
                print(f"   Storage: {data.get('storage_location', 'N/A')}")
                print(f"   Expiry: {data.get('expiry_date', 'N/A')}")
                print(f"   Created: {data.get('created_at', 'N/A')}")
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


async def test_inventory_list_integration():
    """Test inventory_list operation through MCP client integration"""
    # ロギング設定
    setup_logging()
    logger = GenericLogger("test", "inventory_list_integration")
    
    logger.info("🧪 [TEST] Testing Inventory List operation through MCP integration...")
    
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
        # 在庫一覧取得テスト（MCPクライアント経由）
        logger.info("📋 [TEST] Testing inventory_list through MCP client...")
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="inventory_list",
            parameters={
                "user_id": test_user_id
            },
            token=token
        )
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP inventory list successful: {result}")
            print(f"✅ [TEST] MCP inventory list successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", [])
                print(f"   Found {len(data)} inventory items:")
                for i, item in enumerate(data, 1):
                    print(f"   {i}. {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')} ({item.get('storage_location', 'N/A')})")
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


async def main():
    """メインテスト関数"""
    print("🚀 Starting Inventory Add Integration Test")
    print("=" * 60)
    
    # 1. 在庫追加テスト
    print("\n📦 Testing Inventory Add through MCP...")
    add_success = await test_inventory_add_integration()
    
    # 2. 在庫一覧取得テスト
    print("\n📋 Testing Inventory List through MCP...")
    list_success = await test_inventory_list_integration()
    
    print("\n" + "=" * 60)
    if add_success and list_success:
        print("🎉 Inventory Add Integration Test completed successfully!")
        print("✅ MCP client integration is working properly")
    else:
        print("⚠️ Inventory Add Integration Test failed. Please check the error messages above.")
        if not add_success:
            print("❌ Inventory Add test failed")
        if not list_success:
            print("❌ Inventory List test failed")


if __name__ == "__main__":
    asyncio.run(main())