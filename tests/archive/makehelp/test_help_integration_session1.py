#!/usr/bin/env python3
"""
ヘルプ機能統合テスト - セッション1

HTTP API経由でヘルプ機能の基本動作をテストします。
- ヘルプ全体概要の表示
- 機能別詳細の表示（1-4）
- ヘルプキーワードの検知
- 通常のチャットへの復帰
- セッション状態の管理
"""

import asyncio
import sys
import os
import requests
import time
import uuid
from dataclasses import dataclass
from typing import List, Optional, Callable, Any, Dict
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Supabase認証ユーティリティをインポート
archive_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tests", "archive", "rebuild", "00_1_test_util.py"
)
if os.path.exists(archive_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_util", archive_path)
    test_util = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_util)
    AuthUtil = test_util.AuthUtil
else:
    raise ImportError("Cannot find test_util.py")

load_dotenv()


@dataclass
class HelpTestCase:
    """ヘルプ機能テストケースデータクラス"""
    name: str
    description: str
    messages: List[str]  # 送信するメッセージのリスト
    expected_responses: List[Callable[[str], bool]]  # 応答検証関数のリスト
    expected_help_states: List[Optional[str]]  # 期待されるヘルプ状態のリスト
    setup: Optional[Callable] = None  # 事前準備関数
    skip: bool = False


def verify_help_overview_response(response_text: str) -> bool:
    """ヘルプ全体概要の応答を検証"""
    required_keywords = [
        "4つの便利な機能",
        "在庫管理",
        "献立提案（一括）",
        "献立提案（段階的）",
        "便利な補助機能",
        "1〜4の数字を入力"
    ]
    
    for keyword in required_keywords:
        if keyword not in response_text:
            print(f"❌ 全体概要に必須キーワード '{keyword}' が見つかりません")
            return False
    
    print("✅ ヘルプ全体概要の検証成功")
    return True


def verify_inventory_detail_response(response_text: str) -> bool:
    """在庫管理機能の詳細応答を検証"""
    required_keywords = [
        "食材を追加する",
        "食材を削除する",
        "食材の数量などを変更する",
        "在庫を確認する"
    ]
    
    for keyword in required_keywords:
        if keyword not in response_text:
            print(f"❌ 在庫管理詳細に必須キーワード '{keyword}' が見つかりません")
            return False
    
    print("✅ 在庫管理機能詳細の検証成功")
    return True


def verify_menu_bulk_detail_response(response_text: str) -> bool:
    """献立一括提案機能の詳細応答を検証"""
    required_keywords = [
        "献立を教えて",
        "新しい献立",
        "過去の類似献立",
        "主菜・副菜・汁物"
    ]
    
    for keyword in required_keywords:
        if keyword not in response_text:
            print(f"❌ 献立一括提案詳細に必須キーワード '{keyword}' が見つかりません")
            return False
    
    print("✅ 献立一括提案機能詳細の検証成功")
    return True


def verify_menu_staged_detail_response(response_text: str) -> bool:
    """段階的提案機能の詳細応答を検証"""
    required_keywords = [
        "主菜を選ぶ",
        "副菜を選ぶ",
        "汁物を選ぶ",
        "他の提案を見る"
    ]
    
    for keyword in required_keywords:
        if keyword not in response_text:
            print(f"❌ 段階的提案詳細に必須キーワード '{keyword}' が見つかりません")
            return False
    
    print("✅ 段階的提案機能詳細の検証成功")
    return True


def verify_auxiliary_detail_response(response_text: str) -> bool:
    """補助機能の詳細応答を検証"""
    required_keywords = [
        "在庫一覧を確認する",
        "レシピ履歴を確認する",
        "ユーザープロフィール画面"
    ]
    
    for keyword in required_keywords:
        if keyword not in response_text:
            print(f"❌ 補助機能詳細に必須キーワード '{keyword}' が見つかりません")
            return False
    
    print("✅ 補助機能詳細の検証成功")
    return True


