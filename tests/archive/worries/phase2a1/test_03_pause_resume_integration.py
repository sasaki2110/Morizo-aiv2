"""
Phase 2A-1: 統合テスト
"""
from core.models import TaskStatus, Task, TaskChainManager
from core.context_manager import ContextManager


def test_pause_with_context_save():
    """一時停止とコンテキスト保存が正しく連携するか"""
    print("テスト1: 一時停止とコンテキスト保存の連携")
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # タスクを設定
    tasks = [
        Task(
            id="task_001",
            service="RecipeService",
            method="generate_menu_plan",
            parameters={}
        )
    ]
    task_chain_manager.set_tasks(tasks)
    
    # ユーザー選択待ちの処理
    task_chain_manager.pause_for_confirmation()
    task_chain_manager.update_task_status("task_001", TaskStatus.WAITING_FOR_USER)
    
    test_context = {"main_ingredient": "chicken", "step": 1}
    result = context_manager.save_context_for_resume("task_001", test_context)
    
    # 検証
    if task_chain_manager.is_paused:
        print("✅ TaskChainManagerが一時停止状態です")
    else:
        print("❌ TaskChainManagerが一時停止状態ではありません")
        return False
    
    if tasks[0].status == TaskStatus.WAITING_FOR_USER:
        print("✅ タスクがWAITING_FOR_USER状態です")
    else:
        print("❌ タスクがWAITING_FOR_USER状態ではありません")
        return False
    
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
    
    return True


def test_resume_with_context_load():
    """再開とコンテキスト読み込みが正しく連携するか"""
    print("\nテスト2: 再開とコンテキスト読み込みの連携")
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # タスクを設定
    tasks = [
        Task(
            id="task_001",
            service="RecipeService",
            method="generate_menu_plan",
            parameters={},
            status=TaskStatus.WAITING_FOR_USER
        )
    ]
    task_chain_manager.set_tasks(tasks)
    task_chain_manager.is_paused = True
    
    # コンテキストを保存
    test_context = {"main_ingredient": "chicken", "step": 1}
    context_manager.save_context_for_resume("task_001", test_context)
    
    # ユーザー選択後の処理
    loaded_context = context_manager.load_context_for_resume("task_001")
    task_chain_manager.resume_execution()
    task_chain_manager.update_task_status("task_001", TaskStatus.RUNNING)
    
    # 検証
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
    
    if loaded_context["step"] == 1:
        print("✅ ステップが正しく読み込まれました")
    else:
        print("❌ ステップが正しく読み込まれていません")
        return False
    
    if not task_chain_manager.is_paused:
        print("✅ TaskChainManagerが再開状態です")
    else:
        print("❌ TaskChainManagerが再開状態ではありません")
        return False
    
    if tasks[0].status == TaskStatus.RUNNING:
        print("✅ タスクがRUNNING状態です")
    else:
        print("❌ タスクがRUNNING状態ではありません")
        return False
    
    return True


def test_task_status_context_consistency():
    """タスク状態とコンテキスト保存の整合性が取れているか"""
    print("\nテスト3: タスク状態とコンテキストの整合性")
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # タスクを設定
    task = Task(
        id="task_001",
        service="RecipeService",
        method="generate_menu_plan",
        parameters={}
    )
    task_chain_manager.set_tasks([task])
    
    # 一時停止前: コンテキストなし
    if "task_001" not in context_manager.paused_contexts:
        print("✅ 一時停止前はコンテキストがありません")
    else:
        print("❌ 一時停止前にコンテキストが存在します")
        return False
    
    # 一時停止: コンテキスト保存
    task_chain_manager.pause_for_confirmation()
    task_chain_manager.update_task_status("task_001", TaskStatus.WAITING_FOR_USER)
    context_manager.save_context_for_resume("task_001", {"step": 1})
    
    if task_chain_manager.is_paused:
        print("✅ TaskChainManagerが一時停止状態です")
    else:
        print("❌ TaskChainManagerが一時停止状態ではありません")
        return False
    
    if task.status == TaskStatus.WAITING_FOR_USER:
        print("✅ タスクがWAITING_FOR_USER状態です")
    else:
        print("❌ タスクがWAITING_FOR_USER状態ではありません")
        return False
    
    if "task_001" in context_manager.paused_contexts:
        print("✅ コンテキストが保存されました")
    else:
        print("❌ コンテキストが保存されていません")
        return False
    
    # 再開: コンテキスト読み込み
    loaded_context = context_manager.load_context_for_resume("task_001")
    task_chain_manager.resume_execution()
    task_chain_manager.update_task_status("task_001", TaskStatus.COMPLETED)
    
    if loaded_context is not None:
        print("✅ コンテキストが正しく読み込まれました")
    else:
        print("❌ コンテキストが読み込まれませんでした")
        return False
    
    if not task_chain_manager.is_paused:
        print("✅ TaskChainManagerが再開状態です")
    else:
        print("❌ TaskChainManagerが再開状態ではありません")
        return False
    
    if task.status == TaskStatus.COMPLETED:
        print("✅ タスクがCOMPLETED状態です")
    else:
        print("❌ タスクがCOMPLETED状態ではありません")
        return False
    
    if "task_001" not in context_manager.paused_contexts:  # popされて削除
        print("✅ コンテキストが削除されました")
    else:
        print("❌ コンテキストが削除されていません")
        return False
    
    return True


