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
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# ロガーの設定（recipe_mcp.pyと同じ形式）
from config.loggers import GenericLogger
logger = GenericLogger("mcp", "recipe_rag", initialize_logging=False)

# ルートロガーを取得してハンドラーを設定
root_logger = logging.getLogger('morizo_ai')
if not root_logger.handlers:
    from config.logging import setup_logging
    setup_logging(initialize=False)  # ローテーションなし


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
        
        # LLMクライアントの初期化
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.llm_client = AsyncOpenAI()
        
    
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
            
            # ベクトルストアを取得
            vectorstore = self._get_vectorstore()
            
            # より多くの結果を取得して部分マッチングでフィルタリング
            query = f"{' '.join(normalized_ingredients)} {menu_type}"
            
            results = vectorstore.similarity_search(query, k=limit * 4)  # 多めに取得
            
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
                    if not recipe_ingredients or not normalized_ingredients:
                        match_score = 0.0
                    else:
                        recipe_words = recipe_ingredients.split()
                        matched_count = 0
                        total_inventory = len(normalized_ingredients)
                        matched_items = []
                        
                        
                        for inventory_item in normalized_ingredients:
                            # 完全マッチ
                            if inventory_item in recipe_words:
                                matched_count += 1
                                matched_items.append(f"{inventory_item}(完全)")
                            else:
                                # 部分マッチ（在庫食材がレシピ食材に含まれる）
                                for word in recipe_words:
                                    if inventory_item in word or word in inventory_item:
                                        matched_count += 0.5
                                        matched_items.append(f"{inventory_item}(部分)")
                                        break
                        
                        # スコア計算: マッチした食材数 / 在庫食材数
                        match_score = matched_count / total_inventory if total_inventory > 0 else 0.0
                    
                    # 最小スコア以上のレシピのみを追加
                    if match_score >= min_match_score:
                        
                        # マッチした食材を取得
                        matched_ingredients = []
                        if recipe_ingredients and normalized_ingredients:
                            recipe_words = recipe_ingredients.split()
                            for inventory_item in normalized_ingredients:
                                # 完全マッチ
                                if inventory_item in recipe_words:
                                    matched_ingredients.append(inventory_item)
                                else:
                                    # 部分マッチ
                                    for word in recipe_words:
                                        if inventory_item in word or word in inventory_item:
                                            matched_ingredients.append(inventory_item)
                                            break
                        
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
                    else:
                        pass
                        
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
            logger.info(f"📊 [RAG] RAG results: {rag_results}")
            logger.info(f"📊 [RAG] Inventory items: {inventory_items}")
            logger.info(f"📊 [RAG] Menu type: {menu_type}")
            
            
            # レシピをカテゴリ別に分類
            categorized_recipes = self._categorize_recipes(rag_results)
            
            # 各カテゴリから最適なレシピを選択して献立を構成
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
                    best_recipe = None
                    best_score = -1
                    
                    for i, recipe in enumerate(recipes):
                        # レシピの食材を抽出
                        recipe_ingredients = []
                        main_ingredients = recipe.get("main_ingredients", "")
                        if main_ingredients:
                            recipe_ingredients.extend(main_ingredients.split())
                        if not recipe_ingredients:
                            content = recipe.get("content", "")
                            parts = content.split(' | ')
                            if len(parts) > 1:
                                recipe_ingredients.extend(parts[1].split())
                        
                        # 重複スコアを計算（重複が少ないほど高スコア）
                        overlap_count = len(set(recipe_ingredients) & used_ingredients)
                        inventory_match_count = len(set(recipe_ingredients) & set(inventory_items))
                        
                        # スコア計算: 在庫マッチ数 - 重複数
                        score = inventory_match_count - overlap_count
                        
                        if score > best_score:
                            best_score = score
                            best_recipe = recipe
                    
                    if best_recipe:
                        title = best_recipe.get("title", "")
                        
                        selected_menu[category] = {
                            "title": title,
                            "ingredients": recipe_ingredients
                        }
                        
                        # 使用済み食材を記録
                        used_ingredients.update(recipe_ingredients)
                    else:
                        pass  # No recipe selected
                else:
                    pass  # No recipes available
            
            # 候補も生成（複数提案用）
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
                        
                        # レシピの食材を抽出
                        ingredients = []
                        main_ingredients = recipe.get("main_ingredients", "")
                        if main_ingredients:
                            ingredients.extend(main_ingredients.split())
                        if not ingredients:
                            content = recipe.get("content", "")
                            parts = content.split(' | ')
                            if len(parts) > 1:
                                ingredients.extend(parts[1].split())
                        
                        candidate[category] = {
                            "title": title,
                            "ingredients": ingredients
                        }
                        
                        used_ingredients.update(ingredients)
                
                candidates.append(candidate)
            
            # LLMによる制約解決で最適な献立を選択
            if candidates and len(candidates) >= 1:
                
                llm_selected_menu = await self._solve_menu_constraints_with_llm(
                    candidates, inventory_items, menu_type
                )
                # LLMが有効な結果を返した場合はそれを使用
                if llm_selected_menu and any(llm_selected_menu.get(field, {}).get("title") for field in ["main_dish", "side_dish", "soup"]):
                    selected_menu = llm_selected_menu
            else:
                pass  # No candidates available
            
            result = {
                "candidates": candidates,
                "selected": selected_menu
            }
            
            logger.debug(f"📊 [RAG] Selected menu: {selected_menu}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [RAG] Menu format conversion error: {e}")
            logger.error(f"❌ [RAG] RAG results: {rag_results}")
            logger.error(f"❌ [RAG] Inventory items: {inventory_items}")
            logger.error(f"❌ [RAG] Menu type: {menu_type}")
            raise
    
    async def _solve_menu_constraints_with_llm(
        self,
        menu_candidates: List[Dict[str, Any]],
        inventory_items: List[str],
        menu_type: str
    ) -> Dict[str, Any]:
        """
        LLMによる食材重複抑止の制約解決
        
        Args:
            menu_candidates: 複数の献立候補
            inventory_items: 在庫食材リスト
            menu_type: 献立のタイプ
        
        Returns:
            最適な献立選択結果
        """
        try:
            logger.info(f"🤖 [RAG] Solving menu constraints with LLM for {len(menu_candidates)} candidates")
            
            # LLMプロンプトを生成
            prompt = self._create_constraint_solving_prompt(menu_candidates, inventory_items, menu_type)
            
            # LLMに問い合わせ
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # 一貫性を重視
            )
            
            # レスポンスを解析
            selected_menu = self._parse_llm_menu_selection(response.choices[0].message.content)
            
            return selected_menu
            
        except Exception as e:
            logger.error(f"❌ [RAG] LLM constraint solving error: {e}")
            logger.error(f"❌ [RAG] Error details: {str(e)}")
            # エラー時は最初の候補を返す
            fallback = menu_candidates[0] if menu_candidates else {}
            logger.info(f"🔄 [RAG] Using fallback menu: {fallback}")
            return fallback
    
    def _create_constraint_solving_prompt(
        self,
        candidates: List[Dict[str, Any]],
        inventory_items: List[str],
        menu_type: str
    ) -> str:
        """
        制約解決用のLLMプロンプトを生成
        """
        candidates_text = ""
        for i, candidate in enumerate(candidates, 1):
            candidates_text += f"\n候補{i}:\n"
            candidates_text += f"  主菜: {candidate.get('main_dish', {}).get('title', '')} (食材: {candidate.get('main_dish', {}).get('ingredients', [])})\n"
            candidates_text += f"  副菜: {candidate.get('side_dish', {}).get('title', '')} (食材: {candidate.get('side_dish', {}).get('ingredients', [])})\n"
            candidates_text += f"  汁物: {candidate.get('soup', {}).get('title', '')} (食材: {candidate.get('soup', {}).get('ingredients', [])})\n"
        
        prompt = f"""
在庫食材: {inventory_items}
献立タイプ: {menu_type}

以下の複数の献立候補から、以下の条件で最適な組み合わせを選択してください:

1. 食材の重複を最小限に抑える
2. 在庫食材を最大限活用する
3. 栄養バランスが良い
4. {menu_type}らしい献立構成

候補献立:
{candidates_text}

以下のJSON形式で最適な献立を返してください（タイトルは元のレシピタイトルをそのまま使用してください）:
{{
    "main_dish": {{"title": "元のレシピタイトルそのまま", "ingredients": ["食材1", "食材2"]}},
    "side_dish": {{"title": "元のレシピタイトルそのまま", "ingredients": ["食材1", "食材2"]}},
    "soup": {{"title": "元のレシピタイトルそのまま", "ingredients": ["食材1", "食材2"]}},
    "selection_reason": "選択理由"
}}
"""
        return prompt
    
    def _parse_llm_menu_selection(self, llm_response: str) -> Dict[str, Any]:
        """
        LLMレスポンスから献立選択結果を解析
        """
        try:
            import json
            import re
            
            # JSON部分を抽出
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                
                result = json.loads(json_str)
                
                # 必要なフィールドが存在するかチェック
                required_fields = ["main_dish", "side_dish", "soup"]
                for field in required_fields:
                    if field not in result:
                        result[field] = {"title": "", "ingredients": []}
                
                return result
            else:
                return {}
                
        except Exception as e:
            logger.error(f"❌ [RAG] Failed to parse LLM response: {e}")
            logger.error(f"❌ [RAG] Response content: {llm_response}")
            return {}
    
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
        
        for i, recipe in enumerate(rag_results):
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
                if any(keyword in title for keyword in ["スープ", "味噌汁", "汁"]):
                    categorized["soup"].append(recipe)
                elif any(keyword in title for keyword in ["サラダ", "和え物", "漬物", "副菜"]):
                    categorized["side_dish"].append(recipe)
                else:
                    categorized["main_dish"].append(recipe)
        
        
        return categorized
    
    
    
    