"""
Phase 2A-1: ContextManager拡張テスト
"""
import time
from core.context_manager import ContextManager


def test_save_context_basic():
    """コンテキストが正しく保存されるか"""
    print("テスト1: コンテキスト保存の基本動作")
    context_manager = ContextManager("test_session")
    
    test_context = {
        "main_ingredient": "chicken",
        "inventory_items": ["onion", "carrot"],
        "step": 1
    }
    
    result = context_manager.save_context_for_resume("task_001", test_context)
    
    if result["success"]:
        print("✅ コンテキスト保存が成功しました")
    else:
        print(f"❌ コンテキスト保存が失敗しました: {result.get('error', 'Unknown error')}")
        return False
    
    if "task_001" in context_manager.paused_contexts:
        print("✅ コンテキストが正しく保存されました")
    else:
        print("❌ コンテキストが保存されていません")
        return False
    
    if "paused_at" in context_manager.paused_contexts["task_001"]:
        print("✅ タイムスタンプが追加されました")
    else:
        print("❌ タイムスタンプが追加されていません")
        return False
    
    return True


def test_load_context_basic():
    """コンテキストが正しく読み込まれるか"""
    print("\nテスト2: コンテキスト読み込みの基本動作")
    context_manager = ContextManager("test_session")
    
    # 保存
    test_context = {
        "main_ingredient": "chicken",
        "inventory_items": ["onion", "carrot"]
    }
    context_manager.save_context_for_resume("task_001", test_context)
    
    # 読み込み
    loaded_context = context_manager.load_context_for_resume("task_001")
    
    if loaded_context is not None:
        print("✅ コンテキストが正しく読み込まれました")
    else:
        print("❌ コンテキストが読み込まれませんでした")
        return False
    
    if loaded_context["main_ingredient"] == "chicken":
        print("✅ 主要食材が正しく読み込まれました")
    else:
        print("❌ 主要食材が正しく読み込まれていません")
        return False
    
    if loaded_context["inventory_items"] == ["onion", "carrot"]:
        print("✅ 在庫食材が正しく読み込まれました")
    else:
        print("❌ 在庫食材が正しく読み込まれていません")
        return False
    
    if "paused_at" in loaded_context:
        print("✅ タイムスタンプが含まれています")
    else:
        print("❌ タイムスタンプが含まれていません")
        return False
    
    return True


def test_load_context_not_found():
    """存在しないコンテキストを読み込んだ場合、Noneが返るか"""
    print("\nテスト3: 存在しないコンテキストの読み込み")
    context_manager = ContextManager("test_session")
    
    loaded_context = context_manager.load_context_for_resume("nonexistent_task")
    
    if loaded_context is None:
        print("✅ 存在しないコンテキストはNoneを返しました")
        return True
    else:
        print("❌ 存在しないコンテキストがNone以外を返しました")
        return False


def test_context_timeout():
    """タイムアウトしたコンテキストがNoneを返すか"""
    print("\nテスト4: コンテキストタイムアウト")
    context_manager = ContextManager("test_session")
    context_manager.context_ttl = 1  # 1秒に設定
    
    # 保存
    test_context = {"main_ingredient": "chicken"}
    context_manager.save_context_for_resume("task_001", test_context)
    
    # 2秒待機（TTLを超過）
    print("⏳ 2秒待機中...")
    time.sleep(2)
    
    # 読み込み（タイムアウトのためNoneが返る）
    loaded_context = context_manager.load_context_for_resume("task_001")
    
    if loaded_context is None:
        print("✅ タイムアウトしたコンテキストはNoneを返しました")
        return True
    else:
        print("❌ タイムアウトしたコンテキストがNone以外を返しました")
        return False


