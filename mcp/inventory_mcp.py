"""
Morizo AI v2 - Inventory MCP Server

This module provides MCP server for inventory management with tool definitions only.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from mcp import mcp

from .inventory_crud import InventoryCRUD
from .inventory_advanced import InventoryAdvanced
from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()

# MCPサーバー初期化
mcp = mcp.MCPServer("inventory-mcp")

# 処理クラスのインスタンス
crud = InventoryCRUD()
advanced = InventoryAdvanced()
logger = GenericLogger("mcp", "inventory_server")


def get_authenticated_client(user_id: str) -> Client:
    """認証済みのSupabaseクライアントを取得"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not all([supabase_url, supabase_key]):
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
    
    client = create_client(supabase_url, supabase_key)
    # 注意: 実際の認証はAPI層で完了済み、user_idでユーザー識別
    return client


# 基本CRUD操作
@mcp.tool()
async def inventory_add(
    user_id: str,
    item_name: str,
    quantity: float,
    unit: str = "個",
    storage_location: str = "冷蔵庫",
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """在庫にアイテムを1件追加（個別在庫法）"""
    client = get_authenticated_client(user_id)
    return await crud.add_item(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_list(user_id: str) -> Dict[str, Any]:
    """ユーザーの全在庫アイテムを取得"""
    client = get_authenticated_client(user_id)
    return await crud.get_all_items(client, user_id)


@mcp.tool()
async def inventory_list_by_name(user_id: str, item_name: str) -> Dict[str, Any]:
    """指定されたアイテム名の在庫一覧を取得"""
    client = get_authenticated_client(user_id)
    return await crud.get_items_by_name(client, user_id, item_name)


@mcp.tool()
async def inventory_get(user_id: str, item_id: str) -> Dict[str, Any]:
    """特定の在庫アイテムを1件取得"""
    client = get_authenticated_client(user_id)
    return await crud.get_item_by_id(client, user_id, item_id)


@mcp.tool()
async def inventory_update_by_id(
    user_id: str,
    item_id: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """ID指定での在庫アイテム1件更新"""
    client = get_authenticated_client(user_id)
    return await crud.update_item_by_id(client, user_id, item_id, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_delete_by_id(user_id: str, item_id: str) -> Dict[str, Any]:
    """ID指定での在庫アイテム1件削除"""
    client = get_authenticated_client(user_id)
    return await crud.delete_item_by_id(client, user_id, item_id)


# 高度な操作
@mcp.tool()
async def inventory_update_by_name(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """名前指定での在庫アイテム一括更新"""
    client = get_authenticated_client(user_id)
    return await advanced.update_by_name(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_update_by_name_oldest(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """名前指定での最古アイテム更新（FIFO原則）"""
    client = get_authenticated_client(user_id)
    return await advanced.update_by_name_oldest(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_update_by_name_latest(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None
) -> Dict[str, Any]:
    """名前指定での最新アイテム更新"""
    client = get_authenticated_client(user_id)
    return await advanced.update_by_name_latest(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_delete_by_name(user_id: str, item_name: str) -> Dict[str, Any]:
    """名前指定での在庫アイテム一括削除"""
    client = get_authenticated_client(user_id)
    return await advanced.delete_by_name(client, user_id, item_name)


@mcp.tool()
async def inventory_delete_by_name_oldest(user_id: str, item_name: str) -> Dict[str, Any]:
    """名前指定での最古アイテム削除（FIFO原則）"""
    client = get_authenticated_client(user_id)
    return await advanced.delete_by_name_oldest(client, user_id, item_name)


@mcp.tool()
async def inventory_delete_by_name_latest(user_id: str, item_name: str) -> Dict[str, Any]:
    """名前指定での最新アイテム削除"""
    client = get_authenticated_client(user_id)
    return await advanced.delete_by_name_latest(client, user_id, item_name)


if __name__ == "__main__":
    logger.info("🚀 Starting Inventory MCP Server")
    mcp.run()