def test_multiple_task_pause_resume():
    """複数タスクの一時停止と再開が正しく動作するか"""
    print("\nテスト4: 複数タスクの一時停止と再開")
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # 複数タスクを設定
    tasks = [
        Task(id="task_001", service="RecipeService", method="method1", parameters={}),
        Task(id="task_002", service="RecipeService", method="method2", parameters={}),
        Task(id="task_003", service="RecipeService", method="method3", parameters={})
    ]
    task_chain_manager.set_tasks(tasks)
    
    # task_001を一時停止
    task_chain_manager.pause_for_confirmation()
    task_chain_manager.update_task_status("task_001", TaskStatus.WAITING_FOR_USER)
    context_manager.save_context_for_resume("task_001", {"step": 1})
    
    # task_002を一時停止
    task_chain_manager.update_task_status("task_002", TaskStatus.WAITING_FOR_USER)
    context_manager.save_context_for_resume("task_002", {"step": 2})
    
    # 両方が保存されているか確認
    if "task_001" in context_manager.paused_contexts:
        print("✅ task_001が保存されました")
    else:
        print("❌ task_001が保存されていません")
        return False
    
    if "task_002" in context_manager.paused_contexts:
        print("✅ task_002が保存されました")
    else:
        print("❌ task_002が保存されていません")
        return False
    
    if len(context_manager.paused_contexts) == 2:
        print("✅ 2つのコンテキストが保存されました")
    else:
        print(f"❌ コンテキスト数が期待値と異なります: {len(context_manager.paused_contexts)}")
        return False
    
    # task_001を再開
    context_1 = context_manager.load_context_for_resume("task_001")
    if context_1["step"] == 1:
        print("✅ task_001が正しく読み込まれました")
    else:
        print("❌ task_001の読み込みに失敗しました")
        return False
    
    task_chain_manager.update_task_status("task_001", TaskStatus.COMPLETED)
    
    # task_002を再開
    context_2 = context_manager.load_context_for_resume("task_002")
    if context_2["step"] == 2:
        print("✅ task_002が正しく読み込まれました")
    else:
        print("❌ task_002の読み込みに失敗しました")
        return False
    
    task_chain_manager.update_task_status("task_002", TaskStatus.COMPLETED)
    
    # 両方とも削除されているか確認
    if "task_001" not in context_manager.paused_contexts:
        print("✅ task_001が削除されました")
    else:
        print("❌ task_001が削除されていません")
        return False
    
    if "task_002" not in context_manager.paused_contexts:
        print("✅ task_002が削除されました")
    else:
        print("❌ task_002が削除されていません")
        return False
    
    if len(context_manager.paused_contexts) == 0:
        print("✅ すべてのコンテキストが削除されました")
    else:
        print(f"❌ コンテキストが残っています: {len(context_manager.paused_contexts)}")
        return False
    
    return True


def main():
    """メインテスト実行"""
    print("=" * 50)
    print("Phase 2A-1: 統合テスト")
    print("=" * 50)
    
    tests = [
        test_pause_with_context_save,
        test_resume_with_context_load,
        test_task_status_context_consistency,
        test_multiple_task_pause_resume
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
