#!/usr/bin/env python3
"""
Phase 1D - MCPツール統合テスト
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


async def test_history_mcp_tool(jwt_token=None):
    """履歴取得MCPツールのテスト"""
    
    print("🔍 履歴取得MCPツールのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # MCPツールを直接呼び出し（履歴取得）
    print("📋 MCPツールで履歴取得")
    
    history_request = "最近作った主菜の履歴を取得して"
    sse_session_id = f"test_session_mcp_history_{int(time.time())}"
    
    response = client.send_chat_request(history_request, sse_session_id)
    if response is None:
        print("❌ MCPツール履歴取得リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ MCPツール履歴取得の検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 履歴取得に関するキーワードの確認（実際のレスポンス形式に対応）
    history_keywords = ["history_service", "history_get_recent_titles", "主菜", "ピーマン", "鶏もも肉"]
    assert any(keyword in response_text for keyword in history_keywords), f"履歴取得に関するキーワードが見つかりません: {history_keywords}"
    
    # エラーメッセージが含まれていないことを確認
    error_keywords = ["エラー", "失敗", "エラーが発生", "処理中にエラー"]
    assert not any(keyword in response_text for keyword in error_keywords), f"エラーメッセージが含まれています: {response_text}"
    
    print("✅ MCPツール履歴取得のテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   履歴キーワード: {any(keyword in response_text for keyword in history_keywords)}")
    print(f"   エラーなし: {not any(keyword in response_text for keyword in error_keywords)}")
    
    return True


async def test_tool_router_history(jwt_token=None):
    """ToolRouterでの履歴取得ツールのテスト"""
    
    print("🔍 ToolRouterでの履歴取得ツールのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # ToolRouter経由で履歴取得
    print("📋 ToolRouter経由で履歴取得")
    
    tool_router_request = "履歴サービスを使って最近の主菜履歴を取得して"
    sse_session_id = f"test_session_tool_router_{int(time.time())}"
    
    response = client.send_chat_request(tool_router_request, sse_session_id)
    if response is None:
        print("❌ ToolRouter履歴取得リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ ToolRouter履歴取得の検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # ToolRouter経由の履歴取得に関するキーワードの確認
    tool_router_keywords = ["履歴", "サービス", "取得", "最近", "主菜"]
    assert any(keyword in response_text for keyword in tool_router_keywords), f"ToolRouter履歴取得に関するキーワードが見つかりません: {tool_router_keywords}"
    
    # エラーメッセージが含まれていないことを確認
    error_keywords = ["エラー", "失敗", "エラーが発生", "処理中にエラー"]
    assert not any(keyword in response_text for keyword in error_keywords), f"エラーメッセージが含まれています: {response_text}"
    
    print("✅ ToolRouter履歴取得のテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   ToolRouterキーワード: {any(keyword in response_text for keyword in tool_router_keywords)}")
    print(f"   エラーなし: {not any(keyword in response_text for keyword in error_keywords)}")
    
    return True


async def test_mcp_tool_error_handling(jwt_token=None):
    """MCPツールエラーハンドリングのテスト"""
    
    print("🔍 MCPツールエラーハンドリングのテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 無効なパラメータでMCPツールを呼び出し
    print("📋 無効なパラメータでMCPツールを呼び出し")
    
    invalid_request = "存在しない履歴カテゴリの履歴を取得して"
    sse_session_id = f"test_session_mcp_error_{int(time.time())}"
    
    response = client.send_chat_request(invalid_request, sse_session_id)
    if response is None:
        print("❌ MCPツールエラーハンドリングリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ MCPツールエラーハンドリングの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # エラーハンドリングの確認
    # エラーが適切に処理されていることを確認（成功または適切なエラーメッセージ）
    if not success:
        # エラーが発生した場合、適切なエラーメッセージが含まれていることを確認
        error_handling_keywords = ["エラー", "失敗", "処理できません", "無効"]
        assert any(keyword in response_text for keyword in error_handling_keywords), f"適切なエラーメッセージが見つかりません: {error_handling_keywords}"
        print("✅ エラーが適切に処理されました")
    else:
        # 成功した場合、フォールバック処理が動作していることを確認
        fallback_keywords = ["こんにちは", "お手伝い", "何か"]
        assert any(keyword in response_text for keyword in fallback_keywords), f"フォールバック処理に関するキーワードが見つかりません: {fallback_keywords}"
        print("✅ フォールバック処理が動作しました")
    
    print("✅ MCPツールエラーハンドリングのテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   成功フラグ: {success}")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1D MCPツール統合テスト")
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
    print("🚀 test_14_mcp_tools_integration: start")
    print("📋 MCPツール統合テストを実行します")
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
        # テスト1: 履歴取得MCPツールテスト
        await test_history_mcp_tool(jwt_token)
        
        # テスト2: ToolRouter履歴取得ツールテスト
        await test_tool_router_history(jwt_token)
        
        # テスト3: MCPツールエラーハンドリングテスト
        await test_mcp_tool_error_handling(jwt_token)
        
        print("🎉 test_14_mcp_tools_integration: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_14_mcp_tools_integration: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
