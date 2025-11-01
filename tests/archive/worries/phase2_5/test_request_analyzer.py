#!/usr/bin/env python3
"""
Phase 2.5A: RequestAnalyzer の単体テスト

リクエスト分析機能の動作を確認する
実行方法: python test_request_analyzer.py
"""

import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from services.llm.request_analyzer import RequestAnalyzer


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


def test_inventory_operation(results):
    """在庫操作のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="牛乳を2本追加して",
        user_id="test_user",
        sse_session_id=None,
        session_context={}
    )
    
    if result["pattern"] == "inventory" and len(result["ambiguities"]) == 0:
        results.add_test("在庫操作のパターン判定", True)
    else:
        results.add_test("在庫操作のパターン判定", False, 
                        f"期待: inventory, 実際: {result['pattern']}")


def test_menu_generation(results):
    """献立生成のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="献立を教えて",
        user_id="test_user",
        sse_session_id=None,
        session_context={}
    )
    
    if result["pattern"] == "menu" and len(result["ambiguities"]) == 0:
        results.add_test("献立生成のパターン判定", True)
    else:
        results.add_test("献立生成のパターン判定", False,
                        f"期待: menu, 実際: {result['pattern']}")


def test_main_proposal_with_ingredient(results):
    """主菜提案（食材指定）のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="レンコンの主菜を5件提案して",
        user_id="test_user",
        sse_session_id=None,
        session_context={}
    )
    
    if (result["pattern"] == "main" and 
        result["params"]["category"] == "main" and
        result["params"]["main_ingredient"] == "レンコン" and
        len(result["ambiguities"]) == 0):
        results.add_test("主菜提案（食材指定）のパターン判定", True)
    else:
        results.add_test("主菜提案（食材指定）のパターン判定", False,
                        f"pattern={result['pattern']}, main_ingredient={result['params'].get('main_ingredient')}")


def test_main_proposal_without_ingredient(results):
    """主菜提案（食材未指定）のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="主菜を5件提案して",
        user_id="test_user",
        sse_session_id=None,
        session_context={}
    )
    
    if (result["pattern"] == "main" and
        result["params"]["category"] == "main" and
        result["params"]["main_ingredient"] is None and
        len(result["ambiguities"]) == 1 and
        result["ambiguities"][0]["type"] == "missing_main_ingredient"):
        results.add_test("主菜提案（食材未指定）のパターン判定", True)
    else:
        results.add_test("主菜提案（食材未指定）のパターン判定", False,
                        f"pattern={result['pattern']}, ambiguities={len(result['ambiguities'])}")


def test_main_additional_proposal(results):
    """主菜追加提案のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="もう5件主菜を提案して",
        user_id="test_user",
        sse_session_id="test_session_id",
        session_context={}
    )
    
    if (result["pattern"] == "main_additional" and
        result["params"]["category"] == "main" and
        len(result["ambiguities"]) == 0):
        results.add_test("主菜追加提案のパターン判定", True)
    else:
        results.add_test("主菜追加提案のパターン判定", False,
                        f"pattern={result['pattern']}, category={result['params'].get('category')}")


def test_sub_proposal_with_context(results):
    """副菜提案（セッションあり）のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="副菜を5件提案して",
        user_id="test_user",
        sse_session_id=None,
        session_context={
            "used_ingredients": ["レンコン", "肉"]
        }
    )
    
    if (result["pattern"] == "sub" and
        result["params"]["category"] == "sub" and
        result["params"]["used_ingredients"] == ["レンコン", "肉"] and
        len(result["ambiguities"]) == 0):
        results.add_test("副菜提案（セッションあり）のパターン判定", True)
    else:
        results.add_test("副菜提案（セッションあり）のパターン判定", False,
                        f"pattern={result['pattern']}, used_ingredients={result['params'].get('used_ingredients')}")


