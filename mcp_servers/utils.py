"""
Morizo AI v2 - MCP Common Utilities

This module provides common utilities for MCP servers.
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


def get_authenticated_client(user_id: str, token: Optional[str] = None) -> Client:
    """
    認証済みのSupabaseクライアントを取得
    
    Args:
        user_id: ユーザーID（認証はAPI層で完了済み）
        token: 認証トークン（オプション）
    
    Returns:
        Supabaseクライアント
        
    Raises:
        ValueError: 必要な環境変数が設定されていない場合
    """
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not all([supabase_url, supabase_key]):
        raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
    
    client = create_client(supabase_url, supabase_key)
    
    # 認証トークンが提供されている場合はセッションを設定
    if token:
        client.auth.set_session(token, "")
    
    return client
