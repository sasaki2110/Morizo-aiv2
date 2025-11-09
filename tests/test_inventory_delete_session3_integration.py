#!/usr/bin/env python3
"""
セッション3: Phase 2A（食材集約API）の結合テスト

実際に起動しているサーバーでテストするタイプの結合テスト
test_inventory_delete_session2_integration.pyを参考に実装
"""

import asyncio
import sys
import os
import requests
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Supabase認証ユーティリティをインポート
archive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "archive", "00_1_test_util.py")
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
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
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
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def send_selection_request(self, task_id: str, selection: int, sse_session_id: str):
        """ユーザー選択リクエストを送信"""
        url = f"{self.base_url}/chat/selection"
        
        payload = {
            "task_id": task_id,
            "selection": selection,
            "sse_session_id": sse_session_id
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def adopt_recipe(self, recipes: List[Dict[str, Any]]):
        """レシピ採用通知を送信（/api/recipe/adopt）"""
        url = f"{self.base_url}/api/recipe/adopt"
        
        payload = {
            "recipes": recipes,
            "token": self.jwt_token
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def get_ingredient_delete_candidates(self, date: str):
        """食材削除候補を取得（/api/recipe/ingredients/delete-candidates/{date}）"""
        url = f"{self.base_url}/api/recipe/ingredients/delete-candidates/{date}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def add_inventory(self, item_name: str, quantity: float, unit: str = "個"):
        """在庫を追加（/api/inventory/add）"""
        url = f"{self.base_url}/api/inventory/add"
        
        payload = {
            "item_name": item_name,
            "quantity": quantity,
            "unit": unit,
            "token": self.jwt_token
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None


async def wait_for_response_delay(seconds: float = 2.0):
    """レスポンス待機"""
    await asyncio.sleep(seconds)


async def test_stage_proposal_to_delete_candidates():
    """結合テスト1: 段階提案→履歴保存→食材集約APIの呼び出し"""
    print("\n" + "="*80)
    print("[結合テスト1] 段階提案→履歴保存→食材集約APIの呼び出し")
    print("="*80)
    
    client = IntegrationTestClient()
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    # 事前準備: 在庫を追加
    print("\n[事前準備] 在庫を追加...")
    client.add_inventory("レンコン", 2, "個")
    await wait_for_response_delay(0.5)
    client.add_inventory("ニンジン", 3, "個")
    await wait_for_response_delay(0.5)
    client.add_inventory("鶏もも肉", 500, "g")
    await wait_for_response_delay(0.5)
    print("✅ 在庫追加完了")
    
    # 新しいセッションIDを作成
    sse_session_id = f"test_integration_stage_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    print(f"📋 セッションID: {sse_session_id}")
    
    try:
        # 1. 段階提案（主菜）をリクエスト
        print("\n📋 [ステップ1] 段階提案（主菜）をリクエスト...")
        stage_response = client.send_chat_request(
            message="レンコンを使った主菜を教えて",
            sse_session_id=sse_session_id
        )
        
        if not stage_response or not stage_response.get("success"):
            print(f"❌ 段階提案が失敗しました: {stage_response}")
            return False
        
        print(f"✅ 段階提案成功")
        print(f"📋 レスポンス: {stage_response.get('response', '')[:200]}...")
        
        # 提案に時間をかける
        await wait_for_response_delay(5.0)
        
        # 2. 提案されたレシピを採用（ingredientsあり）
        print("\n📋 [ステップ2] 提案されたレシピを採用（ingredientsあり）...")
        
        recipes = [
            {
                "title": "レンコンのきんぴら",
                "category": "main_dish",
                "menu_source": "llm_menu",
                "ingredients": ["レンコン", "ニンジン"]
            }
        ]
        
        adopt_response = client.adopt_recipe(recipes)
        
        if not adopt_response:
            print("❌ adopt_recipe()が失敗しました")
            return False
        
        success = adopt_response.get("success", False)
        total_saved = adopt_response.get("total_saved", 0)
        
        if not success or total_saved == 0:
            print(f"❌ レシピ採用が失敗しました: success={success}, total_saved={total_saved}")
            return False
        
        print(f"✅ レシピ採用成功: {total_saved}件保存")
        await wait_for_response_delay(1.0)
        
        # 3. 食材集約APIを呼び出し
        print("\n📋 [ステップ3] 食材集約APIを呼び出し...")
        today = datetime.now().strftime("%Y-%m-%d")
        candidates_response = client.get_ingredient_delete_candidates(today)
        
        if not candidates_response:
            print("❌ 食材集約APIが失敗しました")
            return False
        
        if not candidates_response.get("success"):
            print(f"❌ 食材集約APIが失敗を返しました: {candidates_response}")
            return False
        
        candidates = candidates_response.get("candidates", [])
        print(f"✅ 食材集約API成功: {len(candidates)}件の候補を取得")
        
        # 候補の内容を確認
        candidate_names = [c.get("item_name") for c in candidates]
        print(f"   候補食材: {candidate_names}")
        
        # 期待される食材が含まれているか確認
        expected_ingredients = ["レンコン", "ニンジン"]
        found_count = 0
        for expected in expected_ingredients:
            for candidate in candidates:
                item_name = candidate.get("item_name", "")
                if expected in item_name or item_name in expected:
                    found_count += 1
                    print(f"   ✅ マッチ: {expected} → {item_name}")
                    break
        
        if found_count >= 1:  # 最低1つは見つかることを期待
            print(f"\n✅ 結合テスト成功: 段階提案→履歴保存→食材集約APIのフローが正常に動作しました")
            return True
        else:
            print(f"❌ 期待される食材が見つかりませんでした（見つかった: {found_count}/{len(expected_ingredients)}）")
            return False
            
    except Exception as e:
        print(f"❌ 結合テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_menu_proposal_to_delete_candidates():
    """結合テスト2: 献立提案→履歴保存→食材集約APIの呼び出し"""
    print("\n" + "="*80)
    print("[結合テスト2] 献立提案→履歴保存→食材集約APIの呼び出し")
    print("="*80)
    
    client = IntegrationTestClient()
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    # 事前準備: 在庫を追加
    print("\n[事前準備] 在庫を追加...")
    client.add_inventory("じゃがいも", 5, "個")
    await wait_for_response_delay(0.5)
    client.add_inventory("玉ねぎ", 2, "個")
    await wait_for_response_delay(0.5)
    client.add_inventory("にんじん", 3, "個")
    await wait_for_response_delay(0.5)
    print("✅ 在庫追加完了")
    
    # 新しいセッションIDを作成
    sse_session_id = f"test_integration_menu_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    print(f"📋 セッションID: {sse_session_id}")
    
    try:
        # 1. 献立提案をリクエスト
        print("\n📋 [ステップ1] 献立提案をリクエスト...")
        menu_response = client.send_chat_request(
            message="じゃがいもを使った献立を提案してください",
            sse_session_id=sse_session_id
        )
        
        if not menu_response or not menu_response.get("success"):
            print(f"❌ 献立提案が失敗しました: {menu_response}")
            return False
        
        print(f"✅ 献立提案成功")
        print(f"📋 レスポンス: {menu_response.get('response', '')[:200]}...")
        
        # 提案に時間をかける
        await wait_for_response_delay(5.0)
        
        # 2. 提案されたレシピを採用（ingredientsあり）
        print("\n📋 [ステップ2] 提案されたレシピを採用（ingredientsあり）...")
        
        recipes = [
            {
                "title": "じゃがいもの煮物",
                "category": "main_dish",
                "menu_source": "llm_menu",
                "ingredients": ["じゃがいも", "にんじん"]
            },
            {
                "title": "玉ねぎサラダ",
                "category": "side_dish",
                "menu_source": "llm_menu",
                "ingredients": ["玉ねぎ"]
            },
            {
                "title": "味噌汁",
                "category": "soup",
                "menu_source": "llm_menu",
                "ingredients": ["味噌", "豆腐"]
            }
        ]
        
        adopt_response = client.adopt_recipe(recipes)
        
        if not adopt_response:
            print("❌ adopt_recipe()が失敗しました")
            return False
        
        success = adopt_response.get("success", False)
        total_saved = adopt_response.get("total_saved", 0)
        
        if not success or total_saved == 0:
            print(f"❌ レシピ採用が失敗しました: success={success}, total_saved={total_saved}")
            return False
        
        print(f"✅ レシピ採用成功: {total_saved}件保存")
        await wait_for_response_delay(1.0)
        
        # 3. 食材集約APIを呼び出し
        print("\n📋 [ステップ3] 食材集約APIを呼び出し...")
        today = datetime.now().strftime("%Y-%m-%d")
        candidates_response = client.get_ingredient_delete_candidates(today)
        
        if not candidates_response:
            print("❌ 食材集約APIが失敗しました")
            return False
        
        if not candidates_response.get("success"):
            print(f"❌ 食材集約APIが失敗を返しました: {candidates_response}")
            return False
        
        candidates = candidates_response.get("candidates", [])
        print(f"✅ 食材集約API成功: {len(candidates)}件の候補を取得")
        
        # 候補の内容を確認
        candidate_names = [c.get("item_name") for c in candidates]
        print(f"   候補食材: {candidate_names}")
        
        # 期待される食材が含まれているか確認（在庫に存在するもののみ）
        expected_ingredients = ["じゃがいも", "にんじん", "玉ねぎ"]
        found_count = 0
        for expected in expected_ingredients:
            for candidate in candidates:
                item_name = candidate.get("item_name", "")
                if expected in item_name or item_name in expected:
                    found_count += 1
                    print(f"   ✅ マッチ: {expected} → {item_name}")
                    break
        
        if found_count >= 2:  # 最低2つは見つかることを期待（在庫に存在するもの）
            print(f"\n✅ 結合テスト成功: 献立提案→履歴保存→食材集約APIのフローが正常に動作しました")
            return True
        else:
            print(f"❌ 期待される食材が見つかりませんでした（見つかった: {found_count}/{len(expected_ingredients)}）")
            return False
            
    except Exception as e:
        print(f"❌ 結合テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メイン関数"""
    print("🚀 セッション3: Phase 2A（食材集約API）の結合テスト開始")
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
    test_cases = [
        ("段階提案→履歴保存→食材集約API", test_stage_proposal_to_delete_candidates),
        ("献立提案→履歴保存→食材集約API", test_menu_proposal_to_delete_candidates),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in test_cases:
        try:
            print(f"\n{'='*80}")
            print(f"🧪 結合テスト実行: {test_name}")
            print(f"{'='*80}")
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ 結合テスト成功: {test_name}")
            else:
                failed += 1
                print(f"❌ 結合テスト失敗: {test_name}")
        except Exception as e:
            print(f"❌ 結合テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        
        # テスト間で少し待機
        await wait_for_response_delay(3.0)
    
    # 結果サマリー
    print(f"\n{'='*80}")
    print(f"📊 結合テスト結果サマリー")
    print(f"{'='*80}")
    print(f"✅ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"📈 成功率: {passed / (passed + failed) * 100:.1f}%")
    
    return failed == 0


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)

