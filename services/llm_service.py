#!/usr/bin/env python3
"""
LLMService - LLM呼び出しサービス

LLM呼び出しのコントロール専用サービス
分割されたサブモジュールを使用してLLM機能を提供
"""

from typing import Dict, Any, List, Optional
from config.loggers import GenericLogger
from .llm.prompt_manager import PromptManager
from .llm.response_processor import ResponseProcessor
from .llm.llm_client import LLMClient
from .llm.request_analyzer import RequestAnalyzer


class LLMService:
    """LLM呼び出しサービス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm")
        
        # 分割されたサブモジュールを初期化
        self.prompt_manager = PromptManager()
        self.response_processor = ResponseProcessor()
        self.llm_client = LLMClient()
        
        # Phase 2.5A: RequestAnalyzer を追加
        self.request_analyzer = RequestAnalyzer()
    
    async def decompose_tasks(
        self, 
        user_request: str, 
        available_tools: List[str], 
        user_id: str,
        sse_session_id: str = None,
        session_context: dict = None
    ) -> List[Dict[str, Any]]:
        """
        実際のLLM呼び出しによるタスク分解
        
        Args:
            user_request: ユーザーリクエスト
            available_tools: 利用可能なツールリスト
            user_id: ユーザーID
            sse_session_id: SSEセッションID
            session_context: セッションコンテキスト
        
        Returns:
            分解されたタスクリスト、または曖昧性確認用のレスポンス
        """
        try:
            self.logger.info(f"🔧 [LLMService] Decomposing tasks for user: {user_id}")
            self.logger.info(f"📝 [LLMService] User request: '{user_request}'")
            
            # Phase 2.5C: リクエスト分析（RequestAnalyzer を使用）
            analysis_result = self.request_analyzer.analyze(
                request=user_request,
                user_id=user_id,
                sse_session_id=sse_session_id,
                session_context=session_context or {}
            )
            
            self.logger.info(f"🔍 [LLMService] Analysis result: pattern={analysis_result['pattern']}")
            
            # 曖昧性がある場合、確認質問を返す
            if analysis_result["ambiguities"]:
                self.logger.info(f"⚠️ [LLMService] Ambiguity detected: {len(analysis_result['ambiguities'])} ambiguities")
                # TODO: 曖昧性確認の実装（Phase 1B参照）
                # 現時点では既存の処理を続行
            
            # Phase 2.5C: 動的プロンプト構築（新プロンプトマネージャーを強制使用）
            from .llm.prompt_manager import PromptManager as NewPromptManager
            new_prompt_manager = NewPromptManager()
            
            try:
                prompt = new_prompt_manager.build_prompt(
                    analysis_result=analysis_result,
                    user_id=user_id,
                    sse_session_id=sse_session_id
                )
                self.logger.info(f"✅ [LLMService] Dynamic prompt built using RequestAnalyzer (pattern={analysis_result['pattern']})")
            except Exception as e:
                import traceback
                self.logger.error(f"❌ [LLMService] Failed to build dynamic prompt: {e}")
                self.logger.error(traceback.format_exc())
                # Phase 2.5C完了後はエラーを例外として扱う（フォールバックしない）
                raise
            
            # 2. OpenAI API呼び出し
            response = await self.llm_client.call_openai_api(prompt)
            
            # 3. JSON解析
            tasks = self.response_processor.parse_llm_response(response)
            
            # 4. タスク形式に変換
            converted_tasks = self.response_processor.convert_to_task_format(tasks, user_id)
            
            # 生成されたタスクの詳細をログ出力
            self.logger.info(f"✅ [LLMService] Tasks decomposed successfully: {len(converted_tasks)} tasks")
            for i, task in enumerate(converted_tasks, 1):
                self.logger.info(f"📋 [LLMService] Task {i}:")
                self.logger.info(f"  Service: {task.get('service')}")
                self.logger.info(f"  Method: {task.get('method')}")
                self.logger.info(f"  Parameters: {task.get('parameters')}")
                self.logger.info(f"  Dependencies: {task.get('dependencies')}")
            
            return converted_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in decompose_tasks: {e}")
            # エラー時はフォールバック
            return self.llm_client.get_fallback_tasks(user_id)
    
    async def format_response(
        self, 
        results: Dict[str, Any],
        sse_session_id: str = None
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        最終回答整形
        
        Args:
            results: タスク実行結果辞書 (task1, task2, task3, task4)
            sse_session_id: SSEセッションID
        
        Returns:
            (整形された回答, JSON形式のレシピデータ)
        """
        response, menu_data = await self.response_processor.format_final_response(results, sse_session_id)
        self.logger.info(f"🔍 [LLMService] Menu data received: {menu_data is not None}")
        if menu_data:
            self.logger.info(f"📊 [LLMService] Menu data size: {len(str(menu_data))} characters")
        return response, menu_data
    
    def create_dynamic_prompt(
        self, 
        base_prompt: str, 
        tool_descriptions: str,
        user_context: Dict[str, Any]
    ) -> str:
        """
        動的プロンプト生成
        
        Args:
            base_prompt: ベースプロンプト
            tool_descriptions: ツール説明
            user_context: ユーザーコンテキスト
        
        Returns:
            動的プロンプト
        """
        # Phase 2.5C: 新プロンプトマネージャーを使用（create_dynamic_promptは実装されていないため、フォールバック処理）
        return self.prompt_manager.create_dynamic_prompt_bak(base_prompt, tool_descriptions, user_context)
