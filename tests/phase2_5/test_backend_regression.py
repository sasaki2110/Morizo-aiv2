#!/usr/bin/env python3
"""
Phase 2.5 - バックエンド回帰テスト（HTTP API経由）

破壊的活動（デグレード）の早期発見のため、各パターンのHTTPリクエストを自動テストします。
Supabase認証で動的にJWTトークンを取得します。
"""

import asyncio
import sys
import os
import requests
import time
from dataclasses import dataclass
from typing import List, Optional, Callable, Any
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Supabase認証ユーティリティをインポート
archive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archive", "00_1_test_util.py")
if os.path.exists(archive_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_util", archive_path)
    test_util = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_util)
    AuthUtil = test_util.AuthUtil
else:
    # フォールバック: 直接実装
    from supabase import create_client
    
    class AuthUtil:
        def __init__(self):
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            self.supabase_email = os.getenv('SUPABASE_EMAIL')
            self.supabase_password = os.getenv('SUPABASE_PASSWORD')
            
            if not all([self.supabase_url, self.supabase_key]):
                raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        
        def get_auth_token(self) -> str:
            """テスト用の認証トークンを取得"""
            if not all([self.supabase_email, self.supabase_password]):
                raise ValueError("SUPABASE_EMAIL and SUPABASE_PASSWORD are required for testing")
            
            client = create_client(self.supabase_url, self.supabase_key)
            
            try:
                response = client.auth.sign_in_with_password({
                    "email": self.supabase_email,
                    "password": self.supabase_password
                })
                
                if response.session and response.session.access_token:
                    return response.session.access_token
                else:
                    raise ValueError("Failed to get access token")
                    
            except Exception as e:
                raise ValueError(f"Authentication failed: {e}")

# .envファイルを読み込み
load_dotenv()


@dataclass
class TestCase:
    """テストケースデータクラス"""
    name: str
    message: str
    expected_pattern: str
    expected_tasks: List[str]
    expected_ambiguity: Optional[str] = None
    setup: Optional[Callable] = None
    verify: Optional[Callable] = None
    requires_two_stage: bool = False  # 曖昧性解消が必要なテスト
    second_stage_message: Optional[str] = None  # 2段階目のメッセージ


class IntegrationTestClient:
    """統合テスト用のHTTPクライアント（Supabase認証版）"""
    
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
            response = self.session.post(url, json=payload, timeout=60)
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
    
    def add_inventory(self, item_name: str, quantity: float, unit: str = "個"):
        """在庫を追加（テスト用ヘルパー）"""
        message = f"{item_name}を{quantity}{unit}追加して"
        return self.send_chat_request(message)
    
    def delete_all_inventory(self, item_name: str):
        """在庫を全削除（テスト用ヘルパー）"""
        message = f"{item_name}を全部削除して"
        return self.send_chat_request(message)


def extract_task_methods(response: dict) -> List[str]:
    """レスポンスからタスクメソッド名を抽出
    
    注意: /chat APIは非同期でタスクを実行し、SSE経由で進捗を送信します。
    レスポンスにはタスク情報は含まれないため、この関数は空リストを返します。
    
    タスク情報を取得するには、SSEストリームを監視する必要があります。
    """
    # APIレスポンスにはタスク情報が含まれない（SSE経由で非同期送信）
    # 代わりに、レスポンスの内容や成功フラグで検証
    return []


