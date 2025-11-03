# Phase 2-1: 在庫CRUD操作 - バックエンド実装

## 概要

在庫アイテムの作成・更新・削除を行うバックエンドAPIエンドポイントを実装します。
Phase 1-1で作成した在庫ルートファイルに、CRUD操作のエンドポイントを追加します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**前提**: Phase 1-1完了

## 対象範囲

### バックエンド
- `/app/Morizo-aiv2/api/routes/inventory.py` (拡張 - CRUD操作エンドポイント追加)
- `/app/Morizo-aiv2/api/models/requests.py` (確認 - InventoryRequestモデルの存在確認)

## 実装計画

### 1. 在庫ルートファイルへのCRUD操作エンドポイント追加

**修正する場所**: `/app/Morizo-aiv2/api/routes/inventory.py` (既存ファイルを拡張)

**実装内容**:

Phase 1-1で作成したファイルに以下のエンドポイントを追加：

```python
from mcp_servers.inventory_mcp import inventory_add, inventory_update_by_id, inventory_delete_by_id
from ..models import InventoryRequest, InventoryResponse

# ... 既存の get_inventory_list 関数 ...

@router.post("/inventory/add", response_model=InventoryResponse)
async def add_inventory_item(request: InventoryRequest, http_request: Request):
    """在庫アイテムを追加するエンドポイント"""
    try:
        logger.info(f"🔍 [API] Inventory add request received: item_name={request.item_name}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        
        # 2. MCPツール経由で在庫を追加
        result = await inventory_add(
            user_id=user_id,
            item_name=request.item_name,
            quantity=request.quantity,
            unit=request.unit,
            storage_location=request.storage_location,
            expiry_date=request.expiry_date,
            token=token
        )
        
        if not result.get("success"):
            logger.error(f"❌ [API] Failed to add inventory: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "在庫追加処理でエラーが発生しました"))
        
        logger.info(f"✅ [API] Inventory item added: {result.get('data', {}).get('id')}")
        
        return {
            "success": True,
            "data": result.get("data")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in add_inventory_item: {e}")
        raise HTTPException(status_code=500, detail="在庫追加処理でエラーが発生しました")


@router.put("/inventory/update/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: str,
    request: InventoryRequest,
    http_request: Request
):
    """在庫アイテムを更新するエンドポイント"""
    try:
        logger.info(f"🔍 [API] Inventory update request received: item_id={item_id}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        
        # 2. MCPツール経由で在庫を更新
        result = await inventory_update_by_id(
            user_id=user_id,
            item_id=item_id,
            quantity=request.quantity,
            unit=request.unit,
            storage_location=request.storage_location,
            expiry_date=request.expiry_date,
            token=token
        )
        
        if not result.get("success"):
            logger.error(f"❌ [API] Failed to update inventory: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "在庫更新処理でエラーが発生しました"))
        
        logger.info(f"✅ [API] Inventory item updated: {item_id}")
        
        return {
            "success": True,
            "data": result.get("data")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in update_inventory_item: {e}")
        raise HTTPException(status_code=500, detail="在庫更新処理でエラーが発生しました")


@router.delete("/inventory/delete/{item_id}")
async def delete_inventory_item(item_id: str, http_request: Request):
    """在庫アイテムを削除するエンドポイント"""
    try:
        logger.info(f"🔍 [API] Inventory delete request received: item_id={item_id}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        
        # 2. MCPツール経由で在庫を削除
        result = await inventory_delete_by_id(user_id, item_id, token)
        
        if not result.get("success"):
            logger.error(f"❌ [API] Failed to delete inventory: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "在庫削除処理でエラーが発生しました"))
        
        logger.info(f"✅ [API] Inventory item deleted: {item_id}")
        
        return {
            "success": True,
            "message": "在庫アイテムを削除しました"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in delete_inventory_item: {e}")
        raise HTTPException(status_code=500, detail="在庫削除処理でエラーが発生しました")
```

**修正の理由**:
- フロントエンドから在庫のCRUD操作を実行できるようにする
- 既存の一覧取得エンドポイントと同様のパターンで実装
- MCPツールを既存の実装に基づいて呼び出し

**修正の影響**:
- 既存の一覧取得エンドポイントには影響なし（拡張のみ）

---

### 2. リクエストモデルの確認

**修正する場所**: `/app/Morizo-aiv2/api/models/requests.py`

**修正内容**:
- `InventoryRequest`モデルが既に存在することを確認
- 必要に応じて、フィールドを確認・修正

**修正の理由**:
- CRUD操作で使用するリクエストモデルが正しく定義されていることを確認

**修正の影響**:
- 既存モデルを確認するのみ（変更なし）

---

## 実装のポイント

### 1. 認証処理

- 既存の認証パターン（一覧取得と同様）を使用
- `user_info`を`request.state`から取得
- JWTトークンを`Authorization`ヘッダーから取得

### 2. MCPツールの呼び出し

- 既存のMCPツール（`inventory_add`, `inventory_update_by_id`, `inventory_delete_by_id`）を呼び出し
- エラーハンドリングを適切に実装

### 3. エラーハンドリング

- 認証エラー（401）
- MCPツール呼び出しエラー（500）
- 予期しないエラー（500）

### 4. ロギング

- 各操作の開始・成功・失敗をログに記録
- デバッグに役立つ情報をログに出力

## テスト項目

### 単体テスト

1. **APIエンドポイント `/api/inventory/add`**
   - 正常系: 在庫アイテムの追加
   - バリデーションエラー: 必須項目未入力
   - 認証エラー: 認証なしでアクセスした場合
   - エラーハンドリング: MCPツール呼び出し失敗時の処理

2. **APIエンドポイント `/api/inventory/update/{item_id}`**
   - 正常系: 在庫アイテムの更新
   - 存在しないID: 存在しないアイテムIDで更新を試みた場合
   - 認証エラー: 認証なしでアクセスした場合
   - エラーハンドリング: MCPツール呼び出し失敗時の処理

3. **APIエンドポイント `/api/inventory/delete/{item_id}`**
   - 正常系: 在庫アイテムの削除
   - 存在しないID: 存在しないアイテムIDで削除を試みた場合
   - 認証エラー: 認証なしでアクセスした場合
   - エラーハンドリング: MCPツール呼び出し失敗時の処理

### 統合テスト

1. **バックエンド ↔ MCPツール連携**
   - MCPツール呼び出しが正しく動作すること
   - レスポンスが正しい形式であること

2. **認証統合**
   - 認証済みユーザーのみアクセス可能であること
   - ユーザーIDが正しく取得できること

3. **エンドツーエンド**
   - 追加 → 一覧取得 → 更新 → 削除 の一連の流れが動作すること

## 期待される効果

- フロントエンドから在庫のCRUD操作を実行できるようになる
- Phase 2-2（フロントエンド）の実装基盤が整う

## 実装順序

1. リクエストモデルの確認
2. 追加エンドポイントの実装
3. 更新エンドポイントの実装
4. 削除エンドポイントの実装

## 次のフェーズ

- **Phase 2-2**: CRUD操作のフロントエンド実装

