#!/usr/bin/env python3
"""
Session モデル

セッションデータモデルとビジネスロジックを提供
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from config.loggers import GenericLogger


class Session:
    """セッションクラス"""
    
    def __init__(self, session_id: str, user_id: str):
        # 基本情報の初期化
        self.id = session_id
        self.user_id = user_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.data: Dict[str, Any] = {}
        
        # 確認コンテキストの初期化
        self.confirmation_context: Dict[str, Any] = {
            "type": None,  # "inventory_operation" | "ambiguity_resolution"
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
        
        # Phase 1F: 提案履歴管理
        self.proposed_recipes: Dict[str, list] = {"main": [], "sub": [], "soup": []}
        
        # Phase 3C-3: 候補情報の保存
        self.candidates: Dict[str, list] = {"main": [], "sub": [], "soup": []}
        
        # Phase 1F: セッション内コンテキスト（在庫情報等）
        self.context: Dict[str, Any] = {
            "inventory_items": [],
            "main_ingredient": None,
            "menu_type": ""
        }
        
        # Phase 2.5D: 段階的選択管理
        self.current_stage: str = "main"  # "main", "sub", "soup", "completed"
        self.selected_main_dish: Optional[Dict[str, Any]] = None
        self.selected_sub_dish: Optional[Dict[str, Any]] = None
        self.selected_soup: Optional[Dict[str, Any]] = None
        self.used_ingredients: list = []
        self.menu_category: str = "japanese"  # "japanese", "western", "chinese"
        
        # ロガー設定
        self.logger = GenericLogger("service", "session")
    
    def is_waiting_for_confirmation(self) -> bool:
        """確認待ち状態かどうか"""
        return self.confirmation_context.get("type") is not None
    
    def set_ambiguity_confirmation(
        self, 
        original_request: str, 
        question: str,
        ambiguity_details: Dict[str, Any]
    ):
        """曖昧性解消の確認状態を設定"""
        self.confirmation_context = {
            "type": "ambiguity_resolution",
            "original_request": original_request,
            "clarification_question": question,
            "detected_ambiguity": ambiguity_details,
            "timestamp": datetime.now()
        }
    
    def clear_confirmation_context(self):
        """確認コンテキストをクリア"""
        self.confirmation_context = {
            "type": None,
            "original_request": None,
            "clarification_question": None,
            "detected_ambiguity": None,
            "timestamp": None
        }
    
    def get_confirmation_type(self) -> Optional[str]:
        """確認タイプを取得"""
        return self.confirmation_context.get("type")
    
    def add_proposed_recipes(self, category: str, titles: list) -> None:
        """提案済みレシピタイトルを追加
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
            titles: 提案済みタイトルのリスト
        """
        if category in self.proposed_recipes:
            self.proposed_recipes[category].extend(titles)
            self.logger.info(f"📝 [SESSION] Added {len(titles)} proposed {category} recipes")
    
    def get_proposed_recipes(self, category: str) -> list:
        """提案済みレシピタイトルを取得
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 提案済みタイトルのリスト
        """
        return self.proposed_recipes.get(category, [])
    
    def clear_proposed_recipes(self, category: str) -> None:
        """提案済みレシピをクリア
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        """
        if category in self.proposed_recipes:
            self.proposed_recipes[category] = []
            self.logger.info(f"🧹 [SESSION] Cleared proposed {category} recipes")
    
    def set_candidates(self, category: str, candidates: list) -> None:
        """候補情報を保存（Phase 3C-3）
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
            candidates: 候補情報のリスト
        """
        if category in self.candidates:
            self.candidates[category] = candidates
            self.logger.info(f"💾 [SESSION] Set {len(candidates)} {category} candidates")
    
    def get_candidates(self, category: str) -> list:
        """候補情報を取得
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
        
        Returns:
            list: 候補情報のリスト
        """
        return self.candidates.get(category, [])
    
    def set_context(self, key: str, value: Any) -> None:
        """セッションコンテキストを設定
        
        Args:
            key: コンテキストキー（"inventory_items", "main_ingredient", "menu_type"等）
            value: 値
        """
        self.context[key] = value
        self.logger.info(f"💾 [SESSION] Context set: {key}")
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """セッションコンテキストを取得
        
        Args:
            key: コンテキストキー
            default: デフォルト値
        
        Returns:
            Any: コンテキスト値
        """
        return self.context.get(key, default)
    
    # Phase 2.5D: 段階管理メソッド
    def get_current_stage(self) -> str:
        """現在の段階を取得
        
        Returns:
            str: 現在の段階（"main", "sub", "soup", "completed"）
        """
        return self.current_stage
    
    def _normalize_ingredient_name(self, name: str) -> str:
        """食材名を正規化（比較用）
        
        Args:
            name: 食材名
            
        Returns:
            str: 正規化された食材名
        """
        # 全角・半角英数字を半角に統一
        normalized = name.translate(str.maketrans('０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ', '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'))
        # 全角カタカナをひらがなに変換（Unicode範囲を使用）
        def katakana_to_hiragana(text):
            result = []
            for char in text:
                if '\u30A1' <= char <= '\u30F6':  # カタカナ範囲
                    hiragana = chr(ord(char) - 0x60)
                    result.append(hiragana)
                else:
                    result.append(char)
            return ''.join(result)
        normalized = katakana_to_hiragana(normalized)
        # 空白と記号を除去
        normalized = re.sub(r'[\s　\-－\(\)（）・，、。．]+', '', normalized)
        # 小文字に統一
        normalized = normalized.lower()
        return normalized
    
    def _map_recipe_ingredients_to_inventory(self, recipe_ingredients: List[str], inventory_items: List[str]) -> List[str]:
        """レシピの材料名を在庫名にマッピング
        
        Args:
            recipe_ingredients: レシピの材料名リスト（ベクトルDB由来）
            inventory_items: 在庫食材名リスト（ユーザーの在庫）
            
        Returns:
            List[str]: マッピングされた在庫名リスト
        """
        if not recipe_ingredients or not inventory_items:
            return []
        
        mapped = []
        
        # 在庫名を正規化してインデックスを作成
        inventory_normalized = {}
        for inv_name in inventory_items:
            normalized = self._normalize_ingredient_name(inv_name)
            if normalized not in inventory_normalized:
                inventory_normalized[normalized] = []
            inventory_normalized[normalized].append(inv_name)
        
        # レシピ材料を在庫名にマッピング
        for recipe_ingredient in recipe_ingredients:
            normalized_recipe = self._normalize_ingredient_name(recipe_ingredient)
            
            # 完全一致を優先
            matched = False
            if normalized_recipe in inventory_normalized:
                # 複数の在庫名が同じ正規化結果を持つ場合は最初のものを使用
                mapped.append(inventory_normalized[normalized_recipe][0])
                matched = True
            else:
                # 部分一致を試行（在庫名にレシピ材料が含まれる場合）
                for inv_name in inventory_items:
                    normalized_inv = self._normalize_ingredient_name(inv_name)
                    if normalized_recipe in normalized_inv or normalized_inv in normalized_recipe:
                        mapped.append(inv_name)
                        matched = True
                        break
            
            # マッチしない場合もログに記録（デバッグ用）
            if not matched:
                self.logger.debug(f"⚠️ [SESSION] Could not map recipe ingredient '{recipe_ingredient}' to inventory")
        
        # 重複除去
        mapped = list(dict.fromkeys(mapped))  # 順序を保持しつつ重複除去
        
        return mapped
    
    def _record_used_ingredients(self, recipe: Dict[str, Any]) -> None:
        """使用済み食材を記録（在庫名にマッピング）
        
        Args:
            recipe: レシピ情報
        """
        if "ingredients" in recipe:
            recipe_ingredients = recipe["ingredients"]
            inventory_items = self.context.get("inventory_items", [])
            
            self.logger.info(f"🔍 [SESSION] Mapping recipe ingredients: {recipe_ingredients}")
            self.logger.info(f"🔍 [SESSION] Available inventory items: {inventory_items}")
            
            # レシピ材料を在庫名にマッピング
            mapped_ingredients = self._map_recipe_ingredients_to_inventory(
                recipe_ingredients, inventory_items
            )
            
            self.used_ingredients.extend(mapped_ingredients)
            self.logger.info(f"📝 [SESSION] Mapped recipe ingredients to inventory: {recipe_ingredients} -> {mapped_ingredients}")
    
    def _determine_menu_category(self, menu_type: str) -> str:
        """献立カテゴリを判定
        
        Args:
            menu_type: メニュータイプ文字列
            
        Returns:
            str: 献立カテゴリ（"japanese", "western", "chinese"）
        """
        if any(x in menu_type for x in ["洋食", "western", "西洋"]):
            return "western"
        elif any(x in menu_type for x in ["中華", "chinese"]):
            return "chinese"
        else:
            return "japanese"
    
    def set_selected_recipe(self, category: str, recipe: Dict[str, Any]) -> None:
        """選択したレシピを保存
        
        Args:
            category: カテゴリ（"main", "sub", "soup"）
            recipe: レシピ情報
        """
        if category == "main":
            self.selected_main_dish = recipe
            self.current_stage = "sub"
            # 使用済み食材を記録（在庫名にマッピング）
            self._record_used_ingredients(recipe)
            # カテゴリ判定
            menu_type = recipe.get("menu_type", "")
            self.menu_category = self._determine_menu_category(menu_type)
        elif category == "sub":
            self.selected_sub_dish = recipe
            self.current_stage = "soup"
            # 使用済み食材を記録（在庫名にマッピング）
            self._record_used_ingredients(recipe)
        elif category == "soup":
            self.selected_soup = recipe
            self.current_stage = "completed"
        
        self.logger.info(f"✅ [SESSION] Recipe selected for {category}")
    
    def get_selected_recipes(self) -> Dict[str, Any]:
        """選択済みレシピを取得
        
        Returns:
            Dict[str, Any]: 選択済みレシピの辞書
        """
        return {
            "main": self.selected_main_dish,
            "sub": self.selected_sub_dish,
            "soup": self.selected_soup
        }
    
    def get_used_ingredients(self) -> list:
        """使用済み食材を取得
        
        Returns:
            list: 使用済み食材のリスト
        """
        return self.used_ingredients
    
    def get_menu_category(self) -> str:
        """献立カテゴリを取得
        
        Returns:
            str: 献立カテゴリ（"japanese", "western", "chinese"）
        """
        return self.menu_category

