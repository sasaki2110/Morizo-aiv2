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
    
    async def convert_rag_results_to_menu_format(
        self,
        rag_results: List[Dict[str, Any]],
        inventory_items: List[str],
        menu_type: str = "和食"
    ) -> Dict[str, Any]:
        """
        RAG検索結果を献立形式（主菜・副菜・汁物）に変換
        
        Args:
            rag_results: RAG検索結果のリスト
            inventory_items: 在庫食材リスト
            menu_type: 献立のタイプ
        
        Returns:
            献立形式の辞書
        """
        try:
            logger.info(f"🔄 [RAG] Converting {len(rag_results)} results to menu format")
            
            # レシピをカテゴリ別に分類
            categorized_recipes = self._categorize_recipes(rag_results)
            
            # 各カテゴリから最適なレシピを選択
            selected_menu = self._select_optimal_menu(
                categorized_recipes, inventory_items, menu_type
            )
            
            # 候補も生成（複数提案用）
            candidates = self._generate_menu_candidates(
                categorized_recipes, inventory_items, menu_type
            )
            
            result = {
                "candidates": candidates,
                "selected": selected_menu
            }
            
            logger.info(f"✅ [RAG] Menu format conversion completed")
            logger.debug(f"📊 [RAG] Selected menu: {selected_menu}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [RAG] Menu format conversion error: {e}")
            raise
    
    def _categorize_recipes(self, rag_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        レシピをカテゴリ別に分類
        
        Args:
            rag_results: RAG検索結果
        
        Returns:
            カテゴリ別に分類されたレシピ辞書
        """
        categorized = {
            "main_dish": [],
            "side_dish": [],
            "soup": [],
            "other": []
        }
        
        for recipe in rag_results:
            category = recipe.get("category", "").lower()
            title = recipe.get("title", "").lower()
            
            # カテゴリベースの分類
            if "主菜" in category or "メイン" in category:
                categorized["main_dish"].append(recipe)
            elif "副菜" in category or "サイド" in category:
                categorized["side_dish"].append(recipe)
            elif "汁物" in category or "スープ" in category or "味噌汁" in category:
                categorized["soup"].append(recipe)
            else:
                # タイトルベースの分類（フォールバック）
                if any(keyword in title for keyword in ["スープ", "味噌汁", "汁", "スープ"]):
                    categorized["soup"].append(recipe)
                elif any(keyword in title for keyword in ["サラダ", "和え物", "漬物", "副菜"]):
                    categorized["side_dish"].append(recipe)
                else:
                    categorized["main_dish"].append(recipe)
        
        logger.info(f"📊 [RAG] Categorized recipes: main={len(categorized['main_dish'])}, "
                   f"side={len(categorized['side_dish'])}, soup={len(categorized['soup'])}")
        
        return categorized
    
    def _select_optimal_menu(
        self, 
        categorized_recipes: Dict[str, List[Dict[str, Any]]], 
        inventory_items: List[str],
        menu_type: str
    ) -> Dict[str, Any]:
        """
        各カテゴリから最適なレシピを選択して献立を構成
        
        Args:
            categorized_recipes: カテゴリ別レシピ
            inventory_items: 在庫食材リスト
            menu_type: 献立タイプ
        
        Returns:
            選択された献立
        """
        selected_menu = {
            "main_dish": {"title": "", "ingredients": []},
            "side_dish": {"title": "", "ingredients": []},
            "soup": {"title": "", "ingredients": []}
        }
        
        used_ingredients = set()
        
        # 各カテゴリから最適なレシピを選択
        for category in ["main_dish", "side_dish", "soup"]:
            recipes = categorized_recipes.get(category, [])
            if recipes:
                # 食材重複を避けながら最適なレシピを選択
                best_recipe = self._select_best_recipe_without_overlap(
                    recipes, inventory_items, used_ingredients
                )
                
                if best_recipe:
                    title = best_recipe.get("title", "")
                    ingredients = self._extract_ingredients_from_recipe(best_recipe)
                    
                    selected_menu[category] = {
                        "title": title,
                        "ingredients": ingredients
                    }
                    
                    # 使用済み食材を記録
                    used_ingredients.update(ingredients)
        
        return selected_menu
    
    def _select_best_recipe_without_overlap(
        self, 
        recipes: List[Dict[str, Any]], 
        inventory_items: List[str],
        used_ingredients: set
    ) -> Optional[Dict[str, Any]]:
        """
        食材重複を避けながら最適なレシピを選択
        
        Args:
            recipes: レシピリスト
            inventory_items: 在庫食材リスト
            used_ingredients: 既に使用済みの食材セット
        
        Returns:
            最適なレシピ
        """
        best_recipe = None
        best_score = -1
        
        for recipe in recipes:
            # レシピの食材を抽出
            recipe_ingredients = self._extract_ingredients_from_recipe(recipe)
            
            # 重複スコアを計算（重複が少ないほど高スコア）
            overlap_count = len(set(recipe_ingredients) & used_ingredients)
            inventory_match_count = len(set(recipe_ingredients) & set(inventory_items))
            
            # スコア計算: 在庫マッチ数 - 重複数
            score = inventory_match_count - overlap_count
            
            if score > best_score:
                best_score = score
                best_recipe = recipe
        
        return best_recipe
    
    def _extract_ingredients_from_recipe(self, recipe: Dict[str, Any]) -> List[str]:
        """
        レシピから食材リストを抽出
        
        Args:
            recipe: レシピ辞書
        
        Returns:
            食材リスト
        """
        ingredients = []
        
        # main_ingredientsフィールドから抽出
        main_ingredients = recipe.get("main_ingredients", "")
        if main_ingredients:
            ingredients.extend(main_ingredients.split())
        
        # contentフィールドから抽出（フォールバック）
        if not ingredients:
            content = recipe.get("content", "")
            parts = content.split(' | ')
            if len(parts) > 1:
                ingredients.extend(parts[1].split())
        
        return ingredients
    
    def _generate_menu_candidates(
        self, 
        categorized_recipes: Dict[str, List[Dict[str, Any]]], 
        inventory_items: List[str],
        menu_type: str
    ) -> List[Dict[str, Any]]:
        """
        複数の献立候補を生成
        
        Args:
            categorized_recipes: カテゴリ別レシピ
            inventory_items: 在庫食材リスト
            menu_type: 献立タイプ
        
        Returns:
            献立候補のリスト
        """
        candidates = []
        
        # 最大3つの候補を生成
        for i in range(min(3, len(categorized_recipes.get("main_dish", [])))):
            candidate = {
                "main_dish": {"title": "", "ingredients": []},
                "side_dish": {"title": "", "ingredients": []},
                "soup": {"title": "", "ingredients": []}
            }
            
            used_ingredients = set()
            
            # 各カテゴリからレシピを選択
            for category in ["main_dish", "side_dish", "soup"]:
                recipes = categorized_recipes.get(category, [])
                if recipes and i < len(recipes):
                    recipe = recipes[i]
                    title = recipe.get("title", "")
                    ingredients = self._extract_ingredients_from_recipe(recipe)
                    
                    candidate[category] = {
                        "title": title,
                        "ingredients": ingredients
                    }
                    
                    used_ingredients.update(ingredients)
            
            candidates.append(candidate)
        
        return candidates