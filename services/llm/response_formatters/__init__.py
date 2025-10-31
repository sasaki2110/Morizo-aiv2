#!/usr/bin/env python3
"""
ResponseFormatters - レスポンスフォーマット処理（ファサード）

後方互換性のためのファサードクラス
各フォーマッターを統合して提供
"""

from typing import Dict, Any, List
from .inventory_formatter import InventoryFormatter
from .recipe_formatter import RecipeFormatter
from .menu_formatter import MenuFormatter
from .generic_formatter import GenericFormatter


class ResponseFormatters:
    """レスポンスフォーマット処理クラス（ファサード）"""
    
    def __init__(self):
        """初期化"""
        self.inventory_formatter = InventoryFormatter()
        self.recipe_formatter = RecipeFormatter()
        self.menu_formatter = MenuFormatter()
        self.generic_formatter = GenericFormatter()
    
    # 在庫フォーマットメソッド
    def format_inventory_list(self, data: Dict, is_menu_scenario: bool = False) -> List[str]:
        """在庫一覧のフォーマット"""
        return self.inventory_formatter.format_inventory_list(data, is_menu_scenario)
    
    def format_inventory_add(self, data: Dict) -> List[str]:
        """在庫追加のフォーマット"""
        return self.inventory_formatter.format_inventory_add(data)
    
    def format_inventory_update(self, data: Dict) -> List[str]:
        """在庫更新のフォーマット"""
        return self.inventory_formatter.format_inventory_update(data)
    
    def format_inventory_delete(self, data: Dict) -> List[str]:
        """在庫削除のフォーマット"""
        return self.inventory_formatter.format_inventory_delete(data)
    
    # レシピフォーマットメソッド
    def format_web_recipes(self, web_data: Any) -> List[str]:
        """Web検索結果のフォーマット"""
        return self.recipe_formatter.format_web_recipes(web_data)
    
    def format_llm_menu(self, llm_menu: Dict[str, Any]) -> List[str]:
        """LLMメニューのフォーマット"""
        return self.recipe_formatter.format_llm_menu(llm_menu)
    
    def format_rag_menu(self, rag_menu: Dict[str, Any]) -> List[str]:
        """RAGメニューのフォーマット"""
        return self.recipe_formatter.format_rag_menu(rag_menu)
    
    def format_dish_item(self, dish_data: Any, dish_type: str) -> str:
        """料理項目のフォーマット"""
        return self.recipe_formatter.format_dish_item(dish_data, dish_type)
    
    def format_main_dish_proposals(self, data: Dict[str, Any]) -> List[str]:
        """主菜5件提案のフォーマット"""
        return self.recipe_formatter.format_main_dish_proposals(data)
    
    # メニュー選択フォーマットメソッド
    def format_selection_request(self, candidates: list, task_id: str) -> dict:
        """選択要求レスポンスのフォーマット"""
        return self.menu_formatter.format_selection_request(candidates, task_id)
    
    def format_selection_result(self, selection: int, task_id: str) -> dict:
        """選択結果レスポンスのフォーマット"""
        return self.menu_formatter.format_selection_result(selection, task_id)
    
    # 汎用フォーマットメソッド
    def format_generic_result(self, service_method: str, data: Any) -> List[str]:
        """汎用結果のフォーマット"""
        return self.generic_formatter.format_generic_result(service_method, data)

