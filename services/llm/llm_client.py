#!/usr/bin/env python3
"""
LLMClient - LLM API呼び出し

LLMServiceから分離したLLM API呼び出し専用クラス
OpenAI API呼び出しとフォールバック処理を担当
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from config.loggers import GenericLogger, log_prompt_with_tokens

# 環境変数を読み込み
load_dotenv()


class LLMClient:
    """LLM API呼び出しクラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.client")
        
        # OpenAI設定を環境変数から取得
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))
        
        # OpenAIクライアントを初期化
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            self.logger.info(f"✅ [LLMClient] OpenAI client initialized with model: {self.openai_model}")
        else:
            self.openai_client = None
            self.logger.warning("⚠️ [LLMClient] OPENAI_API_KEY not found, LLM calls will be disabled")
    
    async def call_openai_api(self, prompt: str) -> str:
        """
        OpenAI APIを呼び出してレスポンスを取得
        
        Args:
            prompt: 送信するプロンプト
        
        Returns:
            LLMからのレスポンス
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized")
            
            self.logger.info(f"🔧 [LLMClient] Calling OpenAI API with model: {self.openai_model}")
            
            # プロンプトとトークン数をログ出力（全文表示）
            log_prompt_with_tokens(prompt, max_tokens=2000, logger_name="service.llm", show_full_prompt=True)
            
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "あなたは優秀なタスク分解アシスタントです。ユーザーの要求を適切なサービスクラスのメソッド呼び出しに分解してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.openai_temperature,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            self.logger.info(f"✅ [LLMClient] OpenAI API response received: {len(content)} characters")
            
            # LLMレスポンスを改行付きでログ出力
            self.logger.info(f"📄 [LLMClient] LLM Response:\n{content}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ [LLMClient] OpenAI API call failed: {e}")
            raise
    
    def get_fallback_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        フォールバック用のタスク（LLM呼び出し失敗時）
        
        Args:
            user_id: ユーザーID
        
        Returns:
            フォールバックタスクリスト
        """
        self.logger.info(f"🔄 [LLMClient] Using fallback tasks for user: {user_id}")
        
        return [
            {
                "service": "InventoryService",
                "method": "get_inventory",
                "parameters": {"user_id": user_id},
                "dependencies": []
            }
        ]
    
    def get_available_tools_description(self) -> str:
        """
        利用可能なツールの説明を取得
        
        Returns:
            ツール説明の文字列
        """
        try:
            self.logger.info(f"🔧 [LLMClient] Getting available tools description")
            
            # TODO: ServiceCoordinator経由で取得するように修正予定
            # 現在は基本的な実装
            description_text = "利用可能なツール:\n"
            description_text += "- inventory_list: ユーザーの全在庫アイテムを取得\n"
            description_text += "- generate_menu_plan: 在庫食材から献立構成を生成\n"
            
            self.logger.info(f"✅ [LLMClient] Tools description generated successfully")
            return description_text
            
        except Exception as e:
            self.logger.error(f"❌ [LLMClient] Error in get_available_tools_description: {e}")
            return "ツール情報の取得に失敗しました。"
