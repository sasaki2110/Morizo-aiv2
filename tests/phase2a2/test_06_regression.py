#!/usr/bin/env python3
"""
Phase 2A-2 - 回帰テスト
"""

import sys
import os
import subprocess
import time

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def test_phase2a1_task_status_regression():
    """Phase 2A-1のTaskStatusテストを再実行"""
    print("🔍 Phase 2A-1 TaskStatus 回帰テスト実行中...")
    
    # Phase 2A-1のテストファイルを実行
    test_file = "/app/Morizo-aiv2/tests/phase2a1/test_01_task_status.py"
    if os.path.exists(test_file):
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
        assert result.returncode == 0, f"Phase 2A-1 TaskStatusテストが失敗: {result.stderr}"
        print("✅ Phase 2A-1 TaskStatus 回帰テスト成功")
        return True
    else:
        print("⚠️ Phase 2A-1 TaskStatusテストファイルが見つかりません")
        return False


def test_phase2a1_task_chain_manager_regression():
    """Phase 2A-1のTaskChainManagerテストを再実行"""
    print("🔍 Phase 2A-1 TaskChainManager 回帰テスト実行中...")
    
    # Phase 2A-1のテストファイルを実行
    test_file = "/app/Morizo-aiv2/tests/phase2a1/test_02_task_chain_manager.py"
    if os.path.exists(test_file):
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
        assert result.returncode == 0, f"Phase 2A-1 TaskChainManagerテストが失敗: {result.stderr}"
        print("✅ Phase 2A-1 TaskChainManager 回帰テスト成功")
        return True
    else:
        print("⚠️ Phase 2A-1 TaskChainManagerテストファイルが見つかりません")
        return False


def test_phase2a1_context_manager_regression():
    """Phase 2A-1のContextManagerテストを再実行"""
    print("🔍 Phase 2A-1 ContextManager 回帰テスト実行中...")
    
    # Phase 2A-1のテストファイルを実行
    test_file = "/app/Morizo-aiv2/tests/phase2a1/test_03_context_manager.py"
    if os.path.exists(test_file):
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
        assert result.returncode == 0, f"Phase 2A-1 ContextManagerテストが失敗: {result.stderr}"
        print("✅ Phase 2A-1 ContextManager 回帰テスト成功")
        return True
    else:
        print("⚠️ Phase 2A-1 ContextManagerテストファイルが見つかりません")
        return False


def test_phase1_regression():
    """Phase 1のテストを再実行"""
    print("🔍 Phase 1 回帰テスト実行中...")
    
    # Phase 1のテストファイルを実行
    test_files = [
        "/app/Morizo-aiv2/tests/phase1c/test_01_basic_integration.py",
        "/app/Morizo-aiv2/tests/phase1d/test_13_history_retrieval.py"
    ]
    
    passed = 0
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"📋 {os.path.basename(test_file)} を実行中...")
            result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {os.path.basename(test_file)} 成功")
                passed += 1
            else:
                print(f"❌ {os.path.basename(test_file)} 失敗: {result.stderr}")
        else:
            print(f"⚠️ {test_file} が見つかりません")
    
    return passed == len(test_files)


def test_import_regression():
    """インポート回帰テスト"""
    print("🔍 インポート回帰テスト実行中...")
    
    try:
        from api.request_models import UserSelectionRequest, SelectionResponse
        print("✅ api.request_models インポート成功")
    except ImportError as e:
        print(f"❌ api.request_models インポート失敗: {e}")
        return False
    
    try:
        from services.llm.response_formatters import ResponseFormatters
        print("✅ services.llm.response_formatters インポート成功")
    except ImportError as e:
        print(f"❌ services.llm.response_formatters インポート失敗: {e}")
        return False
    
    try:
        from core.agent import TrueReactAgent
        print("✅ core.agent インポート成功")
    except ImportError as e:
        print(f"❌ core.agent インポート失敗: {e}")
        return False
    
    try:
        from api.routes.chat import router
        print("✅ api.routes.chat インポート成功")
    except ImportError as e:
        print(f"❌ api.routes.chat インポート失敗: {e}")
        return False
    
    return True


def test_new_functionality_regression():
    """新機能の回帰テスト"""
    print("🔍 新機能の回帰テスト実行中...")
    
    # ResponseFormattersの新メソッドのテスト
    from services.llm.response_formatters import ResponseFormatters
    formatter = ResponseFormatters()
    
    # format_selection_request メソッドの存在確認
    if not hasattr(formatter, 'format_selection_request'):
        print("❌ format_selection_request メソッドが存在しません")
        return False
    print("✅ format_selection_request メソッド存在確認")
    
    # format_selection_result メソッドの存在確認
    if not hasattr(formatter, 'format_selection_result'):
        print("❌ format_selection_result メソッドが存在しません")
        return False
    print("✅ format_selection_result メソッド存在確認")
    
    # TrueReactAgentの新メソッドのテスト
    from core.agent import TrueReactAgent
    agent = TrueReactAgent()
    
    # handle_user_selection_required メソッドの存在確認
    if not hasattr(agent, 'handle_user_selection_required'):
        print("❌ handle_user_selection_required メソッドが存在しません")
        return False
    print("✅ handle_user_selection_required メソッド存在確認")
    
    # process_user_selection メソッドの存在確認
    if not hasattr(agent, 'process_user_selection'):
        print("❌ process_user_selection メソッドが存在しません")
        return False
    print("✅ process_user_selection メソッド存在確認")
    
    return True


def main():
    """メイン関数"""
    print("🚀 Phase 2A-2 回帰テスト開始")
    
    tests = [
        test_phase2a1_task_status_regression,
        test_phase2a1_task_chain_manager_regression,
        test_phase2a1_context_manager_regression,
        test_phase1_regression,
        test_import_regression,
        test_new_functionality_regression
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
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
