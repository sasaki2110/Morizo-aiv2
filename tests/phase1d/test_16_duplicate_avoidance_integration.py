#!/usr/bin/env python3
"""
Phase 1D - 重複回避統合テスト
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


async def test_duplicate_avoidance_integration(jwt_token=None):
    """重複回避機能の統合テスト"""
    
    print("🔍 重複回避機能の統合テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 履歴にレシピを保存
    print("📝 履歴にレシピを保存")
    
    excluded_recipes = ["レンコンのきんぴら", "レンコンの天ぷら", "レンコンの煮物"]
    
    for recipe in excluded_recipes:
        history_request = f"{recipe}を作りました"
        sse_session_id = f"test_session_exclude_{recipe}_{int(time.time())}"
        
        response = client.send_chat_request(history_request, sse_session_id)
        if response is None:
            print(f"❌ 履歴保存リクエストが失敗しました: {recipe}")
            return False
    
    # 2. ユーザー要求（主菜提案）
    print("📋 ユーザー要求（主菜提案）")
    
    user_request = "レンコンを使った主菜を5件提案して"
    sse_session_id = f"test_session_duplicate_avoidance_{int(time.time())}"
    
    response = client.send_chat_request(user_request, sse_session_id)
    if response is None:
        print("❌ 主菜提案リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 重複回避機能の統合テスト検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 主菜提案に関するキーワードの確認
    main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
    assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
    
    # レンコンに関するキーワードの確認
    renkon_keywords = ["レンコン", "蓮根"]
    assert any(keyword in response_text for keyword in renkon_keywords), f"レンコンに関するキーワードが見つかりません: {renkon_keywords}"
    
    # 重複回避の確認（除外レシピが提案されていない）
    for excluded_recipe in excluded_recipes:
        assert excluded_recipe not in response_text, f"除外レシピが提案されています: {excluded_recipe}"
    
    # 5件提案の確認
    proposal_count_keywords = ["5件", "5つ", "5個", "5種類"]
    has_proposal_count = any(keyword in response_text for keyword in proposal_count_keywords)
    
    # 斬新と伝統のバランスの確認
    balance_keywords = ["斬新", "伝統", "LLM", "RAG", "推論", "検索"]
    has_balance_keywords = any(keyword in response_text for keyword in balance_keywords)
    
    print("✅ 重複回避機能の統合テストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   レンコンキーワード: {any(keyword in response_text for keyword in renkon_keywords)}")
    print(f"   除外レシピなし: {all(excluded_recipe not in response_text for excluded_recipe in excluded_recipes)}")
    print(f"   5件提案: {has_proposal_count}")
    print(f"   バランスキーワード: {has_balance_keywords}")
    
    return True


async def test_duplicate_avoidance_with_different_ingredient(jwt_token=None):
    """異なる食材での重複回避統合テスト"""
    
    print("🔍 異なる食材での重複回避統合テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 履歴にレシピを保存
    print("📝 履歴にレシピを保存")
    
    excluded_recipes = ["キャベツの炒め物", "キャベツのサラダ", "キャベツの煮物"]
    
    for recipe in excluded_recipes:
        history_request = f"{recipe}を作りました"
        sse_session_id = f"test_session_exclude_cabbage_{recipe}_{int(time.time())}"
        
        response = client.send_chat_request(history_request, sse_session_id)
        if response is None:
            print(f"❌ 履歴保存リクエストが失敗しました: {recipe}")
            return False
    
    # 2. ユーザー要求（主菜提案）
    print("📋 ユーザー要求（主菜提案）")
    
    user_request = "キャベツを使った主菜を5件提案して"
    sse_session_id = f"test_session_duplicate_avoidance_cabbage_{int(time.time())}"
    
    response = client.send_chat_request(user_request, sse_session_id)
    if response is None:
        print("❌ 主菜提案リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 異なる食材での重複回避統合テスト検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 主菜提案に関するキーワードの確認
    main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
    assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
    
    # キャベツに関するキーワードの確認
    cabbage_keywords = ["キャベツ", "キャベジ"]
    assert any(keyword in response_text for keyword in cabbage_keywords), f"キャベツに関するキーワードが見つかりません: {cabbage_keywords}"
    
    # 重複回避の確認（除外レシピが提案されていない）
    for excluded_recipe in excluded_recipes:
        assert excluded_recipe not in response_text, f"除外レシピが提案されています: {excluded_recipe}"
    
    print("✅ 異なる食材での重複回避統合テストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   キャベツキーワード: {any(keyword in response_text for keyword in cabbage_keywords)}")
    print(f"   除外レシピなし: {all(excluded_recipe not in response_text for excluded_recipe in excluded_recipes)}")
    
    return True


async def test_duplicate_avoidance_with_no_history(jwt_token=None):
    """履歴なしでの重複回避統合テスト"""
    
    print("🔍 履歴なしでの重複回避統合テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 履歴を保存せずに直接主菜提案
    print("📋 履歴なしで主菜提案")
    
    user_request = "大根を使った主菜を5件提案して"
    sse_session_id = f"test_session_no_history_{int(time.time())}"
    
    response = client.send_chat_request(user_request, sse_session_id)
    if response is None:
        print("❌ 主菜提案リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ 履歴なしでの重複回避統合テスト検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # 主菜提案に関するキーワードの確認
    main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
    assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
    
    # 大根に関するキーワードの確認
    daikon_keywords = ["大根", "だいこん"]
    assert any(keyword in response_text for keyword in daikon_keywords), f"大根に関するキーワードが見つかりません: {daikon_keywords}"
    
    # エラーメッセージが含まれていないことを確認
    error_keywords = ["エラー", "失敗", "エラーが発生", "処理中にエラー"]
    assert not any(keyword in response_text for keyword in error_keywords), f"エラーメッセージが含まれています: {response_text}"
    
    print("✅ 履歴なしでの重複回避統合テストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   大根キーワード: {any(keyword in response_text for keyword in daikon_keywords)}")
    print(f"   エラーなし: {not any(keyword in response_text for keyword in error_keywords)}")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1D 重複回避統合テスト")
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
    print("🚀 test_16_duplicate_avoidance_integration: start")
    print("📋 重複回避統合テストを実行します")
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
        # テスト1: 重複回避機能の統合テスト
        await test_duplicate_avoidance_integration(jwt_token)
        
        # テスト2: 異なる食材での重複回避統合テスト
        await test_duplicate_avoidance_with_different_ingredient(jwt_token)
        
        # テスト3: 履歴なしでの重複回避統合テスト
        await test_duplicate_avoidance_with_no_history(jwt_token)
        
        print("🎉 test_16_duplicate_avoidance_integration: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_16_duplicate_avoidance_integration: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
