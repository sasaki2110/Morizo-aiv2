"""
Morizo AI v2 - Inventory CRUD Tests

This module tests basic CRUD operations for inventory management.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 認証ユーティリティのインポート
sys.path.append(os.path.join(os.path.dirname(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("test_util", os.path.join(os.path.dirname(__file__), "00_1_test_util.py"))
test_util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_util)

# モジュールのインポート
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp"))
from inventory_crud import InventoryCRUD
from config.loggers import GenericLogger
from config.logging import setup_logging


async def test_inventory_crud():
    """Test basic CRUD operations"""
    # ロギング設定（初期化なし）
    setup_logging(initialize=False)
    logger = GenericLogger("test", "inventory_crud")
    
    logger.info("🧪 [TEST] Testing Inventory CRUD operations...")
    
    # 認証トークン取得
    token = test_util.get_auth_token()
    client = test_util.get_authenticated_client(token)
    
    # 認証済みユーザーIDを取得
    user_info = test_util.verify_auth_token(token)
    if not user_info:
        logger.error("❌ [TEST] Failed to get user info from token")
        return False
    
    test_user_id = user_info['id']
    logger.info(f"✅ [TEST] Using authenticated user ID: {test_user_id}")
    
    # CRUDインスタンス作成
    crud = InventoryCRUD()
    
    try:
        # 1. 在庫追加テスト
        logger.info("📦 [TEST] Testing inventory_add...")
        add_result = await crud.add_item(
            client=client,
            user_id=test_user_id,
            item_name="テスト牛乳",
            quantity=1.0,
            unit="本",
            storage_location="冷蔵庫",
            expiry_date="2025-01-30"
        )
        
        if add_result["success"]:
            logger.info("✅ [TEST] inventory_add test passed")
            test_item_id = add_result["data"]["id"]
            logger.info(f"📦 [TEST] Added test item: {test_item_id}")
        else:
            logger.error(f"❌ [TEST] inventory_add test failed: {add_result['error']}")
            return False
        
        # 2. 在庫一覧取得テスト
        logger.info("📋 [TEST] Testing inventory_list...")
        list_result = await crud.get_all_items(client, test_user_id)
        
        if list_result["success"]:
            logger.info(f"✅ [TEST] inventory_list test passed - Found {len(list_result['data'])} items")
            logger.info(f"📋 Retrieved {len(list_result['data'])} items")
        else:
            logger.error(f"❌ [TEST] inventory_list test failed: {list_result['error']}")
            return False
        
        # 3. 名前指定取得テスト
        logger.info("🔍 [TEST] Testing inventory_list_by_name...")
        name_result = await crud.get_items_by_name(client, test_user_id, "テスト牛乳")
        
        if name_result["success"]:
            logger.info(f"✅ [TEST] inventory_list_by_name test passed - Found {len(name_result['data'])} items")
            logger.info(f"🔍 Found {len(name_result['data'])} items by name")
        else:
            logger.error(f"❌ [TEST] inventory_list_by_name test failed: {name_result['error']}")
            return False
        
        # 4. ID指定取得テスト
        logger.info("🔍 [TEST] Testing inventory_get...")
        get_result = await crud.get_item_by_id(client, test_user_id, test_item_id)
        
        if get_result["success"]:
            logger.info("✅ [TEST] inventory_get test passed")
            logger.info(f"🔍 Retrieved item by ID: {test_item_id}")
        else:
            logger.error(f"❌ [TEST] inventory_get test failed: {get_result['error']}")
            return False
        
        # 5. 在庫更新テスト
        logger.info("✏️ [TEST] Testing inventory_update_by_id...")
        update_result = await crud.update_item_by_id(
            client=client,
            user_id=test_user_id,
            item_id=test_item_id,
            quantity=2.0,
            unit="パック"
        )
        
        if update_result["success"]:
            logger.info("✅ [TEST] inventory_update_by_id test passed")
            logger.info(f"✏️ Updated item: {test_item_id}")
        else:
            logger.error(f"❌ [TEST] inventory_update_by_id test failed: {update_result['error']}")
            return False
        
        # 6. 在庫削除テスト
        logger.info("🗑️ [TEST] Testing inventory_delete_by_id...")
        delete_result = await crud.delete_item_by_id(client, test_user_id, test_item_id)
        
        if delete_result["success"]:
            logger.info("✅ [TEST] inventory_delete_by_id test passed")
            logger.info(f"🗑️ Deleted item: {test_item_id}")
        else:
            logger.error(f"❌ [TEST] inventory_delete_by_id test failed: {delete_result['error']}")
            return False
        
        logger.info("🎉 [TEST] All Inventory CRUD tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] Test failed with exception: {e}")
        logger.error(f"❌ Test exception: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    
    # テスト開始時に一度だけログ初期化（ローテーション）
    setup_logging(initialize=True)  # テスト開始時のみ初期化
    logger = GenericLogger("test", "main")
    
    logger.info("🚀 [TEST] Starting Inventory CRUD Tests")
    logger.info("=" * 50)
    
    try:
        success = asyncio.run(test_inventory_crud())
        
        logger.info("=" * 50)
        if success:
            logger.info("🎉 [TEST] All Inventory CRUD tests completed successfully!")
        else:
            logger.error("❌ [TEST] Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ [TEST] Test suite failed: {e}")
        sys.exit(1)
