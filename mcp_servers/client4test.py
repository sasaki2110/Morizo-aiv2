"""
MCPClient4test - 疎通確認用のFastMCPクライアント
将来的には05_SERVICE_LAYER.mdの設計思想に従って実装予定
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from fastmcp import FastMCP

from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()


class MCPClient4test:
    """疎通確認用のFastMCPクライアント"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.logger = GenericLogger("mcp", "client4test")
        
        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        
        self._client: Optional[Client] = None
        
        # FastMCPクライアントの初期化
        self.mcp_client = FastMCP("Test Client")
        
        # 各FastMCPサーバーへの接続設定
        self.servers = {
            "inventory": "mcp_servers/inventory_mcp.py",
            "recipe": "mcp_servers/recipe_mcp.py",
            "recipe_history": "mcp_servers/recipe_history_mcp.py"
        }
        
        # ツール名とMCPサーバーの対応表
        self.tool_server_mapping = {
            "inventory_add": "inventory",
            "inventory_list": "inventory",
            "inventory_list_by_name": "inventory",
            "inventory_get": "inventory",
            "inventory_update_by_id": "inventory",
            "inventory_delete_by_id": "inventory",
            "generate_menu_plan_with_history": "recipe",
            "generate_menu_with_llm_constraints": "recipe",
            "get_recipe_history_for_user": "recipe",
            "search_recipe_from_web": "recipe",
            "history_add": "recipe_history",
            "history_list": "recipe_history",
            "history_update_by_id": "recipe_history",
            "history_delete_by_id": "recipe_history",
        }
    
    def get_supabase_client(self) -> Client:
        """Supabaseクライアントを取得"""
        if self._client is None:
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client
    
    def verify_auth_token(self, token: str) -> bool:
        """認証トークンを検証"""
        try:
            client = self.get_supabase_client()
            user = client.auth.get_user(token)
            is_valid = user is not None
            self.logger.info(f"🔐 [MCP4test] Token verification: {'Valid' if is_valid else 'Invalid'}")
            return is_valid
        except Exception as e:
            self.logger.error(f"❌ [MCP4test] Token verification failed: {e}")
            return False
    
    def get_authenticated_client(self, token: str) -> Client:
        """認証済みのSupabaseクライアントを取得"""
        if not self.verify_auth_token(token):
            raise ValueError("Invalid authentication token")
        
        client = self.get_supabase_client()
        client.auth.set_session(token)
        self.logger.info("🔐 [MCP4test] Authenticated client created")
        return client
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """FastMCPクライアントでツールを呼び出し"""
        self.logger.info(f"🔧 [MCP4test] Calling tool: {tool_name}")
        self.logger.debug(f"📝 [MCP4test] Parameters: {parameters}")
        
        try:
            # 認証確認
            if not self.verify_auth_token(token):
                raise ValueError("Authentication failed")
            
            # ツール名から適切なサーバーを特定
            server_name = self.tool_server_mapping.get(tool_name)
            if not server_name:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # FastMCPサーバーに接続してツールを呼び出し
            server_path = self.servers[server_name]
            result = await self.mcp_client.call_tool(server_path, tool_name, parameters)
            
            self.logger.info(f"✅ [MCP4test] Tool {tool_name} completed successfully")
            self.logger.debug(f"📊 [MCP4test] Result: {result}")
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
            
        except Exception as e:
            self.logger.error(f"❌ [MCP4test] Tool {tool_name} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.logger.info("🔧 [MCP4test] MCPクライアントのクリーンアップ")
        # 必要に応じてリソースのクリーンアップ処理を追加
        pass


# テスト実行
if __name__ == "__main__":
    print("🧪 Testing MCPClient4test...")
    
    try:
        client = MCPClient4test()
        print("✅ MCPClient4test created successfully")
        
        # テスト用のトークン（実際のテストでは認証ユーティリティを使用）
        test_token = "test_token"
        
        # 認証テスト
        is_valid = client.verify_auth_token(test_token)
        print(f"🔐 Token verification: {'Valid' if is_valid else 'Invalid'}")
        
        print("🎉 MCPClient4test test completed!")
        
    except Exception as e:
        print(f"❌ MCPClient4test test failed: {e}")
