"""
Morizo AI v2 - Recipe History MCP Server

This module provides MCP server for recipe history management with tool definitions only.
"""

import sys
import os
# プロジェクトルートをPythonのモジュール検索パスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from fastmcp import FastMCP

from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
from mcp_servers.utils import get_authenticated_client
from config.loggers import GenericLogger

# .envファイルを読み込み
load_dotenv()

# MCPサーバー初期化
mcp = FastMCP("Recipe History MCP Server")

# 処理クラスのインスタンス
crud = RecipeHistoryCRUD()
logger = GenericLogger("mcp", "recipe_history_server", initialize_logging=False)


# 基本CRUD操作
@mcp.tool()
async def history_add(
    user_id: str,
    title: str,
    source: str,
    url: Optional[str] = None,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    レシピを保存する
    
    Args:
        user_id: ユーザーID
        title: レシピタイトル
        source: レシピの出典
        url: レシピのURL
    
    Returns:
        保存されたレシピのID
    """
    client = get_authenticated_client(user_id, token)
    return await crud.add_history(client, user_id, title, source, url)


@mcp.tool()
async def history_list(user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    レシピ履歴一覧を取得する
    
    Args:
        user_id: ユーザーID
    
    Returns:
        レシピ履歴のリスト
    """
    client = get_authenticated_client(user_id, token)
    return await crud.get_all_histories(client, user_id)


@mcp.tool()
async def history_get(user_id: str, history_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    特定のレシピ履歴を1件取得
    
    Args:
        user_id: ユーザーID
        history_id: 履歴ID
    
    Returns:
        レシピ履歴の詳細
    """
    client = get_authenticated_client(user_id, token)
    return await crud.get_history_by_id(client, user_id, history_id)


@mcp.tool()
async def history_update_by_id(
    user_id: str,
    history_id: str,
    title: Optional[str] = None,
    source: Optional[str] = None,
    url: Optional[str] = None,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    レシピ履歴を更新する
    
    Args:
        user_id: ユーザーID
        history_id: 履歴ID
        title: レシピタイトル（オプション）
        source: レシピの出典（オプション）
        url: レシピのURL（オプション）
    
    Returns:
        更新成功の可否
    """
    client = get_authenticated_client(user_id, token)
    return await crud.update_history_by_id(client, user_id, history_id, title, source, url)


@mcp.tool()
async def history_delete_by_id(
    user_id: str,
    history_id: str,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    レシピ履歴を削除する
    
    Args:
        user_id: ユーザーID
        history_id: 履歴ID
    
    Returns:
        削除成功の可否
    """
    client = get_authenticated_client(user_id, token)
    return await crud.delete_history_by_id(client, user_id, history_id)


# RecipeHistoryMCPクラスは削除（Phase 3のサービスレイヤ実装時に移動予定）


if __name__ == "__main__":
    logger.info("🚀 Starting Recipe History MCP Server")
    mcp.run()
