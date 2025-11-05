#!/usr/bin/env python3
"""
Phase 1: CSV一括登録機能のテスト
"""

import asyncio
import sys
import os
import csv
import io
import requests
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Supabase認証ユーティリティをインポート
archive_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "archive", "rebuild", "00_1_test_util.py")
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
        })
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_csv(self, csv_content: str, filename: str = "test.csv"):
        """CSVファイルをアップロード"""
        url = f"{self.base_url}/api/inventory/upload-csv"
        
        files = {
            'file': (filename, csv_content.encode('utf-8'), 'text/csv')
        }
        
        try:
            response = self.session.post(url, files=files, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ HTTPリクエストエラー: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   レスポンス: {e.response.text}")
            return None


async def test_csv_upload_success():
    """正常なCSVファイルのアップロードテスト"""
    print("\n=== test_csv_upload_success ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # CSVコンテンツの作成
    csv_content = """item_name,quantity,unit,storage_location,expiry_date
りんご,5,個,冷蔵庫,2024-02-15
米,2,kg,常温倉庫,
牛乳,1,L,冷蔵庫,2024-01-25"""
    
    # CSVアップロード
    result = client.upload_csv(csv_content, "test_inventory.csv")
    
    if not result:
        print("❌ CSVアップロードに失敗しました")
        return False
    
    print(f"✅ アップロード結果:")
    print(f"   Success: {result.get('success')}")
    print(f"   Total: {result.get('total')}")
    print(f"   Success count: {result.get('success_count')}")
    print(f"   Error count: {result.get('error_count')}")
    
    if result.get('errors'):
        print(f"   Errors: {result.get('errors')}")
    
    # 検証
    assert result.get('success'), "アップロードが成功していません"
    assert result.get('success_count') == 3, f"3件登録されるべきですが、{result.get('success_count')}件でした"
    assert result.get('error_count') == 0, f"エラーが発生しています: {result.get('errors')}"
    
    print("✅ テスト成功")
    return True


async def test_csv_upload_with_errors():
    """エラーデータを含むCSVファイルのアップロードテスト"""
    print("\n=== test_csv_upload_with_errors ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # エラーデータを含むCSVコンテンツ
    csv_content = """item_name,quantity,unit,storage_location,expiry_date
りんご,5,個,冷蔵庫,2024-02-15
,2,kg,常温倉庫,
牛乳,-1,L,冷蔵庫,2024-01-25
米,2,kg,常温倉庫,invalid-date"""
    
    # CSVアップロード
    result = client.upload_csv(csv_content, "test_inventory_errors.csv")
    
    if not result:
        print("❌ CSVアップロードに失敗しました")
        return False
    
    print(f"✅ アップロード結果:")
    print(f"   Success: {result.get('success')}")
    print(f"   Total: {result.get('total')}")
    print(f"   Success count: {result.get('success_count')}")
    print(f"   Error count: {result.get('error_count')}")
    
    if result.get('errors'):
        print(f"   Errors:")
        for error in result.get('errors', []):
            print(f"     Row {error.get('row')}: {error.get('error')}")
    
    # 検証
    assert result.get('success_count') == 1, f"1件登録されるべきですが、{result.get('success_count')}件でした"
    assert result.get('error_count') == 3, f"3件のエラーが発生するべきですが、{result.get('error_count')}件でした"
    
    print("✅ テスト成功（部分成功の確認）")
    return True


async def test_csv_upload_empty_file():
    """空のCSVファイルのアップロードテスト"""
    print("\n=== test_csv_upload_empty_file ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # 空のCSVコンテンツ（ヘッダーのみ）
    csv_content = """item_name,quantity,unit,storage_location,expiry_date"""
    
    # CSVアップロード
    result = client.upload_csv(csv_content, "test_empty.csv")
    
    if not result:
        print("❌ CSVアップロードに失敗しました")
        return False
    
    print(f"✅ アップロード結果:")
    print(f"   Success: {result.get('success')}")
    print(f"   Total: {result.get('total')}")
    print(f"   Success count: {result.get('success_count')}")
    print(f"   Error count: {result.get('error_count')}")
    
    # 検証
    assert result.get('total') == 0, "空ファイルなので総件数は0であるべきです"
    assert result.get('success_count') == 0, "空ファイルなので成功件数は0であるべきです"
    
    print("✅ テスト成功（空ファイルの処理確認）")
    return True


async def main():
    """メインテスト実行"""
    print("🧪 Phase 1: CSV一括登録機能のテスト開始")
    
    tests = [
        ("正常系テスト", test_csv_upload_success),
        ("エラーデータテスト", test_csv_upload_with_errors),
        ("空ファイルテスト", test_csv_upload_empty_file),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}でエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "="*50)
    print("📊 テスト結果サマリー")
    print("="*50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n合計: {passed}/{total} テストが成功しました")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

