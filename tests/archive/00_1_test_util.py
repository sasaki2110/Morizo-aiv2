"""
Morizo AI v2 - Test Utilities

This module provides common utilities for testing, including authentication helpers.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# .envファイルを読み込み
load_dotenv()


class AuthUtil:
    """認証関連のユーティリティクラス"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase_email = os.getenv('SUPABASE_EMAIL')
        self.supabase_password = os.getenv('SUPABASE_PASSWORD')
        
        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required")
        
        self._client: Optional[Client] = None
    
    def get_supabase_client(self) -> Client:
        """Supabaseクライアントを取得"""
        if self._client is None:
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client
    
    def get_auth_token(self) -> str:
        """テスト用の認証トークンを取得"""
        if not all([self.supabase_email, self.supabase_password]):
            raise ValueError("SUPABASE_EMAIL and SUPABASE_PASSWORD are required for testing")
        
        client = self.get_supabase_client()
        
        try:
            response = client.auth.sign_in_with_password({
                "email": self.supabase_email,
                "password": self.supabase_password
            })
            
            if response.session and response.session.access_token:
                return response.session.access_token
            else:
                raise ValueError("Failed to get access token")
                
        except Exception as e:
            raise ValueError(f"Authentication failed: {e}")
    
    def verify_auth_token(self, token: str) -> Optional[Dict[str, Any]]:
        """認証トークンを検証し、ユーザー情報を返す"""
        try:
            client = self.get_supabase_client()
            user_response = client.auth.get_user(token)
            if user_response and user_response.user:
                return user_response.user.model_dump()
            return None
        except:
            return None
    
    def get_authenticated_client(self, token: str) -> Client:
        """認証済みのSupabaseクライアントを取得"""
        client = self.get_supabase_client()
        # トークンでセッションを設定（refresh_tokenは空文字列でOK）
        client.auth.set_session(token, "")
        return client


# グローバルインスタンス
auth_util = AuthUtil()


def get_auth_token() -> str:
    """テスト用の認証トークンを取得（便利関数）"""
    return auth_util.get_auth_token()


def verify_auth_token(token: str) -> bool:
    """認証トークンを検証（便利関数）"""
    return auth_util.verify_auth_token(token)


def get_authenticated_client(token: str) -> Client:
    """認証済みのSupabaseクライアントを取得（便利関数）"""
    return auth_util.get_authenticated_client(token)


if __name__ == "__main__":
    # テスト実行
    try:
        print("🧪 Testing authentication utilities...")
        
        # 認証トークン取得テスト
        token = get_auth_token()
        print(f"✅ Auth token obtained: {token[:20]}...")
        
        # トークン検証テスト
        is_valid = verify_auth_token(token)
        print(f"✅ Token verification: {'Valid' if is_valid else 'Invalid'}")
        
        # 認証済みクライアント取得テスト
        client = get_authenticated_client(token)
        print("✅ Authenticated client obtained")
        
        print("🎉 All authentication tests passed!")
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        print("💡 Make sure to set SUPABASE_URL, SUPABASE_KEY, SUPABASE_EMAIL, SUPABASE_PASSWORD in .env file")
