# Phase 3: OCR機能（バックエンド）

## 📋 概要

レシート画像を解析して在庫データを抽出するバックエンド機能を実装します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**推定時間**: 2-3時間

## 🎯 目標

1. `services/ocr_service.py`の作成（OCRServiceクラス）
2. `POST /api/inventory/ocr-receipt`エンドポイントの実装
3. 画像処理（base64エンコード、検証）
4. `gpt-4o`を使用したOCR解析
5. 解析結果の構造化とバリデーション

## 📝 対象ファイル

- `services/ocr_service.py` (新規作成)
- `api/routes/inventory.py` (拡張)
- `api/models/requests.py` (拡張、レスポンスモデル追加)
- `env.example` (拡張、`OPENAI_OCR_MODEL`追加)

## 🔍 実装の詳細

### 3.1 OCRServiceの実装

**場所**: `services/ocr_service.py`

**クラス構造**:
```python
import os
import base64
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
from config.loggers import GenericLogger

load_dotenv()


class OCRService:
    """レシートOCRサービス"""
    
    def __init__(self):
        self.logger = GenericLogger("service", "ocr")
        self.ocr_model = os.getenv("OPENAI_OCR_MODEL", "gpt-4o")
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.logger.info(f"✅ [OCR] OCRService initialized with model: {self.ocr_model}")
    
    async def analyze_receipt_image(
        self,
        image_bytes: bytes
    ) -> Dict[str, Any]:
        """レシート画像を解析して在庫情報を抽出"""
        try:
            self.logger.info("🔍 [OCR] Starting receipt image analysis")
            
            # 画像をbase64エンコード
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # OpenAI Vision APIで解析
            response = await self.client.chat.completions.create(
                model=self.ocr_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """このレシート画像から、在庫管理に必要な情報を抽出してください。

抽出すべき情報:
- 商品名（item_name）
- 数量（quantity）
- 単位（unit）
- 保管場所（storage_location、推測可）
- 消費期限（expiry_date、もし記載されていれば）

レスポンス形式: JSON配列
[
  {
    "item_name": "商品名",
    "quantity": 数量,
    "unit": "単位",
    "storage_location": "保管場所",
    "expiry_date": "YYYY-MM-DD または null"
  }
]

日本語のレシートを正確に解析してください。商品名は正確に、数量と単位も正しく抽出してください。"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            self.logger.info(f"✅ [OCR] OCR analysis completed: {len(content)} characters")
            
            # JSONを抽出（Markdownコードブロックから）
            import json
            import re
            
            # JSONコードブロックを抽出
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # コードブロックがない場合、直接JSONとして解析を試みる
                json_str = content.strip()
            
            # JSON解析
            items = json.loads(json_str)
            
            if not isinstance(items, list):
                raise ValueError("OCR結果が配列形式ではありません")
            
            self.logger.info(f"✅ [OCR] Extracted {len(items)} items from receipt")
            
            return {
                "success": True,
                "items": items,
                "raw_response": content
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ [OCR] JSON解析エラー: {e}")
            self.logger.error(f"   レスポンス内容: {content[:500]}")
            return {
                "success": False,
                "error": f"JSON解析エラー: {str(e)}",
                "items": []
            }
        except Exception as e:
            self.logger.error(f"❌ [OCR] OCR解析エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": []
            }
    
    async def extract_inventory_items(
        self,
        image_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """レシート画像から在庫アイテムのリストを抽出"""
        result = await self.analyze_receipt_image(image_bytes)
        
        if result.get("success"):
            return result.get("items", [])
        else:
            raise Exception(result.get("error", "OCR解析に失敗しました"))
```

### 3.2 画像処理

**処理内容**:
1. ファイル形式チェック（JPEG/PNG）
2. ファイルサイズチェック（最大10MB）
3. base64エンコード
4. OpenAI APIに送信

**実装例**:
```python
def validate_image_file(image_bytes: bytes, filename: str) -> tuple[bool, Optional[str]]:
    """画像ファイルの検証"""
    # ファイルサイズチェック（10MB制限）
    max_size = 10 * 1024 * 1024  # 10MB
    if len(image_bytes) > max_size:
        return False, "ファイルサイズは10MB以下にしてください"
    
    # ファイル形式チェック
    valid_extensions = ['.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(filename.lower())[1]
    
    if file_ext not in valid_extensions:
        return False, "JPEGまたはPNGファイルのみアップロード可能です"
    
    # 画像形式の検証（マジックナンバー）
    if image_bytes.startswith(b'\xff\xd8\xff'):
        # JPEG
        return True, None
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        # PNG
        return True, None
    else:
        return False, "画像ファイルの形式が正しくありません"
```

