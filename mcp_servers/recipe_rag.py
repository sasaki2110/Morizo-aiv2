#!/usr/bin/env python3
"""
レシピRAG検索クライアント

ChromaDBを使用してレシピの類似検索を実行する
環境変数から設定を読み込む
"""

import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class RecipeRAGClient:
    """レシピRAG検索クライアント"""
    
    def __init__(self):
        """初期化"""
        load_dotenv()
        # 環境変数からChromaDBのパスを取得（ベクトルDB構築スクリプトと同じパス）
        self.vector_db_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "./recipe_vector_db")
        # 環境変数から埋め込みモデルを取得
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self._vectorstore = None
    
    def _get_vectorstore(self) -> Chroma:
        """ベクトルストアの取得（遅延初期化）"""
        if self._vectorstore is None:
            try:
                self._vectorstore = Chroma(
                    persist_directory=self.vector_db_path,
                    embedding_function=self.embeddings
                )
                logger.info(f"ベクトルストアを読み込みました: {self.vector_db_path}")
            except Exception as e:
                logger.error(f"ベクトルストア読み込みエラー: {e}")
                raise
        return self._vectorstore
    
    async def search_similar_recipes(
        self,
        ingredients: List[str],
        menu_type: str = "和食",
        excluded_recipes: List[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在庫食材に基づく類似レシピ検索
        
        Args:
            ingredients: 在庫食材リスト
            menu_type: メニュータイプ
            excluded_recipes: 除外するレシピタイトル
            limit: 検索結果の最大件数
        
        Returns:
            検索結果のリスト
        """
        try:
            # 検索クエリを作成
            query = f"{' '.join(ingredients)} {menu_type}"
            
            # ベクトルストアを取得
            vectorstore = self._get_vectorstore()
            
            # 類似検索を実行
            results = vectorstore.similarity_search(query, k=limit * 2)  # 除外処理のため多めに取得
            
            # 除外レシピをフィルタリング
            if excluded_recipes:
                filtered_results = []
                for result in results:
                    title = result.metadata.get('title', '')
                    if not any(excluded in title for excluded in excluded_recipes):
                        filtered_results.append(result)
                results = filtered_results[:limit]
            else:
                results = results[:limit]
            
            # 結果を整形
            return self._format_search_results(results, limit)
            
        except Exception as e:
            logger.error(f"類似レシピ検索エラー: {e}")
            raise
    
    async def search_by_query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        クエリベースのレシピ検索
        
        Args:
            query: 検索クエリ
            limit: 検索結果の最大件数
        
        Returns:
            検索結果のリスト
        """
        try:
            # ベクトルストアを取得
            vectorstore = self._get_vectorstore()
            
            # 類似検索を実行
            results = vectorstore.similarity_search(query, k=limit)
            
            # 結果を整形
            return self._format_search_results(results, limit)
            
        except Exception as e:
            logger.error(f"クエリ検索エラー: {e}")
            raise
    
    def _format_search_results(self, results: List, limit: int) -> List[Dict[str, Any]]:
        """
        検索結果の整形
        
        Args:
            results: 検索結果
            limit: 最大件数
        
        Returns:
            整形された検索結果
        """
        formatted_results = []
        
        for result in results:
            try:
                metadata = result.metadata
                content = result.page_content
                
                # メタデータから直接タイトルを取得
                title = metadata.get('title', '')
                
                # メタデータにタイトルがない場合は、page_contentから抽出
                if not title:
                    title = self._extract_title_from_content(content)
                
                formatted_result = {
                    "title": title,
                    "category": metadata.get('recipe_category', ''),
                    "main_ingredients": metadata.get('main_ingredients', ''),
                    "original_index": metadata.get('original_index', 0),
                    "content": content
                }
                formatted_results.append(formatted_result)
                
                # 指定された件数に達したら終了
                if len(formatted_results) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"結果整形エラー: {e}")
                continue
        
        return formatted_results
    
    def _extract_title_from_content(self, content: str) -> str:
        """
        page_contentからタイトルを抽出
        
        Args:
            content: 結合テキスト（タイトル | 食材 | 分類）
        
        Returns:
            抽出されたタイトル
        """
        if not content:
            return ""
        
        # 分離記号で分割して最初の部分（タイトル）を取得
        parts = content.split(' | ')
        if len(parts) >= 1:
            return parts[0].strip()
        
        return ""
