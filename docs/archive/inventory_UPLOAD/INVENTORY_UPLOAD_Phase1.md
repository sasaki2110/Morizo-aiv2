# Phase 1: CSV一括登録機能（バックエンド）

## 📋 概要

CSVファイルから在庫データを一括登録するバックエンド機能を実装します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**推定時間**: 1-2時間

## 🎯 目標

1. `InventoryCRUD.add_items_bulk`メソッドの追加
2. `POST /api/inventory/upload-csv`エンドポイントの実装
3. CSV解析・バリデーション処理
4. エラーハンドリング（部分成功の処理）

## 📝 対象ファイル

- `mcp_servers/inventory_crud.py` (拡張)
- `api/routes/inventory.py` (拡張)
- `api/models/requests.py` (拡張、レスポンスモデル追加)

## 🔍 実装の詳細

### 1.1 InventoryCRUD.add_items_bulkの実装

**場所**: `mcp_servers/inventory_crud.py`

**メソッドシグネチャ**:
```python
async def add_items_bulk(
    self,
    client: Client,
    user_id: str,
    items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """在庫にアイテムを一括追加
    
    Args:
        client: Supabaseクライアント
        user_id: ユーザーID
        items: 在庫アイテムのリスト
            [
                {
                    "item_name": str,
                    "quantity": float,
                    "unit": str,
                    "storage_location": Optional[str],
                    "expiry_date": Optional[str]
                }
            ]
    
    Returns:
        {
            "success": bool,
            "total": int,
            "success_count": int,
            "error_count": int,
            "errors": List[Dict[str, Any]]
        }
    """
```

**実装方針**:
- Supabaseの`insert`で複数行を一括挿入
- エラーが発生した場合は個別に処理してエラー詳細を収集
- 部分成功を許容（一部失敗しても成功したものは登録）

**実装例**:
```python
async def add_items_bulk(
    self,
    client: Client,
    user_id: str,
    items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """在庫にアイテムを一括追加"""
    try:
        self.logger.info(f"📦 [CRUD] Adding {len(items)} items in bulk")
        
        if not items:
            return {
                "success": False,
                "total": 0,
                "success_count": 0,
                "error_count": 0,
                "errors": [{"error": "アイテムリストが空です"}]
            }
        
        # データ準備
        data_list = []
        for item in items:
            data = {
                "user_id": user_id,
                "item_name": item.get("item_name"),
                "quantity": item.get("quantity"),
                "unit": item.get("unit", "個"),
                "storage_location": item.get("storage_location", "冷蔵庫")
            }
            
            if item.get("expiry_date"):
                data["expiry_date"] = item["expiry_date"]
            
            data_list.append(data)
        
        # 一括挿入
        try:
            result = client.table("inventory").insert(data_list).execute()
            
            if result.data:
                success_count = len(result.data)
                self.logger.info(f"✅ [CRUD] {success_count} items added successfully")
                return {
                    "success": True,
                    "total": len(items),
                    "success_count": success_count,
                    "error_count": 0,
                    "errors": []
                }
            else:
                raise Exception("No data returned from insert")
                
        except Exception as db_error:
            # DBエラーの場合、個別に処理を試みる
            self.logger.warning(f"⚠️ [CRUD] Bulk insert failed, trying individual inserts: {db_error}")
            return await self._add_items_individually(client, user_id, items)
                
    except Exception as e:
        self.logger.error(f"❌ [CRUD] Failed to add items in bulk: {e}")
        return {
            "success": False,
            "total": len(items) if items else 0,
            "success_count": 0,
            "error_count": len(items) if items else 0,
            "errors": [{"error": str(e)}]
        }

async def _add_items_individually(
    self,
    client: Client,
    user_id: str,
    items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """個別にアイテムを追加（フォールバック）"""
    success_count = 0
    errors = []
    
    for idx, item in enumerate(items, 1):
        try:
            result = await self.add_item(
                client=client,
                user_id=user_id,
                item_name=item.get("item_name"),
                quantity=item.get("quantity"),
                unit=item.get("unit", "個"),
                storage_location=item.get("storage_location", "冷蔵庫"),
                expiry_date=item.get("expiry_date")
            )
            
            if result.get("success"):
                success_count += 1
            else:
                errors.append({
                    "row": idx,
                    "item_name": item.get("item_name"),
                    "error": result.get("error", "Unknown error")
                })
        except Exception as e:
            errors.append({
                "row": idx,
                "item_name": item.get("item_name"),
                "error": str(e)
            })
    
    return {
        "success": success_count > 0,
        "total": len(items),
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors
    }
```

