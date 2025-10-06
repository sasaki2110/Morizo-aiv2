#!/usr/bin/env python3
"""
SessionService - セッション管理サービス

セッション管理のビジネスロジックを提供
現在は基本的なセッション管理機能を実装
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from config.loggers import GenericLogger


class Session:
    """セッションクラス"""
    
    def __init__(self, session_id: str, user_id: str):
        self.id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.data: Dict[str, Any] = {}


class SessionService:
    """セッション管理サービス"""
    
    def __init__(self):
        """初期化"""
        self.sessions: Dict[str, Session] = {}
        self.logger = GenericLogger("service", "session")
    
    async def create_session(
        self, 
        user_id: str
    ) -> Session:
        """
        セッションを作成（認証はAPI層で完了済み）
        
        Args:
            user_id: ユーザーID
        
        Returns:
            作成されたセッション
        """
        try:
            self.logger.info(f"🔧 [SessionService] Creating session for user: {user_id}")
            
            # セッションIDを生成
            session_id = str(uuid.uuid4())
            
            # セッションを作成
            session = Session(
                id=session_id,
                user_id=user_id
            )
            
            # セッションを保存
            self.sessions[session_id] = session
            
            self.logger.info(f"✅ [SessionService] Session created successfully: {session_id}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in create_session: {e}")
            raise
    
    async def get_session(
        self, 
        session_id: str
    ) -> Optional[Session]:
        """
        セッションを取得
        
        Args:
            session_id: セッションID
        
        Returns:
            セッション（存在しない場合はNone）
        """
        try:
            self.logger.info(f"🔧 [SessionService] Getting session: {session_id}")
            
            session = self.sessions.get(session_id)
            
            if session:
                # 最終アクセス時刻の更新
                session.last_accessed = datetime.now()
                self.logger.info(f"✅ [SessionService] Session retrieved successfully")
            else:
                self.logger.warning(f"⚠️ [SessionService] Session not found: {session_id}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in get_session: {e}")
            return None
    
    async def update_session(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        セッションを更新
        
        Args:
            session_id: セッションID
            updates: 更新データ
        
        Returns:
            更新成功の可否
        """
        try:
            self.logger.info(f"🔧 [SessionService] Updating session: {session_id}")
            
            session = self.sessions.get(session_id)
            
            if not session:
                self.logger.warning(f"⚠️ [SessionService] Session not found for update: {session_id}")
                return False
            
            # セッションデータを更新
            session.data.update(updates)
            session.last_accessed = datetime.now()
            
            self.logger.info(f"✅ [SessionService] Session updated successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in update_session: {e}")
            return False
    
    async def delete_session(
        self, 
        session_id: str
    ) -> bool:
        """
        セッションを削除
        
        Args:
            session_id: セッションID
        
        Returns:
            削除成功の可否
        """
        try:
            self.logger.info(f"🔧 [SessionService] Deleting session: {session_id}")
            
            if session_id in self.sessions:
                del self.sessions[session_id]
                self.logger.info(f"✅ [SessionService] Session deleted successfully")
                return True
            else:
                self.logger.warning(f"⚠️ [SessionService] Session not found for deletion: {session_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in delete_session: {e}")
            return False
    
    async def cleanup_expired_sessions(
        self, 
        max_age_hours: int = 24
    ) -> int:
        """
        期限切れセッションのクリーンアップ
        
        Args:
            max_age_hours: 最大有効時間（時間）
        
        Returns:
            削除されたセッション数
        """
        try:
            self.logger.info(f"🔧 [SessionService] Cleaning up expired sessions (max_age: {max_age_hours}h)")
            
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            expired_sessions = [
                session_id for session_id, session in self.sessions.items()
                if session.last_accessed < cutoff_time
            ]
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            self.logger.info(f"✅ [SessionService] Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in cleanup_expired_sessions: {e}")
            return 0
