"""
Phase 3B テスト: RequestAnalyzerの副菜・汁物パターン認識
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.llm.request_analyzer import RequestAnalyzer


async def test_sub_pattern_detection():
    """副菜パターン認識テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("副菜を5件提案して", "sub"),
        ("サブを教えて", "sub"),
        ("副菜を提案して", "sub"),
        ("サブの提案", "sub"),
    ]
    
    print("\n=== test_sub_pattern_detection ===")
    for request, expected_pattern in test_cases:
        analysis_result = analyzer.analyze(request, "test_user", None, {})
        pattern = analysis_result["pattern"]
        
        print(f"Request: '{request}'")
        print(f"Expected: {expected_pattern}, Got: {pattern}")
        
        assert pattern == expected_pattern, f"パターンが一致しません: {pattern} != {expected_pattern}"
        print("✅ PASS")
    
    print("✅ All sub pattern tests passed!")


async def test_soup_pattern_detection():
    """汁物パターン認識テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("汁物を提案して", "soup"),
        ("味噌汁を作りたい", "soup"),
        ("スープを教えて", "soup"),
        ("汁物を5件提案して", "soup"),
    ]
    
    print("\n=== test_soup_pattern_detection ===")
    for request, expected_pattern in test_cases:
        analysis_result = analyzer.analyze(request, "test_user", None, {})
        pattern = analysis_result["pattern"]
        
        print(f"Request: '{request}'")
        print(f"Expected: {expected_pattern}, Got: {pattern}")
        
        assert pattern == expected_pattern, f"パターンが一致しません: {pattern} != {expected_pattern}"
        print("✅ PASS")
    
    print("✅ All soup pattern tests passed!")


async def test_sub_additional_pattern_detection():
    """副菜追加提案パターン認識テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("もう副菜を提案して", "sub_additional"),
        ("他のサブは？", "sub_additional"),
        ("もっと副菜を教えて", "sub_additional"),
    ]
    
    print("\n=== test_sub_additional_pattern_detection ===")
    for request, expected_pattern in test_cases:
        analysis_result = analyzer.analyze(request, "test_user", "test_session", {})
        pattern = analysis_result["pattern"]
        
        print(f"Request: '{request}'")
        print(f"Expected: {expected_pattern}, Got: {pattern}")
        
        assert pattern == expected_pattern, f"パターンが一致しません: {pattern} != {expected_pattern}"
        print("✅ PASS")
    
    print("✅ All sub_additional pattern tests passed!")


async def test_soup_additional_pattern_detection():
    """汁物追加提案パターン認識テスト"""
    analyzer = RequestAnalyzer()
    
    test_cases = [
        ("もうスープを提案して", "soup_additional"),
        ("他の汁物は？", "soup_additional"),
        ("もっと味噌汁を教えて", "soup_additional"),
    ]
    
    print("\n=== test_soup_additional_pattern_detection ===")
    for request, expected_pattern in test_cases:
        analysis_result = analyzer.analyze(request, "test_user", "test_session", {})
        pattern = analysis_result["pattern"]
        
        print(f"Request: '{request}'")
        print(f"Expected: {expected_pattern}, Got: {pattern}")
        
        assert pattern == expected_pattern, f"パターンが一致しません: {pattern} != {expected_pattern}"
        print("✅ PASS")
    
    print("✅ All soup_additional pattern tests passed!")


async def test_params_extraction():
    """パラメータ抽出テスト"""
    analyzer = RequestAnalyzer()
    
    # used_ingredients を含むセッションコンテキスト
    session_context = {
        "used_ingredients": ["レンコン", "鶏もも肉"],
        "menu_category": "japanese"
    }
    
    # 副菜提案リクエスト
    sub_analysis = analyzer.analyze("副菜を提案して", "test_user", None, session_context)
    print("\n=== test_params_extraction (sub) ===")
    print(f"Pattern: {sub_analysis['pattern']}")
    print(f"Params: {sub_analysis['params']}")
    
    assert sub_analysis["pattern"] == "sub"
    assert sub_analysis["params"]["category"] == "sub"
    assert sub_analysis["params"]["used_ingredients"] == ["レンコン", "鶏もも肉"]
    
    print("✅ PASS")
    
    # 汁物提案リクエスト
    soup_analysis = analyzer.analyze("汁物を提案して", "test_user", None, session_context)
    print("\n=== test_params_extraction (soup) ===")
    print(f"Pattern: {soup_analysis['pattern']}")
    print(f"Params: {soup_analysis['params']}")
    
    assert soup_analysis["pattern"] == "soup"
    assert soup_analysis["params"]["category"] == "soup"
    assert soup_analysis["params"]["used_ingredients"] == ["レンコン", "鶏もも肉"]
    assert soup_analysis["params"]["menu_category"] == "japanese"
    
    print("✅ PASS")


async def run_all_tests():
    """すべてのテストを実行"""
    print("\n" + "="*60)
    print("Phase 3B: RequestAnalyzer テスト")
    print("="*60)
    
    await test_sub_pattern_detection()
    await test_soup_pattern_detection()
    await test_sub_additional_pattern_detection()
    await test_soup_additional_pattern_detection()
    await test_params_extraction()
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())

