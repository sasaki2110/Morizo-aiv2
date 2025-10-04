"""
Morizo AI v2 - Recipe History CRUD Operations

This module provides basic CRUD operations for recipe history management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from supabase import Client

from config.loggers import GenericLogger


class RecipeHistoryCRUD:
    """レシピ履歴管理の基本CRUD操作"""
    
    def __init__(self):
        self.logger = GenericLogger("mcp", "recipe_history_crud", initialize_logging=False)
    
    async def add_history(
        self, 
        client: Client, 
        user_id: str, 
        title: str, 
        source: str,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """レシピ履歴を1件追加"""
        try:
            self.logger.info(f"📝 [CRUD] Adding recipe history: {title}")
            
            # データ準備
            data = {
                "user_id": user_id,
                "title": title,
                "source": source
            }
            
            if url:
                data["url"] = url
            
            # データベースに挿入
            result = client.table("recipe_historys").insert(data).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Recipe history added successfully: {result.data[0]['id']}")
                return {"success": True, "data": result.data[0]}
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to add recipe history: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_all_histories(self, client: Client, user_id: str) -> Dict[str, Any]:
        """ユーザーの全レシピ履歴を取得"""
        try:
            self.logger.info(f"📋 [CRUD] Getting all recipe histories for user: {user_id}")
            
            result = client.table("recipe_historys").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
            
            self.logger.info(f"✅ [CRUD] Retrieved {len(result.data)} recipe histories")
            return {"success": True, "data": result.data}
            
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to get recipe histories: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_history_by_id(self, client: Client, user_id: str, history_id: str) -> Dict[str, Any]:
        """特定のレシピ履歴を1件取得"""
        try:
            self.logger.info(f"🔍 [CRUD] Getting recipe history by ID: {history_id}")
            
            result = client.table("recipe_historys").select("*").eq("user_id", user_id).eq("id", history_id).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Recipe history retrieved successfully")
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Recipe history not found"}
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to get recipe history by ID: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_history_by_id(
        self, 
        client: Client, 
        user_id: str, 
        history_id: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """ID指定でのレシピ履歴1件更新"""
        try:
            self.logger.info(f"✏️ [CRUD] Updating recipe history by ID: {history_id}")
            
            # 更新データの準備
            update_data = {}
            if title is not None:
                update_data["title"] = title
            if source is not None:
                update_data["source"] = source
            if url is not None:
                update_data["url"] = url
            
            if not update_data:
                return {"success": False, "error": "No update data provided"}
            
            # データベース更新
            result = client.table("recipe_historys").update(update_data).eq("user_id", user_id).eq("id", history_id).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Recipe history updated successfully")
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Recipe history not found"}
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to update recipe history by ID: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_history_by_id(self, client: Client, user_id: str, history_id: str) -> Dict[str, Any]:
        """ID指定でのレシピ履歴1件削除"""
        try:
            self.logger.info(f"🗑️ [CRUD] Deleting recipe history by ID: {history_id}")
            
            result = client.table("recipe_historys").delete().eq("user_id", user_id).eq("id", history_id).execute()
            
            if result.data:
                self.logger.info(f"✅ [CRUD] Recipe history deleted successfully")
                return {"success": True, "data": result.data[0]}
            else:
                return {"success": False, "error": "Recipe history not found"}
                
        except Exception as e:
            self.logger.error(f"❌ [CRUD] Failed to delete recipe history by ID: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("✅ Recipe History CRUD module loaded successfully")
