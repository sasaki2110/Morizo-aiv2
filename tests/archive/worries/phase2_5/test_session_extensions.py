#!/usr/bin/env python3
"""
Phase 2.5D: セッション管理の拡張テスト

Sessionクラスの拡張機能をテストします。
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.session_service import Session


def test_session_new_fields():
    """Sessionに新規フィールドが追加されていること"""
    session = Session(session_id="test", user_id="test_user")
    
    # Phase 1Fで追加済みフィールド
    assert hasattr(session, "proposed_recipes"), "proposed_recipesフィールドが存在すること"
    assert hasattr(session, "context"), "contextフィールドが存在すること"
    
    # Phase 2.5Dで追加される新規フィールド
    assert hasattr(session, "current_stage"), "current_stageフィールドが存在すること"
    assert session.current_stage == "main", "current_stageのデフォルト値が'main'であること"
    
    assert hasattr(session, "selected_main_dish"), "selected_main_dishフィールドが存在すること"
    assert session.selected_main_dish is None, "selected_main_dishのデフォルト値がNoneであること"
    
    assert hasattr(session, "selected_sub_dish"), "selected_sub_dishフィールドが存在すること"
    assert session.selected_sub_dish is None, "selected_sub_dishのデフォルト値がNoneであること"
    
    assert hasattr(session, "selected_soup"), "selected_soupフィールドが存在すること"
    assert session.selected_soup is None, "selected_soupのデフォルト値がNoneであること"
    
    assert hasattr(session, "used_ingredients"), "used_ingredientsフィールドが存在すること"
    assert session.used_ingredients == [], "used_ingredientsのデフォルト値が空リストであること"
    
    assert hasattr(session, "menu_category"), "menu_categoryフィールドが存在すること"
    assert session.menu_category == "japanese", "menu_categoryのデフォルト値が'japanese'であること"


def test_session_methods():
    """Sessionに段階管理メソッドが追加されていること"""
    session = Session(session_id="test", user_id="test_user")
    
    # get_current_stage
    assert hasattr(session, "get_current_stage"), "get_current_stageメソッドが存在すること"
    assert session.get_current_stage() == "main", "get_current_stageが'main'を返すこと"
    
    # set_selected_recipe
    assert hasattr(session, "set_selected_recipe"), "set_selected_recipeメソッドが存在すること"
    
    # get_selected_recipes
    assert hasattr(session, "get_selected_recipes"), "get_selected_recipesメソッドが存在すること"
    assert isinstance(session.get_selected_recipes(), dict), "get_selected_recipesが辞書を返すこと"
    
    # get_used_ingredients
    assert hasattr(session, "get_used_ingredients"), "get_used_ingredientsメソッドが存在すること"
    assert isinstance(session.get_used_ingredients(), list), "get_used_ingredientsがリストを返すこと"
    
    # get_menu_category
    assert hasattr(session, "get_menu_category"), "get_menu_categoryメソッドが存在すること"
    assert session.get_menu_category() == "japanese", "get_menu_categoryが'japanese'を返すこと"


def test_set_selected_recipe_main():
    """主菜選択の動作確認"""
    session = Session(session_id="test", user_id="test_user")
    
    recipe = {
        "title": "レンコンの含め煮",
        "ingredients": ["レンコン", "牛豚合挽肉"],
        "menu_type": "和食"
    }
    
    session.set_selected_recipe("main", recipe)
    
    # 主菜が保存されていること
    assert session.selected_main_dish == recipe, "主菜が保存されていること"
    
    # 段階が"sub"に進んでいること
    assert session.current_stage == "sub", "段階が'sub'に進んでいること"
    
    # 使用食材が記録されていること
    assert "レンコン" in session.used_ingredients, "レンコンが使用済み食材に記録されていること"
    assert "牛豚合挽肉" in session.used_ingredients, "牛豚合挽肉が使用済み食材に記録されていること"
    
    # 献立カテゴリが判定されていること
    assert session.menu_category == "japanese", "献立カテゴリが'japanese'であること"


def test_set_selected_recipe_western():
    """洋食主菜選択の動作確認"""
    session = Session(session_id="test", user_id="test_user")
    
    recipe = {
        "title": "ビーフシチュー",
        "ingredients": ["牛肉", "玉ねぎ", "にんじん"],
        "menu_type": "洋食"
    }
    
    session.set_selected_recipe("main", recipe)
    
    # 献立カテゴリが判定されていること
    assert session.menu_category == "western", "献立カテゴリが'western'であること"


def test_set_selected_recipe_chinese():
    """中華主菜選択の動作確認"""
    session = Session(session_id="test", user_id="test_user")
    
    recipe = {
        "title": "麻婆豆腐",
        "ingredients": ["豆腐", "ひき肉", "豆板醤"],
        "menu_type": "中華"
    }
    
    session.set_selected_recipe("main", recipe)
    
    # 献立カテゴリが判定されていること
    assert session.menu_category == "chinese", "献立カテゴリが'chinese'であること"


def test_set_selected_recipe_sub():
    """副菜選択の動作確認"""
    session = Session(session_id="test", user_id="test_user")
    
    # まず主菜を選択
    main_recipe = {
        "title": "レンコンの含め煮",
        "ingredients": ["レンコン", "牛豚合挽肉"],
        "menu_type": "和食"
    }
    session.set_selected_recipe("main", main_recipe)
    
    # 副菜を選択
    sub_recipe = {
        "title": "ほうれん草のおひたし",
        "ingredients": ["ほうれん草", "めんつゆ"],
        "menu_type": "和食"
    }
    session.set_selected_recipe("sub", sub_recipe)
    
    # 副菜が保存されていること
    assert session.selected_sub_dish == sub_recipe, "副菜が保存されていること"
    
    # 段階が"soup"に進んでいること
    assert session.current_stage == "soup", "段階が'soup'に進んでいること"
    
    # 使用食材が累積されていること
    assert len(session.used_ingredients) == 4, "使用済み食材が4件記録されていること"


def test_set_selected_recipe_soup():
    """汁物選択の動作確認"""
    session = Session(session_id="test", user_id="test_user")
    
    # まず主菜・副菜を選択
    main_recipe = {"title": "レンコンの含め煮", "ingredients": ["レンコン"], "menu_type": "和食"}
    session.set_selected_recipe("main", main_recipe)
    
    sub_recipe = {"title": "ほうれん草のおひたし", "ingredients": ["ほうれん草"], "menu_type": "和食"}
    session.set_selected_recipe("sub", sub_recipe)
    
    # 汁物を選択
    soup_recipe = {
        "title": "豆腐とわかめの味噌汁",
        "ingredients": ["豆腐", "わかめ", "味噌"],
        "menu_type": "和食"
    }
    session.set_selected_recipe("soup", soup_recipe)
    
    # 汁物が保存されていること
    assert session.selected_soup == soup_recipe, "汁物が保存されていること"
    
    # 段階が"completed"に進んでいること
    assert session.current_stage == "completed", "段階が'completed'に進んでいること"


def test_get_selected_recipes():
    """選択済みレシピ取得の動作確認"""
    session = Session(session_id="test", user_id="test_user")
    
    main_recipe = {"title": "主菜", "ingredients": ["食材1"], "menu_type": "和食"}
    session.set_selected_recipe("main", main_recipe)
    
    sub_recipe = {"title": "副菜", "ingredients": ["食材2"], "menu_type": "和食"}
    session.set_selected_recipe("sub", sub_recipe)
    
    soup_recipe = {"title": "汁物", "ingredients": ["食材3"], "menu_type": "和食"}
    session.set_selected_recipe("soup", soup_recipe)
    
    selected = session.get_selected_recipes()
    
    assert selected["main"] == main_recipe, "主菜が取得できること"
    assert selected["sub"] == sub_recipe, "副菜が取得できること"
    assert selected["soup"] == soup_recipe, "汁物が取得できること"


def test_backward_compatibility():
    """既存セッションとの互換性テスト"""
    session = Session(session_id="test", user_id="test_user")
    
    # 既存フィールドが正しく動作すること
    assert session.id == "test", "idフィールドが正しく設定されていること"
    assert session.user_id == "test_user", "user_idフィールドが正しく設定されていること"
    assert hasattr(session, "created_at"), "created_atフィールドが存在すること"
    assert hasattr(session, "last_accessed"), "last_accessedフィールドが存在すること"
    assert hasattr(session, "data"), "dataフィールドが存在すること"
    assert hasattr(session, "confirmation_context"), "confirmation_contextフィールドが存在すること"
    
    # Phase 1Fの既存フィールドが正しく動作すること
    assert isinstance(session.proposed_recipes, dict), "proposed_recipesが辞書であること"
    assert isinstance(session.context, dict), "contextが辞書であること"
    
    # 既存メソッドが正しく動作すること
    assert hasattr(session, "add_proposed_recipes"), "add_proposed_recipesメソッドが存在すること"
    assert hasattr(session, "get_proposed_recipes"), "get_proposed_recipesメソッドが存在すること"
    assert hasattr(session, "set_context"), "set_contextメソッドが存在すること"
    assert hasattr(session, "get_context"), "get_contextメソッドが存在すること"


def run_all_tests():
    """全てのテストを実行"""
    print("=" * 80)
    print("Phase 2.5D: セッション管理の拡張テスト")
    print("=" * 80)
    
    tests = [
        ("test_session_new_fields", test_session_new_fields),
        ("test_session_methods", test_session_methods),
        ("test_set_selected_recipe_main", test_set_selected_recipe_main),
        ("test_set_selected_recipe_western", test_set_selected_recipe_western),
        ("test_set_selected_recipe_chinese", test_set_selected_recipe_chinese),
        ("test_set_selected_recipe_sub", test_set_selected_recipe_sub),
        ("test_set_selected_recipe_soup", test_set_selected_recipe_soup),
        ("test_get_selected_recipes", test_get_selected_recipes),
        ("test_backward_compatibility", test_backward_compatibility),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed += 1
    
    print("=" * 80)
    print(f"テスト結果: {passed} passed, {failed} failed (合計 {len(tests)})")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

