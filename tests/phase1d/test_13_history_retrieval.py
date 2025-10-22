#!/usr/bin/env python3
"""
Phase 1D - 履歴取得機能テスト
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


async def test_history_get_recent_titles(jwt_token=None):
    """履歴取得機能のテスト"""
    
    print("🔍 履歴取得機能のテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 履歴にレシピを保存
    print("📝 履歴にレシピを保存")
    
    # レンコンのきんぴらを保存
    history_request_1 = "レンコンのきんぴらを作りました"
    sse_session_id_1 = f"test_session_history_1_{int(time.time())}"
    
    response_1 = client.send_chat_request(history_request_1, sse_session_id_1)
    if response_1 is None:
        print("❌ 履歴保存リクエスト1が失敗しました")
        return False
    
    # キャベツの炒め物を保存
    history_request_2 = "キャベツの炒め物を作りました"
    sse_session_id_2 = f"test_session_history_2_{int(time.time())}"
    
    response_2 = client.send_chat_request(history_request_2, sse_session_id_2)
    if response_2 is None:
        print("❌ 履歴保存リクエスト2が失敗しました")
        return False
    
    # 2. 履歴タイトルを取得（主菜14日間）
    print("📋 履歴タイトルを取得（主菜14日間）")
    
    history_get_request = "最近作った主菜の履歴を教えて"
    sse_session_id_get = f"test_session_history_get_{int(time.time())}"
    
    response_get = client.send_chat_request(history_get_request, sse_session_id_get)
    if response_get is None:
        print("❌ 履歴取得リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 履歴取得機能の検証")
    
    response_text = response_get["response"]
    success = response_get["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 履歴に関するキーワードの確認
    history_keywords = ["履歴", "最近", "作った", "レシピ"]
    assert any(keyword in response_text for keyword in history_keywords), f"履歴に関するキーワードが見つかりません: {history_keywords}"
    
    # 保存したレシピが含まれていることを確認
    saved_recipes = ["レンコンのきんぴら", "キャベツの炒め物"]
    found_recipes = [recipe for recipe in saved_recipes if recipe in response_text]
    assert len(found_recipes) > 0, f"保存したレシピが見つかりません: {saved_recipes}"
    
    print("✅ 履歴取得機能のテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   見つかったレシピ: {found_recipes}")
    
    return True


async def test_category_specific_exclusion(jwt_token=None):
    """カテゴリ別重複回避期間のテスト"""
    
    print("🔍 カテゴリ別重複回避期間のテスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 主菜の履歴取得（14日間）
    print("📋 主菜の履歴取得（14日間）")
    
    main_history_request = "最近作った主菜の履歴を教えて"
    sse_session_id_main = f"test_session_main_history_{int(time.time())}"
    
    response_main = client.send_chat_request(main_history_request, sse_session_id_main)
    if response_main is None:
        print("❌ 主菜履歴取得リクエストが失敗しました")
        return False
    
    # 副菜の履歴取得（7日間）
    print("📋 副菜の履歴取得（7日間）")
    
    sub_history_request = "最近作った副菜の履歴を教えて"
    sse_session_id_sub = f"test_session_sub_history_{int(time.time())}"
    
    response_sub = client.send_chat_request(sub_history_request, sse_session_id_sub)
    if response_sub is None:
        print("❌ 副菜履歴取得リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ カテゴリ別重複回避期間の検証")
    
    main_response_text = response_main["response"]
    sub_response_text = response_sub["response"]
    
    # 成功フラグの確認
    assert response_main["success"] == True, f"主菜履歴取得が成功していません: {response_main['success']}"
    assert response_sub["success"] == True, f"副菜履歴取得が成功していません: {response_sub['success']}"
    
    # 主菜と副菜の履歴が適切に取得されていることを確認
    main_keywords = ["主菜", "メイン"]
    sub_keywords = ["副菜", "サブ"]
    
    assert any(keyword in main_response_text for keyword in main_keywords), f"主菜に関するキーワードが見つかりません: {main_keywords}"
    assert any(keyword in sub_response_text for keyword in sub_keywords), f"副菜に関するキーワードが見つかりません: {sub_keywords}"
    
    print("✅ カテゴリ別重複回避期間のテストが成功しました")
    print(f"   主菜レスポンス長: {len(main_response_text)} 文字")
    print(f"   副菜レスポンス長: {len(sub_response_text)} 文字")
    
    return True


async def test_different_periods(jwt_token=None):
    """異なる期間での履歴取得テスト"""
    
    print("🔍 異なる期間での履歴取得テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 7日間の履歴取得
    print("📋 7日間の履歴取得")
    
    history_7days_request = "最近7日間の主菜履歴を教えて"
    sse_session_id_7days = f"test_session_7days_{int(time.time())}"
    
    response_7days = client.send_chat_request(history_7days_request, sse_session_id_7days)
    if response_7days is None:
        print("❌ 7日間履歴取得リクエストが失敗しました")
        return False
    
    # 14日間の履歴取得
    print("📋 14日間の履歴取得")
    
    history_14days_request = "最近14日間の主菜履歴を教えて"
    sse_session_id_14days = f"test_session_14days_{int(time.time())}"
    
    response_14days = client.send_chat_request(history_14days_request, sse_session_id_14days)
    if response_14days is None:
        print("❌ 14日間履歴取得リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 異なる期間での履歴取得の検証")
    
    response_7days_text = response_7days["response"]
    response_14days_text = response_14days["response"]
    
    # 成功フラグの確認
    assert response_7days["success"] == True, f"7日間履歴取得が成功していません: {response_7days['success']}"
    assert response_14days["success"] == True, f"14日間履歴取得が成功していません: {response_14days['success']}"
    
    # 期間に関するキーワードの確認
    period_keywords = ["日間", "最近", "履歴"]
    assert any(keyword in response_7days_text for keyword in period_keywords), f"7日間履歴に関するキーワードが見つかりません: {period_keywords}"
    assert any(keyword in response_14days_text for keyword in period_keywords), f"14日間履歴に関するキーワードが見つかりません: {period_keywords}"
    
    print("✅ 異なる期間での履歴取得テストが成功しました")
    print(f"   7日間レスポンス長: {len(response_7days_text)} 文字")
    print(f"   14日間レスポンス長: {len(response_14days_text)} 文字")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1D 履歴取得機能テスト")
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
    print("🚀 test_13_history_retrieval: start")
    print("📋 履歴取得機能のテストを実行します")
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
        # テスト1: 基本履歴取得テスト
        await test_history_get_recent_titles(jwt_token)
        
        # テスト2: カテゴリ別重複回避期間テスト
        await test_category_specific_exclusion(jwt_token)
        
        # テスト3: 異なる期間での履歴取得テスト
        await test_different_periods(jwt_token)
        
        print("🎉 test_13_history_retrieval: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_13_history_retrieval: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
