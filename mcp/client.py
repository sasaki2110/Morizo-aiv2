"""
Morizo AI v2 - MCP Client

This module provides the MCP client for tool communication with authentication.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()


class MCPClient:
    """MCPクライアント（認証機能付き）"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.logger = GenericLogger("mcp", "client")
        
        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        
        self._client: Optional[Client] = None
    
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
            self.logger.info(f"🔐 [MCP] Token verification: {'Valid' if is_valid else 'Invalid'}")
            return is_valid
        except Exception as e:
            self.logger.error(f"❌ [MCP] Token verification failed: {e}")
            return False
    
    def get_authenticated_client(self, token: str) -> Client:
        """認証済みのSupabaseクライアントを取得"""
        if not self.verify_auth_token(token):
            raise ValueError("Invalid authentication token")
        
        client = self.get_supabase_client()
        client.auth.set_session(token)
        self.logger.info("🔐 [MCP] Authenticated client created")
        return client
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """MCPツールを呼び出し"""
        self.logger.info(f"🔧 [MCP] Calling tool: {tool_name}")
        self.logger.debug(f"📝 [MCP] Parameters: {parameters}")
        
        try:
            # 認証確認
            if not self.verify_auth_token(token):
                raise ValueError("Authentication failed")
            
            # ツール呼び出し（各MCPツールに委譲）
            result = self._execute_tool(tool_name, parameters, token)
            
            self.logger.info(f"✅ [MCP] Tool {tool_name} completed successfully")
            self.logger.debug(f"📊 [MCP] Result: {result}")
            
            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
            
        except Exception as e:
            self.logger.error(f"❌ [MCP] Tool {tool_name} failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any], token: str) -> Any:
        """ツール実行の実装（各MCPツールに委譲）"""
        # ツール名に基づいて適切なMCPツールを呼び出し
        if tool_name.startswith("inventory_"):
            from .inventory_mcp import InventoryMCP
            mcp = InventoryMCP()
            return mcp.execute(tool_name, parameters, token)
        
        elif tool_name.startswith("recipe_history_"):
            from .recipe_history_mcp import RecipeHistoryMCP
            mcp = RecipeHistoryMCP()
            return mcp.execute(tool_name, parameters, token)
        
        elif tool_name.startswith("recipe_"):
            from .recipe_mcp import RecipeMCP
            mcp = RecipeMCP()
            return mcp.execute(tool_name, parameters, token)
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")


if __name__ == "__main__":
    # テスト実行
    print("🧪 Testing MCP Client...")
    
    try:
        client = MCPClient()
        print("✅ MCP Client created successfully")
        
        # テスト用のトークン（実際のテストでは認証ユーティリティを使用）
        test_token = "test_token"
        
        # 認証テスト
        is_valid = client.verify_auth_token(test_token)
        print(f"🔐 Token verification: {'Valid' if is_valid else 'Invalid'}")
        
        print("🎉 MCP Client test completed!")
        
    except Exception as e:
        print(f"❌ MCP Client test failed: {e}")
