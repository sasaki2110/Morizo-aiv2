#!/usr/bin/env python3
"""
Morizo AI v2 - Inventory List Integration Test

This module tests the inventory_list operation through MCP client integration.
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


async def test_inventory_list_integration():
    """Test inventory_list operation through MCP client integration"""
    logger = GenericLogger("test", "inventory_list_integration", initialize_logging=False)
    
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
        
        # デバッグ用：resultの型を確認
        logger.info(f"🔍 [DEBUG] Result type: {type(result)}")
        logger.info(f"🔍 [DEBUG] Result content: {result}")
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP inventory list successful: {result}")
            print(f"✅ [TEST] MCP inventory list successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", [])
                print(f"   Found {len(data)} inventory items:")
                
                if len(data) > 0:
                    for i, item in enumerate(data, 1):
                        print(f"   {i}. {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')} ({item.get('storage_location', 'N/A')})")
                        if item.get('expiry_date'):
                            print(f"      Expiry: {item.get('expiry_date')}")
                        print(f"      ID: {item.get('id', 'N/A')}")
                        print(f"      Created: {item.get('created_at', 'N/A')}")
                        print()
                else:
                    print("   No inventory items found.")
                
                logger.info(f"📊 [TEST] Retrieved {len(data)} inventory items")
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


async def test_inventory_list_by_name_integration():
    """Test inventory_list_by_name operation through MCP client integration"""
    logger = GenericLogger("test", "inventory_list_by_name_integration", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Inventory List by Name operation through MCP integration...")
    
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
        # 名前指定在庫一覧取得テスト（MCPクライアント経由）
        logger.info("🔍 [TEST] Testing inventory_list_by_name through MCP client...")
        
        # テスト用のアイテム名（実際のデータに合わせて調整）
        test_item_name = "牛乳"
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="inventory_list_by_name",
            parameters={
                "user_id": test_user_id,
                "item_name": test_item_name
            },
            token=token
        )
        
        # デバッグ用：resultの型を確認
        logger.info(f"🔍 [DEBUG] Result type: {type(result)}")
        logger.info(f"🔍 [DEBUG] Result content: {result}")
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP inventory list by name successful: {result}")
            print(f"✅ [TEST] MCP inventory list by name successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", [])
                print(f"   Found {len(data)} items matching '{test_item_name}':")
                
                if len(data) > 0:
                    for i, item in enumerate(data, 1):
                        print(f"   {i}. {item.get('item_name', 'N/A')} - {item.get('quantity', 0)}{item.get('unit', '')} ({item.get('storage_location', 'N/A')})")
                        if item.get('expiry_date'):
                            print(f"      Expiry: {item.get('expiry_date')}")
                        print(f"      ID: {item.get('id', 'N/A')}")
                        print(f"      Created: {item.get('created_at', 'N/A')}")
                        print()
                else:
                    print(f"   No items found matching '{test_item_name}'.")
                
                logger.info(f"📊 [TEST] Retrieved {len(data)} items matching '{test_item_name}'")
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


async def test_inventory_get_integration():
    """Test inventory_get operation through MCP client integration"""
    logger = GenericLogger("test", "inventory_get_integration", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Inventory Get operation through MCP integration...")
    
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
        # まず在庫一覧を取得して、有効なIDを取得
        logger.info("🔍 [TEST] Getting inventory list to find valid item ID...")
        
        list_result = await mcp_client.call_tool(
            tool_name="inventory_list",
            parameters={
                "user_id": test_user_id
            },
            token=token
        )
        
        if not list_result.get("success"):
            logger.error("❌ [TEST] Failed to get inventory list for ID lookup")
            return False
        
        list_data = list_result.get("result", {}).get("data", [])
        
        if not list_data:
            logger.info("ℹ️ [TEST] No inventory items found, skipping inventory_get test")
            print("ℹ️ [TEST] No inventory items found, skipping inventory_get test")
            return True
        
        # 最初のアイテムのIDを使用
        test_item_id = list_data[0].get('id')
        if not test_item_id:
            logger.error("❌ [TEST] No valid item ID found in inventory list")
            return False
        
        logger.info(f"✅ [TEST] Using item ID for test: {test_item_id}")
        
        # 特定アイテム取得テスト（MCPクライアント経由）
        logger.info("🔍 [TEST] Testing inventory_get through MCP client...")
        
        # MCPツール呼び出し
        result = await mcp_client.call_tool(
            tool_name="inventory_get",
            parameters={
                "user_id": test_user_id,
                "item_id": test_item_id
            },
            token=token
        )
        
        # デバッグ用：resultの型を確認
        logger.info(f"🔍 [DEBUG] Result type: {type(result)}")
        logger.info(f"🔍 [DEBUG] Result content: {result}")
        
        if result.get("success"):
            logger.info(f"✅ [TEST] MCP inventory get successful: {result}")
            print(f"✅ [TEST] MCP inventory get successful")
            
            # 結果の詳細表示
            tool_result = result.get("result", {})
            if tool_result.get("success"):
                data = tool_result.get("data", {})
                if data:
                    print(f"   Item Details:")
                    print(f"   - Name: {data.get('item_name', 'N/A')}")
                    print(f"   - Quantity: {data.get('quantity', 0)}{data.get('unit', '')}")
                    print(f"   - Storage: {data.get('storage_location', 'N/A')}")
                    if data.get('expiry_date'):
                        print(f"   - Expiry: {data.get('expiry_date')}")
                    print(f"   - ID: {data.get('id', 'N/A')}")
                    print(f"   - Created: {data.get('created_at', 'N/A')}")
                else:
                    print("   No item data found.")
                
                logger.info(f"📊 [TEST] Retrieved item details for ID: {test_item_id}")
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
    # ロギング設定（1回だけ実行）
    setup_logging()
    
    print("🚀 Starting Inventory List Integration Test")
    print("=" * 60)
    
    # 1. 在庫一覧取得テスト
    print("\n📋 Testing Inventory List through MCP...")
    list_success = await test_inventory_list_integration()
    
    # 2. 名前指定在庫一覧取得テスト
    print("\n🔍 Testing Inventory List by Name through MCP...")
    list_by_name_success = await test_inventory_list_by_name_integration()
    
    # 3. 特定アイテム取得テスト
    print("\n🔍 Testing Inventory Get through MCP...")
    get_success = await test_inventory_get_integration()
    
    print("\n" + "=" * 60)
    if list_success and list_by_name_success and get_success:
        print("🎉 Inventory List Integration Test completed successfully!")
        print("✅ MCP client integration is working properly")
        print("✅ All inventory list operations are functioning correctly")
    else:
        print("⚠️ Inventory List Integration Test failed. Please check the error messages above.")
        if not list_success:
            print("❌ Inventory List test failed")
        if not list_by_name_success:
            print("❌ Inventory List by Name test failed")
        if not get_success:
            print("❌ Inventory Get test failed")


if __name__ == "__main__":
    asyncio.run(main())
