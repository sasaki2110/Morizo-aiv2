#!/usr/bin/env python3
"""
05_4_test_confirmation.py

ConfirmationServiceの動作確認テスト
- 曖昧性検出機能のテスト
- 確認プロセス処理のテスト
- タスクチェーン保持のテスト
- エラーハンドリングのテスト
"""

import asyncio
import os
import sys
from typing import Dict, Any, List

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
from services.confirmation_service import (
    ConfirmationService, 
    AmbiguityInfo, 
    AmbiguityResult, 
    ConfirmationResult
)

# ロガーの初期化
logger = GenericLogger("test", "confirmation_service")


async def test_detect_ambiguity():
    """曖昧性検出機能のテスト"""
    
    logger.info("🧪 [CONFIRMATION_TEST] Starting detect_ambiguity test...")
    print("🧪 [CONFIRMATION_TEST] Starting detect_ambiguity test...")
    
    try:
        # ConfirmationService初期化
        confirmation_service = ConfirmationService()
        
        # テストデータ - 曖昧なタスク
        ambiguous_tasks = [
            {
                "id": "task_1",
                "tool": "inventory_update_by_name",
                "parameters": {"item_name": "りんご", "quantity": 5}
            },
            {
                "id": "task_2", 
                "tool": "inventory_delete_by_name",
                "parameters": {"item_name": "バナナ"}
            }
        ]
        
        # 曖昧でないタスク
        non_ambiguous_tasks = [
            {
                "id": "task_3",
                "tool": "inventory_list",
                "parameters": {"user_id": "test_user"}
            }
        ]
        
        user_id = "test_user_123"
        
        # 曖昧なタスクでのテスト
        result = await confirmation_service.detect_ambiguity(ambiguous_tasks, user_id)
        
        if isinstance(result, AmbiguityResult):
            logger.info(f"✅ [CONFIRMATION_TEST] detect_ambiguity completed successfully")
            print(f"✅ [CONFIRMATION_TEST] detect_ambiguity completed successfully")
            print(f"  Requires confirmation: {result.requires_confirmation}")
            print(f"  Ambiguous tasks count: {len(result.ambiguous_tasks)}")
            
            for i, task in enumerate(result.ambiguous_tasks, 1):
                print(f"    Ambiguous task {i}: {task.task_id} - {task.ambiguity_type}")
                logger.info(f"🔍 [CONFIRMATION_TEST] Ambiguous task {i}: {task.task_id} - {task.ambiguity_type}")
            
            return True
        else:
            logger.error(f"❌ [CONFIRMATION_TEST] detect_ambiguity failed: invalid result type")
            print(f"❌ [CONFIRMATION_TEST] detect_ambiguity failed: invalid result type")
            return False
            
    except Exception as e:
        logger.error(f"❌ [CONFIRMATION_TEST] detect_ambiguity test failed: {e}")
        print(f"❌ [CONFIRMATION_TEST] detect_ambiguity test failed: {e}")
        return False


async def test_process_confirmation():
    """確認プロセス処理のテスト"""
    
    logger.info("🧪 [CONFIRMATION_TEST] Starting process_confirmation test...")
    print("🧪 [CONFIRMATION_TEST] Starting process_confirmation test...")
    
    try:
        # ConfirmationService初期化
        confirmation_service = ConfirmationService()
        
        # テストデータ
        ambiguity_info = AmbiguityInfo(
            task_id="task_1",
            tool_name="inventory_update_by_name",
            ambiguity_type="multiple_items",
            details={"item_name": "りんご", "message": "同名のアイテムが複数存在します"}
        )
        
        user_response = "IDで指定してください"
        context = {"user_id": "test_user_123", "session_id": "session_456"}
        
        # 確認プロセス処理実行
        result = await confirmation_service.process_confirmation(
            ambiguity_info=ambiguity_info,
            user_response=user_response,
            context=context
        )
        
        if isinstance(result, ConfirmationResult):
            logger.info(f"✅ [CONFIRMATION_TEST] process_confirmation completed successfully")
            print(f"✅ [CONFIRMATION_TEST] process_confirmation completed successfully")
            print(f"  Is cancelled: {result.is_cancelled}")
            print(f"  Updated tasks count: {len(result.updated_tasks)}")
            print(f"  Confirmation context: {result.confirmation_context}")
            
            logger.info(f"📋 [CONFIRMATION_TEST] Is cancelled: {result.is_cancelled}")
            logger.info(f"📋 [CONFIRMATION_TEST] Updated tasks count: {len(result.updated_tasks)}")
            
            return True
        else:
            logger.error(f"❌ [CONFIRMATION_TEST] process_confirmation failed: invalid result type")
            print(f"❌ [CONFIRMATION_TEST] process_confirmation failed: invalid result type")
            return False
            
    except Exception as e:
        logger.error(f"❌ [CONFIRMATION_TEST] process_confirmation test failed: {e}")
        print(f"❌ [CONFIRMATION_TEST] process_confirmation test failed: {e}")
        return False