### 1.2 CSV解析処理

**場所**: `api/routes/inventory.py`

**処理フロー**:
1. ファイル受信（`UploadFile`）
2. CSV解析（`pandas.read_csv`または標準`csv`モジュール）
3. データバリデーション
4. `InventoryCRUD.add_items_bulk`を呼び出し

**バリデーションルール**:
- `item_name`: 必須、1-100文字
- `quantity`: 必須、数値、0より大きい
- `unit`: 必須、1-20文字
- `storage_location`: オプション、最大50文字
- `expiry_date`: オプション、YYYY-MM-DD形式

**実装例**:
```python
@router.post("/inventory/upload-csv", response_model=CSVUploadResponse)
async def upload_csv_inventory(
    file: UploadFile = File(...),
    http_request: Request = None
):
    """CSVファイルから在庫データを一括登録"""
    try:
        logger.info(f"🔍 [API] CSV upload request received: {file.filename}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        
        # 2. ファイル検証
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="CSVファイルのみアップロード可能です")
        
        # ファイルサイズチェック（10MB制限）
        file_content = await file.read()
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="ファイルサイズは10MB以下にしてください")
        
        # 3. CSV解析
        import csv
        import io
        from datetime import datetime
        
        # エンコーディング検出（UTF-8/BOM付き対応）
        try:
            text = file_content.decode('utf-8-sig')
        except:
            text = file_content.decode('utf-8')
        
        csv_reader = csv.DictReader(io.StringIO(text))
        
        # 4. データバリデーションと変換
        items = []
        validation_errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # ヘッダー行を除くため2から開始
            try:
                # 必須項目チェック
                if not row.get('item_name') or not row.get('item_name').strip():
                    validation_errors.append({
                        "row": row_num,
                        "item_name": row.get('item_name', ''),
                        "error": "アイテム名は必須です"
                    })
                    continue
                
                if not row.get('quantity'):
                    validation_errors.append({
                        "row": row_num,
                        "item_name": row.get('item_name', ''),
                        "error": "数量は必須です"
                    })
                    continue
                
                # 数量の型変換と検証
                try:
                    quantity = float(row['quantity'])
                    if quantity <= 0:
                        validation_errors.append({
                            "row": row_num,
                            "item_name": row.get('item_name', ''),
                            "error": "数量は0より大きい値が必要です"
                        })
                        continue
                except ValueError:
                    validation_errors.append({
                        "row": row_num,
                        "item_name": row.get('item_name', ''),
                        "error": "数量は数値である必要があります"
                    })
                    continue
                
                # アイテム名の長さチェック
                item_name = row['item_name'].strip()
                if len(item_name) > 100:
                    validation_errors.append({
                        "row": row_num,
                        "item_name": item_name,
                        "error": "アイテム名は100文字以下である必要があります"
                    })
                    continue
                
                # 単位の検証
                unit = row.get('unit', '個').strip()
                if len(unit) > 20:
                    validation_errors.append({
                        "row": row_num,
                        "item_name": item_name,
                        "error": "単位は20文字以下である必要があります"
                    })
                    continue
                
                # 保管場所の検証
                storage_location = row.get('storage_location', '冷蔵庫').strip()
                if storage_location and len(storage_location) > 50:
                    validation_errors.append({
                        "row": row_num,
                        "item_name": item_name,
                        "error": "保管場所は50文字以下である必要があります"
                    })
                    continue
                
                # 消費期限の検証
                expiry_date = row.get('expiry_date', '').strip()
                if expiry_date:
                    try:
                        datetime.strptime(expiry_date, '%Y-%m-%d')
                    except ValueError:
                        validation_errors.append({
                            "row": row_num,
                            "item_name": item_name,
                            "error": "消費期限はYYYY-MM-DD形式である必要があります"
                        })
                        continue
                
                # バリデーション通過
                items.append({
                    "item_name": item_name,
                    "quantity": quantity,
                    "unit": unit,
                    "storage_location": storage_location if storage_location else "冷蔵庫",
                    "expiry_date": expiry_date if expiry_date else None
                })
                
            except Exception as e:
                validation_errors.append({
                    "row": row_num,
                    "item_name": row.get('item_name', ''),
                    "error": f"データ処理エラー: {str(e)}"
                })
        
        # 5. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 6. 一括登録
        crud = InventoryCRUD()
        result = await crud.add_items_bulk(client, user_id, items)
        
        # バリデーションエラーとDBエラーを統合
        total_errors = validation_errors + result.get("errors", [])
        
        return {
            "success": result.get("success", False) and len(validation_errors) == 0,
            "total": len(items) + len(validation_errors),
            "success_count": result.get("success_count", 0),
            "error_count": len(total_errors),
            "errors": total_errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in upload_csv_inventory: {e}")
        raise HTTPException(status_code=500, detail="CSVアップロード処理でエラーが発生しました")
```

