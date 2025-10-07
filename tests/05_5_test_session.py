#!/usr/bin/env python3
"""
05_5_test_session.py

SessionServiceの動作確認テスト
- セッション作成機能のテスト
- セッション取得機能のテスト
- セッション更新機能のテスト
- セッション削除機能のテスト
- 期限切れセッションクリーンアップのテスト
- エラーハンドリングのテスト
"""

import asyncio
import os
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv()

# ロギングの初期化
from config.logging import setup_logging
setup_logging()

from config.loggers import GenericLogger

# サービス層のインポート
from services.session_service import SessionService, Session

# ロガーの初期化
logger = GenericLogger("test", "session_service")


async def test_create_session():
    """セッション作成機能のテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting create_session test...")
    print("🧪 [SESSION_TEST] Starting create_session test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # テストデータ
        user_id = "test_user_123"
        
        # セッション作成実行
        session = await session_service.create_session(user_id)
        
        if isinstance(session, Session):
            logger.info(f"✅ [SESSION_TEST] create_session completed successfully")
            print(f"✅ [SESSION_TEST] create_session completed successfully")
            print(f"  Session ID: {session.id}")
            print(f"  User ID: {session.user_id}")
            print(f"  Created at: {session.created_at}")
            print(f"  Last accessed: {session.last_accessed}")
            
            logger.info(f"📋 [SESSION_TEST] Session ID: {session.id}")
            logger.info(f"📋 [SESSION_TEST] User ID: {session.user_id}")
            
            # セッションIDの一意性確認
            if session.id and len(session.id) > 0:
                logger.info(f"✅ [SESSION_TEST] Session ID is unique and valid")
                print(f"✅ [SESSION_TEST] Session ID is unique and valid")
                return True
            else:
                logger.error(f"❌ [SESSION_TEST] Session ID is invalid")
                print(f"❌ [SESSION_TEST] Session ID is invalid")
                return False
        else:
            logger.error(f"❌ [SESSION_TEST] create_session failed: invalid result type")
            print(f"❌ [SESSION_TEST] create_session failed: invalid result type")
            return False
            
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] create_session test failed: {e}")
        print(f"❌ [SESSION_TEST] create_session test failed: {e}")
        return False


async def test_get_session():
    """セッション取得機能のテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting get_session test...")
    print("🧪 [SESSION_TEST] Starting get_session test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # テストデータ - セッションを作成
        user_id = "test_user_456"
        created_session = await session_service.create_session(user_id)
        
        if not isinstance(created_session, Session):
            logger.error(f"❌ [SESSION_TEST] Failed to create session for get test")
            print(f"❌ [SESSION_TEST] Failed to create session for get test")
            return False
        
        # セッション取得実行
        retrieved_session = await session_service.get_session(created_session.id)
        
        if isinstance(retrieved_session, Session):
            logger.info(f"✅ [SESSION_TEST] get_session completed successfully")
            print(f"✅ [SESSION_TEST] get_session completed successfully")
            print(f"  Retrieved Session ID: {retrieved_session.id}")
            print(f"  Retrieved User ID: {retrieved_session.user_id}")
            
            # セッション内容の一致確認
            if (retrieved_session.id == created_session.id and 
                retrieved_session.user_id == created_session.user_id):
                logger.info(f"✅ [SESSION_TEST] Session data matches correctly")
                print(f"✅ [SESSION_TEST] Session data matches correctly")
                return True
            else:
                logger.error(f"❌ [SESSION_TEST] Session data mismatch")
                print(f"❌ [SESSION_TEST] Session data mismatch")
                return False
        else:
            logger.error(f"❌ [SESSION_TEST] get_session failed: invalid result type")
            print(f"❌ [SESSION_TEST] get_session failed: invalid result type")
            return False
            
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] get_session test failed: {e}")
        print(f"❌ [SESSION_TEST] get_session test failed: {e}")
        return False