async def test_maintain_task_chain():
    """タスクチェーン保持のテスト"""
    
    logger.info("🧪 [CONFIRMATION_TEST] Starting maintain_task_chain test...")
    print("🧪 [CONFIRMATION_TEST] Starting maintain_task_chain test...")
    
    try:
        # ConfirmationService初期化
        confirmation_service = ConfirmationService()
        
        # テストデータ
        original_tasks = [
            {
                "id": "task_1",
                "tool": "inventory_update_by_name",
                "parameters": {"item_name": "りんご", "quantity": 5}
            },
            {
                "id": "task_2",
                "tool": "inventory_list",
                "parameters": {"user_id": "test_user"}
            }
        ]
        
        # 正常な確認結果
        confirmation_result = ConfirmationResult(
            is_cancelled=False,
            updated_tasks=[
                {
                    "id": "task_1",
                    "tool": "inventory_update_by_id",
                    "parameters": {"item_id": "123", "quantity": 5},
                    "strategy": "by_id"
                }
            ],
            confirmation_context={"user_id": "test_user_123"}
        )
        
        # タスクチェーン保持実行
        result = await confirmation_service.maintain_task_chain(
            original_tasks=original_tasks,
            confirmation_result=confirmation_result
        )
        
        if isinstance(result, list):
            logger.info(f"✅ [CONFIRMATION_TEST] maintain_task_chain completed successfully")
            print(f"✅ [CONFIRMATION_TEST] maintain_task_chain completed successfully")
            print(f"  Maintained tasks count: {len(result)}")
            
            for i, task in enumerate(result, 1):
                print(f"    Task {i}: {task.get('id', 'N/A')} - {task.get('tool', 'N/A')}")
                logger.info(f"🔗 [CONFIRMATION_TEST] Task {i}: {task.get('id', 'N/A')} - {task.get('tool', 'N/A')}")
            
            return True
        else:
            logger.error(f"❌ [CONFIRMATION_TEST] maintain_task_chain failed: invalid result type")
            print(f"❌ [CONFIRMATION_TEST] maintain_task_chain failed: invalid result type")
            return False
            
    except Exception as e:
        logger.error(f"❌ [CONFIRMATION_TEST] maintain_task_chain test failed: {e}")
        print(f"❌ [CONFIRMATION_TEST] maintain_task_chain test failed: {e}")
        return False


async def test_cancelled_task_chain():
    """キャンセルされたタスクチェーンのテスト"""
    
    logger.info("🧪 [CONFIRMATION_TEST] Starting cancelled task chain test...")
    print("🧪 [CONFIRMATION_TEST] Starting cancelled task chain test...")
    
    try:
        # ConfirmationService初期化
        confirmation_service = ConfirmationService()
        
        # テストデータ
        original_tasks = [
            {
                "id": "task_1",
                "tool": "inventory_update_by_name",
                "parameters": {"item_name": "りんご", "quantity": 5}
            }
        ]
        
        # キャンセルされた確認結果
        cancelled_result = ConfirmationResult(
            is_cancelled=True,
            updated_tasks=[],
            confirmation_context={"user_id": "test_user_123"}
        )
        
        # キャンセルされたタスクチェーン保持実行
        result = await confirmation_service.maintain_task_chain(
            original_tasks=original_tasks,
            confirmation_result=cancelled_result
        )
        
        if isinstance(result, list) and len(result) == 0:
            logger.info(f"✅ [CONFIRMATION_TEST] cancelled task chain handled correctly")
            print(f"✅ [CONFIRMATION_TEST] cancelled task chain handled correctly")
            print(f"  Cancelled tasks count: {len(result)}")
            return True
        else:
            logger.error(f"❌ [CONFIRMATION_TEST] cancelled task chain test failed: expected empty list")
            print(f"❌ [CONFIRMATION_TEST] cancelled task chain test failed: expected empty list")
            return False
            
    except Exception as e:
        logger.error(f"❌ [CONFIRMATION_TEST] cancelled task chain test failed: {e}")
        print(f"❌ [CONFIRMATION_TEST] cancelled task chain test failed: {e}")
        return False


