#!/usr/bin/env python3
"""
献立変換機能

RAG検索結果を献立形式（主菜・副菜・汁物）に変換する機能を提供
"""

from typing import List, Dict, Any
from config.loggers import GenericLogger

logger = GenericLogger("mcp", "recipe_rag", initialize_logging=False)


class MenuFormatter:
    """献立フォーマッター"""
    
    def __init__(self, llm_solver):
        """初期化"""
        self.llm_solver = llm_solver
    
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
                    best_recipe = self._select_best_recipe(
                        recipes, used_ingredients, inventory_items
                    )
                    
                    if best_recipe:
                        title = best_recipe.get("title", "")
                        recipe_ingredients = self._extract_recipe_ingredients(best_recipe)
                        
                        selected_menu[category] = {
                            "title": title,
                            "ingredients": recipe_ingredients
                        }
                        
                        # 使用済み食材を記録
                        used_ingredients.update(recipe_ingredients)
            
            # 候補も生成（複数提案用）
            candidates = self._generate_menu_candidates(categorized_recipes)
            
            # LLMによる制約解決で最適な献立を選択
            if candidates and len(candidates) >= 1:
                llm_selected_menu = await self.llm_solver.solve_menu_constraints_with_llm(
                    candidates, inventory_items, menu_type
                )
                # LLMが有効な結果を返した場合はそれを使用
                if llm_selected_menu and any(llm_selected_menu.get(field, {}).get("title") for field in ["main_dish", "side_dish", "soup"]):
                    selected_menu = llm_selected_menu
            
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
    
    def _select_best_recipe(
        self, 
        recipes: List[Dict[str, Any]], 
        used_ingredients: set, 
        inventory_items: List[str]
    ) -> Dict[str, Any]:
        """
        最適なレシピを選択
        
        Args:
            recipes: レシピリスト
            used_ingredients: 使用済み食材セット
            inventory_items: 在庫食材リスト
        
        Returns:
            最適なレシピ
        """
        best_recipe = None
        best_score = -1
        
        for recipe in recipes:
            # レシピの食材を抽出
            recipe_ingredients = self._extract_recipe_ingredients(recipe)
            
            # 重複スコアを計算（重複が少ないほど高スコア）
            overlap_count = len(set(recipe_ingredients) & used_ingredients)
            inventory_match_count = len(set(recipe_ingredients) & set(inventory_items))
            
            # スコア計算: 在庫マッチ数 - 重複数
            score = inventory_match_count - overlap_count
            
            if score > best_score:
                best_score = score
                best_recipe = recipe
        
        return best_recipe
    
    def _extract_recipe_ingredients(self, recipe: Dict[str, Any]) -> List[str]:
        """
        レシピから食材を抽出
        
        Args:
            recipe: レシピ辞書
        
        Returns:
            食材リスト
        """
        recipe_ingredients = []
        main_ingredients = recipe.get("main_ingredients", "")
        if main_ingredients:
            recipe_ingredients.extend(main_ingredients.split())
        if not recipe_ingredients:
            content = recipe.get("content", "")
            parts = content.split(' | ')
            if len(parts) > 1:
                recipe_ingredients.extend(parts[1].split())
        
        return recipe_ingredients
    
    def _generate_menu_candidates(
        self, 
        categorized_recipes: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        献立候補を生成
        
        Args:
            categorized_recipes: カテゴリ別レシピ辞書
        
        Returns:
            献立候補リスト
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
                    
                    # レシピの食材を抽出
                    ingredients = self._extract_recipe_ingredients(recipe)
                    
                    candidate[category] = {
                        "title": title,
                        "ingredients": ingredients
                    }
                    
                    used_ingredients.update(ingredients)
            
            candidates.append(candidate)
        
        return candidates
