#!/usr/bin/env python3
"""
SessionService - セッション管理サービス

セッション管理のビジネスロジックを提供
"""

from typing import Dict, Any, Optional
from config.loggers import GenericLogger

from .models import Session
from .crud_manager import SessionCRUDManager
from .confirmation_manager import ConfirmationManager
from .proposal_manager import ProposalManager
from .candidate_manager import CandidateManager
from .context_manager import ContextManager
from .stage_manager import StageManager


# ============================================================================
# SessionService - セッション管理サービス（シングルトン）
# ============================================================================

class SessionService:
    """セッション管理サービス（シングルトン）"""
    
    # ============================================================================
    # グループ1: シングルトン管理と初期化
    # ============================================================================
    # 
    # このセクションの責任:
    # - シングルトンパターンの実装（_instance, __new__）
    # - クラスレベルの共有ストレージ（_user_sessions）
    # - インスタンス初期化（logger, user_sessions参照の設定）
    # 
    # 将来的な分割時の考慮事項:
    # - シングルトンパターンは維持が必要
    # - _user_sessionsは全機能で共有されるため、分割時も共通アクセス手段が必要
    # ============================================================================
    
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
            
            # マネージャーの初期化（コンポジション）
            self.crud = SessionCRUDManager(self)
            self.confirmation = ConfirmationManager(self)
            self.proposal = ProposalManager(self)
            self.candidate = CandidateManager(self)
            self.context = ContextManager(self)
            self.stage = StageManager(self)
    
    # ============================================================================
    # グループ2: 基本CRUD操作
    # ============================================================================
    # 
    # このセクションの責任:
    # - セッションの作成（create_session）
    # - セッションの取得（get_session）
    # - セッションの更新（update_session）
    # - セッションの削除（delete_session）
    # - 期限切れセッションのクリーンアップ（cleanup_expired_sessions）
    # 
    # 将来的な分割時の考慮事項:
    # - user_sessionsへの直接アクセスが必要
    # - 他のグループ（確認状態、提案レシピ等）から使用される基盤機能
    # - 分割する場合はSessionCRUDManager等として独立させることが可能
    # ============================================================================
    
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
        return await self.crud.create_session(user_id, session_id)
    
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
        return await self.crud.get_session(session_id, user_id)
    
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
        return await self.crud.update_session(session_id, updates)
    
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
        return await self.crud.delete_session(session_id)
    
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
        return await self.crud.cleanup_expired_sessions(max_age_hours)
    
    # ============================================================================
    # グループ3: プライベートヘルパーメソッド
    # ============================================================================
    # 
    # このセクションの責任:
    # - セッションメソッド呼び出しの共通処理（helpers.pyに移動済み）
    # - エラーハンドリングとロギングの統一
    # 
    # 将来的な分割時の考慮事項:
    # - これらのヘルパーは複数の機能グループから使用されている
    # - helpers.pyに移動済み（call_session_method, call_session_void_method）
    # ============================================================================
    
    # ============================================================================
    # グループ4: 確認状態管理
    # ============================================================================
    # 
    # このセクションの責任:
    # - 曖昧性解決の状態を保存（save_confirmation_state）
    # - 曖昧性解決の状態を取得（get_confirmation_state）
    # - 曖昧性解決の状態をクリア（clear_confirmation_state）
    # 
    # 将来的な分割時の考慮事項:
    # - 分割する場合はConfirmationManager等として独立させることが可能
    # - 依存関係: get_session, create_session（グループ2）を使用
    # - session.data['confirmation_state']を直接操作
    # ============================================================================
    
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
        return await self.confirmation.save_confirmation_state(sse_session_id, user_id, state_data)
    
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
        return await self.confirmation.get_confirmation_state(sse_session_id)
    
    async def clear_confirmation_state(
        self,
        sse_session_id: str
    ) -> None:
        """
        曖昧性解決の状態をクリア
        
        Args:
            sse_session_id: SSEセッションID
        """
        return await self.confirmation.clear_confirmation_state(sse_session_id)
    
    # ============================================================================
    # グループ5: 提案レシピ管理
    # ============================================================================
    # 
    # このセクションの責任:
    # - 提案済みレシピをセッションに追加（add_proposed_recipes）
    # - 提案済みレシピをセッションから取得（get_proposed_recipes）
    # 
    # 将来的な分割時の考慮事項:
    # - 分割する場合はProposalManager等として独立させることが可能
    # - 依存関係: _call_session_method, _call_session_void_method（グループ3）を使用
    # - Sessionオブジェクトのadd_proposed_recipes, get_proposed_recipesメソッドを使用
    # ============================================================================
    
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
        return await self.proposal.add_proposed_recipes(sse_session_id, category, titles)
    
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
        return await self.proposal.get_proposed_recipes(sse_session_id, category)
    
    # ============================================================================
    # グループ6: 候補情報管理
    # ============================================================================
    # 
    # このセクションの責任:
    # - 候補情報をセッションに保存（set_candidates）
    # - 候補情報をセッションから取得（get_candidates）
    # 
    # 将来的な分割時の考慮事項:
    # - 分割する場合はCandidateManager等として独立させることが可能
    # - 依存関係: _call_session_method, _call_session_void_method（グループ3）を使用
    # - Sessionオブジェクトのset_candidates, get_candidatesメソッドを使用
    # ============================================================================
    
    async def set_candidates(
        self,
        sse_session_id: str,
        category: str,
        candidates: list
    ) -> None:
        """候補情報をセッションに保存（Phase 3C-3）
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
            candidates: 候補情報のリスト
        """
        return await self.candidate.set_candidates(sse_session_id, category, candidates)
    
    async def get_candidates(
        self,
        sse_session_id: str,
        category: str
    ) -> list:
        """候補情報をセッションから取得
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 候補情報のリスト
        """
        return await self.candidate.get_candidates(sse_session_id, category)
    
    # ============================================================================
    # グループ7: セッションコンテキスト
    # ============================================================================
    # 
    # このセクションの責任:
    # - セッションコンテキストを設定（set_session_context）
    # - セッションコンテキストを取得（get_session_context）
    # 
    # 将来的な分割時の考慮事項:
    # - 分割する場合はContextManager等として独立させることが可能
    # - 依存関係: _call_session_method, _call_session_void_method（グループ3）を使用
    # - Sessionオブジェクトのset_context, get_contextメソッドを使用
    # ============================================================================
    
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
        return await self.context.set_session_context(sse_session_id, key, value)
    
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
        return await self.context.get_session_context(sse_session_id, key, default)
    
    # ============================================================================
    # グループ8: 段階管理
    # ============================================================================
    # 
    # このセクションの責任:
    # - 現在の段階を取得（get_current_stage）
    # - 選択したレシピを保存（set_selected_recipe）
    # - 選択済みレシピを取得（get_selected_recipes）
    # - 使用済み食材を取得（get_used_ingredients）
    # - 献立カテゴリを取得（get_menu_category）
    # 
    # 将来的な分割時の考慮事項:
    # - 分割する場合はStageManager等として独立させることが可能
    # - 依存関係: _call_session_method, _call_session_void_method（グループ3）を使用
    # - Sessionオブジェクトの段階管理メソッド群を使用
    # ============================================================================
    
    async def get_current_stage(self, sse_session_id: str) -> str:
        """現在の段階を取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            str: 現在の段階
        """
        return await self.stage.get_current_stage(sse_session_id)
    
    async def set_selected_recipe(
        self, 
        sse_session_id: str, 
        category: str, 
        recipe: Dict[str, Any]
    ) -> None:
        """選択したレシピを保存
        
        Args:
            sse_session_id: SSEセッションID
            category: カテゴリ（"main", "sub", "soup"）
            recipe: レシピ情報
        """
        return await self.stage.set_selected_recipe(sse_session_id, category, recipe)
    
    async def get_selected_recipes(self, sse_session_id: str) -> Dict[str, Any]:
        """選択済みレシピを取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            Dict[str, Any]: 選択済みレシピの辞書
        """
        return await self.stage.get_selected_recipes(sse_session_id)
    
    async def get_used_ingredients(self, sse_session_id: str) -> list:
        """使用済み食材を取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            list: 使用済み食材のリスト
        """
        return await self.stage.get_used_ingredients(sse_session_id)
    
    async def get_menu_category(self, sse_session_id: str) -> str:
        """献立カテゴリを取得
        
        Args:
            sse_session_id: SSEセッションID
        
        Returns:
            str: 献立カテゴリ（"japanese", "western", "chinese"）
        """
        return await self.stage.get_menu_category(sse_session_id)
    
    # ============================================================================
    # グループ10: ヘルプ状態管理
    # ============================================================================
    # 
    # このセクションの責任:
    # - ヘルプ状態の設定（set_help_state）
    # - ヘルプ状態の取得（get_help_state）
    # - ヘルプ状態のクリア（clear_help_state）
    # 
    # 将来的な分割時の考慮事項:
    # - 分割する場合はHelpStateManager等として独立させることが可能
    # - 依存関係: context（グループ8）を使用
    # ============================================================================
    
    async def set_help_state(
        self,
        sse_session_id: str,
        user_id: str,
        help_state: Optional[str]
    ) -> None:
        """ヘルプ状態を設定
        
        Args:
            sse_session_id: SSEセッションID
            user_id: ユーザーID
            help_state: "overview", "detail_1", "detail_2", "detail_3", "detail_4", または None
        """
        session = await self.get_session(sse_session_id, user_id)
        if not session:
            # セッションが存在しない場合は作成
            self.logger.info(f"🔧 [SESSION] Creating session for help state: {sse_session_id}")
            session = await self.create_session(user_id, sse_session_id)
        
        if session:
            session.set_context("help_state", help_state)
            self.logger.info(f"💾 [SESSION] Help state set: {help_state}")
        else:
            self.logger.warning(f"⚠️ [SESSION] Failed to create session for help state setting: {sse_session_id}")
    
    async def get_help_state(
        self,
        sse_session_id: Optional[str],
        user_id: str
    ) -> Optional[str]:
        """ヘルプ状態を取得
        
        Args:
            sse_session_id: SSEセッションID（Noneの場合はユーザーID単位で検索）
            user_id: ユーザーID
        
        Returns:
            ヘルプ状態（"overview", "detail_1-4", または None）
        """
        self.logger.info(f"🔍 [SESSION] Getting help state: sse_session_id={sse_session_id}, user_id={user_id}")
        
        # まず指定されたセッションIDで検索
        if sse_session_id:
            session = await self.get_session(sse_session_id, user_id)
            if session:
                help_state = session.get_context("help_state", None)
                if help_state:
                    self.logger.info(f"✅ [SESSION] Help state retrieved from session {sse_session_id}: {help_state}")
                    return help_state
        
        # セッションIDで見つからない場合、またはセッションIDがNoneの場合
        # ユーザーID単位で最新のヘルプ状態を持つセッションを検索
        if user_id and user_id in self.user_sessions:
            user_sessions = self.user_sessions[user_id]
            # 最新のアクセス時刻でソートして、ヘルプ状態を持つセッションを検索
            for session_id, session in user_sessions.items():
                if session_id != sse_session_id:  # 既にチェックしたセッションはスキップ
                    help_state = session.get_context("help_state", None)
                    if help_state:
                        self.logger.info(f"✅ [SESSION] Help state retrieved from user's other session {session_id}: {help_state}")
                        return help_state
        
        if sse_session_id:
            self.logger.warning(f"⚠️ [SESSION] Session not found for help state retrieval: {sse_session_id}")
        else:
            self.logger.info(f"ℹ️ [SESSION] No help state found for user: {user_id}")
        return None
    
    async def clear_help_state(
        self,
        sse_session_id: str,
        user_id: str
    ) -> None:
        """ヘルプ状態をクリア（通常モードに戻る）
        
        Args:
            sse_session_id: SSEセッションID
            user_id: ユーザーID
        """
        await self.set_help_state(sse_session_id, user_id, None)
        self.logger.info(f"🧹 [SESSION] Help state cleared")


# ============================================================================
# グループ9: シングルトンインスタンス作成
# ============================================================================
# 
# このセクションの責任:
# - SessionServiceのシングルトンインスタンスを作成
# - グローバルアクセス用のsession_service変数を提供
# 
# 将来的な分割時の考慮事項:
# - 分割後もシングルトンインスタンスの提供は維持
# - 後方互換性のためsession_service変数は必須
# ============================================================================

# シングルトンインスタンスを作成
session_service = SessionService()