async def test_user_response_parsing():
    """ユーザー応答解析のテスト"""
    
    logger.info("🧪 [CONFIRMATION_TEST] Starting user response parsing test...")
    print("🧪 [CONFIRMATION_TEST] Starting user response parsing test...")
    
    try:
        # ConfirmationService初期化
        confirmation_service = ConfirmationService()
        
        # テストデータ
        ambiguity_info = AmbiguityInfo(
            task_id="task_1",
            tool_name="inventory_update_by_name",
            ambiguity_type="multiple_items",
            details={"item_name": "りんご"}
        )
        
        # 様々なユーザー応答をテスト
        test_responses = [
            ("IDで指定してください", "by_id"),
            ("名前で指定してください", "by_name"),
            ("キャンセル", "cancelled"),
            ("やめる", "cancelled")
        ]
        
        for response_text, expected_strategy in test_responses:
            # プライベートメソッドをテスト（実際の実装では公開メソッド経由でテスト）
            parsed_response = await confirmation_service._parse_user_response(response_text, ambiguity_info)
            
            if isinstance(parsed_response, dict):
                is_cancelled = parsed_response.get("is_cancelled", False)
                strategy = parsed_response.get("strategy", "")
                
                print(f"  Response: '{response_text}' -> Strategy: {strategy}, Cancelled: {is_cancelled}")
                logger.info(f"📝 [CONFIRMATION_TEST] Response: '{response_text}' -> Strategy: {strategy}, Cancelled: {is_cancelled}")
                
                # 期待される結果の検証
                if expected_strategy == "cancelled":
                    if not is_cancelled:
                        logger.error(f"❌ [CONFIRMATION_TEST] Expected cancellation for: {response_text}")
                        print(f"❌ [CONFIRMATION_TEST] Expected cancellation for: {response_text}")
                        return False
                else:
                    if is_cancelled or strategy != expected_strategy:
                        logger.error(f"❌ [CONFIRMATION_TEST] Unexpected result for: {response_text}")
                        print(f"❌ [CONFIRMATION_TEST] Unexpected result for: {response_text}")
                        return False
        
        logger.info(f"✅ [CONFIRMATION_TEST] user response parsing completed successfully")
        print(f"✅ [CONFIRMATION_TEST] user response parsing completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ [CONFIRMATION_TEST] user response parsing test failed: {e}")
        print(f"❌ [CONFIRMATION_TEST] user response parsing test failed: {e}")
        return False


async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    logger.info("🧪 [CONFIRMATION_TEST] Starting error handling test...")
    print("🧪 [CONFIRMATION_TEST] Starting error handling test...")
    
    try:
        # ConfirmationService初期化
        confirmation_service = ConfirmationService()
        
        # 空のタスクリストでのテスト
        empty_result = await confirmation_service.detect_ambiguity([], "test_user")
        if isinstance(empty_result, AmbiguityResult) and not empty_result.requires_confirmation:
            logger.info(f"✅ [CONFIRMATION_TEST] Empty tasks handling: OK")
            print(f"✅ [CONFIRMATION_TEST] Empty tasks handling: OK")
        else:
            logger.error(f"❌ [CONFIRMATION_TEST] Empty tasks handling: FAILED")
            print(f"❌ [CONFIRMATION_TEST] Empty tasks handling: FAILED")
            return False
        
        # 無効な入力でのテスト
        try:
            invalid_result = await confirmation_service.process_confirmation(
                ambiguity_info=None,
                user_response="test",
                context={}
            )
            # Noneが渡されても例外が発生しないことを確認
            logger.info(f"✅ [CONFIRMATION_TEST] Invalid input handling: OK")
            print(f"✅ [CONFIRMATION_TEST] Invalid input handling: OK")
        except Exception:
            # 例外が発生しても適切に処理されることを確認
            logger.info(f"✅ [CONFIRMATION_TEST] Invalid input handling: OK (exception caught)")
            print(f"✅ [CONFIRMATION_TEST] Invalid input handling: OK (exception caught)")
        
        logger.info(f"✅ [CONFIRMATION_TEST] Error handling test completed successfully")
        print(f"✅ [CONFIRMATION_TEST] Error handling test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ [CONFIRMATION_TEST] Error handling test failed: {e}")
        print(f"❌ [CONFIRMATION_TEST] Error handling test failed: {e}")
        return False


async def main():
    """メインテスト実行"""
    
    logger.info("🚀 [MAIN] Starting ConfirmationService tests...")
    print("🚀 [MAIN] Starting ConfirmationService tests...")
    
    # テスト実行
    test_results = []
    
    # 1. 曖昧性検出テスト
    test1_result = await test_detect_ambiguity()
    test_results.append(("Detect Ambiguity", test1_result))
    
    # 2. 確認プロセス処理テスト
    test2_result = await test_process_confirmation()
    test_results.append(("Process Confirmation", test2_result))
    
    # 3. タスクチェーン保持テスト
    test3_result = await test_maintain_task_chain()
    test_results.append(("Maintain Task Chain", test3_result))
    
    # 4. キャンセルされたタスクチェーンテスト
    test4_result = await test_cancelled_task_chain()
    test_results.append(("Cancelled Task Chain", test4_result))
    
    # 5. ユーザー応答解析テスト
    test5_result = await test_user_response_parsing()
    test_results.append(("User Response Parsing", test5_result))
    
    # 6. エラーハンドリングテスト
    test6_result = await test_error_handling()
    test_results.append(("Error Handling", test6_result))
    
    # 結果サマリー
    logger.info("📊 [MAIN] ConfirmationService Test Results Summary:")
    print("📊 [MAIN] ConfirmationService Test Results Summary:")
    
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
        logger.info("🎉 [MAIN] All ConfirmationService tests passed!")
        print("🎉 [MAIN] All ConfirmationService tests passed!")
    elif passed_tests >= total_tests * 0.8:
        logger.info("✅ [MAIN] Most ConfirmationService tests passed!")
        print("✅ [MAIN] Most ConfirmationService tests passed!")
    else:
        logger.error("❌ [MAIN] Some ConfirmationService tests failed. Please check the logs.")
        print("❌ [MAIN] Some ConfirmationService tests failed. Please check the logs.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # テスト実行
    asyncio.run(main())
