#!/usr/bin/env python3
"""
05_3_test_llm.py

LLMServiceの動作確認テスト
- タスク分解機能のテスト
- 回答整形機能のテスト
- 制約解決機能のテスト
- ツール説明取得のテスト
- 動的プロンプト生成のテスト
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
from services.llm_service import LLMService
from services.tool_router import ToolRouter

# ロガーの初期化
logger = GenericLogger("test", "llm_service")


async def test_decompose_tasks():
    """タスク分解機能のテスト"""
    
    logger.info("🧪 [LLM_TEST] Starting decompose_tasks test...")
    print("🧪 [LLM_TEST] Starting decompose_tasks test...")
    
    try:
        # LLMService初期化
        llm_service = LLMService()
        
        # テストデータ
        user_request = "在庫を確認して、献立を提案してください"
        available_tools = ["inventory_list", "generate_menu_plan_with_history"]
        user_id = "test_user_123"
        
        # タスク分解実行
        result = await llm_service.decompose_tasks(
            user_request=user_request,
            available_tools=available_tools,
            user_id=user_id
        )
        
        # 結果確認
        if isinstance(result, list) and len(result) > 0:
            logger.info(f"✅ [LLM_TEST] decompose_tasks completed successfully: {len(result)} tasks")
            print(f"✅ [LLM_TEST] decompose_tasks completed successfully: {len(result)} tasks")
            
            # タスクの詳細を表示
            for i, task in enumerate(result, 1):
                print(f"  Task {i}: {task.get('description', 'N/A')}")
                logger.info(f"📋 [LLM_TEST] Task {i}: {task.get('description', 'N/A')}")
            
            return True
        else:
            logger.error(f"❌ [LLM_TEST] decompose_tasks failed: empty result")
            print(f"❌ [LLM_TEST] decompose_tasks failed: empty result")
            return False
            
    except Exception as e:
        logger.error(f"❌ [LLM_TEST] decompose_tasks test failed: {e}")
        print(f"❌ [LLM_TEST] decompose_tasks test failed: {e}")
        return False


async def test_format_response():
    """回答整形機能のテスト"""
    
    logger.info("🧪 [LLM_TEST] Starting format_response test...")
    print("🧪 [LLM_TEST] Starting format_response test...")
    
    try:
        # LLMService初期化
        llm_service = LLMService()
        
        # テストデータ
        results = [
            {
                "task_id": "task_1",
                "success": True,
                "data": {"inventory_count": 5}
            },
            {
                "task_id": "task_2", 
                "success": True,
                "data": {"menu_plan": "和食の献立"}
            }
        ]
        
        # 回答整形実行
        formatted_response = await llm_service.format_response(results)
        
        # 結果確認
        if isinstance(formatted_response, str) and len(formatted_response) > 0:
            logger.info(f"✅ [LLM_TEST] format_response completed successfully")
            print(f"✅ [LLM_TEST] format_response completed successfully")
            print(f"  Formatted response: {formatted_response}")
            logger.info(f"📝 [LLM_TEST] Formatted response: {formatted_response}")
            return True
        else:
            logger.error(f"❌ [LLM_TEST] format_response failed: empty result")
            print(f"❌ [LLM_TEST] format_response failed: empty result")
            return False
            
    except Exception as e:
        logger.error(f"❌ [LLM_TEST] format_response test failed: {e}")
        print(f"❌ [LLM_TEST] format_response test failed: {e}")
        return False


async def test_solve_constraints():
    """制約解決機能のテスト"""
    
    logger.info("🧪 [LLM_TEST] Starting solve_constraints test...")
    print("🧪 [LLM_TEST] Starting solve_constraints test...")
    
    try:
        # LLMService初期化
        llm_service = LLMService()
        
        # テストデータ
        candidates = [
            {"name": "option_1", "score": 0.8},
            {"name": "option_2", "score": 0.6},
            {"name": "option_3", "score": 0.9}
        ]
        constraints = {"min_score": 0.7}
        
        # 制約解決実行
        result = await llm_service.solve_constraints(candidates, constraints)
        
        # 結果確認
        if isinstance(result, dict) and "selected" in result:
            logger.info(f"✅ [LLM_TEST] solve_constraints completed successfully")
            print(f"✅ [LLM_TEST] solve_constraints completed successfully")
            print(f"  Selected: {result.get('selected', {})}")
            print(f"  Reason: {result.get('reason', 'N/A')}")
            logger.info(f"🎯 [LLM_TEST] Selected: {result.get('selected', {})}")
            logger.info(f"💭 [LLM_TEST] Reason: {result.get('reason', 'N/A')}")
            return True
        else:
            logger.error(f"❌ [LLM_TEST] solve_constraints failed: invalid result")
            print(f"❌ [LLM_TEST] solve_constraints failed: invalid result")
            return False
            
    except Exception as e:
        logger.error(f"❌ [LLM_TEST] solve_constraints test failed: {e}")
        print(f"❌ [LLM_TEST] solve_constraints test failed: {e}")
        return False


async def test_get_available_tools_description():
    """ツール説明取得のテスト"""
    
    logger.info("🧪 [LLM_TEST] Starting get_available_tools_description test...")
    print("🧪 [LLM_TEST] Starting get_available_tools_description test...")
    
    try:
        # LLMService初期化
        llm_service = LLMService()
        
        # ToolRouter初期化
        tool_router = ToolRouter()
        
        # ツール説明取得実行
        description = llm_service.get_available_tools_description(tool_router)
        
        # 結果確認
        if isinstance(description, str) and len(description) > 0:
            logger.info(f"✅ [LLM_TEST] get_available_tools_description completed successfully")
            print(f"✅ [LLM_TEST] get_available_tools_description completed successfully")
            
            # 説明の一部を表示
            lines = description.split('\n')
            print(f"  Description preview ({len(lines)} lines):")
            for i, line in enumerate(lines[:5], 1):  # 最初の5行を表示
                print(f"    {i}. {line}")
            
            logger.info(f"📋 [LLM_TEST] Description length: {len(description)} characters")
            return True
        else:
            logger.error(f"❌ [LLM_TEST] get_available_tools_description failed: empty result")
            print(f"❌ [LLM_TEST] get_available_tools_description failed: empty result")
            return False
            
    except Exception as e:
        logger.error(f"❌ [LLM_TEST] get_available_tools_description test failed: {e}")
        print(f"❌ [LLM_TEST] get_available_tools_description test failed: {e}")
        return False


async def test_create_dynamic_prompt():
    """動的プロンプト生成のテスト"""
    
    logger.info("🧪 [LLM_TEST] Starting create_dynamic_prompt test...")
    print("🧪 [LLM_TEST] Starting create_dynamic_prompt test...")
    
    try:
        # LLMService初期化
        llm_service = LLMService()
        
        # テストデータ
        base_prompt = "あなたは料理の専門家です。"
        tool_descriptions = "利用可能なツール:\n- inventory_list: 在庫一覧を取得\n- generate_menu_plan: 献立を生成"
        user_context = {
            "user_id": "test_user_123",
            "session_id": "session_456",
            "timestamp": "2025-01-29 10:00:00"
        }
        
        # 動的プロンプト生成実行
        dynamic_prompt = llm_service.create_dynamic_prompt(
            base_prompt=base_prompt,
            tool_descriptions=tool_descriptions,
            user_context=user_context
        )
        
        # 結果確認
        if isinstance(dynamic_prompt, str) and len(dynamic_prompt) > len(base_prompt):
            logger.info(f"✅ [LLM_TEST] create_dynamic_prompt completed successfully")
            print(f"✅ [LLM_TEST] create_dynamic_prompt completed successfully")
            
            # プロンプトの一部を表示
            print(f"  Dynamic prompt preview:")
            print(f"    {dynamic_prompt[:200]}...")
            
            logger.info(f"📝 [LLM_TEST] Dynamic prompt length: {len(dynamic_prompt)} characters")
            return True
        else:
            logger.error(f"❌ [LLM_TEST] create_dynamic_prompt failed: invalid result")
            print(f"❌ [LLM_TEST] create_dynamic_prompt failed: invalid result")
            return False
            
    except Exception as e:
        logger.error(f"❌ [LLM_TEST] create_dynamic_prompt test failed: {e}")
        print(f"❌ [LLM_TEST] create_dynamic_prompt test failed: {e}")
        return False


async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    logger.info("🧪 [LLM_TEST] Starting error handling test...")
    print("🧪 [LLM_TEST] Starting error handling test...")
    
    try:
        # LLMService初期化
        llm_service = LLMService()
        
        # 空のリストでのテスト
        empty_results = await llm_service.format_response([])
        if isinstance(empty_results, str):
            logger.info(f"✅ [LLM_TEST] Empty results handling: OK")
            print(f"✅ [LLM_TEST] Empty results handling: OK")
        else:
            logger.error(f"❌ [LLM_TEST] Empty results handling: FAILED")
            print(f"❌ [LLM_TEST] Empty results handling: FAILED")
            return False
        
        # 空の候補リストでのテスト
        empty_candidates_result = await llm_service.solve_constraints([], {})
        if isinstance(empty_candidates_result, dict) and "selected" in empty_candidates_result:
            logger.info(f"✅ [LLM_TEST] Empty candidates handling: OK")
            print(f"✅ [LLM_TEST] Empty candidates handling: OK")
        else:
            logger.error(f"❌ [LLM_TEST] Empty candidates handling: FAILED")
            print(f"❌ [LLM_TEST] Empty candidates handling: FAILED")
            return False
        
        logger.info(f"✅ [LLM_TEST] Error handling test completed successfully")
        print(f"✅ [LLM_TEST] Error handling test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ [LLM_TEST] Error handling test failed: {e}")
        print(f"❌ [LLM_TEST] Error handling test failed: {e}")
        return False


async def main():
    """メインテスト実行"""
    
    logger.info("🚀 [MAIN] Starting LLMService tests...")
    print("🚀 [MAIN] Starting LLMService tests...")
    
    # テスト実行
    test_results = []
    
    # 1. タスク分解テスト
    test1_result = await test_decompose_tasks()
    test_results.append(("Decompose Tasks", test1_result))
    
    # 2. 回答整形テスト
    test2_result = await test_format_response()
    test_results.append(("Format Response", test2_result))
    
    # 3. 制約解決テスト
    test3_result = await test_solve_constraints()
    test_results.append(("Solve Constraints", test3_result))
    
    # 4. ツール説明取得テスト
    test4_result = await test_get_available_tools_description()
    test_results.append(("Get Tools Description", test4_result))
    
    # 5. 動的プロンプト生成テスト
    test5_result = await test_create_dynamic_prompt()
    test_results.append(("Create Dynamic Prompt", test5_result))
    
    # 6. エラーハンドリングテスト
    test6_result = await test_error_handling()
    test_results.append(("Error Handling", test6_result))
    
    # 結果サマリー
    logger.info("📊 [MAIN] LLMService Test Results Summary:")
    print("📊 [MAIN] LLMService Test Results Summary:")
    
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
        logger.info("🎉 [MAIN] All LLMService tests passed!")
        print("🎉 [MAIN] All LLMService tests passed!")
    elif passed_tests >= total_tests * 0.8:
        logger.info("✅ [MAIN] Most LLMService tests passed!")
        print("✅ [MAIN] Most LLMService tests passed!")
    else:
        logger.error("❌ [MAIN] Some LLMService tests failed. Please check the logs.")
        print("❌ [MAIN] Some LLMService tests failed. Please check the logs.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # テスト実行
    asyncio.run(main())
