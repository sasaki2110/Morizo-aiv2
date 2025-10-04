"""
Morizo AI v2 - Inventory Advanced Operations

This module provides advanced operations for inventory management including batch operations and FIFO logic.
"""

from typing import Dict, Any, List, Optional
from supabase import Client

from config.loggers import GenericLogger


class InventoryAdvanced:
    """在庫管理の高度な操作"""
    
    def __init__(self):
        self.logger = GenericLogger("mcp", "inventory_advanced")
    
    async def update_by_name(
        self, 
        client: Client, 
        user_id: str, 
        item_name: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        storage_location: Optional[str] = None,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """名前指定での在庫アイテム一括更新"""
        try:
            self.logger.info(f"✏️ [ADVANCED] Batch updating items by name: {item_name}")
            
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
            
            # データベース一括更新
            result = client.table("inventory").update(update_data).eq("user_id", user_id).eq("item_name", item_name).execute()
            
            self.logger.info(f"✅ [ADVANCED] Updated {len(result.data)} items")
            return {"success": True, "data": result.data}
            
        except Exception as e:
            self.logger.error(f"❌ [ADVANCED] Failed to batch update items: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_by_name_oldest(
        self, 
        client: Client, 
        user_id: str, 
        item_name: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        storage_location: Optional[str] = None,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """名前指定での最古アイテム更新（FIFO原則）"""
        try:
            self.logger.info(f"✏️ [ADVANCED] Updating oldest item by name: {item_name}")
            
            # 最古のアイテムを取得
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).order("created_at", desc=False).limit(1).execute()
            
            if not result.data:
                return {"success": False, "error": "No items found"}
            
            oldest_item = result.data[0]
            item_id = oldest_item["id"]
            
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
            
            # 最古アイテムを更新
            update_result = client.table("inventory").update(update_data).eq("user_id", user_id).eq("id", item_id).execute()
            
            self.logger.info(f"✅ [ADVANCED] Updated oldest item: {item_id}")
            return {"success": True, "data": update_result.data[0]}
            
        except Exception as e:
            self.logger.error(f"❌ [ADVANCED] Failed to update oldest item: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_by_name_latest(
        self, 
        client: Client, 
        user_id: str, 
        item_name: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        storage_location: Optional[str] = None,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """名前指定での最新アイテム更新"""
        try:
            self.logger.info(f"✏️ [ADVANCED] Updating latest item by name: {item_name}")
            
            # 最新のアイテムを取得
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).order("created_at", desc=True).limit(1).execute()
            
            if not result.data:
                return {"success": False, "error": "No items found"}
            
            latest_item = result.data[0]
            item_id = latest_item["id"]
            
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
            
            # 最新アイテムを更新
            update_result = client.table("inventory").update(update_data).eq("user_id", user_id).eq("id", item_id).execute()
            
            self.logger.info(f"✅ [ADVANCED] Updated latest item: {item_id}")
            return {"success": True, "data": update_result.data[0]}
            
        except Exception as e:
            self.logger.error(f"❌ [ADVANCED] Failed to update latest item: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_by_name(self, client: Client, user_id: str, item_name: str) -> Dict[str, Any]:
        """名前指定での在庫アイテム一括削除"""
        try:
            self.logger.info(f"🗑️ [ADVANCED] Batch deleting items by name: {item_name}")
            
            # 削除対象のアイテムを取得（削除前に確認）
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).execute()
            
            if not result.data:
                return {"success": False, "error": "No items found"}
            
            # 一括削除実行
            delete_result = client.table("inventory").delete().eq("user_id", user_id).eq("item_name", item_name).execute()
            
            self.logger.info(f"✅ [ADVANCED] Deleted {len(delete_result.data)} items")
            return {"success": True, "data": delete_result.data}
            
        except Exception as e:
            self.logger.error(f"❌ [ADVANCED] Failed to batch delete items: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_by_name_oldest(self, client: Client, user_id: str, item_name: str) -> Dict[str, Any]:
        """名前指定での最古アイテム削除（FIFO原則）"""
        try:
            self.logger.info(f"🗑️ [ADVANCED] Deleting oldest item by name: {item_name}")
            
            # 最古のアイテムを取得
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).order("created_at", desc=False).limit(1).execute()
            
            if not result.data:
                return {"success": False, "error": "No items found"}
            
            oldest_item = result.data[0]
            item_id = oldest_item["id"]
            
            # 最古アイテムを削除
            delete_result = client.table("inventory").delete().eq("user_id", user_id).eq("id", item_id).execute()
            
            self.logger.info(f"✅ [ADVANCED] Deleted oldest item: {item_id}")
            return {"success": True, "data": delete_result.data[0]}
            
        except Exception as e:
            self.logger.error(f"❌ [ADVANCED] Failed to delete oldest item: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_by_name_latest(self, client: Client, user_id: str, item_name: str) -> Dict[str, Any]:
        """名前指定での最新アイテム削除"""
        try:
            self.logger.info(f"🗑️ [ADVANCED] Deleting latest item by name: {item_name}")
            
            # 最新のアイテムを取得
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).order("created_at", desc=True).limit(1).execute()
            
            if not result.data:
                return {"success": False, "error": "No items found"}
            
            latest_item = result.data[0]
            item_id = latest_item["id"]
            
            # 最新アイテムを削除
            delete_result = client.table("inventory").delete().eq("user_id", user_id).eq("id", item_id).execute()
            
            self.logger.info(f"✅ [ADVANCED] Deleted latest item: {item_id}")
            return {"success": True, "data": delete_result.data[0]}
            
        except Exception as e:
            self.logger.error(f"❌ [ADVANCED] Failed to delete latest item: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("✅ Inventory Advanced module loaded successfully")
