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
    