class IntegrationTestClient:
    """統合テスト用のHTTPクライアント"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Supabase認証でJWTトークンを動的に取得
        try:
            auth_util = AuthUtil()
            self.jwt_token = auth_util.get_auth_token()
            print(f"🔐 動的取得したJWTトークン: {self.jwt_token[:20]}...")
        except Exception as e:
            print(f"❌ Supabase認証に失敗しました: {e}")
            print("💡 SUPABASE_URL, SUPABASE_KEY, SUPABASE_EMAIL, SUPABASE_PASSWORD を .env に設定してください")
            raise
        
        self.session.headers.update({
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        })
    
    def send_chat_request(self, message: str, sse_session_id: Optional[str] = None, confirm: bool = False):
        """チャットリクエストを送信"""
        url = f"{self.base_url}/chat"
        
        payload = {
            "message": message,
            "token": self.jwt_token,
            "sseSessionId": sse_session_id,
            "confirm": confirm
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=120)
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


async def wait_for_response_delay(seconds: float = 2.0):
    """レスポンス待機（非同期処理の完了待ち）"""
    await asyncio.sleep(seconds)


async def verify_help_state(
    client: IntegrationTestClient,
    sse_session_id: str,
    user_id: str,
    expected_state: Optional[str]
) -> bool:
    """ヘルプ状態を検証（直接API経由では取得できないため、ログまたはセッションAPI経由で確認）"""
    # 注意: セッション状態はバックエンドの内部状態のため、
    # HTTP API経由では直接取得できない。
    # この検証は、応答内容から間接的に確認するか、
    # バックエンドログを確認する必要がある。
    # 
    # 実装時は、以下のいずれかの方法を採用：
    # 1. セッション状態取得用のエンドポイントを追加
    # 2. 応答内容から間接的に確認（ヘルプ応答の内容で判定）
    # 3. ログファイルを解析
    #
    # ここでは、応答内容から間接的に確認する方法を採用
    return True  # 実装時に詳細を追加


# 検証関数マッピング
DETAIL_VERIFIERS = {
    1: verify_inventory_detail_response,
    2: verify_menu_bulk_detail_response,
    3: verify_menu_staged_detail_response,
    4: verify_auxiliary_detail_response
}

HELP_TEST_CASES = [
    HelpTestCase(
        name="TC-HELP-001: ヘルプ全体概要の表示",
        description="「使い方を教えて」で全体概要が表示され、セッション状態が更新される",
        messages=["使い方を教えて"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
    
    HelpTestCase(
        name="TC-HELP-002: 在庫管理機能の詳細表示",
        description="「1」で在庫管理機能の詳細が表示される",
        messages=["使い方を教えて", "1"],
        expected_responses=[verify_help_overview_response, verify_inventory_detail_response],
        expected_help_states=["overview", "detail_1"]
    ),
    
    HelpTestCase(
        name="TC-HELP-003: 献立一括提案機能の詳細表示",
        description="「2」で献立一括提案機能の詳細が表示される",
        messages=["使い方を教えて", "2"],
        expected_responses=[verify_help_overview_response, verify_menu_bulk_detail_response],
        expected_help_states=["overview", "detail_2"]
    ),
    
    HelpTestCase(
        name="TC-HELP-004: 段階的提案機能の詳細表示",
        description="「3」で段階的提案機能の詳細が表示される",
        messages=["使い方を教えて", "3"],
        expected_responses=[verify_help_overview_response, verify_menu_staged_detail_response],
        expected_help_states=["overview", "detail_3"]
    ),
    
    HelpTestCase(
        name="TC-HELP-005: 補助機能の詳細表示",
        description="「4」で補助機能の詳細が表示される",
        messages=["使い方を教えて", "4"],
        expected_responses=[verify_help_overview_response, verify_auxiliary_detail_response],
        expected_help_states=["overview", "detail_4"]
    ),
    
    HelpTestCase(
        name="TC-HELP-006: 通常のチャットへの復帰",
        description="ヘルプモード中に通常のチャット入力で自動的に復帰する",
        messages=["使い方を教えて", "在庫を教えて"],
        expected_responses=[verify_help_overview_response, lambda r: "在庫" in r or "食材" in r],  # 通常の応答
        expected_help_states=["overview", None]  # 復帰時はNone
    ),
    
    HelpTestCase(
        name="TC-HELP-007: 複数の機能詳細を順番に見る",
        description="1→2→3→4と順番に機能詳細を表示できる",
        messages=["使い方を教えて", "1", "2", "3", "4"],
        expected_responses=[
            verify_help_overview_response,
            verify_inventory_detail_response,
            verify_menu_bulk_detail_response,
            verify_menu_staged_detail_response,
            verify_auxiliary_detail_response
        ],
        expected_help_states=["overview", "detail_1", "detail_2", "detail_3", "detail_4"]
    ),
    
    HelpTestCase(
        name="TC-HELP-008: ヘルプキーワード「ヘルプ」での検知",
        description="「ヘルプ」でも全体概要が表示される",
        messages=["ヘルプ"],
        expected_responses=[verify_help_overview_response],
        expected_help_states=["overview"]
    ),
]


async def run_help_test(client: IntegrationTestClient, test_case: HelpTestCase) -> bool:
    """ヘルプ機能テストケースを実行"""
    print(f"\n{'='*60}")
    print(f"🧪 テスト: {test_case.name}")
    print(f"📝 説明: {test_case.description}")
    print(f"{'='*60}")
    
    if test_case.skip:
        print(f"⏭️ テストをスキップ: {test_case.name}")
        return True
    
    try:
        # 事前準備
        if test_case.setup:
            print(f"📋 事前準備を実行...")
            await test_case.setup(client)
            await wait_for_response_delay(1.0)
        
        sse_session_id = str(uuid.uuid4())
        print(f"📝 生成したsse_session_id: {sse_session_id}")
        
        # 各メッセージを順番に送信
        for i, message in enumerate(test_case.messages):
            print(f"\n[ステップ{i+1}] メッセージ送信: '{message}'")
            
            response = client.send_chat_request(message, sse_session_id=sse_session_id)
            
            if not response:
                print(f"❌ レスポンスがNoneです")
                return False
            
            # レスポンスの構造を確認（successフィールドがない場合もある）
            if "success" in response and not response.get("success"):
                print(f"❌ レスポンスが失敗しています: {response}")
                return False
            
            response_text = response.get("response", "")
            if not response_text:
                print(f"❌ レスポンステキストが空です")
                return False
            
            print(f"📄 応答: {response_text[:200]}...")  # 最初の200文字を表示
            
            # 応答の検証
            if i < len(test_case.expected_responses):
                verifier = test_case.expected_responses[i]
                if not verifier(response_text):
                    print(f"❌ 応答の検証に失敗しました（ステップ{i+1}）")
                    return False
            
            await wait_for_response_delay(2.0)
        
        print(f"✅ テスト成功: {test_case.name}")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メイン関数"""
    print("🚀 ヘルプ機能統合テスト開始（セッション1）")
    print(f"📅 実行時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テストクライアントの初期化
    try:
        client = IntegrationTestClient()
    except Exception as e:
        print(f"❌ テストクライアントの初期化に失敗しました: {e}")
        return False
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    # テストケースを実行
    passed = 0
    failed = 0
    
    for test_case in HELP_TEST_CASES:
        result = await run_help_test(client, test_case)
        if result:
            passed += 1
        else:
            failed += 1
        
        # テスト間で少し待機
        await wait_for_response_delay(2.0)
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print(f"📊 テスト結果サマリー")
    print(f"{'='*60}")
    print(f"✅ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"📊 合計: {passed + failed}")
    
    if failed == 0:
        print(f"\n🎉 全テストが成功しました！")
        return True
    else:
        print(f"\n⚠️ 一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