### 1.3 レスポンスモデルの追加

**場所**: `api/models/requests.py`

**追加内容**:
```python
class CSVUploadError(BaseModel):
    """CSVアップロードエラー情報"""
    row: int = Field(..., description="行番号")
    item_name: Optional[str] = Field(None, description="アイテム名")
    error: str = Field(..., description="エラーメッセージ")


class CSVUploadResponse(BaseModel):
    """CSVアップロードレスポンス"""
    success: bool = Field(..., description="成功したかどうか")
    total: int = Field(..., description="総件数")
    success_count: int = Field(..., description="成功件数")
    error_count: int = Field(..., description="エラー件数")
    errors: List[CSVUploadError] = Field(default_factory=list, description="エラー詳細")
```

### 1.4 エラーハンドリング

**エラーケース**:
- ファイル形式エラー（CSVでない）
- 必須項目の欠損
- データ型エラー（数量が数値でない等）
- DB挿入エラー（重複、制約違反等）

**エラー報告**:
- 行番号、項目名、エラーメッセージを含む詳細なエラー情報を返却

## 🧪 テスト

### テストファイル

**場所**: `tests/test_inventory_csv_upload.py`

### テスト内容

#### 1. 正常系テスト

**テストケース**: `test_csv_upload_success`

正常なCSVファイルをアップロードし、在庫データが正しく登録されることを確認。

```python
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
            if hasattr(e.response, 'text'):
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
# その後、テストを実行

python tests/test_inventory_csv_upload.py
```

### テスト項目

- [x] CSVファイルのアップロード
- [x] 正常データの一括登録
- [x] エラーデータの検出と報告
- [x] 部分成功の処理
- [x] 空ファイルの処理

## 📊 成功基準

- [ ] CSVファイルから在庫データを一括登録できる
- [ ] エラーデータを検出して報告できる
- [ ] 部分成功を処理できる
- [ ] テストがすべて成功する

## 🔄 実装順序

1. `InventoryCRUD.add_items_bulk`メソッドの実装
2. レスポンスモデルの追加（`api/models/requests.py`）
3. `POST /api/inventory/upload-csv`エンドポイントの実装
4. テストファイルの作成と実行
5. 不具合修正

