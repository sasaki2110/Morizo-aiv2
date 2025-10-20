"""
Morizo AI v2 - Recipe LLM Client

This module provides LLM-based recipe title generation functionality.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

from config.loggers import GenericLogger, log_prompt_with_tokens

# .envファイルを読み込み
load_dotenv()


class RecipeLLM:
    """LLM推論クライアント"""
    
    def __init__(self):
        self.logger = GenericLogger("mcp", "recipe_llm", initialize_logging=False)
        
        # 環境変数から設定を取得
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.8'))
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        # OpenAIクライアントを初期化
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        self.logger.info(f"🤖 [LLM] Initialized with model: {self.model}, temperature: {self.temperature}")
    
    # 食材重複抑止機能
    # - プロンプト内で「食材の重複を避ける」と明示的に指示
    # - LLMが1回の推論で主菜・副菜・汁物の3品構成を生成
    # - 各料理間で食材の重複を避けるように設計
    # - 在庫食材を最大限活用し、バランスの良い献立構成を実現
    
    async def generate_menu_titles(
        self, 
        inventory_items: List[str], 
        menu_type: str,
        excluded_recipes: List[str] = None
    ) -> Dict[str, Any]:
        """
        LLM推論による独創的な献立タイトル生成
        
        Args:
            inventory_items: 在庫食材リスト
            menu_type: 献立のタイプ
            excluded_recipes: 除外するレシピタイトル
        
        Returns:
            生成された献立タイトルの候補リスト
        
        実装済み: 食材重複抑止機能
        - プロンプト内で「食材の重複を避ける」と明示的に指示（_build_menu_prompt参照）
        - 1回のLLM推論で主菜・副菜・汁物の3品構成を生成
        - 各料理間で食材が重複しないように設計されたプロンプトを使用
        - LLMの推論能力により、献立内の食材バランスを自動調整
        """
        try:
            self.logger.info(f"🧠 [LLM] Generating menu titles for {menu_type} with {len(inventory_items)} ingredients")
            
            # プロンプトを構築
            prompt = self._build_menu_prompt(inventory_items, menu_type, excluded_recipes)
            
            # プロンプトロギング
            log_prompt_with_tokens(prompt, max_tokens=1000, logger_name="mcp.recipe_llm")
            
            # LLM呼び出し
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            # レスポンスを解析
            menu_titles = self._parse_menu_response(response.choices[0].message.content)
            
            self.logger.info(f"✅ [LLM] Generated {len(menu_titles)} menu titles")
            return {"success": True, "data": menu_titles}
            
        except Exception as e:
            self.logger.error(f"❌ [LLM] Failed to generate menu titles: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_menu_prompt(
        self, 
        inventory_items: List[str], 
        menu_type: str,
        excluded_recipes: List[str] = None
    ) -> str:
        """献立生成用のプロンプトを構築"""
        
        excluded_text = ""
        if excluded_recipes:
            excluded_text = f"\n除外するレシピ: {', '.join(excluded_recipes)}"
        
        prompt = f"""
在庫食材: {', '.join(inventory_items)}
献立タイプ: {menu_type}{excluded_text}

以下の条件で独創的な献立タイトルを生成してください:
1. 主菜・副菜・汁物の3品構成
2. 在庫食材のみを使用
3. 食材の重複を避ける
4. 独創的で新しいレシピタイトル
5. 除外レシピは使用しない

重要: 具体的な調理手順は生成せず、レシピタイトルのみを生成してください。
例: "牛乳と卵のフレンチトースト"、"ほうれん草の胡麻和え"

以下のJSON形式で回答してください:
{{
    "main_dish": "主菜のタイトル",
    "side_dish": "副菜のタイトル", 
    "soup": "汁物のタイトル",
    "ingredients_used": ["使用食材1", "使用食材2", ...]
}}

