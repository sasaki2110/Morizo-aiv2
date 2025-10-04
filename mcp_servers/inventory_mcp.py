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


class InventoryMCP:
    """Inventory MCPクラス（MCPClient用のラッパー）"""
    
    def __init__(self):
        self.crud = InventoryCRUD()
        self.advanced = InventoryAdvanced()
        self.logger = GenericLogger("mcp", "inventory_mcp_class")
    
    async def execute(self, tool_name: str, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """MCPツールを実行"""
        try:
            # 認証済みクライアントを取得（トークン付き）
            client = get_authenticated_client(parameters.get("user_id", ""), token)
            
            # ツール名に基づいて適切なメソッドを呼び出し
            if tool_name == "inventory_add":
                return await self._execute_inventory_add(client, parameters)
            elif tool_name == "inventory_list":
                return await self._execute_inventory_list(client, parameters)
            elif tool_name == "inventory_list_by_name":
                return await self._execute_inventory_list_by_name(client, parameters)
            elif tool_name == "inventory_get":
                return await self._execute_inventory_get(client, parameters)
            elif tool_name == "inventory_update_by_id":
                return await self._execute_inventory_update_by_id(client, parameters)
            elif tool_name == "inventory_delete_by_id":
                return await self._execute_inventory_delete_by_id(client, parameters)
            elif tool_name == "inventory_update_by_name":
                return await self._execute_inventory_update_by_name(client, parameters)
            elif tool_name == "inventory_update_by_name_oldest":
                return await self._execute_inventory_update_by_name_oldest(client, parameters)
            elif tool_name == "inventory_update_by_name_latest":
                return await self._execute_inventory_update_by_name_latest(client, parameters)
            elif tool_name == "inventory_delete_by_name":
                return await self._execute_inventory_delete_by_name(client, parameters)
            elif tool_name == "inventory_delete_by_name_oldest":
                return await self._execute_inventory_delete_by_name_oldest(client, parameters)
            elif tool_name == "inventory_delete_by_name_latest":
                return await self._execute_inventory_delete_by_name_latest(client, parameters)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"❌ [InventoryMCP] Tool {tool_name} failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_inventory_add(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """在庫追加を実行"""
        return await self.crud.add_item(
            client, 
            parameters["user_id"], 
            parameters["item_name"], 
            parameters["quantity"], 
            parameters.get("unit", "個"), 
            parameters.get("storage_location", "冷蔵庫"), 
            parameters.get("expiry_date")
        )
    
    async def _execute_inventory_list(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """在庫一覧取得を実行"""
        return await self.crud.get_all_items(client, parameters["user_id"])
    
    async def _execute_inventory_list_by_name(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定在庫一覧取得を実行"""
        return await self.crud.get_items_by_name(client, parameters["user_id"], parameters["item_name"])
    
    async def _execute_inventory_get(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """在庫アイテム取得を実行"""
        return await self.crud.get_item_by_id(client, parameters["user_id"], parameters["item_id"])
    
    async def _execute_inventory_update_by_id(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """ID指定在庫更新を実行"""
        return await self.crud.update_item_by_id(
            client, 
            parameters["user_id"], 
            parameters["item_id"], 
            parameters.get("quantity"), 
            parameters.get("unit"), 
            parameters.get("storage_location"), 
            parameters.get("expiry_date")
        )
    
    async def _execute_inventory_delete_by_id(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """ID指定在庫削除を実行"""
        return await self.crud.delete_item_by_id(client, parameters["user_id"], parameters["item_id"])
    
    async def _execute_inventory_update_by_name(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定在庫一括更新を実行"""
        return await self.advanced.update_by_name(
            client, 
            parameters["user_id"], 
            parameters["item_name"], 
            parameters.get("quantity"), 
            parameters.get("unit"), 
            parameters.get("storage_location"), 
            parameters.get("expiry_date")
        )
    
    async def _execute_inventory_update_by_name_oldest(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定最古在庫更新を実行"""
        return await self.advanced.update_by_name_oldest(
            client, 
            parameters["user_id"], 
            parameters["item_name"], 
            parameters.get("quantity"), 
            parameters.get("unit"), 
            parameters.get("storage_location"), 
            parameters.get("expiry_date")
        )
    
    async def _execute_inventory_update_by_name_latest(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定最新在庫更新を実行"""
        return await self.advanced.update_by_name_latest(
            client, 
            parameters["user_id"], 
            parameters["item_name"], 
            parameters.get("quantity"), 
            parameters.get("unit"), 
            parameters.get("storage_location"), 
            parameters.get("expiry_date")
        )
    
    async def _execute_inventory_delete_by_name(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定在庫一括削除を実行"""
        return await self.advanced.delete_by_name(client, parameters["user_id"], parameters["item_name"])
    
    async def _execute_inventory_delete_by_name_oldest(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定最古在庫削除を実行"""
        return await self.advanced.delete_by_name_oldest(client, parameters["user_id"], parameters["item_name"])
    
    async def _execute_inventory_delete_by_name_latest(self, client: Client, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """名前指定最新在庫削除を実行"""
        return await self.advanced.delete_by_name_latest(client, parameters["user_id"], parameters["item_name"])


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
