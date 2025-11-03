# Phase 1-1: 在庫一覧表示 - バックエンド実装

## 概要

在庫一覧を取得するバックエンドAPIエンドポイントを実装します。
一覧表示に必要な最小限の機能のみを実装します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**参考実装**: Phase 5C-1 履歴取得API実装

## 対象範囲

### バックエンド
- `/app/Morizo-aiv2/api/routes/inventory.py` (新規作成 - 一覧取得のみ)
- `/app/Morizo-aiv2/api/models/responses.py` (拡張 - InventoryListResponse追加)
- `/app/Morizo-aiv2/api/routes/__init__.py` またはメインアプリケーション (ルーター登録)

## 実装計画

### 1. 在庫ルートファイルの作成（一覧取得のみ）

**修正する場所**: `/app/Morizo-aiv2/api/routes/inventory.py` (新規作成)

**実装内容**:

```python
#!/usr/bin/env python3
"""
API層 - 在庫ルート

在庫管理のエンドポイント（一覧取得のみ）
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
from config.loggers import GenericLogger
from ..models import InventoryResponse, InventoryListResponse
from mcp_servers.inventory_mcp import inventory_list

router = APIRouter()
logger = GenericLogger("api", "inventory")


@router.get("/inventory/list", response_model=InventoryListResponse)
async def get_inventory_list(http_request: Request):
    """在庫一覧を取得するエンドポイント"""
    try:
        logger.info("🔍 [API] Inventory list request received")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 2. MCPツール経由で在庫一覧を取得
        result = await inventory_list(user_id, token)
        
        if not result.get("success"):
            logger.error(f"❌ [API] Failed to get inventory list: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get("error", "在庫取得処理でエラーが発生しました"))
        
        logger.info(f"✅ [API] Retrieved {len(result.get('data', []))} inventory items")
        
        return {
            "success": True,
            "data": result.get("data", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in get_inventory_list: {e}")
        raise HTTPException(status_code=500, detail="在庫取得処理でエラーが発生しました")
```

**修正の理由**:
- フロントエンドから直接在庫データを取得できるようにする
- 履歴ビューアー（`/api/menu/history`）と同様のAPIパターンに統一
- 一覧表示に必要な最小限の機能のみを実装

**修正の影響**:
- 新規ファイルのみ追加（既存機能への影響なし）
- ルーター登録が必要（後述）

---

### 2. レスポンスモデルの拡張

**修正する場所**: `/app/Morizo-aiv2/api/models/responses.py`

**修正内容**:

```python
from typing import List

class InventoryListResponse(BaseModel):
    """在庫一覧レスポンス"""
    success: bool = Field(..., description="成功フラグ")
    data: List[InventoryResponse] = Field(..., description="在庫アイテムリスト")
```

**修正の理由**:
- 在庫一覧取得APIのレスポンス形式を定義
- 既存の`InventoryResponse`を再利用

**修正の影響**:
- 既存の`InventoryResponse`は変更なし（拡張のみ）

---

### 3. ルーターの登録

**修正する場所**: `/app/Morizo-aiv2/api/routes/__init__.py` またはメインアプリケーション

**修正内容**:
- `inventory`ルーターをアプリケーションに登録

**修正の理由**:
- 新規ルートをAPIとして利用可能にする

**修正の影響**:
- 既存ルートへの影響なし

---

## 実装のポイント

### 1. 認証処理

- 既存の認証パターン（`menu.py`と同様）を使用
- `user_info`を`request.state`から取得
- JWTトークンを`Authorization`ヘッダーから取得

### 2. MCPツールの呼び出し

- 既存の`inventory_list`MCPツールを呼び出し
- エラーハンドリングを適切に実装

### 3. エラーハンドリング

- 認証エラー（401）
- MCPツール呼び出しエラー（500）
- 予期しないエラー（500）

## テスト項目

### 単体テスト

1. **APIエンドポイント `/api/inventory/list`**
   - 正常系: 在庫一覧の取得
   - 認証エラー: 認証なしでアクセスした場合
   - 空の在庫: 在庫が0件の場合
   - エラーハンドリング: MCPツール呼び出し失敗時の処理

### 統合テスト

1. **バックエンド ↔ MCPツール連携**
   - MCPツール呼び出しが正しく動作すること
   - レスポンスが正しい形式であること

2. **認証統合**
   - 認証済みユーザーのみアクセス可能であること
   - ユーザーIDが正しく取得できること

## 期待される効果

- フロントエンドから在庫一覧を取得できるようになる
- Phase 1-2（フロントエンド）の実装基盤が整う

## 実装順序

1. レスポンスモデルの拡張
2. 在庫ルートファイルの作成
3. ルーターの登録

## 次のフェーズ

- **Phase 1-2**: フロントエンドでの一覧表示実装

