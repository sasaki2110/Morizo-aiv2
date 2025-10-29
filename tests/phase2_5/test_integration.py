#!/usr/bin/env python3
"""
Phase 2.5E: 統合テスト

Phase 2.5の全コンポーネントを統合した結合テスト
- RequestAnalyzer
- PromptManager
- SessionService
- LLMService

実行方法: python3 test_integration.py
"""

import sys
import os
import asyncio

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.llm.request_analyzer import RequestAnalyzer
from services.llm.prompt_manager import PromptManager
from services.session_service import SessionService
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
        print("\n" + "="*80)
        print(f"テスト結果: {self.passed}/{self.total} 成功, {self.failed} 失敗")
        if self.failed > 0:
            print("\n失敗したテスト:")
            for name, error in self.failures:
                print(f"  - {name}: {error}")
        print("="*80)
        return self.failed == 0


def test_pattern_detection(results):
    """1. パターン判定の正確性テスト"""
    analyzer = RequestAnalyzer()
    
    # 在庫操作パターン
    result = analyzer.analyze("牛乳を2本追加して", "test_user", None, {})
    passed = result["pattern"] == "inventory"
    results.add_test("在庫操作パターン判定", passed, f"期待: inventory, 実際: {result['pattern']}")
    
    # 主菜提案パターン
    result = analyzer.analyze("主菜を5件提案して", "test_user", None, {})
    passed = result["pattern"] == "main"
    results.add_test("主菜提案パターン判定", passed, f"期待: main, 実際: {result['pattern']}")
    
    # 副菜提案パターン
    result = analyzer.analyze("副菜を5件提案して", "test_user", None, {"used_ingredients": ["レンコン"]})
    passed = result["pattern"] == "sub"
    results.add_test("副菜提案パターン判定", passed, f"期待: sub, 実際: {result['pattern']}")
    
    # 汁物提案パターン
    result = analyzer.analyze("汁物を5件提案して", "test_user", None, {"used_ingredients": ["レンコン"], "menu_category": "japanese"})
    passed = result["pattern"] == "soup"
    results.add_test("汁物提案パターン判定", passed, f"期待: soup, 実際: {result['pattern']}")


def test_parameter_extraction(results):
    """2. パラメータ抽出の正確性テスト"""
    analyzer = RequestAnalyzer()
    
    # 主菜提案（食材指定）
    result = analyzer.analyze("レンコンの主菜を5件提案して", "test_user", None, {})
    passed = result["params"].get("category") == "main" and result["params"].get("main_ingredient") == "レンコン"
    results.add_test("主菜提案パラメータ抽出（食材指定）", passed, f"実際: {result['params']}")
    
    # 副菜提案（使用食材）
    result = analyzer.analyze("副菜を5件提案して", "test_user", None, {"used_ingredients": ["レンコン", "肉"]})
    passed = result["params"].get("category") == "sub" and "used_ingredients" in result["params"]
    results.add_test("副菜提案パラメータ抽出", passed, f"実際: {result['params']}")
    
    # 汁物提案（献立カテゴリ）
    result = analyzer.analyze("汁物を5件提案して", "test_user", None, {"used_ingredients": ["レンコン"], "menu_category": "western"})
    passed = result["params"].get("menu_category") == "western"
    results.add_test("汁物提案パラメータ抽出（献立カテゴリ）", passed, f"実際: {result['params']}")


def test_ambiguity_detection(results):
    """3. 曖昧性検出の正確性テスト"""
    analyzer = RequestAnalyzer()
    
    # 主菜提案（食材未指定）
    result = analyzer.analyze("主菜を5件提案して", "test_user", None, {})
    passed = len(result["ambiguities"]) > 0
    results.add_test("主菜提案曖昧性検出（食材未指定）", passed, f"検出数: {len(result['ambiguities'])}")
    
    # 副菜提案（セッションなし）
    result = analyzer.analyze("副菜を5件提案して", "test_user", None, {})
    passed = len(result["ambiguities"]) > 0
    results.add_test("副菜提案曖昧性検出（セッションなし）", passed, f"検出数: {len(result['ambiguities'])}")
    
    # 主菜提案（食材指定）→ 曖昧性なし
    result = analyzer.analyze("レンコンの主菜を5件提案して", "test_user", None, {})
    passed = len(result["ambiguities"]) == 0
    results.add_test("主菜提案曖昧性なし（食材指定）", passed, f"検出数: {len(result['ambiguities'])}")


