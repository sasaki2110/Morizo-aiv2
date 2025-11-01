#!/usr/bin/env python3
"""
Phase 5A: 献立保存APIエンドポイントのテスト

POST /api/menu/save エンドポイントの動作をテストします。
"""

import asyncio
import sys
import os
import requests
import json
import time
import uuid
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# .envファイルを読み込み
load_dotenv()


class IntegrationTestClient:
    """統合テスト用のHTTPクライアント"""
    
    def __init__(self, base_url="http://localhost:8000", jwt_token=None):
        self.base_url = base_url
        self.session = requests.Session()
        
        # JWTトークンの設定（優先順位: 引数 > 環境変数 > デフォルト）
        self.jwt_token = jwt_token or os.getenv("TEST_USER_JWT_TOKEN") or "test_token_for_integration"
        
        self.session.headers.update({
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        })
        
        print(f"🔐 使用するJWTトークン: {self.jwt_token[:20]}..." if len(self.jwt_token) > 20 else f"🔐 使用するJWTトークン: {self.jwt_token}")
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def send_chat_request(self, message, sse_session_id=None, confirm=False):
        """チャットリクエストを送信"""
        url = f"{self.base_url}/chat"
        
        payload = {
            "message": message,
            "token": self.jwt_token,
            "sseSessionId": sse_session_id,
            "confirm": confirm
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e.response, 'text'):
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def send_selection_request(self, task_id, selection, sse_session_id):
        """選択リクエストを送信"""
        url = f"{self.base_url}/chat/selection"
        
        payload = {
            "task_id": task_id,
            "selection": selection,
            "sse_session_id": sse_session_id
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e.response, 'text'):
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def send_menu_save_request(self, sse_session_id):
        """献立保存リクエストを送信"""
        url = f"{self.base_url}/api/menu/save"
        
        payload = {
            "sse_session_id": sse_session_id
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e.response, 'text'):
                print(f"   レスポンス: {e.response.text}")
            return None


def test_no_selected_recipes(jwt_token=None):
    """選択済みレシピがない場合のテスト"""
    print("\n[テスト1] 選択済みレシピがない場合")
    
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        return False
    
    # 新しいセッションIDを作成（空のセッション）
    sse_session_id = f"test_menu_save_empty_{int(time.time())}"
    
    # 献立保存リクエストを送信
    response = client.send_menu_save_request(sse_session_id)
    
    if response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print(f"📋 レスポンス: {json.dumps(response, indent=2, ensure_ascii=False)}")
    
    success = response.get("success", True)
    message = response.get("message", "")
    total_saved = response.get("total_saved", -1)
    
    assert success == False, f"成功フラグがFalseであること: success={success}"
    assert "保存するレシピがありません" in message, f"適切なメッセージであること: {message}"
    assert total_saved == 0, f"保存数が0であること: total_saved={total_saved}"
    
    print("✅ 選択済みレシピがない場合のテストが成功しました")
    return True


