#!/usr/bin/env python3
"""
Phase 2A-2 - リクエストモデルのテスト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.request_models import UserSelectionRequest, SelectionResponse


def test_user_selection_request_valid():
    """有効なユーザー選択リクエストのテスト"""
    print("🔍 有効なユーザー選択リクエストのテスト")
    
    request = UserSelectionRequest(
        task_id="main_dish_proposal_0",
        selection=3,
        sse_session_id="session_abc123"
    )
    assert request.task_id == "main_dish_proposal_0"
    assert request.selection == 3
    assert request.sse_session_id == "session_abc123"
    
    print("✅ 有効なユーザー選択リクエストのテスト成功")


def test_user_selection_request_invalid_selection_too_low():
    """無効な選択番号（下限）のテスト"""
    print("🔍 無効な選択番号（下限）のテスト")
    
    try:
        UserSelectionRequest(
            task_id="main_dish_proposal_0",
            selection=0,  # 無効な選択番号
            sse_session_id="session_abc123"
        )
        print("❌ 無効な選択番号（下限）のテスト失敗: 例外が発生しませんでした")
        return False
    except ValueError:
        print("✅ 無効な選択番号（下限）のテスト成功: 期待通り例外が発生")
        return True


def test_user_selection_request_invalid_selection_too_high():
    """無効な選択番号（上限）のテスト"""
    print("🔍 無効な選択番号（上限）のテスト")
    
    try:
        UserSelectionRequest(
            task_id="main_dish_proposal_0",
            selection=6,  # 無効な選択番号
            sse_session_id="session_abc123"
        )
        print("❌ 無効な選択番号（上限）のテスト失敗: 例外が発生しませんでした")
        return False
    except ValueError:
        print("✅ 無効な選択番号（上限）のテスト成功: 期待通り例外が発生")
        return True


def test_user_selection_request_missing_task_id():
    """タスクID未指定のテスト"""
    print("🔍 タスクID未指定のテスト")
    
    try:
        UserSelectionRequest(
            selection=3,
            sse_session_id="session_abc123"
        )
        print("❌ タスクID未指定のテスト失敗: 例外が発生しませんでした")
        return False
    except ValueError:
        print("✅ タスクID未指定のテスト成功: 期待通り例外が発生")
        return True


def test_user_selection_request_missing_sse_session_id():
    """SSEセッションID未指定のテスト"""
    print("🔍 SSEセッションID未指定のテスト")
    
    try:
        UserSelectionRequest(
            task_id="main_dish_proposal_0",
            selection=3
        )
        print("❌ SSEセッションID未指定のテスト失敗: 例外が発生しませんでした")
        return False
    except ValueError:
        print("✅ SSEセッションID未指定のテスト成功: 期待通り例外が発生")
        return True


def test_selection_response_success():
    """成功時の選択結果レスポンスのテスト"""
    print("🔍 成功時の選択結果レスポンスのテスト")
    
    response = SelectionResponse(
        success=True,
        task_id="main_dish_proposal_0",
        selection=3,
        message="選択肢 3 を受け付けました。"
    )
    assert response.success is True
    assert response.task_id == "main_dish_proposal_0"
    assert response.selection == 3
    assert response.message == "選択肢 3 を受け付けました。"
    assert response.error is None
    
    print("✅ 成功時の選択結果レスポンスのテスト成功")


def test_selection_response_error():
    """エラー時の選択結果レスポンスのテスト"""
    print("🔍 エラー時の選択結果レスポンスのテスト")
    
    response = SelectionResponse(
        success=False,
        task_id="main_dish_proposal_0",
        selection=3,
        message="エラーが発生しました。",
        error="Task not found"
    )
    assert response.success is False
    assert response.task_id == "main_dish_proposal_0"
    assert response.selection == 3
    assert response.message == "エラーが発生しました。"
    assert response.error == "Task not found"
    
    print("✅ エラー時の選択結果レスポンスのテスト成功")


def main():
    """メイン関数"""
    print("🚀 Phase 2A-2 リクエストモデルのテスト開始")
    
    tests = [
        test_user_selection_request_valid,
        test_user_selection_request_invalid_selection_too_low,
        test_user_selection_request_invalid_selection_too_high,
        test_user_selection_request_missing_task_id,
        test_user_selection_request_missing_sse_session_id,
        test_selection_response_success,
        test_selection_response_error
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result is not False:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: テストが失敗しました: {e}")
            failed += 1
    
    print(f"\n📊 テスト結果: {passed}件成功, {failed}件失敗")
    
    if failed == 0:
        print("🎉 すべてのテストが成功しました！")
        return True
    else:
        print("❌ 一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
