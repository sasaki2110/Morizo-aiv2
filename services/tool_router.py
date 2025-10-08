#!/usr/bin/env python3
"""
ToolRouter - MCPツールの自動ルーティング

サービス層とMCP層を疎結合に保つためのルーティング・統合クライアント
既存のmcp_servers/client.pyを内部で使用し、ツール名からMCPサーバーへの自動ルーティングを提供
"""

from typing import Dict, Any, List, Optional
from mcp_servers.client import MCPClient
from config.loggers import GenericLogger


class ToolNotFoundError(Exception):
    """ツールが見つからない場合の例外"""
    pass


class ToolRouterError(Exception):
    """ToolRouter関連の一般的な例外"""
    pass


class ToolRouter:
    """ツールルータ - MCPツールの自動ルーティング"""
    
    def __init__(self):
        """初期化"""
        # 既存のMCPクライアントを使用
        self.mcp_client = MCPClient()
        
        # MCP Clientのマッピングを参照（重複を排除）
        self.tool_server_mapping = self.mcp_client.tool_server_mapping
        
        # サービス名・メソッド名からMCPツール名へのマッピング
        self.service_method_mapping = {
            # InventoryService のマッピング
            ("inventory_service", "get_inventory"): "inventory_list",
            ("inventory_service", "add_inventory"): "inventory_add",
            ("inventory_service", "update_inventory"): "inventory_update_by_id",  # デフォルトはID指定
            ("inventory_service", "delete_inventory"): "inventory_delete_by_id",  # デフォルトはID指定
            
            # RecipeService のマッピング（修正版）
            ("recipe_service", "generate_menu_plan"): "generate_menu_plan_with_history",
            ("recipe_service", "search_menu_from_rag"): "search_menu_from_rag_with_history",
            ("recipe_service", "search_recipes_from_web"): "search_recipe_from_web",
            ("recipe_service", "get_recipe_history"): "get_recipe_history_for_user",
            
            # 他のサービスのマッピング（必要に応じて追加）
        }
        
        # ロガー設定
        self.logger = GenericLogger("service", "tool_router")
    
    async def route_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        token: str
    ) -> Dict[str, Any]:
        """
        ツールを適切なMCPサーバーにルーティング
        
        Args:
            tool_name: 呼び出すツール名
            parameters: ツールに渡すパラメータ
            token: 認証トークン
        
        Returns:
            ツール実行結果
        """
        try:
            # 1. ツール名の検証
            if not self._is_valid_tool(tool_name):
                raise ToolNotFoundError(f"Unknown tool: {tool_name}")
            
            # 2. ログ出力
            self.logger.info(f"🔧 [ToolRouter] Routing tool: {tool_name}")
            
            # 3. パラメータマッピング処理
            mapped_parameters = self._map_parameters(tool_name, parameters)
            
            # 4. 既存のMCPクライアントに処理を委譲
            result = await self.mcp_client.call_tool(tool_name, mapped_parameters, token)
            
            # 4. 結果の検証とログ
            if result.get("success"):
                self.logger.info(f"✅ [ToolRouter] Tool {tool_name} completed successfully")
            else:
                self.logger.warning(f"⚠️ [ToolRouter] Tool {tool_name} failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [ToolRouter] Tool {tool_name} routing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    async def route_service_method(
        self, 
        service: str, 
        method: str, 
        parameters: Dict[str, Any], 
        token: str
    ) -> Dict[str, Any]:
        """
        サービス名・メソッド名からMCPツールをルーティング
        
        Args:
            service: サービス名（例: "inventory_service"）
            method: メソッド名（例: "get_inventory"）
            parameters: ツールに渡すパラメータ
            token: 認証トークン
        
        Returns:
            ツール実行結果
        """
        try:
            # 1. サービス名・メソッド名からMCPツール名を取得
            tool_name = self.service_method_mapping.get((service, method))
            if not tool_name:
                self.logger.error(f"❌ [ToolRouter] Unknown service method: {service}.{method}")
                return {
                    "success": False,
                    "error": f"Unknown service method: {service}.{method}",
                    "service": service,
                    "method": method
                }
            
            # 2. ログ出力
            self.logger.info(f"🔧 [ToolRouter] Routing service method: {service}.{method} → {tool_name}")
            
            # 3. 既存のroute_toolメソッドを使用してMCPツールを実行
            result = await self.route_tool(tool_name, parameters, token)
            
            # 4. 結果にサービス情報を追加
            if isinstance(result, dict):
                result["service"] = service
                result["method"] = method
                result["mapped_tool"] = tool_name
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [ToolRouter] Service method routing failed: {service}.{method} - {e}")
            return {
                "success": False,
                "error": str(e),
                "service": service,
                "method": method
            }
    
    def _is_valid_tool(self, tool_name: str) -> bool:
        """ツール名が有効かチェック"""
        return tool_name in self.mcp_client.tool_server_mapping
    
    def get_available_tools(self) -> List[str]:
        """利用可能なツール一覧を取得"""
        return list(self.mcp_client.tool_server_mapping.keys())
    
    def get_tool_server(self, tool_name: str) -> Optional[str]:
        """ツール名からサーバー名を取得"""
        return self.mcp_client.tool_server_mapping.get(tool_name)
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """ツール名と説明の辞書を取得"""
        # MCP Clientのマッピングから動的に生成
        descriptions = {}
        for tool_name in self.mcp_client.tool_server_mapping.keys():
            if tool_name.startswith("inventory_"):
                if tool_name == "inventory_add":
                    descriptions[tool_name] = "在庫にアイテムを1件追加"
                elif tool_name == "inventory_list":
                    descriptions[tool_name] = "ユーザーの全在庫アイテムを取得"
                elif tool_name == "inventory_list_by_name":
                    descriptions[tool_name] = "指定したアイテム名の在庫アイテムを取得"
                elif tool_name == "inventory_get":
                    descriptions[tool_name] = "指定したIDの在庫アイテムを取得"
                elif tool_name == "inventory_update_by_id":
                    descriptions[tool_name] = "指定したIDの在庫アイテムを更新"
                elif tool_name == "inventory_update_by_name":
                    descriptions[tool_name] = "名前指定での在庫アイテム一括更新"
                elif tool_name == "inventory_update_by_name_oldest":
                    descriptions[tool_name] = "名前指定での最古アイテム更新（FIFO原則）"
                elif tool_name == "inventory_update_by_name_latest":
                    descriptions[tool_name] = "名前指定での最新アイテム更新"
                elif tool_name == "inventory_delete_by_id":
                    descriptions[tool_name] = "指定したIDの在庫アイテムを削除"
                elif tool_name == "inventory_delete_by_name":
                    descriptions[tool_name] = "名前指定での在庫アイテム一括削除"
                elif tool_name == "inventory_delete_by_name_oldest":
                    descriptions[tool_name] = "名前指定での最古アイテム削除（FIFO原則）"
                elif tool_name == "inventory_delete_by_name_latest":
                    descriptions[tool_name] = "名前指定での最新アイテム削除"
                else:
                    descriptions[tool_name] = f"在庫管理ツール: {tool_name}"
            elif tool_name.startswith("generate_menu_") or tool_name.startswith("search_menu_") or tool_name.startswith("search_recipe_") or tool_name.startswith("get_recipe_"):
                if tool_name == "get_recipe_history_for_user":
                    descriptions[tool_name] = "ユーザーのレシピ履歴を取得"
                elif tool_name == "generate_menu_plan_with_history":
                    descriptions[tool_name] = "在庫食材から献立構成を生成（履歴考慮）"
                elif tool_name == "search_menu_from_rag_with_history":
                    descriptions[tool_name] = "RAG検索による伝統的な献立タイトル生成"
                elif tool_name == "search_recipe_from_web":
                    descriptions[tool_name] = "Web検索によるレシピ検索"
                else:
                    descriptions[tool_name] = f"レシピ関連ツール: {tool_name}"
            elif tool_name.startswith("history_"):
                if tool_name == "history_add":
                    descriptions[tool_name] = "レシピを保存する"
                elif tool_name == "history_list":
                    descriptions[tool_name] = "ユーザーのレシピ履歴を取得する"
                elif tool_name == "history_get":
                    descriptions[tool_name] = "特定のレシピ履歴を1件取得"
                elif tool_name == "history_update_by_id":
                    descriptions[tool_name] = "レシピ履歴を更新する"
                elif tool_name == "history_delete_by_id":
                    descriptions[tool_name] = "レシピ履歴を削除する"
                else:
                    descriptions[tool_name] = f"履歴管理ツール: {tool_name}"
            else:
                descriptions[tool_name] = f"ツール: {tool_name}"
        
        return descriptions
    
    def _map_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        ツール名に応じてパラメータをマッピング
        
        Args:
            tool_name: MCPツール名
            parameters: 元のパラメータ
        
        Returns:
            マッピングされたパラメータ
        """
        mapped = parameters.copy()
        
        # search_recipe_from_webツールの場合、recipe_titlesをrecipe_titleにマッピング
        if tool_name == "search_recipe_from_web" and "recipe_titles" in mapped:
            # recipe_titles（リスト）をrecipe_title（文字列）に変換
            recipe_titles = mapped.pop("recipe_titles")
            if isinstance(recipe_titles, list) and recipe_titles:
                # リストの最初の要素をrecipe_titleとして使用
                mapped["recipe_title"] = recipe_titles[0]
                self.logger.info(f"🔧 [ToolRouter] Mapped recipe_titles to recipe_title: {recipe_titles[0]}")
            else:
                # 空のリストの場合は空文字列
                mapped["recipe_title"] = ""
                self.logger.info(f"🔧 [ToolRouter] Mapped empty recipe_titles to empty recipe_title")
        
        return mapped