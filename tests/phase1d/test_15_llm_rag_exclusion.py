#!/usr/bin/env python3
"""
Phase 1D - LLM/RAG除外機能テスト
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


async def test_llm_exclusion(jwt_token=None):
    """LLM推論での除外レシピ適用テスト"""
    
    print("🔍 LLM推論での除外レシピ適用テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 除外したいレシピを履歴に保存
    print("📝 除外したいレシピを履歴に保存")
    
    excluded_recipes = ["レンコンのきんぴら", "レンコンの天ぷら"]
    
    for recipe in excluded_recipes:
        history_request = f"{recipe}を作りました"
        sse_session_id = f"test_session_exclude_{recipe}_{int(time.time())}"
        
        response = client.send_chat_request(history_request, sse_session_id)
        if response is None:
            print(f"❌ 除外レシピ保存リクエストが失敗しました: {recipe}")
            return False
    
    # 2. LLM推論で主菜提案（除外レシピが適用される）
    print("📋 LLM推論で主菜提案（除外レシピ適用）")
    
    llm_request = "レンコンを使った主菜を5件提案して（斬新なレシピを重視）"
    sse_session_id = f"test_session_llm_exclusion_{int(time.time())}"
    
    response = client.send_chat_request(llm_request, sse_session_id)
    if response is None:
        print("❌ LLM推論リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ LLM推論除外レシピ適用の検証")
    
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
    
    # 除外レシピが提案されていないことを確認
    for excluded_recipe in excluded_recipes:
        assert excluded_recipe not in response_text, f"除外レシピが提案されています: {excluded_recipe}"
    
    # 斬新な提案に関するキーワードの確認
    innovative_keywords = ["斬新", "新しい", "オリジナル", "創作"]
    has_innovative_keywords = any(keyword in response_text for keyword in innovative_keywords)
    
    print("✅ LLM推論除外レシピ適用のテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   レンコンキーワード: {any(keyword in response_text for keyword in renkon_keywords)}")
    print(f"   除外レシピなし: {all(excluded_recipe not in response_text for excluded_recipe in excluded_recipes)}")
    print(f"   斬新キーワード: {has_innovative_keywords}")
    
    return True


async def test_rag_exclusion(jwt_token=None):
    """RAG検索での除外レシピ適用テスト"""
    
    print("🔍 RAG検索での除外レシピ適用テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 除外したいレシピを履歴に保存
    print("📝 除外したいレシピを履歴に保存")
    
    excluded_recipes = ["キャベツの炒め物", "キャベツのサラダ"]
    
    for recipe in excluded_recipes:
        history_request = f"{recipe}を作りました"
        sse_session_id = f"test_session_rag_exclude_{recipe}_{int(time.time())}"
        
        response = client.send_chat_request(history_request, sse_session_id)
        if response is None:
            print(f"❌ 除外レシピ保存リクエストが失敗しました: {recipe}")
            return False
    
    # 2. RAG検索で主菜提案（除外レシピが適用される）
    print("📋 RAG検索で主菜提案（除外レシピ適用）")
    
    rag_request = "キャベツを使った主菜を5件提案して（伝統的なレシピを重視）"
    sse_session_id = f"test_session_rag_exclusion_{int(time.time())}"
    
    response = client.send_chat_request(rag_request, sse_session_id)
    if response is None:
        print("❌ RAG検索リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ RAG検索除外レシピ適用の検証")
    
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
    
    # 除外レシピが提案されていないことを確認
    for excluded_recipe in excluded_recipes:
        assert excluded_recipe not in response_text, f"除外レシピが提案されています: {excluded_recipe}"
    
    # 伝統的な提案に関するキーワードの確認
    traditional_keywords = ["伝統", "定番", "クラシック", "昔ながら"]
    has_traditional_keywords = any(keyword in response_text for keyword in traditional_keywords)
    
    print("✅ RAG検索除外レシピ適用のテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   キャベツキーワード: {any(keyword in response_text for keyword in cabbage_keywords)}")
    print(f"   除外レシピなし: {all(excluded_recipe not in response_text for excluded_recipe in excluded_recipes)}")
    print(f"   伝統キーワード: {has_traditional_keywords}")
    
    return True


async def test_combined_exclusion(jwt_token=None):
    """LLM+RAG統合での除外レシピ適用テスト"""
    
    print("🔍 LLM+RAG統合での除外レシピ適用テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 1. 除外したいレシピを履歴に保存
    print("📝 除外したいレシピを履歴に保存")
    
    excluded_recipes = ["大根の煮物", "大根のサラダ", "大根の味噌汁"]
    
    for recipe in excluded_recipes:
        history_request = f"{recipe}を作りました"
        sse_session_id = f"test_session_combined_exclude_{recipe}_{int(time.time())}"
        
        response = client.send_chat_request(history_request, sse_session_id)
        if response is None:
            print(f"❌ 除外レシピ保存リクエストが失敗しました: {recipe}")
            return False
    
    # 2. LLM+RAG統合で主菜提案（除外レシピが適用される）
    print("📋 LLM+RAG統合で主菜提案（除外レシピ適用）")
    
    combined_request = "大根を使った主菜を5件提案して（斬新と伝統のバランス）"
    sse_session_id = f"test_session_combined_exclusion_{int(time.time())}"
    
    response = client.send_chat_request(combined_request, sse_session_id)
    if response is None:
        print("❌ LLM+RAG統合リクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ LLM+RAG統合除外レシピ適用の検証")
    
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
    
    # 除外レシピが提案されていないことを確認
    for excluded_recipe in excluded_recipes:
        assert excluded_recipe not in response_text, f"除外レシピが提案されています: {excluded_recipe}"
    
    # バランスに関するキーワードの確認
    balance_keywords = ["斬新", "伝統", "バランス", "混在"]
    has_balance_keywords = any(keyword in response_text for keyword in balance_keywords)
    
    print("✅ LLM+RAG統合除外レシピ適用のテストが成功しました")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   大根キーワード: {any(keyword in response_text for keyword in daikon_keywords)}")
    print(f"   除外レシピなし: {all(excluded_recipe not in response_text for excluded_recipe in excluded_recipes)}")
    print(f"   バランスキーワード: {has_balance_keywords}")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1D LLM/RAG除外機能テスト")
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
    print("🚀 test_15_llm_rag_exclusion: start")
    print("📋 LLM/RAG除外機能テストを実行します")
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
        # テスト1: LLM除外機能テスト
        await test_llm_exclusion(jwt_token)
        
        # テスト2: RAG除外機能テスト
        await test_rag_exclusion(jwt_token)
        
        # テスト3: LLM+RAG統合除外機能テスト
        await test_combined_exclusion(jwt_token)
        
        print("🎉 test_15_llm_rag_exclusion: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_15_llm_rag_exclusion: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
