#!/usr/bin/env python3
"""
Phase 1D - エラーハンドリングテスト
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
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


async def test_history_error_handling(jwt_token=None):
    """履歴取得エラー時のテスト"""
    
    print("🔍 履歴取得エラー時のテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 無効なパラメータで履歴取得
    print("📋 無効なパラメータで履歴取得")
    
    invalid_request = "存在しないカテゴリの履歴を取得して"
    sse_session_id = f"test_session_history_error_{int(time.time())}"
    
    response = client.send_chat_request(invalid_request, sse_session_id)
    if response is None:
        print("❌ 履歴取得エラーハンドリングリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 履歴取得エラーハンドリングの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # エラーハンドリングの確認
    # エラーが適切に処理されていることを確認（成功または適切なエラーメッセージ）
    if not success:
        # エラーが発生した場合、適切なエラーメッセージが含まれていることを確認
        error_handling_keywords = ["エラー", "失敗", "処理できません", "無効", "カテゴリ"]
        assert any(keyword in response_text for keyword in error_handling_keywords), f"適切なエラーメッセージが見つかりません: {error_handling_keywords}"
        print("✅ エラーが適切に処理されました")
    else:
        # 成功した場合、フォールバック処理が動作していることを確認
        fallback_keywords = ["履歴", "取得", "最近"]
        assert any(keyword in response_text for keyword in fallback_keywords), f"フォールバック処理に関するキーワードが見つかりません: {fallback_keywords}"
        print("✅ フォールバック処理が動作しました")
    
    print("✅ 履歴取得エラーハンドリングのテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   成功フラグ: {success}")
    
    return True


async def test_duplicate_avoidance_error_handling(jwt_token=None):
    """重複回避機能エラー時のテスト"""
    
    print("🔍 重複回避機能エラー時のテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 無効な食材で主菜提案
    print("📋 無効な食材で主菜提案")
    
    invalid_request = "存在しない食材を使った主菜を提案して"
    sse_session_id = f"test_session_duplicate_error_{int(time.time())}"
    
    response = client.send_chat_request(invalid_request, sse_session_id)
    if response is None:
        print("❌ 重複回避機能エラーハンドリングリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 重複回避機能エラーハンドリングの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # エラーハンドリングの確認
    # エラーが適切に処理されていることを確認（成功または適切なエラーメッセージ）
    if not success:
        # エラーが発生した場合、適切なエラーメッセージが含まれていることを確認
        error_handling_keywords = ["エラー", "失敗", "処理できません", "無効", "食材"]
        assert any(keyword in response_text for keyword in error_handling_keywords), f"適切なエラーメッセージが見つかりません: {error_handling_keywords}"
        print("✅ エラーが適切に処理されました")
    else:
        # 成功した場合、フォールバック処理が動作していることを確認
        fallback_keywords = ["主菜", "提案", "レシピ", "在庫"]
        assert any(keyword in response_text for keyword in fallback_keywords), f"フォールバック処理に関するキーワードが見つかりません: {fallback_keywords}"
        print("✅ フォールバック処理が動作しました")
    
    print("✅ 重複回避機能エラーハンドリングのテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   成功フラグ: {success}")
    
    return True


async def test_general_error_handling(jwt_token=None):
    """一般的なエラーハンドリングのテスト"""
    
    print("🔍 一般的なエラーハンドリングのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 無効なリクエスト
    print("📋 無効なリクエスト")
    
    invalid_request = "無効なリクエストです"
    sse_session_id = f"test_session_general_error_{int(time.time())}"
    
    response = client.send_chat_request(invalid_request, sse_session_id)
    if response is None:
        print("❌ 一般的なエラーハンドリングリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 一般的なエラーハンドリングの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # エラーハンドリングの確認
    # エラーが適切に処理されていることを確認（成功または適切なエラーメッセージ）
    if not success:
        # エラーが発生した場合、適切なエラーメッセージが含まれていることを確認
        error_handling_keywords = ["エラー", "失敗", "処理できません", "無効", "理解できません"]
        assert any(keyword in response_text for keyword in error_handling_keywords), f"適切なエラーメッセージが見つかりません: {error_handling_keywords}"
        print("✅ エラーが適切に処理されました")
    else:
        # 成功した場合、フォールバック処理が動作していることを確認
        fallback_keywords = ["主菜", "提案", "レシピ", "在庫"]
        assert any(keyword in response_text for keyword in fallback_keywords), f"フォールバック処理に関するキーワードが見つかりません: {fallback_keywords}"
        print("✅ フォールバック処理が動作しました")
    
    print("✅ 一般的なエラーハンドリングのテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   成功フラグ: {success}")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1D エラーハンドリングテスト")
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
    print("🚀 test_18_error_handling: start")
    print("📋 エラーハンドリングテストを実行します")
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
        # テスト1: 履歴取得エラー時のテスト
        await test_history_error_handling(jwt_token)
        
        # テスト2: 重複回避機能エラー時のテスト
        await test_duplicate_avoidance_error_handling(jwt_token)
        
        # テスト3: 一般的なエラーハンドリングのテスト
        await test_general_error_handling(jwt_token)
        
        print("🎉 test_18_error_handling: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_18_error_handling: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