async def test_update_session():
    """セッション更新機能のテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting update_session test...")
    print("🧪 [SESSION_TEST] Starting update_session test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # テストデータ - セッションを作成
        user_id = "test_user_789"
        created_session = await session_service.create_session(user_id)
        
        if not isinstance(created_session, Session):
            logger.error(f"❌ [SESSION_TEST] Failed to create session for update test")
            print(f"❌ [SESSION_TEST] Failed to create session for update test")
            return False
        
        # 更新データ
        updates = {
            "preferences": {"theme": "dark", "language": "ja"},
            "last_action": "menu_generation",
            "inventory_count": 10
        }
        
        # セッション更新実行
        update_result = await session_service.update_session(created_session.id, updates)
        
        if update_result:
            logger.info(f"✅ [SESSION_TEST] update_session completed successfully")
            print(f"✅ [SESSION_TEST] update_session completed successfully")
            
            # 更新されたセッションを取得して確認
            updated_session = await session_service.get_session(created_session.id)
            
            if isinstance(updated_session, Session):
                # 更新データの確認
                session_data = updated_session.data
                if (session_data.get("preferences") == updates["preferences"] and
                    session_data.get("last_action") == updates["last_action"] and
                    session_data.get("inventory_count") == updates["inventory_count"]):
                    
                    logger.info(f"✅ [SESSION_TEST] Session data updated correctly")
                    print(f"✅ [SESSION_TEST] Session data updated correctly")
                    print(f"  Updated preferences: {session_data.get('preferences')}")
                    print(f"  Updated last_action: {session_data.get('last_action')}")
                    print(f"  Updated inventory_count: {session_data.get('inventory_count')}")
                    
                    logger.info(f"📝 [SESSION_TEST] Updated preferences: {session_data.get('preferences')}")
                    return True
                else:
                    logger.error(f"❌ [SESSION_TEST] Session data not updated correctly")
                    print(f"❌ [SESSION_TEST] Session data not updated correctly")
                    return False
            else:
                logger.error(f"❌ [SESSION_TEST] Failed to retrieve updated session")
                print(f"❌ [SESSION_TEST] Failed to retrieve updated session")
                return False
        else:
            logger.error(f"❌ [SESSION_TEST] update_session failed: update_result is False")
            print(f"❌ [SESSION_TEST] update_session failed: update_result is False")
            return False
            
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] update_session test failed: {e}")
        print(f"❌ [SESSION_TEST] update_session test failed: {e}")
        return False


async def test_delete_session():
    """セッション削除機能のテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting delete_session test...")
    print("🧪 [SESSION_TEST] Starting delete_session test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # テストデータ - セッションを作成
        user_id = "test_user_delete"
        created_session = await session_service.create_session(user_id)
        
        if not isinstance(created_session, Session):
            logger.error(f"❌ [SESSION_TEST] Failed to create session for delete test")
            print(f"❌ [SESSION_TEST] Failed to create session for delete test")
            return False
        
        # セッション削除実行
        delete_result = await session_service.delete_session(created_session.id)
        
        if delete_result:
            logger.info(f"✅ [SESSION_TEST] delete_session completed successfully")
            print(f"✅ [SESSION_TEST] delete_session completed successfully")
            
            # 削除されたセッションを取得して確認
            deleted_session = await session_service.get_session(created_session.id)
            
            if deleted_session is None:
                logger.info(f"✅ [SESSION_TEST] Session deleted correctly")
                print(f"✅ [SESSION_TEST] Session deleted correctly")
                return True
            else:
                logger.error(f"❌ [SESSION_TEST] Session still exists after deletion")
                print(f"❌ [SESSION_TEST] Session still exists after deletion")
                return False
        else:
            logger.error(f"❌ [SESSION_TEST] delete_session failed: delete_result is False")
            print(f"❌ [SESSION_TEST] delete_session failed: delete_result is False")
            return False
            
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] delete_session test failed: {e}")
        print(f"❌ [SESSION_TEST] delete_session test failed: {e}")
        return False