def test_prompt_construction(results):
    """4. プロンプト構築の正確性テスト"""
    analyzer = RequestAnalyzer()
    manager = PromptManager()
    
    # 主菜提案プロンプト
    analysis = analyzer.analyze("レンコンの主菜を5件提案して", "test_user", None, {})
    prompt = manager.build_prompt(analysis, "test_user")
    passed = "task1" in prompt and "inventory_service.get_inventory()" in prompt
    results.add_test("主菜提案プロンプト構築", passed, "プロンプトに基本的なタスク定義が含まれること")
    
    # 在庫操作プロンプト
    analysis = analyzer.analyze("牛乳を2本追加して", "test_user", None, {})
    prompt = manager.build_prompt(analysis, "test_user")
    passed = len(prompt) > 0 and "牛乳" in prompt
    results.add_test("在庫操作プロンプト構築", passed, "プロンプトにアイテム名が含まれること")


def test_session_management(results):
    """6. セッション管理テスト"""
    service = SessionService()
    
    # セッション作成と新規フィールドの確認
    async def test():
        session = await service.create_session("test_user")
        passed = (
            hasattr(session, "current_stage") and
            hasattr(session, "selected_main_dish") and
            hasattr(session, "selected_sub_dish") and
            hasattr(session, "selected_soup") and
            hasattr(session, "used_ingredients") and
            hasattr(session, "menu_category")
        )
        results.add_test("セッション新規フィールド確認", passed, "Phase 2.5Dで追加したフィールドが存在すること")
        
        # セッション段階管理のテスト
        passed = session.get_current_stage() == "main"
        results.add_test("セッション段階取得", passed, f"初期段階: {session.get_current_stage()}")
        
        # レシピ選択のテスト
        recipe = {"title": "テストレシピ", "ingredients": ["テスト食材"], "menu_type": "和食"}
        session.set_selected_recipe("main", recipe)
        passed = session.get_current_stage() == "sub"
        results.add_test("セッション段階更新", passed, f"選択後段階: {session.get_current_stage()}")
        
        # 使用食材の確認
        passed = len(session.get_used_ingredients()) > 0
        results.add_test("セッション使用食材記録", passed, f"使用食材: {session.get_used_ingredients()}")
        
        # 献立カテゴリの確認
        passed = session.get_menu_category() == "japanese"
        results.add_test("セッション献立カテゴリ", passed, f"献立カテゴリ: {session.get_menu_category()}")
    
    # テスト実行
    asyncio.run(test())


async def test_end_to_end(results):
    """5. エンドツーエンドテスト（リクエスト→タスク生成）"""
    service = LLMService()
    
    # 利用可能なツールリスト（簡易版）
    available_tools = [
        "inventory_service.add_inventory",
        "inventory_service.get_inventory",
        "recipe_service.generate_proposals",
        "recipe_service.search_recipes_from_web"
    ]
    
    try:
        # 在庫操作リクエスト
        tasks = await service.decompose_tasks(
            "牛乳を2本追加して", 
            available_tools, 
            "test_user"
        )
        passed = len(tasks) > 0
        results.add_test("エンドツーエンド（在庫操作）", passed, f"生成されたタスク数: {len(tasks)}")
        
        # 主菜提案リクエスト
        tasks = await service.decompose_tasks(
            "レンコンの主菜を5件提案して", 
            available_tools, 
            "test_user"
        )
        passed = len(tasks) > 0
        results.add_test("エンドツーエンド（主菜提案）", passed, f"タスク数: {len(tasks)}")
        
    except Exception as e:
        results.add_test("エンドツーエンドテスト", False, f"エラー: {e}")


def run_all_tests():
    """全てのテストを実行"""
    print("="*80)
    print("Phase 2.5E: 統合テスト")
    print("="*80)
    
    results = TestResults()
    
    # 1. パターン判定の正確性テスト
    print("\n1. パターン判定の正確性テスト")
    test_pattern_detection(results)
    
    # 2. パラメータ抽出の正確性テスト
    print("\n2. パラメータ抽出の正確性テスト")
    test_parameter_extraction(results)
    
    # 3. 曖昧性検出の正確性テスト
    print("\n3. 曖昧性検出の正確性テスト")
    test_ambiguity_detection(results)
    
    # 4. プロンプト構築の正確性テスト
    print("\n4. プロンプト構築の正確性テスト")
    test_prompt_construction(results)
    
    # 5. エンドツーエンドテスト
    print("\n5. エンドツーエンドテスト（リクエスト→タスク生成）")
    asyncio.run(test_end_to_end(results))
    
    # 6. セッション管理テスト
    print("\n6. セッション管理テスト")
    test_session_management(results)
    
    # 結果サマリー
    return results.print_summary()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

