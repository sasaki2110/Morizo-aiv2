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
        self.confirmation_context: Dict[str, Any] = {
            "type": None,  # "inventory_operation" | "ambiguity_resolution"
            "original_request": None,  # 元のユーザーリクエスト
            "clarification_question": None,  # システムが出した確認質問
            "detected_ambiguity": None,  # 検出された曖昧性の詳細
            "timestamp": None
        }
        
        # Phase 1F: 提案履歴管理
        self.proposed_recipes: Dict[str, list] = {
            "main": [],
            "sub": [],
            "soup": []
        }
        
        # Phase 1F: セッション内コンテキスト（在庫情報等）
        self.context: Dict[str, Any] = {
            "inventory_items": [],
            "main_ingredient": None,
            "menu_type": ""
        }
        
        # ロガー設定
        self.logger = GenericLogger("service", "session")
    
    def is_waiting_for_confirmation(self) -> bool:
        """確認待ち状態かどうか"""
        return self.confirmation_context.get("type") is not None
    
    def set_ambiguity_confirmation(
        self, 
        original_request: str, 
        question: str,
        ambiguity_details: Dict[str, Any]
    ):
        """曖昧性解消の確認状態を設定"""
        self.confirmation_context = {
            "type": "ambiguity_resolution",
            "original_request": original_request,
            "clarification_question": question,
            "detected_ambiguity": ambiguity_details,
            "timestamp": datetime.now()
        }
    
    def clear_confirmation_context(self):
        """確認コンテキストをクリア"""
        self.confirmation_context = {
            "type": None,
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
    
    def get_confirmation_type(self) -> Optional[str]:
        """確認タイプを取得"""
        return self.confirmation_context.get("type")
    
    def add_proposed_recipes(self, category: str, titles: list) -> None:
        """提案済みレシピタイトルを追加
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
            titles: 提案済みタイトルのリスト
        """
        if category in self.proposed_recipes:
            self.proposed_recipes[category].extend(titles)
            self.logger.info(f"📝 [SESSION] Added {len(titles)} proposed {category} recipes")
    
    def get_proposed_recipes(self, category: str) -> list:
        """提案済みレシピタイトルを取得
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 提案済みタイトルのリスト
        """
        return self.proposed_recipes.get(category, [])
    
    def clear_proposed_recipes(self, category: str) -> None:
        """提案済みレシピをクリア
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        """
        if category in self.proposed_recipes:
            self.proposed_recipes[category] = []
            self.logger.info(f"🧹 [SESSION] Cleared proposed {category} recipes")
    
    def set_context(self, key: str, value: Any) -> None:
        """セッションコンテキストを設定
        
        Args:
            key: コンテキストキー（"inventory_items", "main_ingredient", "menu_type"等）
            value: 値
        """
        self.context[key] = value
        self.logger.info(f"💾 [SESSION] Context set: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """セッションコンテキストを取得
        
        Args:
            key: コンテキストキー
            default: デフォルト値
        
        Returns:
            Any: コンテキスト値
        """
        return self.context.get(key, default)


class SessionService:
    """セッション管理サービス（シングルトン）"""
    
    _instance = None
    _user_sessions: Dict[str, Dict[str, Session]] = {}
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if not hasattr(self, 'logger'):
            self.logger = GenericLogger("service", "session")
            self.user_sessions = self._user_sessions
    
    async def create_session(
        self, 
        user_id: str,
        session_id: Optional[str] = None
    ) -> Session:
        """
        セッションを作成（認証はAPI層で完了済み）
        
        Args:
            user_id: ユーザーID
            session_id: 指定するセッションID（Noneの場合は自動生成）
        
        Returns:
            作成されたセッション
        """
        try:
            self.logger.info(f"🔧 [SessionService] Creating session for user: {user_id}")
            
            # セッションIDを生成または指定されたIDを使用
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # セッションを作成（user_idがNoneの場合は"system"を使用）
            actual_user_id = user_id if user_id else "system"
            session = Session(
                session_id=session_id,
                user_id=actual_user_id
            )
            
            # ユーザー別セッション管理
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {}
            self.user_sessions[user_id][session_id] = session
            
            self.logger.info(f"✅ [SessionService] Session created successfully: {session_id}")
            
            return session
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in create_session: {e}")
            raise
    
    async def get_session(
        self, 
        session_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Session]:
        """
        セッションを取得
        
        Args:
            session_id: セッションID
            user_id: ユーザーID（指定された場合はそのユーザーのセッションのみ検索）
        
        Returns:
            セッション（存在しない場合はNone）
        """
        try:
            self.logger.info(f"🔧 [SessionService] Getting session: {session_id}")
            
            session = None
            
            if user_id:
                # 特定ユーザーのセッションを検索
                user_sessions = self.user_sessions.get(user_id, {})
                session = user_sessions.get(session_id)
            else:
                # 全ユーザーからセッションを検索
                for user_sessions in self.user_sessions.values():
                    if session_id in user_sessions:
                        session = user_sessions[session_id]
                        break
            
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
            
            # 全ユーザーからセッションを検索
            session = None
            for user_sessions in self.user_sessions.values():
                if session_id in user_sessions:
                    session = user_sessions[session_id]
                    break
            
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
            
            # 全ユーザーからセッションを検索して削除
            deleted = False
            for user_id, user_sessions in self.user_sessions.items():
                if session_id in user_sessions:
                    del user_sessions[session_id]
                    deleted = True
                    break
            
            if deleted:
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
            
            expired_sessions = []
            for user_id, user_sessions in self.user_sessions.items():
                for session_id, session in user_sessions.items():
                    if session.last_accessed < cutoff_time:
                        expired_sessions.append((user_id, session_id))
            
            for user_id, session_id in expired_sessions:
                del self.user_sessions[user_id][session_id]
            
            self.logger.info(f"✅ [SessionService] Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in cleanup_expired_sessions: {e}")
            return 0
    
    async def save_confirmation_state(
        self,
        sse_session_id: str,
        user_id: str,
        state_data: Dict[str, Any]
    ) -> None:
        """
        曖昧性解決の状態を保存
        
        Args:
            sse_session_id: SSEセッションID
            user_id: ユーザーID
            state_data: {
                'task_chain_manager': TaskChainManager,
                'execution_result': ExecutionResult,
                'original_tasks': List[Task],
                'ambiguity_info': AmbiguityInfo,
                'created_at': datetime
            }
        """
        try:
            self.logger.info(f"💾 [SessionService] Saving confirmation state for session: {sse_session_id}")
            
            # セッションを取得または作成
            session = await self.get_session(sse_session_id)
            if not session:
                session = Session(sse_session_id, user_id)
                # ユーザー別セッション管理
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = {}
                self.user_sessions[user_id][sse_session_id] = session
                self.logger.info(f"📝 [SessionService] Created new session for confirmation state")
            
            # 曖昧性解決状態を保存
            session.data['confirmation_state'] = state_data
            session.data['state_type'] = 'awaiting_confirmation'
            session.last_accessed = datetime.now()
            
            # デバッグログ: 保存された状態の詳細
            self.logger.info(f"🔍 [SessionService] Saved state keys: {list(state_data.keys())}")
            self.logger.info(f"🔍 [SessionService] Session data keys: {list(session.data.keys())}")
            self.logger.info(f"✅ [SessionService] Confirmation state saved successfully")
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in save_confirmation_state: {e}")
            raise
    
    async def get_confirmation_state(
        self,
        sse_session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        曖昧性解決の状態を取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            保存された状態データ（存在しない場合はNone）
        """
        try:
            self.logger.info(f"🔍 [SessionService] Getting confirmation state for session: {sse_session_id}")
            
            session = await self.get_session(sse_session_id)
            if not session:
                self.logger.warning(f"⚠️ [SessionService] Session not found: {sse_session_id}")
                return None
            
            if 'confirmation_state' not in session.data:
                self.logger.warning(f"⚠️ [SessionService] No confirmation_state in session data for: {sse_session_id}")
                self.logger.info(f"🔍 [SessionService] Available session data keys: {list(session.data.keys())}")
                return None
            
            state_data = session.data.get('confirmation_state')
            self.logger.info(f"🔍 [SessionService] Retrieved state keys: {list(state_data.keys()) if state_data else 'None'}")
            self.logger.info(f"✅ [SessionService] Confirmation state retrieved successfully")
            
            return state_data
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in get_confirmation_state: {e}")
            return None
    
    async def clear_confirmation_state(
        self,
        sse_session_id: str
    ) -> None:
        """
        曖昧性解決の状態をクリア
        
        Args:
            sse_session_id: SSEセッションID
        """
        try:
            self.logger.info(f"🧹 [SessionService] Clearing confirmation state for session: {sse_session_id}")
            
            session = await self.get_session(sse_session_id)
            if session and 'confirmation_state' in session.data:
                del session.data['confirmation_state']
                if 'state_type' in session.data:
                    del session.data['state_type']
                session.last_accessed = datetime.now()
                self.logger.info(f"✅ [SessionService] Confirmation state cleared successfully")
            else:
                self.logger.warning(f"⚠️ [SessionService] No confirmation state to clear for session: {sse_session_id}")
            
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in clear_confirmation_state: {e}")
    
    async def add_proposed_recipes(
        self, 
        sse_session_id: str, 
        category: str, 
        titles: list
    ) -> None:
        """提案済みレシピをセッションに追加
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
            titles: 提案済みタイトルのリスト
        """
        try:
            session = await self.get_session(sse_session_id, user_id=None)
            if session:
                session.add_proposed_recipes(category, titles)
                self.logger.info(f"✅ [SessionService] Added {len(titles)} proposed {category} recipes to session")
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in add_proposed_recipes: {e}")
    
    async def get_proposed_recipes(
        self, 
        sse_session_id: str, 
        category: str
    ) -> list:
        """提案済みレシピをセッションから取得
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 提案済みタイトルのリスト
        """
        try:
            session = await self.get_session(sse_session_id, user_id=None)
            if session:
                titles = session.get_proposed_recipes(category)
                self.logger.info(f"✅ [SessionService] Retrieved {len(titles)} proposed {category} recipes from session")
                return titles
            return []
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in get_proposed_recipes: {e}")
            return []
    
    async def set_session_context(
        self, 
        sse_session_id: str, 
        key: str, 
        value: Any
    ) -> None:
        """セッションコンテキストを設定
        
        Args:
            sse_session_id: SSEセッションID
            key: コンテキストキー
            value: 値
        """
        try:
            session = await self.get_session(sse_session_id, user_id=None)
            if session:
                session.set_context(key, value)
                self.logger.info(f"✅ [SessionService] Set session context: {key}")
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in set_session_context: {e}")
    
    async def get_session_context(
        self, 
        sse_session_id: str, 
        key: str, 
        default: Any = None
    ) -> Any:
        """セッションコンテキストを取得
        
        Args:
            sse_session_id: SSEセッションID
            key: コンテキストキー
            default: デフォルト値
        
        Returns:
            Any: コンテキスト値
        """
        try:
            session = await self.get_session(sse_session_id, user_id=None)
            if session:
                value = session.get_context(key, default)
                self.logger.info(f"✅ [SessionService] Retrieved session context: {key}")
                return value
            return default
        except Exception as e:
            self.logger.error(f"❌ [SessionService] Error in get_session_context: {e}")
            return default


# シングルトンインスタンスを作成
session_service = SessionService()