async def run_test_case(client: IntegrationTestClient, test_case: TestCase) -> bool:
    """テストケースを実行"""
    print(f"\n{'='*60}")
    print(f"🧪 テスト: {test_case.name}")
    print(f"{'='*60}")
    
    try:
        # 1. 事前準備（setup）
        if test_case.setup:
            print(f"📋 事前準備を実行...")
            await test_case.setup(client)
        
        # 2. リクエスト送信
        print(f"📤 リクエスト送信: {test_case.message}")
        response = client.send_chat_request(test_case.message)
        
        if response is None:
            print(f"❌ リクエストが失敗しました")
            return False
        
        # 3. レスポンス検証
        assert "response" in response, f"レスポンスに'response'フィールドがありません"
        assert "success" in response, f"レスポンスに'success'フィールドがありません"
        
        success = response["success"]
        response_text = response.get("response", "")
        
        assert success is True, f"処理が成功していません: success={success}"
        
        # レスポンス内容の基本検証
        assert len(response_text) > 0, f"レスポンスが空です"
        
        print(f"📝 レスポンス内容: {response_text[:200]}...")
        
        # 4. レスポンス内容の検証（タスク情報はSSE経由のため検証しない）
        if test_case.expected_tasks:
            print(f"📊 タスクチェーン検証（スキップ）:")
            print(f"   期待されるタスク: {test_case.expected_tasks}")
            print(f"   ⚠️ タスク情報はSSE経由で非同期送信されるため、APIレスポンスには含まれません")
            print(f"   ✅ レスポンスの内容と成功フラグで動作確認します")
        
        # 5. 曖昧性検証
        if test_case.expected_ambiguity:
            # APIレスポンスにはrequires_confirmationフィールドが含まれる
            requires_confirmation = response.get("requires_confirmation", False)
            confirmation_session_id = response.get("confirmation_session_id")
            
            print(f"🔍 曖昧性検証:")
            print(f"   requires_confirmation: {requires_confirmation}")
            print(f"   confirmation_session_id: {confirmation_session_id}")
            
            # 期待される曖昧性の場合、レスポンスに複数の選択肢が含まれる
            # （例: 「12件見つかりました」のように複数アイテムを表示）
            if test_case.expected_ambiguity == "multiple_items":
                # 複数アイテム検出の場合、レスポンスに「X件見つかりました」が含まれる
                assert "件見つかりました" in response_text, f"複数アイテムのメッセージが見つかりません: {response_text}"
                print(f"✅ 曖昧性検出（複数アイテム）")
            else:
                # その他の曖昧性の場合
                assert requires_confirmation, f"requires_confirmation が True になっていません"
                print(f"✅ 曖昧性検出: {test_case.expected_ambiguity}")
        
        # 6. 追加検証
        if test_case.verify:
            print(f"🔍 追加検証を実行...")
            await test_case.verify(client, response)
        
        # 7. 2段階テスト（曖昧性解消）
        if test_case.requires_two_stage and response.get("requires_confirmation") and test_case.second_stage_message:
            print(f"\n{'─'*60}")
            print(f"🔄 2段階テスト: 曖昧性解消")
            print(f"{'─'*60}")
            
            confirmation_session_id = response.get("confirmation_session_id")
            if not confirmation_session_id:
                print(f"❌ confirmation_session_id がありません")
                return False
            
            print(f"📤 確認質問への回答送信: {test_case.second_stage_message}")
            print(f"📝 confirmation_session_id: {confirmation_session_id}")
            
            # 2段階目のリクエスト送信
            second_response = client.send_chat_request(
                test_case.second_stage_message,
                sse_session_id=confirmation_session_id,
                confirm=True
            )
            
            if second_response is None:
                print(f"❌ 2段階目のリクエストが失敗しました")
                return False
            
            # 2段階目のレスポンス検証
            assert "response" in second_response, f"レスポンスに'response'フィールドがありません"
            assert "success" in second_response, f"レスポンスに'success'フィールドがありません"
            
            second_success = second_response["success"]
            second_response_text = second_response.get("response", "")
            
            assert second_success is True, f"2段階目の処理が成功していません: success={second_success}"
            assert len(second_response_text) > 0, f"2段階目のレスポンスが空です"
            
            print(f"📝 2段階目のレスポンス: {second_response_text[:200]}...")
            print(f"✅ 2段階目のテスト成功")
        
        print(f"✅ テスト成功: {test_case.name}")
        return True
        
    except AssertionError as e:
        print(f"❌ アサーションエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


# テストケース定義
TEST_CASES = [
    # パターン1-1: 在庫追加（単純ケース）
    TestCase(
        name="在庫追加",
        message="牛乳を2本追加して",
        expected_pattern="inventory",
        expected_tasks=["add_inventory"],
        expected_ambiguity=None
    ),
    
    # パターン1-2: 在庫削除（曖昧性あり） - 複数の牛乳を登録してから実行
    TestCase(
        name="在庫削除（曖昧性あり）",
        message="牛乳を削除して",
        expected_pattern="inventory",
        expected_tasks=[],  # 曖昧性検出のためタスクは生成されない
        expected_ambiguity="multiple_items",
        setup=lambda client: setup_multiple_items(client)
    ),
    
    # パターン1-2b: 在庫削除（曖昧性解消）
    TestCase(
        name="在庫削除（曖昧性解消）",
        message="牛乳を削除して",
        expected_pattern="inventory",
        expected_tasks=[],  # 曖昧性検出のためタスクは生成されない
        expected_ambiguity="multiple_items",
        requires_two_stage=True,
        second_stage_message="最新の",
        setup=lambda client: setup_multiple_items(client)
    ),
    
    # パターン1-3: 在庫更新（全件）
    TestCase(
        name="在庫更新（全件）",
        message="牛乳を全部1本に変えて",
        expected_pattern="inventory",
        expected_tasks=["update_inventory"],
        expected_ambiguity=None,
        setup=lambda client: setup_multiple_items(client)
    ),
    
    # パターン2-1: 献立生成
    TestCase(
        name="献立生成",
        message="献立を教えて",
        expected_pattern="menu",
        expected_tasks=["get_inventory", "generate_menu_plan", "search_menu_from_rag", "search_recipes_from_web"],
        expected_ambiguity=None,
        setup=lambda client: setup_menu_inventory(client)
    ),
    
    # パターン3-1: 主菜提案（食材指定）
    TestCase(
        name="主菜提案（食材指定）",
        message="レンコンの主菜を5件提案して",
        expected_pattern="main",
        expected_tasks=["get_inventory", "history_get_recent_titles", "generate_proposals", "search_recipes_from_web"],
        expected_ambiguity=None,
        setup=lambda client: setup_renkon_inventory(client)
    ),
]


async def setup_multiple_items(client: IntegrationTestClient):
    """複数のアイテムを登録（曖昧性テスト用）"""
    # 牛乳を2つ登録
    client.add_inventory("牛乳", 2, "本")
    await asyncio.sleep(0.5)  # 登録の完了を待つ
    client.add_inventory("牛乳", 3, "本")
    await asyncio.sleep(0.5)


async def setup_renkon_inventory(client: IntegrationTestClient):
    """レンコンを在庫に登録"""
    client.add_inventory("レンコン", 1, "個")
    await asyncio.sleep(0.5)


async def setup_menu_inventory(client: IntegrationTestClient):
    """献立生成用の在庫を登録（野菜・肉・調味料）"""
    client.add_inventory("キャベツ", 1, "個")
    await asyncio.sleep(0.5)
    client.add_inventory("人参", 2, "本")
    await asyncio.sleep(0.5)
    client.add_inventory("もやし", 1, "袋")
    await asyncio.sleep(0.5)
    client.add_inventory("豚肉", 300, "g")
    await asyncio.sleep(0.5)


async def main():
    """メイン関数"""
    print("🚀 Phase 2.5 バックエンド回帰テスト開始")
    print(f"📅 実行時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テストクライアントの初期化
    try:
        client = IntegrationTestClient()
    except Exception as e:
        print(f"❌ テストクライアントの初期化に失敗しました: {e}")
        return False
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python main.py でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    # テストケースを実行
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        try:
            result = await run_test_case(client, test_case)
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            failed += 1
    
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

