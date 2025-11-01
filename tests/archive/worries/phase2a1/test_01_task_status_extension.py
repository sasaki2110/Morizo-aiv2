"""
Phase 2A-1: TaskStatus拡張テスト
"""
from core.models import TaskStatus, Task


def test_waiting_for_user_status_exists():
    """WAITING_FOR_USER状態が正しく定義されているか"""
    print("テスト1: WAITING_FOR_USER状態の存在確認")
    if hasattr(TaskStatus, 'WAITING_FOR_USER'):
        print("✅ WAITING_FOR_USER状態が定義されています")
    else:
        print("❌ WAITING_FOR_USER状態が定義されていません")
        return False
    
    if TaskStatus.WAITING_FOR_USER.value == "waiting_for_user":
        print("✅ WAITING_FOR_USER状態の値が正しいです")
    else:
        print("❌ WAITING_FOR_USER状態の値が正しくありません")
        return False
    
    return True


def test_waiting_for_user_status_string():
    """WAITING_FOR_USER状態の文字列表現が正しいか"""
    print("\nテスト2: WAITING_FOR_USER状態の文字列表現確認")
    status = TaskStatus.WAITING_FOR_USER
    
    if str(status) == "TaskStatus.WAITING_FOR_USER":
        print("✅ 文字列表現が正しいです")
    else:
        print("❌ 文字列表現が正しくありません")
        return False
    
    if status.value == "waiting_for_user":
        print("✅ 値が正しいです")
    else:
        print("❌ 値が正しくありません")
        return False
    
    return True


def test_existing_statuses_unchanged():
    """既存の状態に影響がないか"""
    print("\nテスト3: 既存状態への影響確認")
    
    statuses = [
        (TaskStatus.PENDING, "pending"),
        (TaskStatus.RUNNING, "running"),
        (TaskStatus.COMPLETED, "completed"),
        (TaskStatus.FAILED, "failed")
    ]
    
    for status, expected_value in statuses:
        if status.value == expected_value:
            print(f"✅ {status.name} = {expected_value}")
        else:
            print(f"❌ {status.name} = {status.value} (期待値: {expected_value})")
            return False
    
    return True


def test_task_with_waiting_for_user_status():
    """TaskクラスでWAITING_FOR_USER状態を使用できるか"""
    print("\nテスト4: TaskクラスでのWAITING_FOR_USER使用確認")
    
    task = Task(
        id="test_task",
        service="RecipeService",
        method="generate_menu_plan",
        parameters={},
        status=TaskStatus.WAITING_FOR_USER
    )
    
    if task.status == TaskStatus.WAITING_FOR_USER:
        print("✅ TaskでWAITING_FOR_USER状態を設定できました")
    else:
        print("❌ TaskでWAITING_FOR_USER状態を設定できませんでした")
        return False
    
    if task.status.value == "waiting_for_user":
        print("✅ Taskの状態値が正しいです")
    else:
        print("❌ Taskの状態値が正しくありません")
        return False
    
    return True


def main():
    """メインテスト実行"""
    print("=" * 50)
    print("Phase 2A-1: TaskStatus拡張テスト")
    print("=" * 50)
    
    tests = [
        test_waiting_for_user_status_exists,
        test_waiting_for_user_status_string,
        test_existing_statuses_unchanged,
        test_task_with_waiting_for_user_status
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