def test_sub_proposal_without_context(results):
    """副菜提案（セッションなし）のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="副菜を5件提案して",
        user_id="test_user",
        sse_session_id=None,
        session_context={}
    )
    
    if (result["pattern"] == "sub" and
        result["params"]["category"] == "sub" and
        result["params"]["used_ingredients"] == [] and
        len(result["ambiguities"]) == 1 and
        result["ambiguities"][0]["type"] == "missing_used_ingredients"):
        results.add_test("副菜提案（セッションなし）のパターン判定", True)
    else:
        results.add_test("副菜提案（セッションなし）のパターン判定", False,
                        f"pattern={result['pattern']}, ambiguities={len(result['ambiguities'])}")


def test_soup_proposal_japanese(results):
    """汁物提案（和食）のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="味噌汁を5件提案して",
        user_id="test_user",
        sse_session_id=None,
        session_context={
            "used_ingredients": ["豆腐", "ワカメ"],
            "menu_category": "japanese"
        }
    )
    
    if (result["pattern"] == "soup" and
        result["params"]["category"] == "soup" and
        result["params"]["menu_category"] == "japanese" and
        len(result["ambiguities"]) == 0):
        results.add_test("汁物提案（和食）のパターン判定", True)
    else:
        results.add_test("汁物提案（和食）のパターン判定", False,
                        f"pattern={result['pattern']}, menu_category={result['params'].get('menu_category')}")


def test_soup_proposal_western(results):
    """汁物提案（洋食）のパターン判定"""
    analyzer = RequestAnalyzer()
    
    result = analyzer.analyze(
        request="スープを5件提案して",
        user_id="test_user",
        sse_session_id=None,
        session_context={
            "used_ingredients": ["鶏肉", "キャベツ"],
            "menu_category": "western"
        }
    )
    
    if (result["pattern"] == "soup" and
        result["params"]["category"] == "soup" and
        result["params"]["menu_category"] == "western" and
        len(result["ambiguities"]) == 0):
        results.add_test("汁物提案（洋食）のパターン判定", True)
    else:
        results.add_test("汁物提案（洋食）のパターン判定", False,
                        f"pattern={result['pattern']}, menu_category={result['params'].get('menu_category')}")


def test_ingredient_extraction(results):
    """主要食材の抽出テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("レンコンの主菜を教えて", "レンコン"),
        ("鶏肉を使った副菜を提案して", "鶏肉"),
        ("大根で味噌汁を作りたい", "大根"),
        ("キャベツ主菜", "キャベツ"),
    ]
    
    all_passed = True
    for request, expected in test_cases:
        ingredient = analyzer._extract_ingredient(request)
        if ingredient != expected:
            all_passed = False
    
    if all_passed:
        results.add_test("主要食材の抽出テスト", True)
    else:
        results.add_test("主要食材の抽出テスト", False, "一部の抽出に失敗")


def test_additional_proposal_keywords(results):
    """追加提案キーワードの判定テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("もう5件主菜を提案して", "test_session", True),
        ("他の提案を見せて", "test_session", True),
        ("もっと教えて", "test_session", True),
        ("追加で主菜を", "test_session", True),
        ("主菜を提案して", "test_session", False),
        ("もう5件主菜を提案して", None, False),
    ]
    
    all_passed = True
    for request, sse_session_id, expected in test_cases:
        result = analyzer._is_additional_proposal(request, sse_session_id)
        if result != expected:
            all_passed = False
    
    if all_passed:
        results.add_test("追加提案キーワードの判定テスト", True)
    else:
        results.add_test("追加提案キーワードの判定テスト", False, "一部の判定に失敗")


def test_inventory_operation_keywords(results):
    """在庫操作キーワードの判定テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("牛乳を追加して", True),
        ("ピーマンを削除して", True),
        ("在庫を更新して", True),
        ("牛乳を変えて", True),
        ("在庫を確認して", True),
        ("主菜を提案して", False),
    ]
    
    all_passed = True
    for request, expected in test_cases:
        result = analyzer._is_inventory_operation(request)
        if result != expected:
            all_passed = False
    
    if all_passed:
        results.add_test("在庫操作キーワードの判定テスト", True)
    else:
        results.add_test("在庫操作キーワードの判定テスト", False, "一部の判定に失敗")


def main():
    """メイン関数"""
    print("="*50)
    print("Phase 2.5A: RequestAnalyzer 単体テスト")
    print("="*50)
    print()
    
    results = TestResults()
    
    # テスト実行
    test_inventory_operation(results)
    test_menu_generation(results)
    test_main_proposal_with_ingredient(results)
    test_main_proposal_without_ingredient(results)
    test_main_additional_proposal(results)
    test_sub_proposal_with_context(results)
    test_sub_proposal_without_context(results)
    test_soup_proposal_japanese(results)
    test_soup_proposal_western(results)
    test_ingredient_extraction(results)
    test_additional_proposal_keywords(results)
    test_inventory_operation_keywords(results)
    
    # 結果表示
    results.print_summary()
    
    # 終了コード
    return 0 if results.failed == 0 else 1


if __name__ == "__main__":
    exit(main())
