#!/usr/bin/env python3
"""
LLMService - LLM呼び出しサービス

LLM呼び出しのコントロール専用サービス
分割されたサブモジュールを使用してLLM機能を提供
"""

from typing import Dict, Any, List
from config.loggers import GenericLogger
from .llm.prompt_manager import PromptManager
from .llm.response_processor import ResponseProcessor
from .llm.llm_client import LLMClient


class LLMService:
    """LLM呼び出しサービス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm")
        
        # 分割されたサブモジュールを初期化
        self.prompt_manager = PromptManager()
        self.response_processor = ResponseProcessor()
        self.llm_client = LLMClient()
    
    async def decompose_tasks(
        self, 
        user_request: str, 
        available_tools: List[str], 
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        実際のLLM呼び出しによるタスク分解
        
        Args:
            user_request: ユーザーリクエスト
            available_tools: 利用可能なツールリスト
            user_id: ユーザーID
        
        Returns:
            分解されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [LLMService] Decomposing tasks for user: {user_id}")
            self.logger.info(f"📝 [LLMService] User request: '{user_request}'")
            
            # 1. プロンプト構築
            prompt = self.prompt_manager.build_planning_prompt(user_request)
            
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
        results: Dict[str, Any]
    ) -> str:
        """
        最終回答整形
        
        Args:
            results: タスク実行結果辞書 (task1, task2, task3, task4)
        
        Returns:
            整形された回答
        """
        return self.response_processor.format_final_response(results)
    
    async def solve_constraints(
        self, 
        candidates: List[Dict], 
        constraints: Dict
    ) -> Dict:
        """
        制約解決（子ファイル委譲）
        
        Args:
            candidates: 候補リスト
            constraints: 制約条件
        
        Returns:
            制約解決結果
        """
        try:
            self.logger.info(f"🔧 [LLMService] Solving constraints for {len(candidates)} candidates")
            
            # TODO: 実際の制約解決ロジックを実装
            # 現在は基本的な実装
            result = {
                "selected": candidates[0] if candidates else {},
                "reason": "制約解決により選択されました"
            }
            
            self.logger.info(f"✅ [LLMService] Constraints solved successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in solve_constraints: {e}")
            return {"selected": {}, "reason": "エラーが発生しました"}
    
    def get_available_tools_description(self) -> str:
        """
        利用可能なツールの説明を取得
        
        Returns:
            ツール説明の文字列
        """
        return self.llm_client.get_available_tools_description()
    
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
        return self.prompt_manager.create_dynamic_prompt(base_prompt, tool_descriptions, user_context)
