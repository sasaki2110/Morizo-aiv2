"""
Phase 3B テスト: PromptManagerの副菜・汁物プロンプト生成
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.llm.prompt_manager.patterns.sub_proposal import build_sub_proposal_prompt
from services.llm.prompt_manager.patterns.soup_proposal import build_soup_proposal_prompt


def test_sub_proposal_prompt():
    """副菜プロンプト構築テスト"""
    print("\n=== test_sub_proposal_prompt ===")
    
    user_request = "副菜を5件提案して"
    user_id = "test_user_123"
    used_ingredients = ["レンコン", "鶏もも肉"]
    
    prompt = build_sub_proposal_prompt(user_request, user_id, used_ingredients)
    
    print(f"Prompt length: {len(prompt)} characters")
    print(f"\nPrompt preview (first 500 chars):\n{prompt[:500]}")
    
    # 必須要素のチェック
    assert "category=\"sub\"" in prompt, "category=\"sub\" が含まれていません"
    assert "レンコン" in prompt, "used_ingredients がプロンプトに含まれていません"
    assert "鶏もも肉" in prompt, "used_ingredients がプロンプトに含まれていません"
    assert "副菜提案の4段階タスク構成" in prompt, "タスク構成の説明がありません"
    assert "get_inventory" in prompt, "task1の説明がありません"
    assert "history_get_recent_titles" in prompt, "task2の説明がありません"
    assert "generate_proposals" in prompt, "task3の説明がありません"
    assert "search_recipes_from_web" in prompt, "task4の説明がありません"
    
    print("✅ All sub proposal prompt assertions passed!")


def test_soup_proposal_prompt():
    """汁物プロンプト構築テスト"""
    print("\n=== test_soup_proposal_prompt ===")
    
    user_request = "味噌汁を提案して"
    user_id = "test_user_456"
    used_ingredients = ["レンコン", "玉ねぎ", "ニンジン"]
    menu_category = "japanese"
    
    prompt = build_soup_proposal_prompt(user_request, user_id, used_ingredients, menu_category)
    
    print(f"Prompt length: {len(prompt)} characters")
    print(f"\nPrompt preview (first 500 chars):\n{prompt[:500]}")
    
    # 必須要素のチェック
    assert "category=\"soup\"" in prompt, "category=\"soup\" が含まれていません"
    assert "レンコン" in prompt, "used_ingredients がプロンプトに含まれていません"
    assert "玉ねぎ" in prompt, "used_ingredients がプロンプトに含まれていません"
    assert "ニンジン" in prompt, "used_ingredients がプロンプトに含まれていません"
    assert "menu_category" in prompt, "menu_category がプロンプトに含まれていません"
    assert "japanese" in prompt, "menu_category がプロンプトに含まれていません"
    assert "汁物提案の4段階タスク構成" in prompt, "タスク構成の説明がありません"
    assert "get_inventory" in prompt, "task1の説明がありません"
    assert "history_get_recent_titles" in prompt, "task2の説明がありません"
    assert "generate_proposals" in prompt, "task3の説明がありません"
    assert "search_recipes_from_web" in prompt, "task4の説明がありません"
    
    print("✅ All soup proposal prompt assertions passed!")


def test_sub_proposal_prompt_without_used_ingredients():
    """used_ingredientsなしの場合の副菜プロンプトテスト"""
    print("\n=== test_sub_proposal_prompt_without_used_ingredients ===")
    
    user_request = "副菜を提案して"
    user_id = "test_user"
    
    prompt = build_sub_proposal_prompt(user_request, user_id, None)
    
    # used_ingredientsが指定されていない場合、プロンプトに"なし"が含まれる
    assert "主菜で使った食材: なし" in prompt, "used_ingredientsなしの場合の処理が正しくありません"
    
    print("✅ PASS")


def test_soup_proposal_prompt_different_categories():
    """異なる献立カテゴリの汁物プロンプトテスト"""
    print("\n=== test_soup_proposal_prompt_different_categories ===")
    
    test_cases = [
        ("japanese", "和食"),
        ("western", "洋食"),
        ("chinese", "中華"),
    ]
    
    for menu_category, category_name in test_cases:
        prompt = build_soup_proposal_prompt(
            "スープを提案して",
            "test_user",
            ["玉ねぎ", "ニンジン"],
            menu_category
        )
        
        assert category_name in prompt, f"{category_name} がプロンプトに含まれていません"
        assert "menu_category" in prompt, "menu_category がプロンプトに含まれていません"
        assert menu_category in prompt, f"menu_category={menu_category} がプロンプトに含まれていません"
        print(f"✅ {category_name} ({menu_category}) prompt test passed")
    
    print("✅ All category tests passed!")


def run_all_tests():
    """すべてのテストを実行"""
    print("\n" + "="*60)
    print("Phase 3B: PromptManager テスト")
    print("="*60)
    
    test_sub_proposal_prompt()
    test_soup_proposal_prompt()
    test_sub_proposal_prompt_without_used_ingredients()
    test_soup_proposal_prompt_different_categories()
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()

