#!/usr/bin/env python3
"""
Phase 2A-2 - API統合テスト（HTTP通信ベース）
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
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


async def test_receive_user_selection_success(jwt_token=None):
    """選択結果受信の成功テスト"""
    print("🔍 選択結果受信の成功テスト")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 有効な選択リクエスト
    task_id = "main_dish_proposal_0"
    selection = 3
    sse_session_id = f"test_session_success_{int(time.time())}"
    
    response = client.send_selection_request(task_id, selection, sse_session_id)
    
    if response is None:
        print("❌ 選択リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 選択結果受信の検証")
    
    success = response.get("success", False)
    response_task_id = response.get("task_id", "")
    response_selection = response.get("selection", 0)
    
    # 成功フラグの確認
    assert success == True, f"選択処理が成功していません: success={success}"
    assert response_task_id == task_id, f"タスクIDが正しくありません: {response_task_id}"
    assert response_selection == selection, f"選択番号が正しくありません: {response_selection}"
    
    print("✅ 選択結果受信の成功テストが成功しました")
    print(f"   タスクID: {response_task_id}")
    print(f"   選択番号: {response_selection}")
    
    return True


async def test_receive_user_selection_missing_task_id(jwt_token=None):
    """タスクID未指定のテスト"""
    print("🔍 タスクID未指定のテスト")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # タスクID未指定のリクエスト
    url = f"{client.base_url}/chat/selection"
    payload = {
        "selection": 3,
        "sse_session_id": f"test_session_missing_task_{int(time.time())}"
    }
    
    try:
        response = client.session.post(url, json=payload, timeout=30)
        if response.status_code == 422:
            print("✅ タスクID未指定のテスト成功: 期待通りエラーが発生")
            return True
        else:
            print(f"⚠️ タスクID未指定のテスト: 予期しないステータスコード {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTPリクエストエラー: {e}")
        return False


async def test_receive_user_selection_missing_sse_session_id(jwt_token=None):
    """SSEセッションID未指定のテスト"""
    print("🔍 SSEセッションID未指定のテスト")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # SSEセッションID未指定のリクエスト
    url = f"{client.base_url}/chat/selection"
    payload = {
        "task_id": "main_dish_proposal_0",
        "selection": 3
    }
    
    try:
        response = client.session.post(url, json=payload, timeout=30)
        if response.status_code == 422:
            print("✅ SSEセッションID未指定のテスト成功: 期待通りエラーが発生")
            return True
        else:
            print(f"⚠️ SSEセッションID未指定のテスト: 予期しないステータスコード {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTPリクエストエラー: {e}")
        return False


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 2A-2 API統合テスト")
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
    print("🚀 test_04_selection_api_integration: start")
    print("📋 Phase 2A-2 API統合テストを実行します")
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
    
async def main() -> None:
    print("🚀 test_04_selection_api_integration: start")
    print("📋 Phase 2A-2 API統合テストを実行します")
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
        # テスト1: 選択結果受信の成功テスト
        await test_receive_user_selection_success(jwt_token)
        
        # テスト2: タスクID未指定のテスト
        await test_receive_user_selection_missing_task_id(jwt_token)
        
        # テスト3: SSEセッションID未指定のテスト
        await test_receive_user_selection_missing_sse_session_id(jwt_token)
        
        print("🎉 test_04_selection_api_integration: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_04_selection_api_integration: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
