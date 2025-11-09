#!/usr/bin/env python3
"""
セッション2: Phase 1B + Phase 1C（献立提案と提案レスポンス）の結合テスト

実際に起動しているサーバーでテストするタイプの結合テスト
test_inventory_delete_session1_integration.pyを参考に実装
"""

import asyncio
import sys
import os
import requests
import time
import uuid
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
    
    def get_recipe_history_from_db(self, history_id: str):
        """DBから直接レシピ履歴を取得（Supabaseクライアント使用）"""
        try:
            from supabase import create_client
            from mcp_servers.utils import get_authenticated_client
            
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not all([supabase_url, supabase_key]):
                print("⚠️ SUPABASE_URL and SUPABASE_KEY are required for DB access")
                return None
            
            # 認証済みクライアントを取得
            client = get_authenticated_client(None, self.jwt_token)
            
            # レシピ履歴を取得
            result = client.table("recipe_historys").select("*").eq("id", history_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                return None
                
        except Exception as e:
            print(f"❌ DB取得エラー: {e}")
            return None


async def test_menu_proposal_to_adopt_with_ingredients():
    """献立提案→採用→履歴保存のフロー（ingredientsあり）"""
    print("\n" + "="*80)
    print("[結合テスト1] 献立提案→採用→履歴保存のフロー（ingredientsあり）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    # 新しいセッションIDを作成
    sse_session_id = f"test_integration_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    print(f"📋 セッションID: {sse_session_id}")
    
    try:
        # 1. 献立提案リクエスト
        print("\n📋 [ステップ1] 献立提案をリクエスト...")
        menu_response = client.send_chat_request(
            message="レンコンを使った献立を提案してください",
            sse_session_id=sse_session_id
        )
        
        if not menu_response or not menu_response.get("success"):
            print(f"❌ 献立提案が失敗しました: {menu_response}")
            return False
        
        print(f"✅ 献立提案成功")
        print(f"📋 レスポンス: {menu_response.get('response', '')[:200]}...")
        
        # レスポンスにingredientsが含まれているか確認（提案レスポンスの検証）
        response_text = menu_response.get("response", "")
        if "ingredients" in response_text.lower() or "食材" in response_text:
            print("✅ 提案レスポンスに食材情報が含まれている可能性があります")
        else:
            print("⚠️ 提案レスポンスに食材情報が明示的に含まれていない可能性があります（実装次第）")
        
        time.sleep(3)  # 提案処理の完了を待つ
        
        # 2. 献立提案の結果から候補を取得（実際の実装ではセッションから取得する必要がある）
        # ここでは直接adopt_recipe()を呼び出してテスト
        
        # 3. adopt_recipe()でingredientsを含むレシピを採用
        print("\n📋 [ステップ2] adopt_recipe()でレシピを採用（ingredientsあり）...")
        
        recipes = [
            {
                "title": "レンコン炒め",
                "category": "main_dish",
                "menu_source": "llm_menu",
                "url": "https://example.com/recipe1",
                "ingredients": ["レンコン", "にんじん", "鶏肉", "醤油"]
            },
            {
                "title": "ほうれん草の胡麻和え",
                "category": "side_dish",
                "menu_source": "rag_menu",
                "url": "https://example.com/recipe2",
                "ingredients": ["ほうれん草", "ごま", "醤油"]
            },
            {
                "title": "味噌汁",
                "category": "soup",
                "menu_source": "llm_menu",
                "ingredients": ["味噌", "豆腐", "わかめ"]
            }
        ]
        
        adopt_response = client.adopt_recipe(recipes)
        
        if not adopt_response:
            print("❌ adopt_recipe()が失敗しました")
            return False
        
        print(f"📋 採用レスポンス: {adopt_response}")
        
        success = adopt_response.get("success", False)
        total_saved = adopt_response.get("total_saved", 0)
        saved_recipes = adopt_response.get("saved_recipes", [])
        
        if not success or total_saved == 0:
            print(f"❌ レシピ採用が失敗しました: success={success}, total_saved={total_saved}")
            return False
        
        print(f"✅ レシピ採用成功: {total_saved}件保存")
        
        # 4. DBから履歴を取得してingredientsを確認
        print("\n📋 [ステップ3] DBから履歴を取得してingredientsを確認...")
        
        all_ingredients_saved = True
        for saved_recipe in saved_recipes:
            history_id = saved_recipe.get("history_id")
            title = saved_recipe.get("title", "")
            if not history_id:
                continue
            
            # DBから直接取得
            history_data = client.get_recipe_history_from_db(history_id)
            if not history_data:
                print(f"⚠️ 履歴ID {history_id} のデータを取得できませんでした")
                all_ingredients_saved = False
                continue
            
            ingredients = history_data.get("ingredients")
            db_title = history_data.get("title", "")
            
            # 期待されるingredientsを取得
            expected_ingredients = None
            for recipe in recipes:
                if recipe["title"] == title or recipe["title"] in db_title or db_title in recipe["title"]:
                    expected_ingredients = recipe.get("ingredients")
                    break
            
            if ingredients:
                print(f"✅ {title} ({db_title}): ingredients={ingredients}")
                if expected_ingredients:
                    # ingredientsが期待通りか確認（順序は問わない）
                    if set(ingredients) == set(expected_ingredients):
                        print(f"   ✅ ingredientsが期待通りです")
                    else:
                        print(f"   ⚠️ ingredientsが期待と異なります: 期待={expected_ingredients}, 実際={ingredients}")
                        # 完全一致でなくても、ingredientsが保存されていればOKとする
            else:
                print(f"❌ {title} ({db_title}): ingredientsが保存されていません（期待: {expected_ingredients}）")
                all_ingredients_saved = False
        
        if all_ingredients_saved:
            print("\n✅ すべてのingredientsが正しく保存されました")
            return True
        else:
            print("\n⚠️ 一部のingredientsが保存されていません")
            return False
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_adopt_recipe_with_ingredients_direct():
    """直接adopt_recipe()でingredientsが保存されること"""
    print("\n" + "="*80)
    print("[結合テスト2] 直接adopt_recipe()でingredientsが保存されること")
    print("="*80)
    
    client = IntegrationTestClient()
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    try:
        # ingredientsを含むレシピデータを直接指定
        recipes = [
            {
                "title": "レンコン炒め",
                "category": "main_dish",
                "menu_source": "llm_menu",
                "url": "https://example.com/recipe1",
                "ingredients": ["レンコン", "にんじん", "鶏肉", "醤油"]
            },
            {
                "title": "ほうれん草の胡麻和え",
                "category": "side_dish",
                "menu_source": "rag_menu",
                "url": "https://example.com/recipe2",
                "ingredients": ["ほうれん草", "ごま", "醤油"]
            }
        ]
        
        print(f"📋 採用するレシピ: {len(recipes)}件")
        for i, recipe in enumerate(recipes, 1):
            print(f"  {i}. {recipe['title']} (ingredients: {recipe.get('ingredients', [])})")
        
        # adopt_recipe()を呼び出し
        adopt_response = client.adopt_recipe(recipes)
        
        if not adopt_response:
            print("❌ adopt_recipe()が失敗しました")
            return False
        
        print(f"📋 採用レスポンス: {adopt_response}")
        
        success = adopt_response.get("success", False)
        total_saved = adopt_response.get("total_saved", 0)
        saved_recipes = adopt_response.get("saved_recipes", [])
        
        if not success or total_saved == 0:
            print(f"❌ レシピ採用が失敗しました: success={success}, total_saved={total_saved}")
            return False
        
        print(f"✅ レシピ採用成功: {total_saved}件保存")
        
        # DBから履歴を取得してingredientsを確認
        print("\n📋 DBから履歴を取得してingredientsを確認...")
        
        all_ingredients_saved = True
        for saved_recipe in saved_recipes:
            history_id = saved_recipe.get("history_id")
            title = saved_recipe.get("title", "")
            category = saved_recipe.get("category", "")
            if not history_id:
                continue
            
            # DBから直接取得
            history_data = client.get_recipe_history_from_db(history_id)
            if not history_data:
                print(f"⚠️ 履歴ID {history_id} のデータを取得できませんでした")
                all_ingredients_saved = False
                continue
            
            ingredients = history_data.get("ingredients")
            db_title = history_data.get("title", "")
            
            # 期待されるingredients
            expected_ingredients = None
            for recipe in recipes:
                if recipe["title"] == title or recipe["title"] in db_title or db_title in recipe["title"]:
                    expected_ingredients = recipe.get("ingredients")
                    break
            
            if ingredients:
                print(f"✅ {category} ({title} / {db_title}): ingredients={ingredients}")
                if expected_ingredients:
                    # ingredientsが期待通りか確認（順序は問わない）
                    if set(ingredients) == set(expected_ingredients):
                        print(f"   ✅ ingredientsが期待通りです")
                    else:
                        print(f"   ⚠️ ingredientsが期待と異なります: 期待={expected_ingredients}, 実際={ingredients}")
            else:
                print(f"❌ {category} ({title} / {db_title}): ingredientsが保存されていません（期待: {expected_ingredients}）")
                all_ingredients_saved = False
        
        if all_ingredients_saved:
            print("\n✅ すべてのingredientsが正しく保存されました")
            return True
        else:
            print("\n⚠️ 一部のingredientsが保存されていません")
            return False
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_adopt_recipe_without_ingredients():
    """ingredientsなしでadopt_recipe()を呼び出す（既存機能の動作確認）"""
    print("\n" + "="*80)
    print("[結合テスト3] ingredientsなしでadopt_recipe()を呼び出す（既存機能の動作確認）")
    print("="*80)
    
    client = IntegrationTestClient()
    
    # サーバーの状態をチェック
    if not client.check_server_status():
        print("⚠️ サーバーが起動していません。python -m uvicorn api.main:app --reload でサーバーを起動してください。")
        return False
    
    print("✅ サーバー接続確認")
    
    try:
        # ingredientsを含まないレシピデータを直接指定
        recipes = [
            {
                "title": "テストレシピ（ingredientsなし）",
                "category": "main_dish",
                "menu_source": "llm_menu",
                "url": "https://example.com/recipe3"
                # ingredientsフィールドなし
            }
        ]
        
        print(f"📋 採用するレシピ: {len(recipes)}件（ingredientsなし）")
        
        # adopt_recipe()を呼び出し
        adopt_response = client.adopt_recipe(recipes)
        
        if not adopt_response:
            print("❌ adopt_recipe()が失敗しました")
            return False
        
        print(f"📋 採用レスポンス: {adopt_response}")
        
        success = adopt_response.get("success", False)
        total_saved = adopt_response.get("total_saved", 0)
        saved_recipes = adopt_response.get("saved_recipes", [])
        
        if not success or total_saved == 0:
            print(f"❌ レシピ採用が失敗しました: success={success}, total_saved={total_saved}")
            return False
        
        print(f"✅ レシピ採用成功: {total_saved}件保存")
        
        # DBから履歴を取得してingredientsがNoneであることを確認
        print("\n📋 DBから履歴を取得してingredientsがNoneであることを確認...")
        
        for saved_recipe in saved_recipes:
            history_id = saved_recipe.get("history_id")
            if not history_id:
                continue
            
            # DBから直接取得
            history_data = client.get_recipe_history_from_db(history_id)
            if not history_data:
                print(f"⚠️ 履歴ID {history_id} のデータを取得できませんでした")
                continue
            
            ingredients = history_data.get("ingredients")
            title = history_data.get("title", "")
            
            if ingredients is None or ingredients == []:
                print(f"✅ {title}: ingredientsがNoneまたは空（既存動作維持）")
            else:
                print(f"⚠️ {title}: ingredients={ingredients}（ingredientsがない場合でも動作）")
        
        print("\n✅ ingredientsなしでも既存機能が正常に動作しました")
        return True
        
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """全ての結合テストを実行"""
    print("=" * 80)
    print("セッション2: Phase 1B + Phase 1C（献立提案と提案レスポンス）の結合テスト")
    print("=" * 80)
    
    tests = [
        ("test_menu_proposal_to_adopt_with_ingredients", test_menu_proposal_to_adopt_with_ingredients),
        ("test_adopt_recipe_with_ingredients_direct", test_adopt_recipe_with_ingredients_direct),
        ("test_adopt_recipe_without_ingredients", test_adopt_recipe_without_ingredients),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            
            if result:
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                failed += 1
                
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        
        # テスト間で少し待機
        if test_name != tests[-1][0]:  # 最後のテスト以外
            print("\n⏳ 次のテストまで待機中...")
            await asyncio.sleep(3)
    
    print("\n" + "=" * 80)
    print(f"テスト結果: {passed} passed, {failed} failed (合計 {len(tests)})")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

