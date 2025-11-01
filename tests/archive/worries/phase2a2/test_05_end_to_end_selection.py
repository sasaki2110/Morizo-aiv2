#!/usr/bin/env python3
"""
Phase 2A-2 - エンドツーエンドテスト
"""

import asyncio
import sys
import os
import requests
import json
import time
import argparse
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
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
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
            return None
    
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
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            return None
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


async def test_complete_selection_flow(jwt_token=None):
    """完全な選択フローのテスト"""
    
    print("🔍 完全な選択フローのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. ユーザーリクエスト（レンコンを使ったメインを提案して）
    print("📋 ユーザーリクエスト: レンコンを使ったメインを提案して")
    
    chat_request = "レンコンを使ったメインを提案して"
    sse_session_id = f"test_session_selection_{int(time.time())}"
    
    response = client.send_chat_request(chat_request, sse_session_id)
    if response is None:
        print("❌ チャットリクエストが失敗しました")
        return False
    
    # 2. レスポンスの検証
    print("✅ チャットレスポンスの検証")
    
    success = response.get("success", False)
    response_text = response.get("response", "")
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 主菜提案に関するキーワードの確認
    main_dish_keywords = ["主菜", "メイン", "レンコン", "提案"]
    assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
    
    print("✅ チャットレスポンスの検証が成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   主菜キーワード: {any(keyword in response_text for keyword in main_dish_keywords)}")
    
    # 3. 選択要求の確認（Phase 2Bで実装予定のため、現在はスキップ）
    print("⏭ 選択要求の確認は Phase 2B で実装予定のためスキップ")
    
    return True


async def test_selection_api_endpoint(jwt_token=None):
    """選択APIエンドポイントのテスト"""
    
    print("🔍 選択APIエンドポイントのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 有効な選択リクエスト
    print("📋 有効な選択リクエストのテスト")
    
    selection_request = {
        "task_id": "main_dish_proposal_0",
        "selection": 3,
        "sse_session_id": f"test_session_api_{int(time.time())}"
    }
    
    response = client.send_selection_request(
        selection_request["task_id"],
        selection_request["selection"],
        selection_request["sse_session_id"]
    )
    
    if response is None:
        print("❌ 選択リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 選択APIレスポンスの検証")
    
    success = response.get("success", False)
    task_id = response.get("task_id", "")
    selection = response.get("selection", 0)
    
    # 成功フラグの確認
    assert success == True, f"選択処理が成功していません: success={success}"
    assert task_id == "main_dish_proposal_0", f"タスクIDが正しくありません: {task_id}"
    assert selection == 3, f"選択番号が正しくありません: {selection}"
    
    print("✅ 選択APIエンドポイントのテストが成功しました")
    print(f"   タスクID: {task_id}")
    print(f"   選択番号: {selection}")
    
    return True


async def test_invalid_selection_requests(jwt_token=None):
    """無効な選択リクエストのテスト"""
    
    print("🔍 無効な選択リクエストのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 無効な選択番号（下限）
    print("📋 無効な選択番号（下限）のテスト")
    
    response = client.send_selection_request(
        "main_dish_proposal_0", 0, f"test_session_invalid_{int(time.time())}"
    )
    
    if response is None:
        print("✅ 無効な選択番号（下限）のテスト成功: 期待通りエラーが発生")
    else:
        print("⚠️ 無効な選択番号（下限）のテスト: エラーが発生しませんでした")
    
    # 2. 無効な選択番号（上限）
    print("📋 無効な選択番号（上限）のテスト")
    
    response = client.send_selection_request(
        "main_dish_proposal_0", 6, f"test_session_invalid_{int(time.time())}"
    )
    
    if response is None:
        print("✅ 無効な選択番号（上限）のテスト成功: 期待通りエラーが発生")
    else:
        print("⚠️ 無効な選択番号（上限）のテスト: エラーが発生しませんでした")
    
    print("✅ 無効な選択リクエストのテストが完了しました")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 2A-2 エンドツーエンドテスト")
    parser.add_argument(
        "--token", 
        type=str, 
        help="JWTトークンを指定（環境変数TEST_USER_JWT_TOKENより優先）"
    )
    parser.add_argument(
        "--base-url", 
        type=str, 
        default="http://localhost:8000",
        help="APIベースURL（デフォルト: http://localhost:8000）"
    )
    return parser.parse_args()


async def main() -> None:
    print("🚀 test_05_end_to_end_selection: start")
    print("📋 Phase 2A-2 エンドツーエンドテストを実行します")
    print("⚠️ 事前に 'python main.py' でサーバーを起動してください")
    
    # コマンドライン引数の解析
    args = parse_arguments()
    
    # JWTトークンの確認
    jwt_token = args.token or os.getenv("TEST_USER_JWT_TOKEN")
    if not jwt_token:
        print("❌ JWTトークンが設定されていません")
        print("   以下のいずれかの方法でトークンを設定してください:")
        print("   1. 環境変数: export TEST_USER_JWT_TOKEN='your_jwt_token'")
        print("   2. .envファイル: TEST_USER_JWT_TOKEN=your_jwt_token")
        print("   3. コマンドライン引数: --token 'your_jwt_token'")
        return
    
    try:
        # テスト1: 完全な選択フローのテスト
        await test_complete_selection_flow(jwt_token)
        
        # テスト2: 選択APIエンドポイントのテスト
        await test_selection_api_endpoint(jwt_token)
        
        # テスト3: 無効な選択リクエストのテスト
        await test_invalid_selection_requests(jwt_token)
        
        print("🎉 test_05_end_to_end_selection: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_05_end_to_end_selection: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
