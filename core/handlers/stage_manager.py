"""
StageManager: Manages stage progression (main/sub/soup).

This handler manages:
- Current stage retrieval
- Stage advancement
- Recipe selection from tasks
- Next stage request generation
- Selected recipe retrieval
"""

from typing import Optional, Dict, Any
from services.session_service import SessionService
from config.loggers import GenericLogger


class StageManager:
    """Manages stage progression (main/sub/soup)."""
    
    def __init__(self, session_service: SessionService):
        self.logger = GenericLogger("core", "stage_manager")
        self.session_service = session_service
    
    async def get_current_stage(self, sse_session_id: str, user_id: str) -> str:
        """現在の段階を取得
        
        Args:
            sse_session_id: SSEセッションID
            user_id: ユーザーID
        
        Returns:
            str: 現在の段階（"main", "sub", "soup", "completed"）
        """
        try:
            session = await self.session_service.get_session(sse_session_id, user_id)
            if not session:
                self.logger.warning(f"⚠️ [STAGE] Session not found, returning default stage 'main'")
                return "main"
            
            stage = session.get_current_stage()
            self.logger.info(f"✅ [STAGE] Current stage: {stage}")
            return stage
            
        except Exception as e:
            self.logger.error(f"❌ [STAGE] Failed to get current stage: {e}")
            return "main"
    
    async def get_selected_recipe_from_task(self, task_id: str, selection: int, sse_session_id: str) -> Dict[str, Any]:
        """選択されたレシピをタスクから取得
        
        Args:
            task_id: タスクID
            selection: 選択されたインデックス
            sse_session_id: SSEセッションID
        
        Returns:
            Dict[str, Any]: 選択されたレシピ情報
        """
        try:
            self.logger.info(f"🔍 [STAGE] Getting selected recipe: task_id={task_id}, selection={selection}")
            
            # セッションから候補情報を取得
            session = await self.session_service.get_session(sse_session_id, user_id=None)
            if not session:
                self.logger.error(f"❌ [STAGE] Session not found: {sse_session_id}")
                return {}
            
            # 現在の段階を取得
            current_stage = session.get_current_stage()
            category = current_stage  # "main", "sub", "soup"
            
            # セッションから候補情報を取得
            candidates = session.get_candidates(category)
            if not candidates or len(candidates) < selection:
                self.logger.error(f"❌ [STAGE] Invalid selection: {selection} for {len(candidates)} candidates")
                return {}
            
            # 選択されたレシピを取得
            selected_recipe = candidates[selection - 1]  # インデックスは1ベース
            self.logger.info(f"✅ [STAGE] Selected recipe: title='{selected_recipe.get('title', 'Unknown')}', source='{selected_recipe.get('source', 'N/A')}'")
            
            return selected_recipe
            
        except Exception as e:
            self.logger.error(f"❌ [STAGE] Failed to get selected recipe: {e}")
            return {}
    
    async def advance_stage(self, sse_session_id: str, user_id: str, selected_recipe: Dict[str, Any]) -> str:
        """段階を進める
        
        Args:
            sse_session_id: SSEセッションID
            user_id: ユーザーID
            selected_recipe: 選択されたレシピ情報
        
        Returns:
            str: 次の段階の名前
        """
        try:
            # セッションを取得
            session = await self.session_service.get_session(sse_session_id, user_id)
            if not session:
                self.logger.error(f"❌ [STAGE] Session not found")
                return "main"
            
            # 現在の段階を取得
            current_stage = session.get_current_stage()
            self.logger.info(f"🔍 [STAGE] Current stage: {current_stage}")
            
            # 段階に応じて処理
            if current_stage == "main":
                # 主菜を選択した場合、副菜段階に進む
                session.set_selected_recipe("main", selected_recipe)
                next_stage = "sub"
                self.logger.info(f"✅ [STAGE] Advanced to stage: sub")
                
            elif current_stage == "sub":
                # 副菜を選択した場合、汁物段階に進む
                session.set_selected_recipe("sub", selected_recipe)
                next_stage = "soup"
                self.logger.info(f"✅ [STAGE] Advanced to stage: soup")
                
            elif current_stage == "soup":
                # 汁物を選択した場合、完了
                session.set_selected_recipe("soup", selected_recipe)
                next_stage = "completed"
                self.logger.info(f"✅ [STAGE] Completed all stages")
                
            else:
                self.logger.warning(f"⚠️ [STAGE] Unexpected stage: {current_stage}")
                next_stage = current_stage
            
            return next_stage
            
        except Exception as e:
            self.logger.error(f"❌ [STAGE] Failed to advance stage: {e}")
            return "main"
    
    async def generate_sub_dish_request(
        self, main_dish: Dict, sse_session_id: str, user_id: str
    ) -> str:
        """
        副菜提案用のリクエストを生成
        
        例: "副菜を5件提案して"（主菜で使った食材を除外）
        """
        session = await self.session_service.get_session(sse_session_id, user_id)
        if not session:
            return "副菜を5件提案して"
        
        used_ingredients = session.get_used_ingredients()
        main_ingredient_text = f"（主菜で使った食材: {', '.join(used_ingredients)} は除外して）"
        
        return f"主菜で使っていない食材で副菜を5件提案して。{main_ingredient_text}"
    
    async def generate_soup_request(
        self, sub_dish: Dict, sse_session_id: str, user_id: str
    ) -> str:
        """
        汁物提案用のリクエストを生成
        
        例: "汁物を5件提案して"（和食なら味噌汁、洋食ならスープ）
        """
        session = await self.session_service.get_session(sse_session_id, user_id)
        if not session:
            return "汁物を5件提案して"
        
        used_ingredients = session.get_used_ingredients()
        menu_category = session.get_menu_category()
        
        soup_type = "味噌汁" if menu_category == "japanese" else "スープ"
        used_ingredients_text = f"（主菜・副菜で使った食材: {', '.join(used_ingredients)} は除外して）"
        
        return f"{soup_type}を5件提案して。{used_ingredients_text}"
    
    async def get_selected_sub_dish(self, sse_session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """選択済み副菜を取得"""
        try:
            session = await self.session_service.get_session(sse_session_id, user_id)
            if session:
                return session.selected_sub_dish
            return None
        except Exception as e:
            self.logger.error(f"❌ [STAGE] Failed to get selected sub dish: {e}")
            return None
    
    async def get_selected_soup(self, sse_session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """選択済み汁物を取得"""
        try:
            session = await self.session_service.get_session(sse_session_id, user_id)
            if session:
                return session.selected_soup
            return None
        except Exception as e:
            self.logger.error(f"❌ [STAGE] Failed to get selected soup: {e}")
            return None

