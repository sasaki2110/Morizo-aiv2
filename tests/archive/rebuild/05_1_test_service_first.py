#!/usr/bin/env python3
"""
Morizo AI v2 - Service Layer First Test

サービス層の初回テスト
ToolRouter経由でinventory_listを実行して動作確認
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

from config.loggers import GenericLogger

# 認証ユーティリティのインポート
import importlib.util
spec = importlib.util.spec_from_file_location("test_util", os.path.join(project_root, "tests", "00_1_test_util.py"))
test_util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_util)

# サービス層のインポート
from services.tool_router import ToolRouter

# ロガーの初期化
logger = GenericLogger("test", "service_first")


async def test_service_layer_inventory_list():
    """サービス層のinventory_listテスト"""
    
    logger.info("🧪 [SERVICE_TEST] Starting service layer inventory_list test...")
    print("🧪 [SERVICE_TEST] Starting service layer inventory_list test...")
    
    try:
        # 1. 認証トークン取得
        logger.info("🔐 [SERVICE_TEST] Getting authentication token...")
        print("🔐 [SERVICE_TEST] Getting authentication token...")
        
        token = test_util.get_auth_token()
        user_info = test_util.verify_auth_token(token)
        
        if not user_info:
            raise ValueError("Failed to verify authentication token")
        
        user_id = user_info.get('id')
        logger.info(f"✅ [SERVICE_TEST] Authentication successful, user_id: {user_id}")
        print(f"✅ [SERVICE_TEST] Authentication successful, user_id: {user_id}")
        
        # 2. ToolRouter初期化
        logger.info("🔧 [SERVICE_TEST] Initializing ToolRouter...")
        print("🔧 [SERVICE_TEST] Initializing ToolRouter...")
        
        tool_router = ToolRouter()
        
        # 利用可能なツールを確認
        available_tools = tool_router.get_available_tools()
        logger.info(f"📋 [SERVICE_TEST] Available tools: {len(available_tools)} tools")
        print(f"📋 [SERVICE_TEST] Available tools: {len(available_tools)} tools")
        
        # inventory_listツールが存在するかチェック
        if "inventory_list" not in available_tools:
            raise ValueError("inventory_list tool not found in available tools")
        
        logger.info("✅ [SERVICE_TEST] ToolRouter initialized successfully")
        print("✅ [SERVICE_TEST] ToolRouter initialized successfully")
        
        # 3. inventory_list実行
        logger.info("🔧 [SERVICE_TEST] Executing inventory_list...")
        print("🔧 [SERVICE_TEST] Executing inventory_list...")
        
        result = await tool_router.route_tool(
            "inventory_list",
            {"user_id": user_id},
            token
        )
        
        # 4. 結果確認
        logger.info(f"📊 [SERVICE_TEST] Test result: {result}")
        print(f"📊 [SERVICE_TEST] Test result: {result}")
        
        if result.get("success"):
            logger.info("✅ [SERVICE_TEST] inventory_list executed successfully!")
            print("✅ [SERVICE_TEST] inventory_list executed successfully!")
            
            # 結果の詳細をログ出力
            result_data = result.get("result", {})
            logger.info(f"📋 [SERVICE_TEST] Result data: {result_data}")
            print(f"📋 [SERVICE_TEST] Result data: {result_data}")
            
        else:
            logger.error(f"❌ [SERVICE_TEST] inventory_list failed: {result.get('error')}")
            print(f"❌ [SERVICE_TEST] inventory_list failed: {result.get('error')}")
            return False
        
        logger.info("🎉 [SERVICE_TEST] Service layer test completed successfully!")
        print("🎉 [SERVICE_TEST] Service layer test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ [SERVICE_TEST] Test failed with error: {e}")
        print(f"❌ [SERVICE_TEST] Test failed with error: {e}")
        return False


async def test_tool_router_basic():
    """ToolRouterの基本動作テスト"""
    
    logger.info("🧪 [TOOL_ROUTER_TEST] Starting ToolRouter basic test...")
    print("🧪 [TOOL_ROUTER_TEST] Starting ToolRouter basic test...")
    
    try:
        # ToolRouter初期化
        tool_router = ToolRouter()
        
        # 利用可能なツール一覧を取得
        available_tools = tool_router.get_available_tools()
        logger.info(f"📋 [TOOL_ROUTER_TEST] Available tools count: {len(available_tools)}")
        print(f"📋 [TOOL_ROUTER_TEST] Available tools count: {len(available_tools)}")
        
        # ツール説明を取得
        tool_descriptions = tool_router.get_tool_descriptions()
        logger.info(f"📝 [TOOL_ROUTER_TEST] Tool descriptions count: {len(tool_descriptions)}")
        print(f"📝 [TOOL_ROUTER_TEST] Tool descriptions count: {len(tool_descriptions)}")
        
        # inventory_listツールのサーバー情報を取得
        server_name = tool_router.get_tool_server("inventory_list")
        logger.info(f"🔧 [TOOL_ROUTER_TEST] inventory_list server: {server_name}")
        print(f"🔧 [TOOL_ROUTER_TEST] inventory_list server: {server_name}")
        
        # 無効なツール名のテスト
        invalid_server = tool_router.get_tool_server("invalid_tool")
        expected_result = None
        if invalid_server == expected_result:
            logger.info(f"✅ [TOOL_ROUTER_TEST] invalid_tool server: {invalid_server} (Expected: {expected_result})")
            print(f"✅ [TOOL_ROUTER_TEST] invalid_tool server: {invalid_server} (Expected: {expected_result})")
        else:
            logger.error(f"❌ [TOOL_ROUTER_TEST] invalid_tool server: {invalid_server} (Expected: {expected_result})")
            print(f"❌ [TOOL_ROUTER_TEST] invalid_tool server: {invalid_server} (Expected: {expected_result})")
        
        logger.info("✅ [TOOL_ROUTER_TEST] ToolRouter basic test completed successfully!")
        print("✅ [TOOL_ROUTER_TEST] ToolRouter basic test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ [TOOL_ROUTER_TEST] Test failed with error: {e}")
        print(f"❌ [TOOL_ROUTER_TEST] Test failed with error: {e}")
        return False


async def main():
    """メインテスト実行"""
    
    logger.info("🚀 [MAIN] Starting service layer tests...")
    print("🚀 [MAIN] Starting service layer tests...")
    
    # テスト1: ToolRouter基本動作テスト
    test1_result = await test_tool_router_basic()
    
    # テスト2: inventory_list実行テスト
    test2_result = await test_service_layer_inventory_list()
    
    # 結果サマリー
    logger.info("📊 [MAIN] Test Results Summary:")
    print("📊 [MAIN] Test Results Summary:")
    logger.info(f"  - ToolRouter Basic Test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"  - ToolRouter Basic Test: {'✅ PASS' if test1_result else '❌ FAIL'}")
    logger.info(f"  - inventory_list Test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    print(f"  - inventory_list Test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        logger.info("🎉 [MAIN] All tests passed! Service layer is working correctly.")
        print("🎉 [MAIN] All tests passed! Service layer is working correctly.")
    else:
        logger.error("❌ [MAIN] Some tests failed. Please check the logs.")
        print("❌ [MAIN] Some tests failed. Please check the logs.")


if __name__ == "__main__":
    # テスト実行
    asyncio.run(main())
