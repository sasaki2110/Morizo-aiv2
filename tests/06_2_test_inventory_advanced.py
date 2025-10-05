"""
Morizo AI v2 - Inventory Advanced Tests

This module tests advanced operations for inventory management including batch operations and FIFO logic.
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
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_servers"))
from inventory_crud import InventoryCRUD
from inventory_advanced import InventoryAdvanced
from config.loggers import GenericLogger
from config.logging import setup_logging


async def test_inventory_advanced():
    """Test advanced operations"""
    # ロギング設定（初期化なし）
    setup_logging(initialize=False)
    logger = GenericLogger("test", "inventory_advanced")
    
    logger.info("🧪 [TEST] Testing Inventory Advanced operations...")
    
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
    
    # インスタンス作成
    crud = InventoryCRUD()
    advanced = InventoryAdvanced()
    
    # テスト用のアイテム名
    test_item_name = "テストアイテム"
    
    try:
        # テストデータの準備（複数レコード作成）
        logger.info("📦 [TEST] Preparing test data...")
        test_items = []
        
        # 3つのテストアイテムを作成（FIFOテスト用）
        for i in range(3):
            add_result = await crud.add_item(
                client=client,
                user_id=test_user_id,
                item_name=test_item_name,
                quantity=1.0 + i,
                unit="個",
                storage_location="冷蔵庫"
            )
            
            if add_result["success"]:
                test_items.append(add_result["data"])
                logger.info(f"📦 Created test item {i+1}: {add_result['data']['id']}")
            else:
                print(f"❌ Failed to create test item {i+1}: {add_result['error']}")
                return False
        
        print(f"✅ Created {len(test_items)} test items")
        
        # 1. 名前指定一括更新テスト
        logger.info("✏️ [TEST] Testing inventory_update_by_name...")
        update_result = await advanced.update_by_name(
            client=client,
            user_id=test_user_id,
            item_name=test_item_name,
            quantity=5.0,
            unit="パック"
        )
        
        if update_result["success"]:
            print(f"✅ inventory_update_by_name test passed - Updated {len(update_result['data'])} items")
            logger.info(f"✏️ Batch updated {len(update_result['data'])} items")
        else:
            print(f"❌ inventory_update_by_name test failed: {update_result['error']}")
            return False
        
        # 2. 最古アイテム更新テスト（FIFO）
        print("✏️ Testing inventory_update_by_name_oldest...")
        oldest_result = await advanced.update_by_name_oldest(
            client=client,
            user_id=test_user_id,
            item_name=test_item_name,
            quantity=10.0,
            storage_location="冷凍庫"
        )
        
        if oldest_result["success"]:
            logger.info("✅ [TEST] inventory_update_by_name_oldest test passed")
            logger.info(f"✏️ Updated oldest item: {oldest_result['data']['id']}")
        else:
            print(f"❌ inventory_update_by_name_oldest test failed: {oldest_result['error']}")
            return False
        
        # 3. 最新アイテム更新テスト
        print("✏️ Testing inventory_update_by_name_latest...")
        latest_result = await advanced.update_by_name_latest(
            client=client,
            user_id=test_user_id,
            item_name=test_item_name,
            quantity=15.0,
            storage_location="野菜室"
        )
        
        if latest_result["success"]:
            logger.info("✅ [TEST] inventory_update_by_name_latest test passed")
            logger.info(f"✏️ Updated latest item: {latest_result['data']['id']}")
        else:
            print(f"❌ inventory_update_by_name_latest test failed: {latest_result['error']}")
            return False
        
        # 4. 最古アイテム削除テスト（FIFO）
        logger.info("🗑️ [TEST] Testing inventory_delete_by_name_oldest...")
        delete_oldest_result = await advanced.delete_by_name_oldest(
            client=client,
            user_id=test_user_id,
            item_name=test_item_name
        )
        
        if delete_oldest_result["success"]:
            logger.info("✅ [TEST] inventory_delete_by_name_oldest test passed")
            logger.info(f"🗑️ Deleted oldest item: {delete_oldest_result['data']['id']}")
        else:
            print(f"❌ inventory_delete_by_name_oldest test failed: {delete_oldest_result['error']}")
            return False
        
        # 5. 最新アイテム削除テスト
        logger.info("🗑️ [TEST] Testing inventory_delete_by_name_latest...")
        delete_latest_result = await advanced.delete_by_name_latest(
            client=client,
            user_id=test_user_id,
            item_name=test_item_name
        )
        
        if delete_latest_result["success"]:
            logger.info("✅ [TEST] inventory_delete_by_name_latest test passed")
            logger.info(f"🗑️ Deleted latest item: {delete_latest_result['data']['id']}")
        else:
            print(f"❌ inventory_delete_by_name_latest test failed: {delete_latest_result['error']}")
            return False
        
        # 6. 名前指定一括削除テスト（残りのアイテムを削除）
        logger.info("🗑️ [TEST] Testing inventory_delete_by_name...")
        delete_all_result = await advanced.delete_by_name(
            client=client,
            user_id=test_user_id,
            item_name=test_item_name
        )
        
        if delete_all_result["success"]:
            print(f"✅ inventory_delete_by_name test passed - Deleted {len(delete_all_result['data'])} items")
            logger.info(f"🗑️ Batch deleted {len(delete_all_result['data'])} items")
        else:
            print(f"❌ inventory_delete_by_name test failed: {delete_all_result['error']}")
            return False
        
        logger.info("🎉 [TEST] All Inventory Advanced tests passed!")
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
    
    logger.info("🚀 [TEST] Starting Inventory Advanced Tests")
    logger.info("=" * 50)
    
    try:
        success = asyncio.run(test_inventory_advanced())
        
        logger.info("=" * 50)
        if success:
            logger.info("🎉 [TEST] All Inventory Advanced tests completed successfully!")
        else:
            logger.error("❌ [TEST] Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ [TEST] Test suite failed: {e}")
        sys.exit(1)
