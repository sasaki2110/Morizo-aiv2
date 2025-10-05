#!/usr/bin/env python3
"""
レシピ埋め込みサービス

OpenAI Embeddings APIを使用してレシピテキストの埋め込みを生成する
環境変数から設定を読み込む
"""

import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class RecipeEmbeddingsService:
    """レシピ埋め込みサービス"""
    
    def __init__(self):
        """初期化"""
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # 環境変数から埋め込みモデルを取得
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        if not self.client.api_key:
            raise ValueError("OPENAI_API_KEYが設定されていません")
    
    async def generate_recipe_embedding(self, recipe_text: str) -> List[float]:
        """
        レシピテキストの埋め込み生成
        
        Args:
            recipe_text: レシピテキスト（タイトル + 食材 + 分類）
        
        Returns:
            埋め込みベクトル
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=recipe_text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"レシピ埋め込み生成エラー: {e}")
            raise
    
    async def generate_ingredients_embedding(self, ingredients: List[str]) -> List[float]:
        """
        食材リストの埋め込み生成
        
        Args:
            ingredients: 食材リスト
        
        Returns:
            埋め込みベクトル
        """
        try:
            # 食材リストを文字列に結合
            ingredients_text = " ".join(ingredients)
            
            response = self.client.embeddings.create(
                model=self.model,
                input=ingredients_text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"食材埋め込み生成エラー: {e}")
            raise
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        検索クエリの埋め込み生成
        
        Args:
            query: 検索クエリ
        
        Returns:
            埋め込みベクトル
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=query
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"クエリ埋め込み生成エラー: {e}")
            raise