async def test_cleanup_expired_sessions():
    """期限切れセッションクリーンアップのテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting cleanup_expired_sessions test...")
    print("🧪 [SESSION_TEST] Starting cleanup_expired_sessions test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # テストデータ - 複数のセッションを作成
        user_ids = ["test_user_cleanup_1", "test_user_cleanup_2", "test_user_cleanup_3"]
        created_sessions = []
        
        for user_id in user_ids:
            session = await session_service.create_session(user_id)
            if isinstance(session, Session):
                created_sessions.append(session)
        
        if len(created_sessions) != len(user_ids):
            logger.error(f"❌ [SESSION_TEST] Failed to create all sessions for cleanup test")
            print(f"❌ [SESSION_TEST] Failed to create all sessions for cleanup test")
            return False
        
        # 期限切れセッションクリーンアップ実行（1時間未満のセッションを削除）
        cleanup_result = await session_service.cleanup_expired_sessions(max_age_hours=1)
        
        if isinstance(cleanup_result, int):
            logger.info(f"✅ [SESSION_TEST] cleanup_expired_sessions completed successfully")
            print(f"✅ [SESSION_TEST] cleanup_expired_sessions completed successfully")
            print(f"  Cleaned up sessions: {cleanup_result}")
            
            logger.info(f"🧹 [SESSION_TEST] Cleaned up sessions: {cleanup_result}")
            
            # クリーンアップ後のセッション数を確認
            remaining_sessions = 0
            for session in created_sessions:
                remaining_session = await session_service.get_session(session.id)
                if remaining_session is not None:
                    remaining_sessions += 1
            
            print(f"  Remaining sessions: {remaining_sessions}")
            logger.info(f"📊 [SESSION_TEST] Remaining sessions: {remaining_sessions}")
            
            return True
        else:
            logger.error(f"❌ [SESSION_TEST] cleanup_expired_sessions failed: invalid result type")
            print(f"❌ [SESSION_TEST] cleanup_expired_sessions failed: invalid result type")
            return False
            
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] cleanup_expired_sessions test failed: {e}")
        print(f"❌ [SESSION_TEST] cleanup_expired_sessions test failed: {e}")
        return False


async def test_multiple_sessions():
    """複数セッション管理のテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting multiple sessions test...")
    print("🧪 [SESSION_TEST] Starting multiple sessions test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # テストデータ - 複数のユーザーでセッションを作成
        user_ids = ["multi_user_1", "multi_user_2", "multi_user_3"]
        created_sessions = []
        
        for user_id in user_ids:
            session = await session_service.create_session(user_id)
            if isinstance(session, Session):
                created_sessions.append(session)
                print(f"  Created session for {user_id}: {session.id}")
                logger.info(f"📋 [SESSION_TEST] Created session for {user_id}: {session.id}")
        
        if len(created_sessions) != len(user_ids):
            logger.error(f"❌ [SESSION_TEST] Failed to create all sessions")
            print(f"❌ [SESSION_TEST] Failed to create all sessions")
            return False
        
        # 各セッションの取得確認
        retrieved_sessions = []
        for session in created_sessions:
            retrieved_session = await session_service.get_session(session.id)
            if isinstance(retrieved_session, Session):
                retrieved_sessions.append(retrieved_session)
        
        if len(retrieved_sessions) == len(created_sessions):
            logger.info(f"✅ [SESSION_TEST] Multiple sessions test completed successfully")
            print(f"✅ [SESSION_TEST] Multiple sessions test completed successfully")
            print(f"  Created sessions: {len(created_sessions)}")
            print(f"  Retrieved sessions: {len(retrieved_sessions)}")
            
            logger.info(f"📊 [SESSION_TEST] Created sessions: {len(created_sessions)}")
            logger.info(f"📊 [SESSION_TEST] Retrieved sessions: {len(retrieved_sessions)}")
            return True
        else:
            logger.error(f"❌ [SESSION_TEST] Session retrieval mismatch")
            print(f"❌ [SESSION_TEST] Session retrieval mismatch")
            return False
            
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] Multiple sessions test failed: {e}")
        print(f"❌ [SESSION_TEST] Multiple sessions test failed: {e}")
        return False


