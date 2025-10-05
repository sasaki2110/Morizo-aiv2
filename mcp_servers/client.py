"""
Morizo AI v2 - MCP Client

This module provides the MCP client for tool communication with authentication.

TODO: 05_SERVICE_LAYER.mdの設計思想に従って実装予定
- ルーティング情報の一元管理
- 統一インターフェースの提供
- 処理の振り分け
- FastMCPサーバーとの通信

現在は疎通確認用のFastMCPクライアント（MCPClient4test）を使用
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()


class MCPClient:
    """
    MCPクライアント（認証機能付き）
    
    TODO: 05_SERVICE_LAYER.mdの設計思想に従って実装予定
    - サービスロケータ/ルータとしての役割
    - ルーティング情報の一元管理
    - 統一インターフェースの提供
    - 処理の振り分け
    - FastMCPサーバーとの通信
    
    現在は疎通確認用のFastMCPクライアント（MCPClient4test）を使用
    """
    
    def __init__(self):
        # 現在は疎通確認用のFastMCPクライアント（MCPClient4test）を使用
        from mcp_servers.client4test import MCPClient4test
        self.test_client = MCPClient4test()
        self.logger = GenericLogger("mcp", "client")
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any], token: str) -> Dict[str, Any]:
        """統一インターフェースでツールを呼び出し"""
        # 現在は疎通確認用のFastMCPクライアント（MCPClient4test）に委譲
        return await self.test_client.call_tool(tool_name, parameters, token)
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self.logger.info("🔧 [MCP] MCPクライアントのクリーンアップ")
        # FastMCPクライアント（MCPClient4test）のクリーンアップも実行
        self.test_client.cleanup()


# テスト実行
if __name__ == "__main__":
    print("🧪 Testing MCP Client...")
    
    try:
        client = MCPClient()
        print("✅ MCP Client created successfully")
        
        # テスト用のトークン（実際のテストでは認証ユーティリティを使用）
        test_token = "test_token"
        
        # 認証テスト
        is_valid = client.test_client.verify_auth_token(test_token)
        print(f"🔐 Token verification: {'Valid' if is_valid else 'Invalid'}")
        
        print("🎉 MCP Client test completed!")
        
    except Exception as e:
        print(f"❌ MCP Client test failed: {e}")
