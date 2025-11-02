#!/usr/bin/env python3
"""
API層 - 在庫ルート

在庫管理のエンドポイント（一覧取得のみ）
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional
from config.loggers import GenericLogger
from ..models import InventoryResponse, InventoryListResponse
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
        # 注意: 直接DB呼び出しは設計思想に反するが、在庫ビューアーは例外とする
        # (CRUD操作のためにLLM→MCP経由は重いため、パフォーマンス重視で直接呼び出し)
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