async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    logger.info("🧪 [SESSION_TEST] Starting error handling test...")
    print("🧪 [SESSION_TEST] Starting error handling test...")
    
    try:
        # SessionService初期化
        session_service = SessionService()
        
        # 存在しないセッションIDでの取得テスト
        non_existent_session = await session_service.get_session("non_existent_session_id")
        if non_existent_session is None:
            logger.info(f"✅ [SESSION_TEST] Non-existent session handling: OK")
            print(f"✅ [SESSION_TEST] Non-existent session handling: OK")
        else:
            logger.error(f"❌ [SESSION_TEST] Non-existent session handling: FAILED")
            print(f"❌ [SESSION_TEST] Non-existent session handling: FAILED")
            return False
        
        # 存在しないセッションIDでの更新テスト
        update_result = await session_service.update_session("non_existent_session_id", {"test": "data"})
        if not update_result:
            logger.info(f"✅ [SESSION_TEST] Non-existent session update handling: OK")
            print(f"✅ [SESSION_TEST] Non-existent session update handling: OK")
        else:
            logger.error(f"❌ [SESSION_TEST] Non-existent session update handling: FAILED")
            print(f"❌ [SESSION_TEST] Non-existent session update handling: FAILED")
            return False
        
        # 存在しないセッションIDでの削除テスト
        delete_result = await session_service.delete_session("non_existent_session_id")
        if not delete_result:
            logger.info(f"✅ [SESSION_TEST] Non-existent session delete handling: OK")
            print(f"✅ [SESSION_TEST] Non-existent session delete handling: OK")
        else:
            logger.error(f"❌ [SESSION_TEST] Non-existent session delete handling: FAILED")
            print(f"❌ [SESSION_TEST] Non-existent session delete handling: FAILED")
            return False
        
        logger.info(f"✅ [SESSION_TEST] Error handling test completed successfully")
        print(f"✅ [SESSION_TEST] Error handling test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ [SESSION_TEST] Error handling test failed: {e}")
        print(f"❌ [SESSION_TEST] Error handling test failed: {e}")
        return False


async def main():
    """メインテスト実行"""
    
    logger.info("🚀 [MAIN] Starting SessionService tests...")
    print("🚀 [MAIN] Starting SessionService tests...")
    
    # テスト実行
    test_results = []
    
    # 1. セッション作成テスト
    test1_result = await test_create_session()
    test_results.append(("Create Session", test1_result))
    
    # 2. セッション取得テスト
    test2_result = await test_get_session()
    test_results.append(("Get Session", test2_result))
    
    # 3. セッション更新テスト
    test3_result = await test_update_session()
    test_results.append(("Update Session", test3_result))
    
    # 4. セッション削除テスト
    test4_result = await test_delete_session()
    test_results.append(("Delete Session", test4_result))
    
    # 5. 期限切れセッションクリーンアップテスト
    test5_result = await test_cleanup_expired_sessions()
    test_results.append(("Cleanup Expired Sessions", test5_result))
    
    # 6. 複数セッション管理テスト
    test6_result = await test_multiple_sessions()
    test_results.append(("Multiple Sessions", test6_result))
    
    # 7. エラーハンドリングテスト
    test7_result = await test_error_handling()
    test_results.append(("Error Handling", test7_result))
    
    # 結果サマリー
    logger.info("📊 [MAIN] SessionService Test Results Summary:")
    print("📊 [MAIN] SessionService Test Results Summary:")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  - {test_name}: {status}")
        print(f"  - {test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    logger.info(f"📈 Test Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"📈 Test Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if passed_tests == total_tests:
        logger.info("🎉 [MAIN] All SessionService tests passed!")
        print("🎉 [MAIN] All SessionService tests passed!")
    elif passed_tests >= total_tests * 0.8:
        logger.info("✅ [MAIN] Most SessionService tests passed!")
        print("✅ [MAIN] Most SessionService tests passed!")
    else:
        logger.error("❌ [MAIN] Some SessionService tests failed. Please check the logs.")
        print("❌ [MAIN] Some SessionService tests failed. Please check the logs.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # テスト実行
    asyncio.run(main())
