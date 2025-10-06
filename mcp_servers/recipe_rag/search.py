#!/usr/bin/env python3
"""
レシピ検索機能

ChromaDBを使用したレシピの類似検索と部分マッチング機能を提供
"""

from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from config.loggers import GenericLogger

logger = GenericLogger("mcp", "recipe_rag", initialize_logging=False)


class RecipeSearchEngine:
    """レシピ検索エンジン"""
    
    def __init__(self, vectorstore: Chroma):
        """初期化"""
        self.vectorstore = vectorstore
    
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
            # 在庫食材の重複を除去して正規化
            normalized_ingredients = list(set(ingredients))
            
            # より多くの結果を取得して部分マッチングでフィルタリング
            query = f"{' '.join(normalized_ingredients)} {menu_type}"
            
            results = self.vectorstore.similarity_search(query, k=limit * 4)  # 多めに取得
            
            # 部分マッチングでフィルタリングとスコアリング
            scored_results = []
            
            for i, result in enumerate(results):
                try:
                    metadata = result.metadata
                    content = result.page_content
                    
                    # タイトルを取得
                    title = metadata.get('title', '')
                    if not title:
                        # page_contentからタイトルを抽出
                        parts = content.split(' | ')
                        if len(parts) >= 1:
                            title = parts[0].strip()
                    
                    # 除外レシピチェック
                    if excluded_recipes and any(excluded in title for excluded in excluded_recipes):
                        continue
                    
                    # レシピの食材部分を抽出
                    parts = content.split(' | ')
                    recipe_ingredients = parts[1] if len(parts) > 1 else ""
                    
                    # 部分マッチングスコアを計算
                    match_score, matched_ingredients = self._calculate_match_score(
                        recipe_ingredients, normalized_ingredients
                    )
                    
                    # 最小スコア以上のレシピのみを追加
                    if match_score >= min_match_score:
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
            
            final_results = scored_results[:limit]
            
            return final_results
            
        except Exception as e:
            logger.error(f"部分マッチング検索エラー: {e}")
            raise
    
    def _calculate_match_score(
        self, 
        recipe_ingredients: str, 
        normalized_ingredients: List[str]
    ) -> tuple[float, List[str]]:
        """
        マッチングスコアを計算
        
        Args:
            recipe_ingredients: レシピの食材文字列
            normalized_ingredients: 正規化された在庫食材リスト
        
        Returns:
            (マッチングスコア, マッチした食材リスト)
        """
        if not recipe_ingredients or not normalized_ingredients:
            return 0.0, []
        
        recipe_words = recipe_ingredients.split()
        matched_count = 0
        total_inventory = len(normalized_ingredients)
        matched_items = []
        
        for inventory_item in normalized_ingredients:
            # 完全マッチ
            if inventory_item in recipe_words:
                matched_count += 1
                matched_items.append(inventory_item)
            else:
                # 部分マッチ（在庫食材がレシピ食材に含まれる）
                for word in recipe_words:
                    if inventory_item in word or word in inventory_item:
                        matched_count += 0.5
                        matched_items.append(inventory_item)
                        break
        
        # スコア計算: マッチした食材数 / 在庫食材数
        match_score = matched_count / total_inventory if total_inventory > 0 else 0.0
        
        return match_score, matched_items