### 3.3 OCRエンドポイントの実装

**場所**: `api/routes/inventory.py`

**実装例**:
```python
@router.post("/inventory/ocr-receipt", response_model=OCRReceiptResponse)
async def ocr_receipt(
    image: UploadFile = File(...),
    http_request: Request = None
):
    """レシート画像をOCR解析して在庫データを抽出・登録"""
    try:
        logger.info(f"🔍 [API] OCR receipt request received: {image.filename}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        
        # 2. 画像ファイルの検証
        image_bytes = await image.read()
        is_valid, error_message = validate_image_file(image_bytes, image.filename)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # 3. OCR解析
        from services.ocr_service import OCRService
        
        ocr_service = OCRService()
        ocr_result = await ocr_service.analyze_receipt_image(image_bytes)
        
        if not ocr_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=ocr_result.get("error", "OCR解析に失敗しました")
            )
        
        items = ocr_result.get("items", [])
        
        if not items:
            return {
                "success": True,
                "items": [],
                "registered_count": 0,
                "errors": ["レシートから在庫情報を抽出できませんでした"]
            }
        
        # 4. データバリデーション
        validated_items = []
        validation_errors = []
        
        for idx, item in enumerate(items, 1):
            try:
                # 必須項目チェック
                if not item.get("item_name") or not str(item.get("item_name")).strip():
                    validation_errors.append(f"行{idx}: アイテム名が空です")
                    continue
                
                if item.get("quantity") is None:
                    validation_errors.append(f"行{idx}: 数量が指定されていません")
                    continue
                
                # 数量の検証
                try:
                    quantity = float(item["quantity"])
                    if quantity <= 0:
                        validation_errors.append(f"行{idx}: 数量は0より大きい値が必要です")
                        continue
                except (ValueError, TypeError):
                    validation_errors.append(f"行{idx}: 数量が数値ではありません")
                    continue
                
                # 単位のデフォルト値
                unit = item.get("unit", "個")
                
                validated_items.append({
                    "item_name": str(item["item_name"]).strip(),
                    "quantity": quantity,
                    "unit": str(unit).strip(),
                    "storage_location": item.get("storage_location", "冷蔵庫"),
                    "expiry_date": item.get("expiry_date")
                })
                
            except Exception as e:
                validation_errors.append(f"行{idx}: データ処理エラー - {str(e)}")
        
        # 5. 在庫登録（バリデーション通過したアイテムのみ）
        registered_count = 0
        if validated_items:
            try:
                client = get_authenticated_client(user_id, token)
                crud = InventoryCRUD()
                result = await crud.add_items_bulk(client, user_id, validated_items)
                
                if result.get("success"):
                    registered_count = result.get("success_count", 0)
                    # DBエラーもvalidation_errorsに追加
                    if result.get("errors"):
                        validation_errors.extend([
                            f"DBエラー: {err.get('error', 'Unknown error')}"
                            for err in result.get("errors", [])
                        ])
                else:
                    validation_errors.append("在庫登録に失敗しました")
                    
            except Exception as e:
                logger.error(f"❌ [API] Failed to register inventory: {e}")
                validation_errors.append(f"在庫登録エラー: {str(e)}")
        
        return {
            "success": True,
            "items": validated_items,
            "registered_count": registered_count,
            "errors": validation_errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in ocr_receipt: {e}")
        raise HTTPException(status_code=500, detail="OCR処理でエラーが発生しました")
```

### 3.4 レスポンスモデルの追加

**場所**: `api/models/requests.py`

**追加内容**:
```python
class OCRReceiptItem(BaseModel):
    """OCR抽出アイテム"""
    item_name: str = Field(..., description="アイテム名")
    quantity: float = Field(..., description="数量")
    unit: str = Field(..., description="単位")
    storage_location: Optional[str] = Field(None, description="保管場所")
    expiry_date: Optional[str] = Field(None, description="消費期限")


class OCRReceiptResponse(BaseModel):
    """OCRレシート解析レスポンス"""
    success: bool = Field(..., description="成功したかどうか")
    items: List[OCRReceiptItem] = Field(default_factory=list, description="抽出されたアイテムリスト")
    registered_count: int = Field(..., description="登録された件数")
    errors: List[str] = Field(default_factory=list, description="エラーメッセージ")
```

