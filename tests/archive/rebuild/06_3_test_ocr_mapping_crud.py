"""
Morizo AI v2 - OCR Mapping CRUD Tests

This module tests basic CRUD operations for OCR mapping management.
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
# プロジェクトルートを取得（tests/archive/rebuild/ から /app/Morizo-aiv2/ へ）
# __file__ = tests/archive/rebuild/06_3_test_ocr_mapping_crud.py
# dirname x4 で /app/Morizo-aiv2/ に到達
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)  # プロジェクトルートを追加（configモジュール用）
sys.path.append(os.path.join(project_root, "mcp_servers"))
from ocr_mapping_crud import OCRMappingCRUD
from config.loggers import GenericLogger
from config.logging import setup_logging


async def test_ocr_mapping_crud():
    """Test basic CRUD operations for OCR mapping"""
    # ロギング設定（初期化なし）
    setup_logging(initialize=False)
    logger = GenericLogger("test", "ocr_mapping_crud")
    
    logger.info("🧪 [TEST] Testing OCR Mapping CRUD operations...")
    
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
    crud = OCRMappingCRUD()
    
    # テストデータ
    test_original_name = "もっちり仕込み"
    test_normalized_name = "食パン"
    test_original_name2 = "新ＢＰコクのある絹豆腐"
    test_normalized_name2 = "豆腐"
    
    try:
        # 1. 変換テーブル登録テスト（UPSERT）
        logger.info("📝 [TEST] Testing add_mapping (UPSERT)...")
        add_result = await crud.add_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name,
            normalized_name=test_normalized_name
        )
        
        if add_result["success"]:
            logger.info("✅ [TEST] add_mapping test passed")
            test_mapping_id = add_result["data"]["id"]
            logger.info(f"📝 [TEST] Added test mapping: {test_mapping_id}")
            logger.info(f"   Original: '{test_original_name}' -> Normalized: '{test_normalized_name}'")
        else:
            logger.error(f"❌ [TEST] add_mapping test failed: {add_result.get('error', 'Unknown error')}")
            return False
        
        # 2. 変換テーブル取得テスト（単一）
        logger.info("🔍 [TEST] Testing get_mapping...")
        get_result = await crud.get_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name
        )
        
        if get_result["success"]:
            if get_result["data"]:
                logger.info("✅ [TEST] get_mapping test passed")
                logger.info(f"🔍 [TEST] Retrieved mapping: {get_result['data']['id']}")
                logger.info(f"   Original: '{get_result['data']['original_name']}' -> Normalized: '{get_result['data']['normalized_name']}'")
                
                # データの整合性チェック
                if get_result["data"]["original_name"] != test_original_name:
                    logger.error(f"❌ [TEST] Original name mismatch: expected '{test_original_name}', got '{get_result['data']['original_name']}'")
                    return False
                if get_result["data"]["normalized_name"] != test_normalized_name:
                    logger.error(f"❌ [TEST] Normalized name mismatch: expected '{test_normalized_name}', got '{get_result['data']['normalized_name']}'")
                    return False
            else:
                logger.error("❌ [TEST] get_mapping returned no data")
                return False
        else:
            logger.error(f"❌ [TEST] get_mapping test failed: {get_result.get('error', 'Unknown error')}")
            return False
        
        # 3. 変換テーブル一覧取得テスト
        logger.info("📋 [TEST] Testing get_all_mappings...")
        list_result = await crud.get_all_mappings(client, test_user_id)
        
        if list_result["success"]:
            logger.info(f"✅ [TEST] get_all_mappings test passed - Found {len(list_result['data'])} mappings")
            logger.info(f"📋 [TEST] Retrieved {len(list_result['data'])} mappings")
            
            # 登録したマッピングが含まれているか確認
            found = False
            for mapping in list_result["data"]:
                if mapping["original_name"] == test_original_name and mapping["normalized_name"] == test_normalized_name:
                    found = True
                    break
            
            if not found:
                logger.warning(f"⚠️ [TEST] Registered mapping not found in list")
        else:
            logger.error(f"❌ [TEST] get_all_mappings test failed: {list_result.get('error', 'Unknown error')}")
            return False
        
        # 4. 変換テーブル更新テスト
        logger.info("✏️ [TEST] Testing update_mapping...")
        updated_normalized_name = "パン"
        update_result = await crud.update_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name,
            normalized_name=updated_normalized_name
        )
        
        if update_result["success"]:
            logger.info("✅ [TEST] update_mapping test passed")
            logger.info(f"✏️ [TEST] Updated mapping: {update_result['data']['id']}")
            logger.info(f"   Original: '{test_original_name}' -> Normalized: '{updated_normalized_name}'")
            
            # 更新後のデータを確認
            get_result_after_update = await crud.get_mapping(
                client=client,
                user_id=test_user_id,
                original_name=test_original_name
            )
            
            if get_result_after_update["success"] and get_result_after_update["data"]:
                if get_result_after_update["data"]["normalized_name"] != updated_normalized_name:
                    logger.error(f"❌ [TEST] Update verification failed: expected '{updated_normalized_name}', got '{get_result_after_update['data']['normalized_name']}'")
                    return False
                logger.info("✅ [TEST] Update verification passed")
            else:
                logger.error("❌ [TEST] Failed to verify update")
                return False
        else:
            logger.error(f"❌ [TEST] update_mapping test failed: {update_result.get('error', 'Unknown error')}")
            return False
        
        # 5. UPSERTテスト（既存のマッピングを再度登録）
        logger.info("🔄 [TEST] Testing add_mapping (UPSERT with existing data)...")
        upsert_normalized_name = "食パン"  # 元の値に戻す
        upsert_result = await crud.add_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name,
            normalized_name=upsert_normalized_name
        )
        
        if upsert_result["success"]:
            logger.info("✅ [TEST] add_mapping (UPSERT) test passed")
            logger.info(f"🔄 [TEST] UPSERTed mapping: {upsert_result['data']['id']}")
            
            # UPSERT後のデータを確認
            get_result_after_upsert = await crud.get_mapping(
                client=client,
                user_id=test_user_id,
                original_name=test_original_name
            )
            
            if get_result_after_upsert["success"] and get_result_after_upsert["data"]:
                if get_result_after_upsert["data"]["normalized_name"] != upsert_normalized_name:
                    logger.error(f"❌ [TEST] UPSERT verification failed: expected '{upsert_normalized_name}', got '{get_result_after_upsert['data']['normalized_name']}'")
                    return False
                logger.info("✅ [TEST] UPSERT verification passed")
            else:
                logger.error("❌ [TEST] Failed to verify UPSERT")
                return False
        else:
            logger.error(f"❌ [TEST] add_mapping (UPSERT) test failed: {upsert_result.get('error', 'Unknown error')}")
            return False
        
        # 6. 別のマッピングを追加して、複数マッピングのテスト
        logger.info("📝 [TEST] Testing add_mapping (second mapping)...")
        add_result2 = await crud.add_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name2,
            normalized_name=test_normalized_name2
        )
        
        if add_result2["success"]:
            logger.info("✅ [TEST] add_mapping (second) test passed")
            logger.info(f"📝 [TEST] Added second mapping: {add_result2['data']['id']}")
        else:
            logger.error(f"❌ [TEST] add_mapping (second) test failed: {add_result2.get('error', 'Unknown error')}")
            return False
        
        # 7. 全マッピング取得で2件以上あることを確認
        logger.info("📋 [TEST] Testing get_all_mappings (multiple mappings)...")
        list_result2 = await crud.get_all_mappings(client, test_user_id)
        
        if list_result2["success"]:
            if len(list_result2["data"]) >= 2:
                logger.info(f"✅ [TEST] get_all_mappings (multiple) test passed - Found {len(list_result2['data'])} mappings")
            else:
                logger.warning(f"⚠️ [TEST] Expected at least 2 mappings, found {len(list_result2['data'])}")
        else:
            logger.error(f"❌ [TEST] get_all_mappings (multiple) test failed: {list_result2.get('error', 'Unknown error')}")
            return False
        
        # 8. 変換テーブル削除テスト（1件目）
        logger.info("🗑️ [TEST] Testing delete_mapping (first mapping)...")
        delete_result = await crud.delete_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name
        )
        
        if delete_result["success"]:
            logger.info("✅ [TEST] delete_mapping (first) test passed")
            logger.info(f"🗑️ [TEST] Deleted mapping: '{test_original_name}'")
            
            # 削除後の確認
            get_result_after_delete = await crud.get_mapping(
                client=client,
                user_id=test_user_id,
                original_name=test_original_name
            )
            
            if get_result_after_delete["success"]:
                if get_result_after_delete["data"] is None:
                    logger.info("✅ [TEST] Delete verification passed (mapping not found)")
                else:
                    logger.error("❌ [TEST] Delete verification failed (mapping still exists)")
                    return False
            else:
                logger.error(f"❌ [TEST] Failed to verify delete: {get_result_after_delete.get('error', 'Unknown error')}")
                return False
        else:
            logger.error(f"❌ [TEST] delete_mapping (first) test failed: {delete_result.get('error', 'Unknown error')}")
            return False
        
        # 9. 変換テーブル削除テスト（2件目）
        logger.info("🗑️ [TEST] Testing delete_mapping (second mapping)...")
        delete_result2 = await crud.delete_mapping(
            client=client,
            user_id=test_user_id,
            original_name=test_original_name2
        )
        
        if delete_result2["success"]:
            logger.info("✅ [TEST] delete_mapping (second) test passed")
            logger.info(f"🗑️ [TEST] Deleted mapping: '{test_original_name2}'")
        else:
            logger.error(f"❌ [TEST] delete_mapping (second) test failed: {delete_result2.get('error', 'Unknown error')}")
            return False
        
        # 10. 存在しないマッピングの取得テスト
        logger.info("🔍 [TEST] Testing get_mapping (non-existent mapping)...")
        get_result_nonexistent = await crud.get_mapping(
            client=client,
            user_id=test_user_id,
            original_name="存在しない商品名"
        )
        
        if get_result_nonexistent["success"]:
            if get_result_nonexistent["data"] is None:
                logger.info("✅ [TEST] get_mapping (non-existent) test passed (correctly returned None)")
            else:
                logger.error("❌ [TEST] get_mapping (non-existent) test failed (should return None)")
                return False
        else:
            logger.error(f"❌ [TEST] get_mapping (non-existent) test failed: {get_result_nonexistent.get('error', 'Unknown error')}")
            return False
        
        logger.info("🎉 [TEST] All OCR Mapping CRUD tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    
    # テスト開始時に一度だけログ初期化（ローテーション）
    setup_logging(initialize=True)  # テスト開始時のみ初期化
    logger = GenericLogger("test", "main")
    
    logger.info("🚀 [TEST] Starting OCR Mapping CRUD Tests")
    logger.info("=" * 50)
    
    try:
        success = asyncio.run(test_ocr_mapping_crud())
        
        logger.info("=" * 50)
        if success:
            logger.info("🎉 [TEST] All OCR Mapping CRUD tests completed successfully!")
        else:
            logger.error("❌ [TEST] Some tests failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ [TEST] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

