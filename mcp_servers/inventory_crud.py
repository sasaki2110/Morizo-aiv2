"""
Morizo AI v2 - Inventory CRUD Operations

This module provides basic CRUD operations for inventory management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import Client

from config.loggers import GenericLogger


class InventoryCRUD:
    """在庫管理の基本CRUD操作"""
    
    def __init__(self):
        self.logger = GenericLogger("mcp", "inventory_crud", initialize_logging=False)
    
    async def add_item(
        self, 
        client: Client, 
        user_id: str, 
        item_name: str, 
        quantity: float, 
        unit: str = "個",
        storage_location: str = "冷蔵庫",
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """在庫にアイテムを1件追加"""
        try:
            self.logger.info(f"📦 [CRUD] Adding item: {item_name} ({quantity}{unit})")
            
            # データ準備
            data = {
                "user_id": user_id,
                "item_name": item_name,
                "quantity": quantity,
                "unit": unit,
                "storage_location": storage_location
            }
            
            if expiry_date:
                data["expiry_date"] = expiry_date
            
            # データベースに挿入
            result = client.table("inventory").insert(data).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Item added successfully: {result.data[0]['id']}")
                return {"success": True, "data": result.data[0]}
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to add item: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_all_items(self, client: Client, user_id: str) -> Dict[str, Any]:
        """ユーザーの全在庫アイテムを取得"""
        try:
            self.logger.info(f"📋 [CRUD] Getting all items for user: {user_id}")
            
            result = client.table("inventory").select("*").eq("user_id", user_id).execute()
            
            self.logger.info(f"✅ [CRUD] Retrieved {len(result.data)} items")
            return {"success": True, "data": result.data}
            
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to get items: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_items_by_name(self, client: Client, user_id: str, item_name: str) -> Dict[str, Any]:
        """指定されたアイテム名の在庫一覧を取得"""
        try:
            self.logger.info(f"🔍 [CRUD] Getting items by name: {item_name}")
            
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).execute()
            
            self.logger.info(f"✅ [CRUD] Retrieved {len(result.data)} items")
            return {"success": True, "data": result.data}
            
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to get items by name: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_item_by_id(self, client: Client, user_id: str, item_id: str) -> Dict[str, Any]:
        """特定の在庫アイテムを1件取得"""
        try:
            self.logger.info(f"🔍 [CRUD] Getting item by ID: {item_id}")
            
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("id", item_id).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Item retrieved successfully")
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Item not found"}
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to get item by ID: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_item_by_id(
        self, 
        client: Client, 
        user_id: str, 
        item_id: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        storage_location: Optional[str] = None,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """ID指定での在庫アイテム1件更新"""
        try:
            self.logger.info(f"✏️ [CRUD] Updating item by ID: {item_id}")
            
            # 更新データの準備
            update_data = {}
            if quantity is not None:
                update_data["quantity"] = quantity
            if unit is not None:
                update_data["unit"] = unit
            if storage_location is not None:
                update_data["storage_location"] = storage_location
            if expiry_date is not None:
                update_data["expiry_date"] = expiry_date
            
            if not update_data:
                return {"success": False, "error": "No update data provided"}
            
            # データベース更新
            result = client.table("inventory").update(update_data).eq("user_id", user_id).eq("id", item_id).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Item updated successfully")
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Item not found"}
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to update item by ID: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_item_by_id(self, client: Client, user_id: str, item_id: str) -> Dict[str, Any]:
        """ID指定での在庫アイテム1件削除"""
        try:
            self.logger.info(f"🗑️ [CRUD] Deleting item by ID: {item_id}")
            
            result = client.table("inventory").delete().eq("user_id", user_id).eq("id", item_id).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Item deleted successfully")
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Item not found"}
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to delete item by ID: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("✅ Inventory CRUD module loaded successfully")