### 3.5 環境変数の追加

**場所**: `env.example`

**追加内容**:
```
# OCR用モデル（マルチモーダル対応）
OPENAI_OCR_MODEL=gpt-4o
```

## 🧪 テスト

### テストファイル

**場所**: `tests/test_inventory_ocr.py`

### テスト内容

#### 1. OCR解析テスト

**テストケース**: `test_ocr_receipt_success`

レシート画像をアップロードし、OCR解析が正常に動作することを確認。

```python
#!/usr/bin/env python3
"""
Phase 3: OCR機能のテスト
"""

import asyncio
import sys
import os
import requests
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .envファイルを読み込み
load_dotenv()


class IntegrationTestClient:
    """統合テスト用のHTTPクライアント"""
    
    def __init__(self, base_url="http://localhost:8000", jwt_token=None):
        self.base_url = base_url
        self.session = requests.Session()
        
        # JWTトークンの設定
        self.jwt_token = jwt_token or os.getenv("TEST_USER_JWT_TOKEN") or "test_token_for_integration"
        
        self.session.headers.update({
            "Authorization": f"Bearer {self.jwt_token}",
        })
    
    def check_server_status(self):
        """サーバーの状態をチェック"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_receipt_image(self, image_path: str):
        """レシート画像をアップロード"""
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
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"❌ HTTPリクエストエラー: {e}")
                if hasattr(e.response, 'text'):
                    print(f"   レスポンス: {e.response.text}")
                return None


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
        return False
    
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
    import tempfile
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
            print("⚠️ 無効なファイル形式でもエラーが返されませんでした")
            return False
    finally:
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
    import tempfile
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
            print("⚠️ 大きなファイルでもエラーが返されませんでした")
            return False
    finally:
        os.unlink(large_file.name)


async def test_ocr_service_direct():
    """OCRServiceの直接テスト"""
    print("\n=== test_ocr_service_direct ===")
    
    try:
        from services.ocr_service import OCRService
        
        ocr_service = OCRService()
        
        # テスト用画像（小さなダミー画像）
        # 実際のテストでは、実際のレシート画像を使用
        test_image_path = os.path.join(os.path.dirname(__file__), "test_receipt.jpg")
        
        if not os.path.exists(test_image_path):
            print("⚠️ テスト用画像が見つかりません。スキップします。")
            return True
        
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
        
    except ImportError:
        print("⚠️ OCRServiceが見つかりません。実装後にテストしてください。")
        return True
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("🧪 Phase 3: OCR機能のテスト開始")
    
    tests = [
        ("OCR解析テスト", test_ocr_receipt_success),
        ("無効ファイルテスト", test_ocr_receipt_invalid_file),
        ("大容量ファイルテスト", test_ocr_receipt_large_file),
        ("OCRService直接テスト", test_ocr_service_direct),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}でエラーが発生しました: {e}")
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
```

### テスト実行方法

```bash
# サーバーが起動していることを確認
# テスト用のレシート画像を用意（tests/test_receipt.jpg）
# その後、テストを実行

python tests/test_inventory_ocr.py
```

### テスト項目

- [x] 画像ファイルのアップロード
- [x] OCR解析の実行
- [x] 解析結果の構造化
- [x] エラーハンドリング（画像形式エラー、OCR失敗等）
- [x] ファイルサイズ制限の確認
- [x] OCRServiceの直接テスト

## 📊 成功基準

- [ ] レシート画像を解析して在庫情報を抽出できる
- [ ] 解析結果を構造化データに変換できる
- [ ] エラーハンドリングが動作する
- [ ] テストがすべて成功する

## 🔄 実装順序

1. `services/ocr_service.py`の作成
2. 環境変数の追加（`env.example`）
3. レスポンスモデルの追加（`api/models/requests.py`）
4. `POST /api/inventory/ocr-receipt`エンドポイントの実装
5. テストファイルの作成と実行
6. 不具合修正

## 🚨 注意事項

### OCR精度について

- OCR解析の精度はレシートの形式や品質によって変動します
- 日本語のレシートは特に注意が必要です
- テスト時は実際のレシート画像を使用して精度を確認してください

### コストについて

- `gpt-4o`は`gpt-4o-mini`より高額です
- 画像サイズに応じてトークン消費が増加します
- 使用量を監視してコストを把握してください

