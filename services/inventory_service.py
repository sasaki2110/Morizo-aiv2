#!/usr/bin/env python3
"""
InventoryService - 在庫管理サービス

在庫管理のビジネスロジックを提供
ToolRouter経由でMCPツールを呼び出し
"""

from typing import Dict, Any, List, Optional
from .tool_router import ToolRouter
from config.loggers import GenericLogger


class InventoryService:
    """在庫管理サービス"""
    
    def __init__(self, tool_router: ToolRouter):
        """初期化"""
        self.tool_router = tool_router
        self.logger = GenericLogger("service", "inventory")
    
    async def add_inventory(
        self, 
        user_id: str, 
        item_name: str,
        quantity: float,
        unit: str = "個",
        storage_location: str = "冷蔵庫",
        expiry_date: Optional[str] = None,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        在庫を追加
        
        Args:
            user_id: ユーザーID
            item_name: アイテム名
            quantity: 数量
            unit: 単位
            storage_location: 保管場所
            expiry_date: 賞味期限
            token: 認証トークン
        
        Returns:
            追加結果
        """
        try:
            self.logger.info(f"🔧 [InventoryService] Adding inventory for user: {user_id}, item: {item_name}")
            
            # ToolRouter経由でInventoryMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "inventory_add",
                {
                    "user_id": user_id,
                    "item_name": item_name,
                    "quantity": quantity,
                    "unit": unit,
                    "storage_location": storage_location,
                    "expiry_date": expiry_date
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [InventoryService] Inventory added successfully")
            else:
                self.logger.error(f"❌ [InventoryService] Inventory addition failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [InventoryService] Error in add_inventory: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_inventory(
        self, 
        user_id: str,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        在庫一覧を取得
        
        Args:
            user_id: ユーザーID
            token: 認証トークン
        
        Returns:
            在庫一覧
        """
        try:
            self.logger.info(f"🔧 [InventoryService] Getting inventory for user: {user_id}")
            
            # ToolRouter経由でInventoryMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "inventory_list",
                {"user_id": user_id},
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [InventoryService] Inventory retrieved successfully")
            else:
                self.logger.error(f"❌ [InventoryService] Inventory retrieval failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [InventoryService] Error in get_inventory: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_inventory_by_name(
        self, 
        user_id: str, 
        item_name: str,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        指定したアイテム名の在庫を取得
        
        Args:
            user_id: ユーザーID
            item_name: アイテム名
            token: 認証トークン
        
        Returns:
            指定アイテムの在庫一覧
        """
        try:
            self.logger.info(f"🔧 [InventoryService] Getting inventory by name for user: {user_id}, item: {item_name}")
            
            # ToolRouter経由でInventoryMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "inventory_list_by_name",
                {
                    "user_id": user_id,
                    "item_name": item_name
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [InventoryService] Inventory by name retrieved successfully")
            else:
                self.logger.error(f"❌ [InventoryService] Inventory by name retrieval failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [InventoryService] Error in get_inventory_by_name: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_inventory_by_id(
        self, 
        user_id: str, 
        item_id: str,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        storage_location: Optional[str] = None,
        expiry_date: Optional[str] = None,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        ID指定での在庫更新
        
        Args:
            user_id: ユーザーID
            item_id: アイテムID
            quantity: 数量
            unit: 単位
            storage_location: 保管場所
            expiry_date: 賞味期限
            token: 認証トークン
        
        Returns:
            更新結果
        """
        try:
            self.logger.info(f"🔧 [InventoryService] Updating inventory by ID for user: {user_id}, item_id: {item_id}")
            
            # ToolRouter経由でInventoryMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "inventory_update_by_id",
                {
                    "user_id": user_id,
                    "item_id": item_id,
                    "quantity": quantity,
                    "unit": unit,
                    "storage_location": storage_location,
                    "expiry_date": expiry_date
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [InventoryService] Inventory updated by ID successfully")
            else:
                self.logger.error(f"❌ [InventoryService] Inventory update by ID failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [InventoryService] Error in update_inventory_by_id: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_inventory_by_id(
        self, 
        user_id: str, 
        item_id: str,
        token: str = ""
    ) -> Dict[str, Any]:
        """
        ID指定での在庫削除
        
        Args:
            user_id: ユーザーID
            item_id: アイテムID
            token: 認証トークン
        
        Returns:
            削除結果
        """
        try:
            self.logger.info(f"🔧 [InventoryService] Deleting inventory by ID for user: {user_id}, item_id: {item_id}")
            
            # ToolRouter経由でInventoryMCPツールを呼び出し
            result = await self.tool_router.route_tool(
                "inventory_delete_by_id",
                {
                    "user_id": user_id,
                    "item_id": item_id
                },
                token
            )
            
            if result.get("success"):
                self.logger.info(f"✅ [InventoryService] Inventory deleted by ID successfully")
            else:
                self.logger.error(f"❌ [InventoryService] Inventory deletion by ID failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [InventoryService] Error in delete_inventory_by_id: {e}")
            return {"success": False, "error": str(e)}
