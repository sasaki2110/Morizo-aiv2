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
    
    async def update_item_by_name_with_ambiguity_check(
        self, 
        client: Client, 
        user_id: str, 
        item_name: str, 
        quantity: Optional[int] = None,
        unit: Optional[str] = None,
        storage_location: Optional[str] = None,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """名前指定での在庫アイテム更新（曖昧性チェック付き）"""
        try:
            self.logger.info(f"🔍 [CRUD] Searching items by name for ambiguity check: {item_name}")
            
            # 1. 名前でアイテムを検索
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).execute()
            
            if not result.data:
                return {"success": False, "error": f"Item '{item_name}' not found"}
            
            items = result.data
            
            # 2. 曖昧性チェック
            if len(items) == 1:
                # 1件の場合は直接更新
                item_id = items[0]["id"]
                self.logger.info(f"✅ [CRUD] Single item found, updating directly: {item_id}")
                
                # 更新データを準備
                update_data = {}
                if quantity is not None:
                    update_data["quantity"] = quantity
                if unit is not None:
                    update_data["unit"] = unit
                if storage_location is not None:
                    update_data["storage_location"] = storage_location
                if expiry_date is not None:
                    update_data["expiry_date"] = expiry_date
                
                # 更新実行
                update_result = client.table("inventory").update(update_data).eq("user_id", user_id).eq("id", item_id).execute()
                
                if update_result.data:
                    self.logger.info(f"✅ [CRUD] Item updated successfully")
                    return {"success": True, "data": update_result.data[0]}
                else:
                    return {"success": False, "error": "Update failed"}
            
            else:
                # 複数件の場合は曖昧性エラーを返す
                self.logger.warning(f"⚠️ [CRUD] Multiple items found ({len(items)}), ambiguity detected")
                
                # アイテム情報を整理
                items_info = []
                for item in items:
                    items_info.append({
                        "id": item["id"],
                        "quantity": item["quantity"],
                        "unit": item["unit"],
                        "storage_location": item["storage_location"],
                        "expiry_date": item["expiry_date"],
                        "created_at": item["created_at"]
                    })
                
                return {
                    "success": False,
                    "error": "AMBIGUITY_DETECTED",
                    "message": f"在庫が複数あるため更新できません。最新の、一番古い、全部などを指定し、更新対象を特定して頂きたいです。",
                    "items": items_info,
                    "count": len(items)
                }
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to update item with ambiguity check: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_item_by_name_with_ambiguity_check(
        self, 
        client: Client, 
        user_id: str, 
        item_name: str
    ) -> Dict[str, Any]:
        """名前指定での在庫アイテム削除（曖昧性チェック付き）"""
        try:
            self.logger.info(f"🔍 [CRUD] Searching items by name for ambiguity check: {item_name}")
            
            # 1. 名前でアイテムを検索
            result = client.table("inventory").select("*").eq("user_id", user_id).eq("item_name", item_name).execute()
            
            if not result.data:
                return {"success": False, "error": "No items found"}
            
            items = result.data
            
            if len(items) == 1:
                # 2. 1件のみの場合は直接削除
                item_id = items[0]["id"]
                delete_result = client.table("inventory").delete().eq("user_id", user_id).eq("id", item_id).execute()
                
                self.logger.info(f"✅ [CRUD] Single item deleted: {item_id}")
                return {"success": True, "data": delete_result.data[0]}
            else:
                # 3. 複数件の場合は曖昧性エラー
                items_info = []
                for item in items:
                    items_info.append({
                        "id": item["id"],
                        "item_name": item["item_name"],
                        "quantity": item["quantity"],
                        "unit": item["unit"],
                        "storage_location": item["storage_location"],
                        "expiry_date": item["expiry_date"],
                        "created_at": item["created_at"]
                    })
                
                return {
                    "success": False,
                    "status": "ambiguity_detected",
                    "error": "AMBIGUITY_DETECTED",
                    "message": f"在庫が複数あるため削除できません。最新の、一番古い、全部などを指定し、削除対象を特定して頂きたいです。",
                    "items": items_info,
                    "count": len(items),
                    "context": {
                        "items": items_info,
                        "count": len(items),
                        "operation": "delete"
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to delete item with ambiguity check: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("✅ Inventory CRUD module loaded successfully")
