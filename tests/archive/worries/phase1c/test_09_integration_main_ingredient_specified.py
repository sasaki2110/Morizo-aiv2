#!/usr/bin/env python3
"""
Phase 1C - 統合テスト（主要食材指定ケース）- HTTP API経由
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


async def test_main_ingredient_specified_flow(jwt_token=None):
    """主要食材指定ケースの統合テスト（HTTP API経由）"""
    
    print("🔍 主要食材指定ケースの統合テスト開始（HTTP API経由）")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # ユーザー要求（プロンプトの例に合わせた表現）
    user_request = "レンコンを使った主菜を教えて"
    sse_session_id = f"test_session_{int(time.time())}"
    
    # APIリクエストを送信
    print(f"📤 APIリクエスト送信: {user_request}")
    response = client.send_chat_request(user_request, sse_session_id)
    
    if response is None:
        print("❌ APIリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ APIレスポンスの検証")
    
    # レスポンス構造の確認
    assert "response" in response, f"レスポンスに'response'フィールドがありません: {response.keys()}"
    assert "success" in response, f"レスポンスに'success'フィールドがありません: {response.keys()}"
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # レスポンス内容の検証
    print(f"📝 レスポンス内容: {response_text[:200]}...")
    
    # 主菜提案に関するキーワードの確認
    main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
    assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
    
    # レンコンに関するキーワードの確認
    renkon_keywords = ["レンコン", "蓮根"]
    assert any(keyword in response_text for keyword in renkon_keywords), f"レンコンに関するキーワードが見つかりません: {renkon_keywords}"
    
    # エラーメッセージが含まれていないことを確認
    error_keywords = ["エラー", "失敗", "エラーが発生", "処理中にエラー"]
    assert not any(keyword in response_text for keyword in error_keywords), f"エラーメッセージが含まれています: {response_text}"
    
    # 曖昧性検出のメッセージが含まれていないことを確認（主要食材が指定されているため）
    ambiguity_keywords = ["なにか主な食材を指定しますか", "在庫から作れる主菜を提案しましょうか"]
    assert not any(keyword in response_text for keyword in ambiguity_keywords), f"曖昧性検出のメッセージが含まれています: {response_text}"
    
    print("✅ 主要食材指定ケースの統合テストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   レンコンキーワード: {any(keyword in response_text for keyword in renkon_keywords)}")
    print(f"   エラーなし: {not any(keyword in response_text for keyword in error_keywords)}")
    print(f"   曖昧性なし: {not any(keyword in response_text for keyword in ambiguity_keywords)}")
    
    return True


async def test_main_ingredient_specified_flow_with_different_ingredient(jwt_token=None):
    """異なる主要食材指定ケースの統合テスト（HTTP API経由）"""
    
    print("🔍 異なる主要食材指定ケースの統合テスト開始（HTTP API経由）")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # ユーザー要求（キャベツを指定）
    user_request = "キャベツを使った主菜を5件提案して"
    sse_session_id = f"test_session_2_{int(time.time())}"
    
    # APIリクエストを送信
    print(f"📤 APIリクエスト送信: {user_request}")
    response = client.send_chat_request(user_request, sse_session_id)
    
    if response is None:
        print("❌ APIリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 異なる主要食材指定ケースの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # キャベツに関するキーワードの確認
    cabbage_keywords = ["キャベツ", "キャベジ"]
    assert any(keyword in response_text for keyword in cabbage_keywords), f"キャベツに関するキーワードが見つかりません: {cabbage_keywords}"
    
    # エラーメッセージが含まれていないことを確認
    error_keywords = ["エラー", "失敗", "エラーが発生", "処理中にエラー"]
    assert not any(keyword in response_text for keyword in error_keywords), f"エラーメッセージが含まれています: {response_text}"
    
    print("✅ 異なる主要食材指定ケースの統合テストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   キャベツキーワード: {any(keyword in response_text for keyword in cabbage_keywords)}")
    print(f"   エラーなし: {not any(keyword in response_text for keyword in error_keywords)}")
    
    return True


async def test_main_ingredient_unspecified_flow(jwt_token=None):
    """主要食材未指定ケースの統合テスト（HTTP API経由）"""
    
    print("🔍 主要食材未指定ケースの統合テスト開始（HTTP API経由）")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # ユーザー要求（主要食材未指定）
    user_request = "主菜を5件提案して"
    sse_session_id = f"test_session_3_{int(time.time())}"
    
    # APIリクエストを送信
    print(f"📤 APIリクエスト送信: {user_request}")
    response = client.send_chat_request(user_request, sse_session_id)
    
    if response is None:
        print("❌ APIリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 主要食材未指定ケースの検証")
    
    response_text = response["response"]
    success = response["success"]
    requires_confirmation = response.get("requires_confirmation", False)
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 曖昧性検出のメッセージが含まれていることを確認
    ambiguity_keywords = ["なにか主な食材を指定しますか", "在庫から作れる主菜を提案しましょうか"]
    has_ambiguity_message = any(keyword in response_text for keyword in ambiguity_keywords)
    
    # 曖昧性確認が必要な場合の検証
    if requires_confirmation:
        assert has_ambiguity_message, f"曖昧性検出のメッセージが含まれていません: {response_text}"
        assert "confirmation_session_id" in response, f"確認セッションIDが含まれていません: {response.keys()}"
        print("✅ 曖昧性確認が必要なケースとして正しく処理されました")
    else:
        # 曖昧性確認が不要な場合（直接提案された場合）
        main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
        assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
        print("✅ 直接提案されたケースとして正しく処理されました")
    
    print("✅ 主要食材未指定ケースの統合テストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   曖昧性確認必要: {requires_confirmation}")
    print(f"   曖昧性メッセージ: {has_ambiguity_message}")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1C 統合テスト")
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
    print("🚀 test_09_integration_main_ingredient_specified: start")
    print("📋 HTTP API経由の統合テストを実行します")
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
        # テスト1: レンコン指定ケース
        await test_main_ingredient_specified_flow(jwt_token)
        
        # テスト2: キャベツ指定ケース
        await test_main_ingredient_specified_flow_with_different_ingredient(jwt_token)
        
        # テスト3: 主要食材未指定ケース
        await test_main_ingredient_unspecified_flow(jwt_token)
        
        print("🎉 test_09_integration_main_ingredient_specified: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_09_integration_main_ingredient_specified: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
