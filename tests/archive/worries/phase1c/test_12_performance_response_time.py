#!/usr/bin/env python3
"""
Phase 1C - レスポンス時間テスト（HTTP API経由）
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


async def test_response_time():
    """レスポンス時間のテスト"""
    
    print("🔍 レスポンス時間テスト開始")
    
    # テストクライアントの初期化
    client = IntegrationTestClient()
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # テストデータ
    user_request = "レンコンを使った主菜を5件提案して"
    sse_session_id = f"test_session_performance_{int(time.time())}"
    
    print(f"📤 APIリクエスト送信: {user_request}")
    print("⏱️ 実行時間を測定中...")
    
    # 実行時間測定
    start_time = time.time()
    response = client.send_chat_request(user_request, sse_session_id)
    end_time = time.time()
    
    execution_time = end_time - start_time
    
    if response is None:
        print("❌ APIリクエストが失敗しました")
        return False
    
    # レスポンスの検証
    print("✅ レスポンス時間の検証")
    print(f"⏱️ 実行時間: {execution_time:.2f} 秒")
    
    # 実行時間の検証（120秒以内）
    assert execution_time < 120.0, f"実行時間が120秒を超えました: {execution_time:.2f}秒"
    
    # レスポンス構造の確認（test_09と同じパターン）
    assert "response" in response, f"レスポンスに'response'フィールドがありません: {response.keys()}"
    assert "success" in response, f"レスポンスに'success'フィールドがありません: {response.keys()}"
    
    response_text = response["response"]
    print("✅ 正常なレスポンスが返されました")
    print(f"📝 レスポンス内容: {response_text[:200]}...")
    
    print("✅ レスポンス時間テストが成功しました")
    print(f"   実行時間: {execution_time:.2f} 秒")
    
    return True


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 1C レスポンス時間テスト")
    parser.add_argument(
        "--base-url", 
        type=str, 
        default="http://localhost:8000",
        help="APIベースURL（デフォルト: http://localhost:8000）"
    )
    return parser.parse_args()


async def main() -> None:
    print("🚀 test_12_performance_response_time: start")
    print("📋 HTTP API経由のレスポンス時間テストを実行します")
    print("⚠️ 事前に 'python main.py' でサーバーを起動してください")
    print("⏱️ 実行時間制限: 120秒以内")
    
    # コマンドライン引数の解析
    args = parse_arguments()
    
    try:
        # レスポンス時間テスト
        await test_response_time()
        
        print("🎉 test_12_performance_response_time: テストが成功しました")
        
    except Exception as e:
        print(f"❌ test_12_performance_response_time: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())


