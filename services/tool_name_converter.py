#!/usr/bin/env python3
"""
ToolNameConverter - ツール名変換ユーティリティ

ツール名からサービス名・メソッド名への変換ロジックを提供
ConfirmationServiceから分離された責任
"""

from typing import Dict, Any


class ToolNameConverter:
    """ツール名変換クラス"""
    
    @staticmethod
    def get_service_from_tool(tool_name: str) -> str:
        """
        ツール名からサービス名を取得
        
        Args:
            tool_name: ツール名（例: "inventory_update_by_name"）
        
        Returns:
            サービス名（例: "inventory_service"）
        """
        # ツール名の最初の部分をサービス名として使用
        if tool_name.startswith("inventory_"):
            return "inventory_service"
        elif tool_name.startswith("recipe_"):
            return "recipe_service"
        elif tool_name.startswith("menu_"):
            return "menu_service"
        else:
            # デフォルトは最初の部分を_serviceに変換
            parts = tool_name.split("_")
            if len(parts) > 1:
                return f"{parts[0]}_service"
            return "unknown_service"
    
    @staticmethod
    def get_method_from_tool(tool_name: str) -> str:
        """
        ツール名からメソッド名を取得
        
        Args:
            tool_name: ツール名（例: "inventory_update_by_name"）
        
        Returns:
            メソッド名（例: "update_inventory"）
        """
        # ツール名からメソッド名を推測
        if tool_name.startswith("inventory_"):
            if "update" in tool_name:
                return "update_inventory"
            elif "delete" in tool_name:
                return "delete_inventory"
            elif "add" in tool_name:
                return "add_inventory"
            elif "get" in tool_name:
                return "get_inventory"
        elif tool_name.startswith("recipe_"):
            if "generate" in tool_name:
                return "generate_recipe"
            elif "get" in tool_name:
                return "get_recipe"
        elif tool_name.startswith("menu_"):
            if "generate" in tool_name:
                return "generate_menu"
            elif "get" in tool_name:
                return "get_menu"
        
        # デフォルトはツール名の2番目の部分以降を使用
        parts = tool_name.split("_")
        if len(parts) > 1:
            return "_".join(parts[1:])
        return tool_name
