#!/usr/bin/env python3
"""
API層 - 在庫ルート

在庫管理のエンドポイント（一覧取得、CRUD操作）
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from typing import Dict, Any, Optional
from config.loggers import GenericLogger
from ..models import InventoryResponse, InventoryListResponse, InventoryItemResponse, InventoryRequest, CSVUploadResponse
from mcp_servers.inventory_crud import InventoryCRUD
from mcp_servers.utils import get_authenticated_client

router = APIRouter()
logger = GenericLogger("api", "inventory")


@router.get("/inventory/list", response_model=InventoryListResponse)
async def get_inventory_list(
    http_request: Request,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc"
):
    """在庫一覧を取得するエンドポイント
    
    Args:
        sort_by: ソート対象カラム (item_name, quantity, created_at, storage_location, expiry_date)
        sort_order: ソート順序 (asc, desc)
    """
    try:
        logger.info(f"🔍 [API] Inventory list request received: sort_by={sort_by}, sort_order={sort_order}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 2. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 3. CRUDクラスを使用して在庫一覧を取得
        # 【特例】直接DB呼び出しは設計思想に反するが、在庫ビューアーは例外とする
        # CRUD操作のためにLLM→MCP経由は重いため、パフォーマンス重視で直接呼び出し
        crud = InventoryCRUD()
        result = await crud.get_all_items(client, user_id, sort_by=sort_by, sort_order=sort_order)
        
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


@router.post("/inventory/add", response_model=InventoryItemResponse)
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
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 2. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 3. CRUDクラスを使用して在庫を追加
        # 【特例】直接DB呼び出しは設計思想に反するが、在庫ビューアーは例外とする
        # CRUD操作のためにLLM→MCP経由は重いため、パフォーマンス重視で直接呼び出し
        crud = InventoryCRUD()
        result = await crud.add_item(
            client=client,
            user_id=user_id,
            item_name=request.item_name,
            quantity=request.quantity,
            unit=request.unit,
            storage_location=request.storage_location,
            expiry_date=request.expiry_date
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


@router.put("/inventory/update/{item_id}", response_model=InventoryItemResponse)
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
        
        # 2. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 3. CRUDクラスを使用して在庫を更新
        # 【特例】直接DB呼び出しは設計思想に反するが、在庫ビューアーは例外とする
        # CRUD操作のためにLLM→MCP経由は重いため、パフォーマンス重視で直接呼び出し
        crud = InventoryCRUD()
        result = await crud.update_item_by_id(
            client=client,
            user_id=user_id,
            item_id=item_id,
            quantity=request.quantity,
            unit=request.unit,
            storage_location=request.storage_location,
            expiry_date=request.expiry_date
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
        
        # 2. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 3. CRUDクラスを使用して在庫を削除
        # 【特例】直接DB呼び出しは設計思想に反するが、在庫ビューアーは例外とする
        # CRUD操作のためにLLM→MCP経由は重いため、パフォーマンス重視で直接呼び出し
        crud = InventoryCRUD()
        result = await crud.delete_item_by_id(client, user_id, item_id)
        
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

