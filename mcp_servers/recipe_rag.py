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
        在庫食材に基づく類似レシピ検索（部分マッチング機能付き）
        
        Args:
            ingredients: 在庫食材リスト
            menu_type: メニュータイプ
            excluded_recipes: 除外するレシピタイトル
            limit: 検索結果の最大件数
        
        Returns:
            検索結果のリスト
        """
        try:
            # 部分マッチング機能を使用
            results = await self.search_recipes_by_partial_match(
                ingredients=ingredients,
                menu_type=menu_type,
                excluded_recipes=excluded_recipes,
                limit=limit,
                min_match_score=0.05  # 低い閾値で幅広く検索
            )
            
            # 既存のAPIとの互換性のため、不要なフィールドを削除
            formatted_results = []
            for result in results:
                formatted_result = {
                    "title": result["title"],
                    "category": result["category"],
                    "main_ingredients": result["main_ingredients"],
                    "original_index": result["original_index"],
                    "content": result["content"]
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
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
    
    def _calculate_partial_match_score(self, recipe_ingredients: str, inventory_items: List[str]) -> float:
        """
        レシピの食材と在庫食材の部分マッチングスコアを計算
        
        Args:
            recipe_ingredients: レシピの食材文字列
            inventory_items: 在庫食材リスト
        
        Returns:
            マッチングスコア (0.0 - 1.0)
        """
        if not recipe_ingredients or not inventory_items:
            return 0.0
        
        # レシピの食材を単語に分割
        recipe_words = recipe_ingredients.split()
        
        # マッチした食材数
        matched_count = 0
        total_inventory = len(inventory_items)
        
        for inventory_item in inventory_items:
            # 完全マッチ
            if inventory_item in recipe_words:
                matched_count += 1
            else:
                # 部分マッチ（在庫食材がレシピ食材に含まれる）
                for word in recipe_words:
                    if inventory_item in word or word in inventory_item:
                        matched_count += 0.5
                        break
        
        # スコア計算: マッチした食材数 / 在庫食材数
        return matched_count / total_inventory if total_inventory > 0 else 0.0
    
    def _get_matched_ingredients(self, recipe_ingredients: str, inventory_items: List[str]) -> List[str]:
        """
        レシピで使用可能な在庫食材を取得
        
        Args:
            recipe_ingredients: レシピの食材文字列
            inventory_items: 在庫食材リスト
        
        Returns:
            マッチした在庫食材のリスト
        """
        if not recipe_ingredients or not inventory_items:
            return []
        
        recipe_words = recipe_ingredients.split()
        matched = []
        
        for inventory_item in inventory_items:
            # 完全マッチ
            if inventory_item in recipe_words:
                matched.append(inventory_item)
            else:
                # 部分マッチ
                for word in recipe_words:
                    if inventory_item in word or word in inventory_item:
                        matched.append(inventory_item)
                        break
        
        return matched
    
    async def search_recipes_by_partial_match(
        self,
        ingredients: List[str],
        menu_type: str = "和食",
        excluded_recipes: List[str] = None,
        limit: int = 5,
        min_match_score: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        在庫食材の部分マッチングでレシピを検索
        
        Args:
            ingredients: 在庫食材リスト
            menu_type: メニュータイプ
            excluded_recipes: 除外するレシピタイトル
            limit: 検索結果の最大件数
            min_match_score: 最小マッチングスコア
        
        Returns:
            検索結果のリスト（マッチングスコア付き）
        """
        try:
            # ベクトルストアを取得
            vectorstore = self._get_vectorstore()
            
            # より多くの結果を取得して部分マッチングでフィルタリング
            query = f"{' '.join(ingredients)} {menu_type}"
            results = vectorstore.similarity_search(query, k=limit * 4)  # 多めに取得
            
            # 部分マッチングでフィルタリングとスコアリング
            scored_results = []
            
            for result in results:
                try:
                    metadata = result.metadata
                    content = result.page_content
                    
                    # タイトルを取得
                    title = metadata.get('title', '')
                    if not title:
                        title = self._extract_title_from_content(content)
                    
                    # 除外レシピチェック
                    if excluded_recipes and any(excluded in title for excluded in excluded_recipes):
                        continue
                    
                    # レシピの食材部分を抽出
                    parts = content.split(' | ')
                    recipe_ingredients = parts[1] if len(parts) > 1 else ""
                    
                    # 部分マッチングスコアを計算
                    match_score = self._calculate_partial_match_score(recipe_ingredients, ingredients)
                    
                    # 最小スコア以上のレシピのみを追加
                    if match_score >= min_match_score:
                        matched_ingredients = self._get_matched_ingredients(recipe_ingredients, ingredients)
                        
                        formatted_result = {
                            "title": title,
                            "category": metadata.get('recipe_category', ''),
                            "main_ingredients": metadata.get('main_ingredients', ''),
                            "original_index": metadata.get('original_index', 0),
                            "content": content,
                            "match_score": match_score,
                            "matched_ingredients": matched_ingredients,
                            "recipe_ingredients": recipe_ingredients
                        }
                        scored_results.append(formatted_result)
                        
                except Exception as e:
                    logger.warning(f"結果処理エラー: {e}")
                    continue
            
            # マッチングスコア順にソート
            scored_results.sort(key=lambda x: x['match_score'], reverse=True)
            
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"部分マッチング検索エラー: {e}")
            raise
