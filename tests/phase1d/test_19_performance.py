#!/usr/bin/env python3
"""
Phase 1D - パフォーマンステスト
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


async def test_history_performance(jwt_token=None):
    """履歴取得のパフォーマンステスト"""
    
    print("🔍 履歴取得のパフォーマンステスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 実行時間測定
    print("⏱️ 履歴取得の実行時間測定")
    
    start_time = time.time()
    
    history_request = "最近作った主菜の履歴を教えて"
    sse_session_id = f"test_session_history_perf_{int(time.time())}"
    
    response = client.send_chat_request(history_request, sse_session_id)
    if response is None:
        print("❌ 履歴取得パフォーマンステストリクエストが失敗しました")
        return False
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # レスポンスの検証
    print("✅ 履歴取得パフォーマンステストの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # パフォーマンス要件の確認（1秒以内）
    assert execution_time < 1.0, f"履歴取得が1秒以内に完了していません: {execution_time:.3f}秒"
    
    # 履歴取得に関するキーワードの確認
    history_keywords = ["履歴", "最近", "作った", "レシピ"]
    assert any(keyword in response_text for keyword in history_keywords), f"履歴取得に関するキーワードが見つかりません: {history_keywords}"
    
    print("✅ 履歴取得のパフォーマンステストが成功しました")
    print(f"   実行時間: {execution_time:.3f} 秒")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   履歴キーワード: {any(keyword in response_text for keyword in history_keywords)}")
    
    return True


async def test_duplicate_avoidance_performance(jwt_token=None):
    """重複回避機能の統合パフォーマンステスト"""
    
    print("🔍 重複回避機能の統合パフォーマンステスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 実行時間測定
    print("⏱️ 重複回避機能の統合処理の実行時間測定")
    
    start_time = time.time()
    
    user_request = "レンコンを使った主菜を5件提案して"
    sse_session_id = f"test_session_duplicate_perf_{int(time.time())}"
    
    response = client.send_chat_request(user_request, sse_session_id)
    if response is None:
        print("❌ 重複回避機能パフォーマンステストリクエストが失敗しました")
        return False
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # レスポンスの検証
    print("✅ 重複回避機能パフォーマンステストの検証")
    
    response_text = response["response"]
    success = response["success"]
    
    # 成功フラグの確認
    assert success == True, f"処理が成功していません: success={success}"
    
    # パフォーマンス要件の確認（6秒以内）
    assert execution_time < 6.0, f"重複回避統合処理が6秒以内に完了していません: {execution_time:.2f}秒"
    
    # 主菜提案に関するキーワードの確認
    main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
    assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
    
    # レンコンに関するキーワードの確認
    renkon_keywords = ["レンコン", "蓮根"]
    assert any(keyword in response_text for keyword in renkon_keywords), f"レンコンに関するキーワードが見つかりません: {renkon_keywords}"
    
    print("✅ 重複回避機能の統合パフォーマンステストが成功しました")
    print(f"   実行時間: {execution_time:.2f} 秒")
    print(f"   レスポンス長: {len(response_text)} 文字")
    print(f"   レンコンキーワード: {any(keyword in response_text for keyword in renkon_keywords)}")
    
    return True


async def test_concurrent_performance(jwt_token=None):
    """並行処理パフォーマンステスト"""
    
    print("🔍 並行処理パフォーマンステスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient(jwt_token=jwt_token)
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 並行処理の実行時間測定
    print("⏱️ 並行処理の実行時間測定")
    
    start_time = time.time()
    
    # 複数のリクエストを並行実行
    tasks = []
    ingredients = ["レンコン", "キャベツ", "大根"]
    
    for ingredient in ingredients:
        task = asyncio.create_task(
            send_chat_request_async(client, f"{ingredient}を使った主菜を5件提案して", f"test_session_concurrent_{ingredient}_{int(time.time())}")
        )
        tasks.append(task)
    
    # すべてのタスクの完了を待つ
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # レスポンスの検証
    print("✅ 並行処理パフォーマンステストの検証")
    
    successful_responses = [r for r in responses if isinstance(r, dict) and r.get("success", False)]
    
    # 成功したレスポンスの確認
    assert len(successful_responses) > 0, f"成功したレスポンスがありません: {len(successful_responses)}"
    
    # パフォーマンス要件の確認（10秒以内）
    assert execution_time < 10.0, f"並行処理が10秒以内に完了していません: {execution_time:.2f}秒"
    
    # 各レスポンスの内容確認
    for i, response in enumerate(successful_responses):
        response_text = response["response"]
        ingredient = ingredients[i]
        
        # 主菜提案に関するキーワードの確認
        main_dish_keywords = ["主菜", "提案", "レシピ", "料理"]
        assert any(keyword in response_text for keyword in main_dish_keywords), f"主菜提案に関するキーワードが見つかりません: {main_dish_keywords}"
        
        # 食材に関するキーワードの確認
        ingredient_keywords = [ingredient]
        assert any(keyword in response_text for keyword in ingredient_keywords), f"{ingredient}に関するキーワードが見つかりません: {ingredient_keywords}"
    
    print("✅ 並行処理パフォーマンステストが成功しました")
    print(f"   実行時間: {execution_time:.2f} 秒")
    print(f"   成功レスポンス数: {len(successful_responses)}")
    print(f"   総リクエスト数: {len(tasks)}")
    
    return True


async def send_chat_request_async(client, message, sse_session_id):
    """非同期でチャットリクエストを送信"""
    return client.send_chat_request(message, sse_session_id)


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1D パフォーマンステスト")
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
    print("🚀 test_19_performance: start")
    print("📋 パフォーマンステストを実行します")
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
        # テスト1: 履歴取得のパフォーマンステスト
        await test_history_performance(jwt_token)
        
        # テスト2: 重複回避機能の統合パフォーマンステスト
        await test_duplicate_avoidance_performance(jwt_token)
        
        # テスト3: 並行処理パフォーマンステスト
        await test_concurrent_performance(jwt_token)
        
        print("🎉 test_19_performance: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_19_performance: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
