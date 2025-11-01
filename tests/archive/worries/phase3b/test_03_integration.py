"""
Phase 3B 統合テスト: RequestAnalyzer → PromptManager連携
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.llm.request_analyzer import RequestAnalyzer
from services.llm.prompt_manager import PromptManager


def test_sub_proposal_integration():
    """副菜提案の統合テスト"""
    print("\n=== test_sub_proposal_integration ===")
    
    # リクエスト分析
    analyzer = RequestAnalyzer()
    user_id = "test_user_123"
    session_context = {
        "used_ingredients": ["レンコン", "鶏もも肉"],
    }
    
    analysis_result = analyzer.analyze("副菜を5件提案して", user_id, None, session_context)
    
    print(f"Analysis result:")
    print(f"  - Pattern: {analysis_result['pattern']}")
    print(f"  - Category: {analysis_result['params'].get('category')}")
    print(f"  - Used ingredients: {analysis_result['params'].get('used_ingredients')}")
    
    # パターン検証
    assert analysis_result["pattern"] == "sub", "副菜パターンが認識されていません"
    assert analysis_result["params"]["category"] == "sub", "category が正しく設定されていません"
    assert "レンコン" in analysis_result["params"]["used_ingredients"], "used_ingredients が正しく設定されていません"
    
    # プロンプト生成
    prompt_manager = PromptManager()
    prompt = prompt_manager.build_prompt(analysis_result, user_id)
    
    print(f"\nGenerated prompt length: {len(prompt)} characters")
    
    # プロンプト検証
    assert "category=\"sub\"" in prompt, "プロンプトに category=\"sub\" が含まれていません"
    assert "レンコン" in prompt, "プロンプトに used_ingredients が含まれていません"
    assert "副菜提案の4段階タスク構成" in prompt, "プロンプトにタスク構成の説明が含まれていません"
    
    print("✅ Integration test passed!")


def test_soup_proposal_integration():
    """汁物提案の統合テスト"""
    print("\n=== test_soup_proposal_integration ===")
    
    # リクエスト分析
    analyzer = RequestAnalyzer()
    user_id = "test_user_456"
    session_context = {
        "used_ingredients": ["玉ねぎ", "ニンジン", "キャベツ"],
        "menu_category": "japanese",
    }
    
    analysis_result = analyzer.analyze("味噌汁を提案して", user_id, None, session_context)
    
    print(f"Analysis result:")
    print(f"  - Pattern: {analysis_result['pattern']}")
    print(f"  - Category: {analysis_result['params'].get('category')}")
    print(f"  - Used ingredients: {analysis_result['params'].get('used_ingredients')}")
    print(f"  - Menu category: {analysis_result['params'].get('menu_category')}")
    
    # パターン検証
    assert analysis_result["pattern"] == "soup", "汁物パターンが認識されていません"
    assert analysis_result["params"]["category"] == "soup", "category が正しく設定されていません"
    assert "玉ねぎ" in analysis_result["params"]["used_ingredients"], "used_ingredients が正しく設定されていません"
    assert analysis_result["params"]["menu_category"] == "japanese", "menu_category が正しく設定されていません"
    
    # プロンプト生成
    prompt_manager = PromptManager()
    prompt = prompt_manager.build_prompt(analysis_result, user_id)
    
    print(f"\nGenerated prompt length: {len(prompt)} characters")
    
    # プロンプト検証
    assert "category=\"soup\"" in prompt, "プロンプトに category=\"soup\" が含まれていません"
    assert "玉ねぎ" in prompt, "プロンプトに used_ingredients が含まれていません"
    assert "japanese" in prompt, "プロンプトに menu_category が含まれていません"
    assert "汁物提案の4段階タスク構成" in prompt, "プロンプトにタスク構成の説明が含まれていません"
    
    print("✅ Integration test passed!")


def test_sub_additional_proposal_integration():
    """副菜追加提案の統合テスト"""
    print("\n=== test_sub_additional_proposal_integration ===")
    
    # リクエスト分析
    analyzer = RequestAnalyzer()
    user_id = "test_user_789"
    sse_session_id = "test_session_123"
    session_context = {}
    
    analysis_result = analyzer.analyze("もう副菜を提案して", user_id, sse_session_id, session_context)
    
    print(f"Analysis result:")
    print(f"  - Pattern: {analysis_result['pattern']}")
    print(f"  - Category: {analysis_result['params'].get('category')}")
    
    # パターン検証
    assert analysis_result["pattern"] == "sub_additional", "副菜追加提案パターンが認識されていません"
    assert analysis_result["params"]["category"] == "sub", "category が正しく設定されていません"
    
    # プロンプト生成
    prompt_manager = PromptManager()
    prompt = prompt_manager.build_prompt(analysis_result, user_id, sse_session_id)
    
    print(f"Generated prompt length: {len(prompt)} characters")
    
    # プロンプト検証
    assert "副菜追加提案" in prompt, "プロンプトに追加提案の説明が含まれていません"
    assert "session_get_proposed_titles" in prompt, "セッション提案履歴取得がプロンプトに含まれていません"
    
    print("✅ Integration test passed!")


def test_soup_additional_proposal_integration():
    """汁物追加提案の統合テスト"""
    print("\n=== test_soup_additional_proposal_integration ===")
    
    # リクエスト分析
    analyzer = RequestAnalyzer()
    user_id = "test_user_101"
    sse_session_id = "test_session_456"
    session_context = {}
    
    analysis_result = analyzer.analyze("もうスープを提案して", user_id, sse_session_id, session_context)
    
    print(f"Analysis result:")
    print(f"  - Pattern: {analysis_result['pattern']}")
    print(f"  - Category: {analysis_result['params'].get('category')}")
    
    # パターン検証
    assert analysis_result["pattern"] == "soup_additional", "汁物追加提案パターンが認識されていません"
    assert analysis_result["params"]["category"] == "soup", "category が正しく設定されていません"
    
    # プロンプト生成
    prompt_manager = PromptManager()
    prompt = prompt_manager.build_prompt(analysis_result, user_id, sse_session_id)
    
    print(f"Generated prompt length: {len(prompt)} characters")
    
    # プロンプト検証
    assert "汁物追加提案" in prompt, "プロンプトに追加提案の説明が含まれていません"
    assert "session_get_proposed_titles" in prompt, "セッション提案履歴取得がプロンプトに含まれていません"
    
    print("✅ Integration test passed!")


def run_all_tests():
    """すべてのテストを実行"""
    print("\n" + "="*60)
    print("Phase 3B: 統合テスト")
    print("="*60)
    
    test_sub_proposal_integration()
    test_soup_proposal_integration()
    test_sub_additional_proposal_integration()
    test_soup_additional_proposal_integration()
    
    print("\n" + "="*60)
    print("✅ All integration tests passed!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()

