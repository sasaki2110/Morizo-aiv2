#!/usr/bin/env python3
"""
Phase 2.5C: LLMService統合テスト

RequestAnalyzer が LLMService に正しく統合されているか確認
"""

import sys
import os
import asyncio

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.llm_service import LLMService


class TestResults:
    """テスト結果を保持"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.total = 0
        self.failures = []
    
    def add_test(self, name, passed, error_msg=None):
        self.total += 1
        if passed:
            self.passed += 1
            print(f"✅ {name}")
        else:
            self.failed += 1
            self.failures.append((name, error_msg))
            print(f"❌ {name}: {error_msg}")
    
    def print_summary(self):
        print("\n" + "="*50)
        print(f"テスト結果: {self.passed}/{self.total} 成功")
        if self.failed > 0:
            print(f"失敗: {self.failed}")
            for name, error in self.failures:
                print(f"  - {name}: {error}")
        print("="*50)


async def test_inventory_request(results):
    """在庫操作リクエストのテスト"""
    service = LLMService()
    
    try:
        # decompose_tasks を呼び出し
        tasks = await service.decompose_tasks(
            user_request="牛乳を2本追加して",
            available_tools=[],
            user_id="test_user",
            sse_session_id=None,
            session_context={}
        )
        
        if tasks and len(tasks) > 0:
            results.add_test("在庫操作リクエスト", True)
        else:
            results.add_test("在庫操作リクエスト", False, "タスクが生成されなかった")
    except Exception as e:
        results.add_test("在庫操作リクエスト", False, str(e))


async def test_main_proposal_request(results):
    """主菜提案リクエストのテスト"""
    service = LLMService()
    
    try:
        tasks = await service.decompose_tasks(
            user_request="レンコンの主菜を5件提案して",
            available_tools=[],
            user_id="test_user",
            sse_session_id=None,
            session_context={}
        )
        
        if tasks and len(tasks) > 0:
            results.add_test("主菜提案リクエスト", True)
        else:
            results.add_test("主菜提案リクエスト", False, "タスクが生成されなかった")
    except Exception as e:
        results.add_test("主菜提案リクエスト", False, str(e))


async def test_menu_request(results):
    """献立生成リクエストのテスト"""
    service = LLMService()
    
    try:
        tasks = await service.decompose_tasks(
            user_request="献立を教えて",
            available_tools=[],
            user_id="test_user",
            sse_session_id=None,
            session_context={}
        )
        
        if tasks and len(tasks) > 0:
            results.add_test("献立生成リクエスト", True)
        else:
            results.add_test("献立生成リクエスト", False, "タスクが生成されなかった")
    except Exception as e:
        results.add_test("献立生成リクエスト", False, str(e))


async def main():
    """メイン関数"""
    print("="*50)
    print("Phase 2.5C: LLMService統合テスト")
    print("="*50)
    print()
    
    results = TestResults()
    
    # テスト実行
    await test_inventory_request(results)
    await test_main_proposal_request(results)
    await test_menu_request(results)
    
    # 結果表示
    results.print_summary()
    
    # 終了コード
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

