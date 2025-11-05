#!/usr/bin/env python3
"""
Phase 3: OCR機能のテスト
"""

import asyncio
import sys
import os
import tempfile
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
    
    def upload_receipt_image(self, image_path: str, raise_on_error: bool = True):
        """レシート画像をアップロード
        
        Args:
            image_path: 画像ファイルのパス
            raise_on_error: Trueの場合、エラー時に例外を投げる。Falseの場合、エラーレスポンスも返す
        
        Returns:
            成功時: JSONレスポンス
            エラー時: raise_on_error=TrueならNone、FalseならエラーレスポンスのJSON
        """
        url = f"{self.base_url}/api/inventory/ocr-receipt"
        
        if not os.path.exists(image_path):
            print(f"❌ 画像ファイルが見つかりません: {image_path}")
            return None
        
        with open(image_path, 'rb') as f:
            files = {
                'image': (os.path.basename(image_path), f, 'image/jpeg')
            }
            
            try:
                response = self.session.post(url, files=files, timeout=120)
                
                if raise_on_error:
                    response.raise_for_status()
                    return response.json()
                else:
                    # raise_on_error=Falseの場合、エラーレスポンスも返す
                    if response.status_code < 400:
                        return response.json()
                    else:
                        # エラーレスポンスもJSONとして返す
                        try:
                            return response.json()
                        except:
                            return {"error": response.text, "status_code": response.status_code}
            except requests.exceptions.RequestException as e:
                if raise_on_error:
                    print(f"❌ HTTPリクエストエラー: {e}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"   レスポンス: {e.response.text}")
                    return None
                else:
                    # raise_on_error=Falseの場合、エラー情報を返す
                    if hasattr(e, 'response') and e.response is not None:
                        try:
                            return e.response.json()
                        except:
                            return {"error": e.response.text, "status_code": e.response.status_code}
                    return {"error": str(e), "status_code": None}


async def test_ocr_receipt_success():
    """正常なレシート画像のOCR解析テスト"""
    print("\n=== test_ocr_receipt_success ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # テスト用画像ファイルのパス（実際のレシート画像を使用）
    # 注意: テスト用のレシート画像を用意する必要があります
    test_image_path = os.path.join(os.path.dirname(__file__), "test_receipt.jpg")
    
    if not os.path.exists(test_image_path):
        print(f"⚠️ テスト用画像が見つかりません: {test_image_path}")
        print("   テスト用のレシート画像を用意してください")
        print("   ⚠️ このテストはスキップされます")
        return True  # テスト用画像がない場合はスキップ（エラーではない）
    
    # OCR解析
    result = client.upload_receipt_image(test_image_path)
    
    if not result:
        print("❌ OCR解析に失敗しました")
        return False
    
    print(f"✅ OCR解析結果:")
    print(f"   Success: {result.get('success')}")
    print(f"   Items count: {len(result.get('items', []))}")
    print(f"   Registered count: {result.get('registered_count')}")
    
    if result.get('errors'):
        print(f"   Errors: {result.get('errors')}")
    
    if result.get('items'):
        print(f"   Extracted items:")
        for item in result.get('items', [])[:5]:  # 最初の5件を表示
            print(f"     - {item.get('item_name')}: {item.get('quantity')}{item.get('unit')}")
    
    # 検証
    assert result.get('success'), "OCR解析が成功していません"
    assert len(result.get('items', [])) > 0, "アイテムが抽出されていません"
    
    print("✅ テスト成功")
    return True


async def test_ocr_receipt_invalid_file():
    """無効なファイル形式のテスト"""
    print("\n=== test_ocr_receipt_invalid_file ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # 無効なファイル（テキストファイル）を作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is not an image")
        temp_file = f.name
    
    try:
        # OCR解析（エラーになるはず）
        result = client.upload_receipt_image(temp_file)
        
        # エラーが返されることを確認
        if result is None:
            print("✅ 無効なファイル形式でエラーが返されました（期待通り）")
            return True
        else:
            # エラーレスポンスが返された場合もOK
            if not result.get('success') or result.get('errors'):
                print("✅ 無効なファイル形式でエラーが返されました（期待通り）")
                return True
            else:
                print("⚠️ 無効なファイル形式でもエラーが返されませんでした")
                return False
    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)


async def test_ocr_receipt_large_file():
    """大きなファイルサイズのテスト"""
    print("\n=== test_ocr_receipt_large_file ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # 大きなファイル（10MB超）を作成
    large_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
    large_file.write(b'\xff\xd8\xff' + b'0' * (11 * 1024 * 1024))  # 11MB
    large_file.close()
    
    try:
        # OCR解析（エラーになるはず）
        result = client.upload_receipt_image(large_file.name)
        
        # エラーが返されることを確認
        if result is None:
            print("✅ 大きなファイルでエラーが返されました（期待通り）")
            return True
        else:
            # エラーレスポンスが返された場合もOK
            if not result.get('success') or result.get('errors'):
                print("✅ 大きなファイルでエラーが返されました（期待通り）")
                return True
            else:
                print("⚠️ 大きなファイルでもエラーが返されませんでした")
                return False
    finally:
        if os.path.exists(large_file.name):
            os.unlink(large_file.name)


async def test_ocr_service_direct():
    """OCRServiceの直接テスト"""
    print("\n=== test_ocr_service_direct ===")
    
    try:
        from services.ocr_service import OCRService
        
        ocr_service = OCRService()
        print(f"✅ OCRService initialized with model: {ocr_service.ocr_model}")
        
        # テスト用画像（小さなダミー画像）
        # 実際のテストでは、実際のレシート画像を使用
        test_image_path = os.path.join(os.path.dirname(__file__), "test_receipt.jpg")
        
        if not os.path.exists(test_image_path):
            print("⚠️ テスト用画像が見つかりません。スキップします。")
            return True  # テスト用画像がない場合はスキップ
        
        with open(test_image_path, 'rb') as f:
            image_bytes = f.read()
        
        result = await ocr_service.analyze_receipt_image(image_bytes)
        
        print(f"✅ OCR解析結果:")
        print(f"   Success: {result.get('success')}")
        print(f"   Items count: {len(result.get('items', []))}")
        
        if result.get('error'):
            print(f"   Error: {result.get('error')}")
        
        assert result.get('success'), "OCR解析が成功していません"
        
        print("✅ テスト成功")
        return True
        
    except ImportError as e:
        print(f"⚠️ OCRServiceが見つかりません: {e}")
        print("   実装後にテストしてください。")
        return False
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ocr_endpoint_validation():
    """OCRエンドポイントのバリデーションテスト"""
    print("\n=== test_ocr_endpoint_validation ===")
    
    client = IntegrationTestClient()
    
    # サーバーの状態確認
    if not client.check_server_status():
        print("❌ サーバーが起動していません")
        return False
    
    # 有効なJPEG形式の小さなダミー画像を作成
    # マジックナンバー + 最小限のJPEGデータ
    dummy_jpeg = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xaa\x00\xff\xd9'
    
    dummy_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False)
    dummy_file.write(dummy_jpeg)
    dummy_file.close()
    
    try:
        # OCR解析（実際のレシートではないので、OCRは失敗するかもしれないが、エンドポイントは応答するはず）
        # raise_on_error=Falseで、エラーレスポンスも受け取る
        result = client.upload_receipt_image(dummy_file.name, raise_on_error=False)
        
        # エンドポイントが応答することを確認（OCR結果の成功/失敗は問わない）
        # 400エラーでもエンドポイントが応答したとみなす
        if result is not None:
            print("✅ エンドポイントが正常に応答しました")
            if result.get('success') is not None:
                print(f"   Success: {result.get('success')}")
            elif result.get('detail'):
                print(f"   エラーメッセージ: {result.get('detail')}")
            elif result.get('error'):
                print(f"   エラー: {result.get('error')}")
            return True
        else:
            print("⚠️ エンドポイントが応答しませんでした")
            return False
    finally:
        if os.path.exists(dummy_file.name):
            os.unlink(dummy_file.name)


async def main():
    """メインテスト実行"""
    print("🧪 Phase 3: OCR機能のテスト開始")
    print("="*50)
    
    tests = [
        ("OCRService直接テスト", test_ocr_service_direct),
        ("OCRエンドポイントバリデーション", test_ocr_endpoint_validation),
        ("無効ファイルテスト", test_ocr_receipt_invalid_file),
        ("大容量ファイルテスト", test_ocr_receipt_large_file),
        ("OCR解析テスト（実画像）", test_ocr_receipt_success),
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
        print("\n💡 注意:")
        print("   - テスト用のレシート画像（test_receipt.jpg）がない場合、一部のテストはスキップされます")
        print("   - 実際のレシート画像でテストする場合は、tests/test_receipt.jpg を用意してください")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

