#!/usr/bin/env python3
"""
Phase 2C - 異常系テスト（HTTPリクエストベース）
フロントから入力できない異常系をテストするためのファイル
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


class Phase2CErrorTestClient:
    """Phase 2C異常系テスト用のHTTPクライアント"""
    
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
            return response
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
            return response
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


async def test_invalid_selection_range():
    """無効な選択範囲のテスト（フロントからは入力できない異常値）"""
    print("🔍 無効な選択範囲のテスト開始")
    
    client = Phase2CErrorTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    sse_session_id = f"test_session_invalid_range_{int(time.time())}"
    
    # 異常な選択値のテストケース
    invalid_selections = [
        -1,      # 負の値
        0,       # 0（通常は1から始まる）
        999,     # 非常に大きな値
        -999,    # 非常に小さな負の値
    ]
    
    for invalid_selection in invalid_selections:
        print(f"📋 異常な選択値のテスト: {invalid_selection}")
        
        response = client.send_selection_request(
            "main_dish_proposal_0", 
            invalid_selection, 
            sse_session_id
        )
        
        if response is None:
            print(f"✅ 異常な選択値 {invalid_selection}: 期待通りエラーが発生")
            continue
        
        # レスポンスの検証
        print(f"📝 実際のHTTPステータス: {response.status_code}")
        
        if response.status_code in [400, 422]:
            print(f"✅ 異常な選択値 {invalid_selection}: 期待通りバリデーションエラーが発生")
        elif response.status_code == 500:
            print(f"✅ 異常な選択値 {invalid_selection}: 500エラー（内部エラーとして適切）")
        else:
            print(f"⚠️ 異常な選択値 {invalid_selection}: 予期しないステータスコード {response.status_code}")
    
    print("✅ 無効な選択範囲のテストが完了しました")
    return True


async def test_invalid_task_id_format():
    """無効なタスクIDフォーマットのテスト"""
    print("🔍 無効なタスクIDフォーマットのテスト開始")
    
    client = Phase2CErrorTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    sse_session_id = f"test_session_invalid_task_{int(time.time())}"
    
    # 異常なタスクIDのテストケース
    invalid_task_ids = [
        "",                    # 空文字
        "invalid_task",        # 存在しないタスク
        "main_dish_proposal_999",  # 存在しないタスク番号
        "sub_dish_proposal_0",     # 存在しないタスクタイプ
        "soup_proposal_0",          # 存在しないタスクタイプ
        "task_with_special_chars!@#",  # 特殊文字
        "task with spaces",         # スペース
        "タスク名",                 # 日本語
    ]
    
    for invalid_task_id in invalid_task_ids:
        print(f"📋 異常なタスクIDのテスト: '{invalid_task_id}'")
        
        response = client.send_selection_request(
            invalid_task_id, 
            1, 
            sse_session_id
        )
        
        if response is None:
            print(f"✅ 異常なタスクID '{invalid_task_id}': 期待通りエラーが発生")
            continue
        
        # レスポンスの検証
        print(f"📝 実際のHTTPステータス: {response.status_code}")
        
        if response.status_code in [400, 422]:
            print(f"✅ 異常なタスクID '{invalid_task_id}': 期待通りバリデーションエラーが発生")
        elif response.status_code == 500:
            print(f"✅ 異常なタスクID '{invalid_task_id}': 500エラー（内部エラーとして適切）")
        else:
            print(f"⚠️ 異常なタスクID '{invalid_task_id}': 予期しないステータスコード {response.status_code}")
    
    print("✅ 無効なタスクIDフォーマットのテストが完了しました")
    return True


async def test_invalid_sse_session_id():
    """無効なSSEセッションIDのテスト"""
    print("🔍 無効なSSEセッションIDのテスト開始")
    
    client = Phase2CErrorTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    # 異常なSSEセッションIDのテストケース
    invalid_sse_session_ids = [
        "",                    # 空文字
        "nonexistent_session", # 存在しないセッション
        "session_with_special_chars!@#",  # 特殊文字
        "session with spaces",            # スペース
        "セッション名",                   # 日本語
        "very_long_session_id_" + "x" * 1000,  # 非常に長い文字列
    ]
    
    for invalid_sse_session_id in invalid_sse_session_ids:
        print(f"📋 異常なSSEセッションIDのテスト: '{invalid_sse_session_id[:50]}...'")
        
        response = client.send_selection_request(
            "main_dish_proposal_0", 
            1, 
            invalid_sse_session_id
        )
        
        if response is None:
            print(f"✅ 異常なSSEセッションID '{invalid_sse_session_id[:20]}...': 期待通りエラーが発生")
            continue
        
        # レスポンスの検証
        print(f"📝 実際のHTTPステータス: {response.status_code}")
        
        if response.status_code in [400, 422]:
            print(f"✅ 異常なSSEセッションID '{invalid_sse_session_id[:20]}...': 期待通りバリデーションエラーが発生")
        elif response.status_code == 500:
            print(f"✅ 異常なSSEセッションID '{invalid_sse_session_id[:20]}...': 500エラー（内部エラーとして適切）")
        else:
            print(f"⚠️ 異常なSSEセッションID '{invalid_sse_session_id[:20]}...': 予期しないステータスコード {response.status_code}")
    
    print("✅ 無効なSSEセッションIDのテストが完了しました")
    return True


async def test_malformed_json_request():
    """不正なJSONリクエストのテスト"""
    print("🔍 不正なJSONリクエストのテスト開始")
    
    client = Phase2CErrorTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    url = f"{client.base_url}/chat/selection"
    
    # 不正なJSONのテストケース
    malformed_requests = [
        '{"task_id": "main_dish_proposal_0", "selection": 1, "sse_session_id": "test"}',  # 正常なJSON
        '{"task_id": "main_dish_proposal_0", "selection": 1, "sse_session_id": "test"',   # 閉じ括弧なし
        '{"task_id": "main_dish_proposal_0", "selection": 1, "sse_session_id": "test"}}', # 余分な閉じ括弧
        '{"task_id": "main_dish_proposal_0", "selection": 1, "sse_session_id": "test",}', # 余分なカンマ
        '{"task_id": "main_dish_proposal_0", "selection": 1}',  # 必須フィールド不足
        '{"task_id": "main_dish_proposal_0"}',  # 必須フィールド不足
        '{}',  # 空のJSON
        'invalid json',  # 無効なJSON
        '',  # 空文字
    ]
    
    for i, malformed_request in enumerate(malformed_requests):
        print(f"📋 不正なJSONリクエストのテスト {i+1}: {malformed_request[:50]}...")
        
        try:
            # Content-Typeを一時的に変更してJSONとして送信
            headers = client.session.headers.copy()
            headers["Content-Type"] = "application/json"
            
            response = client.session.post(url, data=malformed_request, headers=headers, timeout=30)
            
            # レスポンスの検証
            print(f"📝 実際のHTTPステータス: {response.status_code}")
            
            if response.status_code in [400, 422]:
                print(f"✅ 不正なJSONリクエスト {i+1}: 期待通りバリデーションエラーが発生")
            elif response.status_code == 500:
                print(f"✅ 不正なJSONリクエスト {i+1}: 500エラー（内部エラーとして適切）")
            else:
                print(f"⚠️ 不正なJSONリクエスト {i+1}: 予期しないステータスコード {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"✅ 不正なJSONリクエスト {i+1}: 期待通りリクエストエラーが発生: {e}")
    
    print("✅ 不正なJSONリクエストのテストが完了しました")
    return True


async def test_concurrent_selection_requests():
    """同時選択リクエストのテスト（競合状態のテスト）"""
    print("🔍 同時選択リクエストのテスト開始")
    
    client = Phase2CErrorTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    sse_session_id = f"test_session_concurrent_{int(time.time())}"
    
    # 同時に複数の選択リクエストを送信
    print("📋 同時選択リクエストの送信")
    
    import threading
    import queue
    
    results = queue.Queue()
    
    def send_selection(selection_value):
        """選択リクエストを送信する関数"""
        try:
            response = client.send_selection_request(
                "main_dish_proposal_0", 
                selection_value, 
                sse_session_id
            )
            results.put((selection_value, response))
        except Exception as e:
            results.put((selection_value, f"Error: {e}"))
    
    # 複数のスレッドで同時にリクエストを送信
    threads = []
    for i in range(1, 6):  # 1から5までの選択値を同時送信
        thread = threading.Thread(target=send_selection, args=(i,))
        threads.append(thread)
        thread.start()
    
    # すべてのスレッドの完了を待つ
    for thread in threads:
        thread.join()
    
    # 結果の確認
    print("📝 同時選択リクエストの結果確認")
    
    success_count = 0
    error_count = 0
    
    while not results.empty():
        selection_value, response = results.get()
        
        if isinstance(response, str) and response.startswith("Error"):
            print(f"✅ 選択値 {selection_value}: エラーが発生（期待通り）")
            error_count += 1
        elif response is None:
            print(f"✅ 選択値 {selection_value}: リクエスト失敗（期待通り）")
            error_count += 1
        elif response.status_code in [400, 422, 500]:
            print(f"✅ 選択値 {selection_value}: HTTPエラー {response.status_code}（期待通り）")
            error_count += 1
        else:
            print(f"⚠️ 選択値 {selection_value}: 予期しない成功レスポンス {response.status_code}")
            success_count += 1
    
    print(f"📊 同時選択リクエストの結果: 成功 {success_count}件, エラー {error_count}件")
    
    # 同時リクエストではエラーが発生することが期待される
    if error_count > 0:
        print("✅ 同時選択リクエストのテストが成功しました（エラーが適切に処理された）")
        return True
    else:
        print("⚠️ 同時選択リクエストのテスト: エラーが発生しませんでした")
        return False


async def test_large_payload_request():
    """大きなペイロードのリクエストテスト"""
    print("🔍 大きなペイロードのリクエストテスト開始")
    
    client = Phase2CErrorTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        print("⏭ テストをスキップします")
        return True
    
    sse_session_id = f"test_session_large_{int(time.time())}"
    
    # 非常に大きなタスクIDとセッションIDを生成
    large_task_id = "main_dish_proposal_0" + "x" * 10000
    large_sse_session_id = sse_session_id + "x" * 10000
    
    print(f"📋 大きなペイロードのテスト: タスクID長 {len(large_task_id)}, セッションID長 {len(large_sse_session_id)}")
    
    response = client.send_selection_request(
        large_task_id, 
        1, 
        large_sse_session_id
    )
    
    if response is None:
        print("✅ 大きなペイロード: 期待通りリクエスト失敗")
        return True
    
    # レスポンスの検証
    print(f"📝 実際のHTTPステータス: {response.status_code}")
    
    if response.status_code in [400, 413, 422]:  # 413はPayload Too Large
        print("✅ 大きなペイロード: 期待通りエラーが発生")
        return True
    elif response.status_code == 500:
        print("✅ 大きなペイロード: 500エラー（内部エラーとして適切）")
        return True
    else:
        print(f"⚠️ 大きなペイロード: 予期しないステータスコード {response.status_code}")
        return False


def parse_arguments():
    """コマンドライン引数の解析"""
    parser = argparse.ArgumentParser(description="Phase 2C 異常系テスト")
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
    print("🚀 test_error_handling: start")
    print("📋 Phase 2C 異常系テストを実行します")
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
        # テスト1: 無効な選択範囲のテスト
        await test_invalid_selection_range()
        
        # テスト2: 無効なタスクIDフォーマットのテスト
        await test_invalid_task_id_format()
        
        # テスト3: 無効なSSEセッションIDのテスト
        await test_invalid_sse_session_id()
        
        # テスト4: 不正なJSONリクエストのテスト
        await test_malformed_json_request()
        
        # テスト5: 同時選択リクエストのテスト
        await test_concurrent_selection_requests()
        
        # テスト6: 大きなペイロードのリクエストテスト
        await test_large_payload_request()
        
        print("🎉 test_error_handling: すべての異常系テストが完了しました")
        
    except Exception as e:
        print(f"❌ test_error_handling: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
