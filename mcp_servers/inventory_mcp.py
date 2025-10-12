"""
Morizo AI v2 - Inventory MCP Server

This module provides MCP server for inventory management with tool definitions only.
"""

import sys
import os
# プロジェクトルートをPythonのモジュール検索パスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from fastmcp import FastMCP

from mcp_servers.inventory_crud import InventoryCRUD
from mcp_servers.inventory_advanced import InventoryAdvanced
from mcp_servers.utils import get_authenticated_client
from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()

# MCPサーバー初期化
mcp = FastMCP("Inventory MCP Server")

# 処理クラスのインスタンス
crud = InventoryCRUD()
advanced = InventoryAdvanced()
logger = GenericLogger("mcp", "inventory_server", initialize_logging=False)

# 手動でログハンドラーを設定
from config.logging import get_logger
import logging

# ルートロガーを取得してハンドラーを設定
root_logger = logging.getLogger('morizo_ai')
if not root_logger.handlers:
    from config.logging import setup_logging
    setup_logging(initialize=False)  # ローテーションなし

# 基本CRUD操作
@mcp.tool()
async def inventory_add(
    user_id: str,
    item_name: str,
    quantity: float,
    unit: str = "個",
    storage_location: str = "冷蔵庫",
    expiry_date: Optional[str] = None,
    token: str = ""
) -> Dict[str, Any]:
    """在庫にアイテムを1件追加（個別在庫法）"""
    logger.info(f"🔧 [INVENTORY] Starting inventory_add for user: {user_id}, item: {item_name}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [INVENTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.add_item(client, user_id, item_name, quantity, unit, storage_location, expiry_date)
        logger.info(f"✅ [INVENTORY] inventory_add completed successfully")
        logger.debug(f"📊 [INVENTORY] Add result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [INVENTORY] Error in inventory_add: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def inventory_list(user_id: str, token: str = "") -> Dict[str, Any]:
    """ユーザーの全在庫アイテムを取得"""
    logger.info(f"🔧 [INVENTORY] Starting inventory_list for user: {user_id}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [INVENTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.get_all_items(client, user_id)
        logger.info(f"✅ [INVENTORY] inventory_list completed successfully")
        logger.debug(f"📊 [INVENTORY] List result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [INVENTORY] Error in inventory_list: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def inventory_list_by_name(user_id: str, item_name: str, token: str = "") -> Dict[str, Any]:
    """指定したアイテム名の在庫アイテムを取得"""
    logger.info(f"🔧 [INVENTORY] Starting inventory_list_by_name for user: {user_id}, item: {item_name}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [INVENTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.get_items_by_name(client, user_id, item_name)
        logger.info(f"✅ [INVENTORY] inventory_list_by_name completed successfully")
        logger.debug(f"📊 [INVENTORY] List by name result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [INVENTORY] Error in inventory_list_by_name: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def inventory_get(user_id: str, item_id: str, token: str = "") -> Dict[str, Any]:
    """指定したIDの在庫アイテムを取得"""
    logger.info(f"🔧 [INVENTORY] Starting inventory_get for user: {user_id}, item_id: {item_id}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [INVENTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.get_item_by_id(client, user_id, item_id)
        logger.info(f"✅ [INVENTORY] inventory_get completed successfully")
        logger.debug(f"📊 [INVENTORY] Get result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [INVENTORY] Error in inventory_get: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def inventory_update_by_id(
    user_id: str,
    item_id: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    token: str = ""
) -> Dict[str, Any]:
    """指定したIDの在庫アイテムを更新"""
    logger.info(f"🔧 [INVENTORY] Starting inventory_update_by_id for user: {user_id}, item_id: {item_id}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [INVENTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.update_item_by_id(client, user_id, item_id, quantity, unit, storage_location, expiry_date)
        logger.info(f"✅ [INVENTORY] inventory_update_by_id completed successfully")
        logger.debug(f"📊 [INVENTORY] Update by id result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [INVENTORY] Error in inventory_update_by_id: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def inventory_delete_by_id(user_id: str, item_id: str, token: str = "") -> Dict[str, Any]:
    """指定したIDの在庫アイテムを削除"""
    logger.info(f"🔧 [INVENTORY] Starting inventory_delete_by_id for user: {user_id}, item_id: {item_id}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [INVENTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.delete_item_by_id(client, user_id, item_id)
        logger.info(f"✅ [INVENTORY] inventory_delete_by_id completed successfully")
        logger.debug(f"📊 [INVENTORY] Delete by id result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [INVENTORY] Error in inventory_delete_by_id: {e}")
        return {"success": False, "error": str(e)}


# 高度な操作
@mcp.tool()
async def inventory_update_by_name(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    token: str = ""
) -> Dict[str, Any]:
    """名前指定での在庫アイテム一括更新"""
    client = get_authenticated_client(user_id, token)
    return await advanced.update_by_name(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_update_by_name_oldest(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    token: str = ""
) -> Dict[str, Any]:
    """名前指定での最古アイテム更新（FIFO原則）"""
    client = get_authenticated_client(user_id, token)
    return await advanced.update_by_name_oldest(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_update_by_name_latest(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    token: str = ""
) -> Dict[str, Any]:
    """名前指定での最新アイテム更新"""
    client = get_authenticated_client(user_id, token)
    return await advanced.update_by_name_latest(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_update_by_name_with_ambiguity_check(
    user_id: str,
    item_name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    storage_location: Optional[str] = None,
    expiry_date: Optional[str] = None,
    token: str = ""
) -> Dict[str, Any]:
    """名前指定での在庫アイテム更新（曖昧性チェック付き）"""
    client = get_authenticated_client(user_id, token)
    return await crud.update_item_by_name_with_ambiguity_check(client, user_id, item_name, quantity, unit, storage_location, expiry_date)


@mcp.tool()
async def inventory_delete_by_name_with_ambiguity_check(
    user_id: str,
    item_name: str,
    token: str = ""
) -> Dict[str, Any]:
    """名前指定での在庫アイテム削除（曖昧性チェック付き）"""
    client = get_authenticated_client(user_id, token)
    return await crud.delete_item_by_name_with_ambiguity_check(client, user_id, item_name)


@mcp.tool()
async def inventory_delete_by_name(user_id: str, item_name: str, token: str = "") -> Dict[str, Any]:
    """名前指定での在庫アイテム一括削除"""
    client = get_authenticated_client(user_id, token)
    return await advanced.delete_by_name(client, user_id, item_name)


@mcp.tool()
async def inventory_delete_by_name_oldest(user_id: str, item_name: str, token: str = "") -> Dict[str, Any]:
    """名前指定での最古アイテム削除（FIFO原則）"""
    client = get_authenticated_client(user_id, token)
    return await advanced.delete_by_name_oldest(client, user_id, item_name)


@mcp.tool()
async def inventory_delete_by_name_latest(user_id: str, item_name: str, token: str = "") -> Dict[str, Any]:
    """名前指定での最新アイテム削除"""
    client = get_authenticated_client(user_id, token)
    return await advanced.delete_by_name_latest(client, user_id, item_name)


if __name__ == "__main__":
    logger.info("🚀 Starting Inventory MCP Server")
    mcp.run()