生成する献立:
"""
        return prompt
    
    def _parse_menu_response(self, response_content: str) -> Dict[str, Any]:
        """LLMレスポンスを解析して献立タイトルを抽出"""
        try:
            import json
            
            # JSON形式のレスポンスを解析
            menu_data = json.loads(response_content.strip())
            
            return {
                "main_dish": menu_data.get("main_dish", ""),
                "side_dish": menu_data.get("side_dish", ""),
                "soup": menu_data.get("soup", ""),
                "ingredients_used": menu_data.get("ingredients_used", [])
            }
            
        except json.JSONDecodeError:
            # JSON解析に失敗した場合、テキストから抽出を試行
            self.logger.warning("⚠️ [LLM] Failed to parse JSON response, attempting text extraction")
            return self._extract_from_text(response_content)
        except Exception as e:
            self.logger.error(f"❌ [LLM] Failed to parse response: {e}")
            return {"main_dish": "", "side_dish": "", "soup": "", "ingredients_used": []}
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """テキストから献立タイトルを抽出（フォールバック）"""
        # 簡単なテキスト解析（実際の実装ではより高度な解析が必要）
        lines = text.strip().split('\n')
        
        main_dish = ""
        side_dish = ""
        soup = ""
        ingredients = []
        
        for line in lines:
            line = line.strip()
            if "主菜" in line:
                main_dish = line.replace("主菜:", "").replace("主菜：", "").strip()
            elif "副菜" in line:
                side_dish = line.replace("副菜:", "").replace("副菜：", "").strip()
            elif "汁物" in line:
                soup = line.replace("汁物:", "").replace("汁物：", "").strip()
        
        return {
            "main_dish": main_dish,
            "side_dish": side_dish,
            "soup": soup,
            "ingredients_used": ingredients
        }
    
    async def generate_main_dish_candidates(
        self, 
        inventory_items: List[str], 
        menu_type: str,
        main_ingredient: str = None,  # 主要食材
        excluded_recipes: List[str] = None,
        count: int = 2
    ) -> Dict[str, Any]:
        """主菜候補を複数件生成（主要食材考慮）"""
        
        main_ingredient_text = ""
        if main_ingredient:
            main_ingredient_text = f"\n重要: {main_ingredient}を必ず使用してください。"
        
        # 除外レシピの追加
        excluded_text = ""
        if excluded_recipes:
            excluded_text = f"\n除外レシピ（提案しないでください）: {', '.join(excluded_recipes)}"
        
        prompt = f"""
在庫食材: {', '.join(inventory_items)}
献立タイプ: {menu_type}{main_ingredient_text}{excluded_text}

以下の条件で主菜のタイトルを{count}件生成してください:
1. 在庫食材のみを使用
2. 独創的で新しいレシピタイトル
3. 除外レシピは絶対に使用しない
4. 各提案に使用食材リストを含める

以下のJSON形式で回答してください:
{{
    "candidates": [
        {{"title": "主菜タイトル1", "ingredients": ["食材1", "食材2"]}},
        {{"title": "主菜タイトル2", "ingredients": ["食材1", "食材3"]}}
    ]
}}
"""
        
        try:
            self.logger.info(f"🤖 [LLM] Generating {count} main dish candidates with main ingredient: {main_ingredient}")
            
            # プロンプトロギング
            log_prompt_with_tokens(prompt, max_tokens=1000, logger_name="mcp.recipe_llm")
            
            # LLM呼び出し
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=1000
            )
            
            # レスポンスを解析
            candidates = self._parse_main_dish_response(response.choices[0].message.content)
            
            self.logger.info(f"✅ [LLM] Generated {len(candidates)} main dish candidates")
            return {"success": True, "data": {"candidates": candidates}}
            
        except Exception as e:
            self.logger.error(f"❌ [LLM] Failed to generate main dish candidates: {e}")
            return {"success": False, "error": str(e)}

    def _parse_main_dish_response(self, response_content: str) -> List[Dict[str, Any]]:
        """LLMレスポンスを解析して主菜候補を抽出"""
        try:
            import json
            import re
            
            # JSON部分を抽出
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                return data.get("candidates", [])
            
            return []
        except Exception as e:
            self.logger.error(f"❌ [LLM] Failed to parse main dish response: {e}")
            return []


if __name__ == "__main__":
    print("✅ Recipe LLM module loaded successfully")
