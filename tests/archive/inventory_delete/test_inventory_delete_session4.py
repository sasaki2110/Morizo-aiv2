#!/usr/bin/env python3
"""
セッション4: Phase 2B（在庫更新API）の単体テスト

実際に起動しているサーバーでテストするタイプの統合テスト
test_inventory_delete_session3.pyを参考に実装
"""

import asyncio
import sys
import os
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
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
    
    def add_inventory(self, item_name: str, quantity: float, unit: str = "個"):
        """在庫を追加（/api/inventory/add）"""
        url = f"{self.base_url}/api/inventory/add"
        
        payload = {
            "item_name": item_name,
            "quantity": quantity,
            "unit": unit
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
    
    def get_inventory_list(self):
        """在庫一覧を取得（/api/inventory/list）"""
        url = f"{self.base_url}/api/inventory/list"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None
    
    def delete_ingredients(self, date: str, ingredients: List[Dict[str, Any]]):
        """食材を削除（/api/recipe/ingredients/delete）"""
        url = f"{self.base_url}/api/recipe/ingredients/delete"
        
        payload = {
            "date": date,
            "ingredients": ingredients
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


async def wait_for_response_delay(seconds: float = 1.0):
    """レスポンス待機"""
    await asyncio.sleep(seconds)


async def test_delete_single_ingredient_by_id():
    """テスト1: 単一食材の削除（在庫ID指定）"""
    print("\n" + "="*80)
    print("[テスト1] 単一食材の削除（在庫ID指定）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # 事前準備: 在庫を追加
    print("\n[事前準備] 在庫を追加...")
    add_response = client.add_inventory("テスト食材1", 5.0, "個")
    if not add_response or not add_response.get("success"):
        print("❌ 在庫追加に失敗しました")
        return False
    
    inventory_id = add_response.get("data", {}).get("id")
    if not inventory_id:
        print("❌ 在庫IDが取得できませんでした")
        return False
    
    print(f"✅ 在庫追加完了: ID={inventory_id}, 数量=5.0")
    await wait_for_response_delay(0.5)
    
    # テスト: 在庫ID指定で削除（数量を0に設定）
    print(f"\n[テスト実行] 在庫ID指定で削除...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {
                "item_name": "テスト食材1",
                "quantity": 0,
                "inventory_id": inventory_id
            }
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    deleted_count = delete_response.get("deleted_count", 0)
    failed_items = delete_response.get("failed_items", [])
    
    if deleted_count == 1 and len(failed_items) == 0:
        print("✅ 正常系: 在庫ID指定で削除が成功しました")
        print(f"   削除件数: {deleted_count}")
        return True
    else:
        print(f"❌ 削除が失敗しました: deleted_count={deleted_count}, failed_items={failed_items}")
        return False


async def test_delete_single_ingredient_by_name():
    """テスト2: 単一食材の削除（食材名指定）"""
    print("\n" + "="*80)
    print("[テスト2] 単一食材の削除（食材名指定）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # 事前準備: 在庫を追加
    print("\n[事前準備] 在庫を追加...")
    add_response = client.add_inventory("テスト食材2", 3.0, "個")
    if not add_response or not add_response.get("success"):
        print("❌ 在庫追加に失敗しました")
        return False
    
    print(f"✅ 在庫追加完了: 数量=3.0")
    await wait_for_response_delay(0.5)
    
    # テスト: 食材名指定で削除
    print(f"\n[テスト実行] 食材名指定で削除...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {
                "item_name": "テスト食材2",
                "quantity": 0
            }
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    deleted_count = delete_response.get("deleted_count", 0)
    failed_items = delete_response.get("failed_items", [])
    
    if deleted_count >= 1 and len(failed_items) == 0:
        print("✅ 正常系: 食材名指定で削除が成功しました")
        print(f"   削除件数: {deleted_count}")
        return True
    else:
        print(f"❌ 削除が失敗しました: deleted_count={deleted_count}, failed_items={failed_items}")
        return False


async def test_delete_multiple_ingredients_by_name():
    """テスト3: 複数食材の削除（食材名指定、複数在庫がある場合）"""
    print("\n" + "="*80)
    print("[テスト3] 複数食材の削除（食材名指定、複数在庫がある場合）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # 事前準備: 同じ食材名で複数の在庫を追加
    print("\n[事前準備] 同じ食材名で複数の在庫を追加...")
    add_response1 = client.add_inventory("テスト食材3", 2.0, "個")
    await wait_for_response_delay(0.5)
    add_response2 = client.add_inventory("テスト食材3", 3.0, "個")
    await wait_for_response_delay(0.5)
    
    if not add_response1 or not add_response1.get("success") or not add_response2 or not add_response2.get("success"):
        print("❌ 在庫追加に失敗しました")
        return False
    
    print(f"✅ 在庫追加完了: 2件")
    
    # テスト: 食材名指定で削除（複数在庫がすべて削除される）
    print(f"\n[テスト実行] 食材名指定で削除（複数在庫）...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {
                "item_name": "テスト食材3",
                "quantity": 0
            }
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    deleted_count = delete_response.get("deleted_count", 0)
    failed_items = delete_response.get("failed_items", [])
    
    if deleted_count >= 2 and len(failed_items) == 0:
        print("✅ 正常系: 複数在庫がすべて削除されました")
        print(f"   削除件数: {deleted_count}")
        return True
    else:
        print(f"❌ 削除が失敗しました: deleted_count={deleted_count}, failed_items={failed_items}")
        return False


async def test_delete_multiple_ingredients_batch():
    """テスト4: 複数食材の一括削除"""
    print("\n" + "="*80)
    print("[テスト4] 複数食材の一括削除")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # 事前準備: 複数の在庫を追加
    print("\n[事前準備] 複数の在庫を追加...")
    add_response1 = client.add_inventory("テスト食材4", 2.0, "個")
    await wait_for_response_delay(0.5)
    add_response2 = client.add_inventory("テスト食材5", 3.0, "個")
    await wait_for_response_delay(0.5)
    add_response3 = client.add_inventory("テスト食材6", 4.0, "個")
    await wait_for_response_delay(0.5)
    
    if not all([add_response1 and add_response1.get("success"),
                add_response2 and add_response2.get("success"),
                add_response3 and add_response3.get("success")]):
        print("❌ 在庫追加に失敗しました")
        return False
    
    print(f"✅ 在庫追加完了: 3件")
    
    # テスト: 複数食材を一度に削除
    print(f"\n[テスト実行] 複数食材を一度に削除...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {"item_name": "テスト食材4", "quantity": 0},
            {"item_name": "テスト食材5", "quantity": 0},
            {"item_name": "テスト食材6", "quantity": 0}
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    deleted_count = delete_response.get("deleted_count", 0)
    failed_items = delete_response.get("failed_items", [])
    
    if deleted_count >= 3 and len(failed_items) == 0:
        print("✅ 正常系: 複数食材の一括削除が成功しました")
        print(f"   削除件数: {deleted_count}")
        return True
    else:
        print(f"❌ 削除が失敗しました: deleted_count={deleted_count}, failed_items={failed_items}")
        return False


async def test_delete_partial_failure():
    """テスト5: 一部の食材削除に失敗した場合の処理"""
    print("\n" + "="*80)
    print("[テスト5] 一部の食材削除に失敗した場合の処理")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # 事前準備: 在庫を追加（1つだけ）
    print("\n[事前準備] 在庫を追加（1つだけ）...")
    add_response = client.add_inventory("テスト食材7", 2.0, "個")
    if not add_response or not add_response.get("success"):
        print("❌ 在庫追加に失敗しました")
        return False
    
    print(f"✅ 在庫追加完了: 1件")
    await wait_for_response_delay(0.5)
    
    # テスト: 存在する食材と存在しない食材を同時に削除
    print(f"\n[テスト実行] 存在する食材と存在しない食材を同時に削除...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {"item_name": "テスト食材7", "quantity": 0},  # 存在する
            {"item_name": "存在しない食材999", "quantity": 0}  # 存在しない
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    deleted_count = delete_response.get("deleted_count", 0)
    failed_items = delete_response.get("failed_items", [])
    
    # 成功した分は反映され、失敗した分はfailed_itemsに含まれることを確認
    if deleted_count >= 1 and len(failed_items) >= 1:
        print("✅ 正常系: 一部成功、一部失敗が正しく処理されました")
        print(f"   削除件数: {deleted_count}")
        print(f"   失敗アイテム: {failed_items}")
        return True
    else:
        print(f"❌ 期待される動作と異なります: deleted_count={deleted_count}, failed_items={failed_items}")
        return False


async def test_update_quantity_non_zero():
    """テスト6: 数量更新（数量を0以外に更新する場合）"""
    print("\n" + "="*80)
    print("[テスト6] 数量更新（数量を0以外に更新する場合）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # 事前準備: 在庫を追加
    print("\n[事前準備] 在庫を追加...")
    add_response = client.add_inventory("テスト食材8", 10.0, "個")
    if not add_response or not add_response.get("success"):
        print("❌ 在庫追加に失敗しました")
        return False
    
    inventory_id = add_response.get("data", {}).get("id")
    if not inventory_id:
        print("❌ 在庫IDが取得できませんでした")
        return False
    
    print(f"✅ 在庫追加完了: ID={inventory_id}, 数量=10.0")
    await wait_for_response_delay(0.5)
    
    # テスト: 数量を5.0に更新
    print(f"\n[テスト実行] 数量を5.0に更新...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {
                "item_name": "テスト食材8",
                "quantity": 5.0,
                "inventory_id": inventory_id
            }
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    updated_count = delete_response.get("updated_count", 0)
    deleted_count = delete_response.get("deleted_count", 0)
    failed_items = delete_response.get("failed_items", [])
    
    if updated_count == 1 and deleted_count == 0 and len(failed_items) == 0:
        print("✅ 正常系: 数量更新が成功しました")
        print(f"   更新件数: {updated_count}")
        return True
    else:
        print(f"❌ 更新が失敗しました: updated_count={updated_count}, deleted_count={deleted_count}, failed_items={failed_items}")
        return False


async def test_delete_nonexistent_ingredient():
    """テスト7: エラーハンドリング（在庫に存在しない食材の処理）"""
    print("\n" + "="*80)
    print("[テスト7] エラーハンドリング（在庫に存在しない食材の処理）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # テスト: 存在しない食材を削除
    print(f"\n[テスト実行] 存在しない食材を削除...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {
                "item_name": "存在しない食材12345",
                "quantity": 0
            }
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    failed_items = delete_response.get("failed_items", [])
    
    # 存在しない食材はfailed_itemsに含まれることを確認
    if len(failed_items) >= 1:
        print("✅ 正常系: 存在しない食材が適切に処理されました")
        print(f"   失敗アイテム: {failed_items}")
        return True
    else:
        print(f"❌ 期待される動作と異なります: failed_items={failed_items}")
        return False


async def test_delete_invalid_inventory_id():
    """テスト8: エラーハンドリング（無効な在庫IDの処理）"""
    print("\n" + "="*80)
    print("[テスト8] エラーハンドリング（無効な在庫IDの処理）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。")
        return False
    
    # テスト: 無効な在庫IDで削除
    print(f"\n[テスト実行] 無効な在庫IDで削除...")
    today = datetime.now().strftime("%Y-%m-%d")
    delete_response = client.delete_ingredients(
        date=today,
        ingredients=[
            {
                "item_name": "テスト食材",
                "quantity": 0,
                "inventory_id": "invalid-id-12345"
            }
        ]
    )
    
    if delete_response is None:
        print("❌ リクエストが失敗しました")
        return False
    
    if not delete_response.get("success"):
        print(f"❌ APIが失敗を返しました: {delete_response}")
        return False
    
    failed_items = delete_response.get("failed_items", [])
    
    # 無効な在庫IDはfailed_itemsに含まれることを確認
    if len(failed_items) >= 1:
        print("✅ 正常系: 無効な在庫IDが適切に処理されました")
        print(f"   失敗アイテム: {failed_items}")
        return True
    else:
        print(f"❌ 期待される動作と異なります: failed_items={failed_items}")
        return False


async def main():
    """メイン関数"""
    print("🚀 セッション4: Phase 2B（在庫更新API）の単体テスト開始")
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
        ("単一食材の削除（在庫ID指定）", test_delete_single_ingredient_by_id),
        ("単一食材の削除（食材名指定）", test_delete_single_ingredient_by_name),
        ("複数食材の削除（複数在庫）", test_delete_multiple_ingredients_by_name),
        ("複数食材の一括削除", test_delete_multiple_ingredients_batch),
        ("一部失敗の処理", test_delete_partial_failure),
        ("数量更新（0以外）", test_update_quantity_non_zero),
        ("存在しない食材の処理", test_delete_nonexistent_ingredient),
        ("無効な在庫IDの処理", test_delete_invalid_inventory_id),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in test_cases:
        try:
            print(f"\n{'='*80}")
            print(f"🧪 テスト実行: {test_name}")
            print(f"{'='*80}")
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ テスト成功: {test_name}")
            else:
                failed += 1
                print(f"❌ テスト失敗: {test_name}")
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        
        # テスト間で少し待機
        await wait_for_response_delay(2.0)
    
    # 結果サマリー
    print(f"\n{'='*80}")
    print(f"📊 テスト結果サマリー")
    print(f"{'='*80}")
    print(f"✅ 成功: {passed}")
    print(f"❌ 失敗: {failed}")
    if passed + failed > 0:
        print(f"📈 成功率: {passed / (passed + failed) * 100:.1f}%")
    
    return failed == 0


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)