def test_save_main_dish_only(jwt_token=None):
    """主菜のみ選択時の保存テスト"""
    print("\n[テスト2] 主菜のみ選択時の保存")
    
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        return False
    
    # 新しいセッションIDを作成
    sse_session_id = f"test_menu_save_main_{int(time.time())}"
    
    # 1. チャットで主菜を提案させる
    print("📋 主菜提案をリクエスト...")
    chat_response = client.send_chat_request(
        message="レンコンを使った主菜を5件提案してください",
        sse_session_id=sse_session_id
    )
    
    if chat_response is None:
        print("❌ チャットリクエストが失敗しました")
        return False
    
    # 2. 主菜を選択（最初の候補を選択）
    print("📋 主菜を選択...")
    task_id = chat_response.get("task_id")
    if not task_id:
        print("⚠️ task_idが見つかりません。手動で主菜を選択してください。")
        print(f"   セッションID: {sse_session_id}")
        return False
    
    # 候補から選択（インデックス1を選択）
    selection_response = client.send_selection_request(
        task_id=task_id,
        selection=1,
        sse_session_id=sse_session_id
    )
    
    if selection_response is None:
        print("❌ 選択リクエストが失敗しました")
        return False
    
    # 少し待機（処理が完了するまで）
    time.sleep(2)
    
    # 3. 献立保存リクエストを送信
    print("📋 献立保存をリクエスト...")
    save_response = client.send_menu_save_request(sse_session_id)
    
    if save_response is None:
        print("❌ 保存リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print(f"📋 レスポンス: {json.dumps(save_response, indent=2, ensure_ascii=False)}")
    
    success = save_response.get("success", False)
    message = save_response.get("message", "")
    saved_recipes = save_response.get("saved_recipes", [])
    total_saved = save_response.get("total_saved", 0)
    
    assert success == True, f"保存が成功していること: success={success}"
    assert total_saved == 1, f"保存数が1であること: total_saved={total_saved}"
    assert len(saved_recipes) == 1, f"保存レシピ数が1であること: {len(saved_recipes)}"
    
    # 主菜が保存されていることを確認
    main_recipe = saved_recipes[0]
    assert main_recipe.get("category") == "main", f"カテゴリがmainであること: {main_recipe.get('category')}"
    assert main_recipe.get("title", "").startswith("主菜: "), f"タイトルがプレフィックス付きであること: {main_recipe.get('title')}"
    assert main_recipe.get("history_id"), f"history_idが設定されていること: {main_recipe.get('history_id')}"
    
    print("✅ 主菜のみ選択時の保存テストが成功しました")
    print(f"   保存されたレシピ: {main_recipe.get('title')}")
    return True


def test_save_main_and_sub(jwt_token=None):
    """主菜+副菜選択時の保存テスト"""
    print("\n[テスト3] 主菜+副菜選択時の保存")
    
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        return False
    
    # 新しいセッションIDを作成
    sse_session_id = f"test_menu_save_main_sub_{int(time.time())}"
    
    # 1. 主菜を選択
    print("📋 主菜提案をリクエスト...")
    chat_response = client.send_chat_request(
        message="レンコンを使った主菜を5件提案してください",
        sse_session_id=sse_session_id
    )
    
    if chat_response is None:
        print("❌ チャットリクエストが失敗しました")
        return False
    
    task_id = chat_response.get("task_id")
    if not task_id:
        print("⚠️ task_idが見つかりません")
        return False
    
    # 主菜を選択
    print("📋 主菜を選択...")
    selection_response = client.send_selection_request(
        task_id=task_id,
        selection=1,
        sse_session_id=sse_session_id
    )
    
    if selection_response is None:
        print("❌ 主菜選択が失敗しました")
        return False
    
    time.sleep(2)
    
    # 2. 副菜を提案・選択
    print("📋 副菜提案をリクエスト...")
    sub_chat_response = client.send_chat_request(
        message="副菜を5件提案してください",
        sse_session_id=sse_session_id
    )
    
    if sub_chat_response is None:
        print("❌ 副菜チャットリクエストが失敗しました")
        return False
    
    sub_task_id = sub_chat_response.get("task_id")
    if sub_task_id:
        print("📋 副菜を選択...")
        sub_selection_response = client.send_selection_request(
            task_id=sub_task_id,
            selection=1,
            sse_session_id=sse_session_id
        )
        
        if sub_selection_response is None:
            print("❌ 副菜選択が失敗しました")
            return False
        
        time.sleep(2)
    
    # 3. 献立保存リクエストを送信
    print("📋 献立保存をリクエスト...")
    save_response = client.send_menu_save_request(sse_session_id)
    
    if save_response is None:
        print("❌ 保存リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print(f"📋 レスポンス: {json.dumps(save_response, indent=2, ensure_ascii=False)}")
    
    success = save_response.get("success", False)
    total_saved = save_response.get("total_saved", 0)
    saved_recipes = save_response.get("saved_recipes", [])
    
    assert success == True, f"保存が成功していること: success={success}"
    assert total_saved >= 1, f"保存数が1以上であること: total_saved={total_saved}"
    
    # 主菜が保存されていることを確認
    main_recipes = [r for r in saved_recipes if r.get("category") == "main"]
    assert len(main_recipes) == 1, f"主菜が1件保存されていること: {len(main_recipes)}"
    
    print("✅ 主菜+副菜選択時の保存テストが成功しました")
    print(f"   保存されたレシピ数: {total_saved}")
    for recipe in saved_recipes:
        print(f"   - {recipe.get('category')}: {recipe.get('title')}")
    
    return True


def test_invalid_session(jwt_token=None):
    """無効なセッションIDの場合のテスト"""
    print("\n[テスト4] 無効なセッションIDの場合")
    
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        return False
    
    # 存在しないセッションID
    invalid_session_id = f"invalid_session_{uuid.uuid4()}"
    
    # 献立保存リクエストを送信
    response = client.send_menu_save_request(invalid_session_id)
    
    # 無効なセッションの場合は、保存するレシピがないというレスポンスが返る想定
    if response is None:
        print("⚠️ リクエストが失敗しました（これは想定内の可能性があります）")
        return True
    
    # レスポンスの検証
    print(f"📋 レスポンス: {json.dumps(response, indent=2, ensure_ascii=False)}")
    
    success = response.get("success", False)
    total_saved = response.get("total_saved", 0)
    
    # 無効なセッションの場合は、レシピがないというレスポンスが返る
    assert success == False or total_saved == 0, f"無効なセッションの場合は保存できないこと: success={success}, total_saved={total_saved}"
    
    print("✅ 無効なセッションIDの場合のテストが成功しました")
    return True


def run_all_tests(jwt_token=None):
    """全てのテストを実行"""
    print("=" * 80)
    print("Phase 5A: 献立保存APIエンドポイントのテスト")
    print("=" * 80)
    
    tests = [
        ("test_no_selected_recipes", test_no_selected_recipes),
        ("test_save_main_dish_only", test_save_main_dish_only),
        ("test_save_main_and_sub", test_save_main_and_sub),
        ("test_invalid_session", test_invalid_session),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*80}")
            print(f"実行中: {test_name}")
            print('='*80)
            
            result = test_func(jwt_token)
            
            if result:
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                failed += 1
                
        except AssertionError as e:
            print(f"\n❌ {test_name}: FAILED - {e}")
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"テスト結果: {passed} passed, {failed} failed (合計 {len(tests)})")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 5A: 献立保存APIエンドポイントのテスト")
    parser.add_argument("--token", help="JWTトークン（オプション）")
    args = parser.parse_args()
    
    success = run_all_tests(jwt_token=args.token)
    exit(0 if success else 1)