def test_multiple_contexts():
    """複数のコンテキストを同時に管理できるか"""
    print("\nテスト5: 複数コンテキスト管理")
    context_manager = ContextManager("test_session")
    
    # 複数保存
    context_manager.save_context_for_resume("task_001", {"step": 1})
    context_manager.save_context_for_resume("task_002", {"step": 2})
    context_manager.save_context_for_resume("task_003", {"step": 3})
    
    if len(context_manager.paused_contexts) == 3:
        print("✅ 3つのコンテキストが保存されました")
    else:
        print(f"❌ コンテキスト数が期待値と異なります: {len(context_manager.paused_contexts)}")
        return False
    
    # 個別に読み込み
    context_1 = context_manager.load_context_for_resume("task_001")
    if context_1["step"] == 1:
        print("✅ task_001が正しく読み込まれました")
    else:
        print("❌ task_001の読み込みに失敗しました")
        return False
    
    if len(context_manager.paused_contexts) == 2:  # popされるので減る
        print("✅ task_001が削除されました")
    else:
        print("❌ task_001が削除されていません")
        return False
    
    context_2 = context_manager.load_context_for_resume("task_002")
    if context_2["step"] == 2:
        print("✅ task_002が正しく読み込まれました")
    else:
        print("❌ task_002の読み込みに失敗しました")
        return False
    
    if len(context_manager.paused_contexts) == 1:
        print("✅ task_002が削除されました")
    else:
        print("❌ task_002が削除されていません")
        return False
    
    return True


def test_context_independence():
    """保存されたコンテキストが元のコンテキストから独立しているか"""
    print("\nテスト6: コンテキストの独立性")
    context_manager = ContextManager("test_session")
    
    # 元のコンテキスト
    original_context = {"items": ["apple", "banana"]}
    
    # 保存
    context_manager.save_context_for_resume("task_001", original_context)
    
    # 元のコンテキストを変更
    original_context["items"].append("cherry")
    
    # 読み込み（変更が影響しないことを確認）
    loaded_context = context_manager.load_context_for_resume("task_001")
    
    if len(loaded_context["items"]) == 2:  # cherryは含まれない
        print("✅ 保存されたコンテキストは独立しています")
    else:
        print("❌ 保存されたコンテキストが独立していません")
        return False
    
    if "cherry" not in loaded_context["items"]:
        print("✅ 元のコンテキストの変更が影響していません")
    else:
        print("❌ 元のコンテキストの変更が影響しています")
        return False
    
    return True


def test_save_context_error_handling():
    """保存時のエラーハンドリングが正しく動作するか"""
    print("\nテスト7: エラーハンドリング")
    context_manager = ContextManager("test_session")
    
    # 正常なコンテキスト
    test_context = {"data": "normal"}
    
    result = context_manager.save_context_for_resume("task_001", test_context)
    
    if result["success"]:
        print("✅ 正常なコンテキストの保存が成功しました")
    else:
        print(f"❌ 正常なコンテキストの保存が失敗しました: {result.get('error', 'Unknown error')}")
        return False
    
    return True


def test_existing_context_methods_unaffected():
    """既存のコンテキスト管理メソッドに影響がないか"""
    print("\nテスト8: 既存メソッドへの影響確認")
    context_manager = ContextManager("test_session")
    
    # 既存メソッドの動作確認
    context_manager.set_main_ingredient("chicken")
    if context_manager.get_main_ingredient() == "chicken":
        print("✅ set_main_ingredient/get_main_ingredientが正常動作")
    else:
        print("❌ set_main_ingredient/get_main_ingredientが異常")
        return False
    
    context_manager.set_inventory_items(["onion", "carrot"])
    if len(context_manager.get_inventory_items()) == 2:
        print("✅ set_inventory_items/get_inventory_itemsが正常動作")
    else:
        print("❌ set_inventory_items/get_inventory_itemsが異常")
        return False
    
    # 新しいメソッドを使用
    context_manager.save_context_for_resume("task_001", {"test": "data"})
    
    # 既存のコンテキストが影響を受けていないか確認
    if context_manager.get_main_ingredient() == "chicken":
        print("✅ 既存のコンテキストが影響を受けていません")
    else:
        print("❌ 既存のコンテキストが影響を受けています")
        return False
    
    if len(context_manager.get_inventory_items()) == 2:
        print("✅ 既存の在庫リストが影響を受けていません")
    else:
        print("❌ 既存の在庫リストが影響を受けています")
        return False
    
    return True


def main():
    """メインテスト実行"""
    print("=" * 50)
    print("Phase 2A-1: ContextManager拡張テスト")
    print("=" * 50)
    
    tests = [
        test_save_context_basic,
        test_load_context_basic,
        test_load_context_not_found,
        test_context_timeout,
        test_multiple_contexts,
        test_context_independence,
        test_save_context_error_handling,
        test_existing_context_methods_unaffected
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ テストエラー: {e}")
    
    print("\n" + "=" * 50)
    print(f"テスト結果: {passed}/{total} 成功")
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        return True
    else:
        print("💥 一部のテストが失敗しました")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
