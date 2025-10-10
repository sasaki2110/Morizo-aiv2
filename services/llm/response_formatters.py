#!/usr/bin/env python3
"""
ResponseFormatters - レスポンスフォーマット処理

レスポンスの整形とフォーマット処理を担当
"""

from typing import Dict, Any, List
from config.loggers import GenericLogger
from .utils import STORAGE_EMOJI_MAP


class ResponseFormatters:
    """レスポンスフォーマット処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.formatters")
    
    def format_inventory_list(self, inventory_data: List[Dict], is_menu_scenario: bool = False) -> List[str]:
        """在庫一覧のフォーマット"""
        if not inventory_data:
            return []
        
        response_parts = []
        
        # 献立提案シナリオの場合は表示しない
        if is_menu_scenario:
            return []
        
        # 通常の在庫表示（詳細）
        response_parts.append("📋 **現在の在庫一覧**")
        response_parts.append(f"総アイテム数: {len(inventory_data)}個")
        response_parts.append("")
        
        # アイテムをカテゴリ別に整理
        categories = {}
        for item in inventory_data:
            storage = item.get('storage_location', 'その他')
            if storage not in categories:
                categories[storage] = []
            categories[storage].append(item)
        
        # カテゴリ別に表示
        for storage, items in categories.items():
            storage_emoji = STORAGE_EMOJI_MAP.get(storage, "📦")
            response_parts.append(f"{storage_emoji} **{storage}**")
            response_parts.append("")  # セクションタイトル後の空行
            for item in items:
                expiry_info = f" (期限: {item['expiry_date']})" if item.get('expiry_date') else ""
                response_parts.append(f"  • {item['item_name']}: {item['quantity']} {item['unit']}{expiry_info}")
            response_parts.append("")  # セクション終了後の空行
        
        return response_parts
    
    def format_web_recipes(self, web_data: Any) -> List[str]:
        """Web検索結果のフォーマット（簡素化版）"""
        response_parts = []
        
        try:
            # web_dataが辞書の場合、献立提案のみを表示
            if isinstance(web_data, dict):
                # 斬新な提案（LLM）
                if 'llm_menu' in web_data:
                    response_parts.extend(self.format_llm_menu(web_data['llm_menu']))
                
                # 伝統的な提案（RAG）
                if 'rag_menu' in web_data:
                    response_parts.extend(self.format_rag_menu(web_data['rag_menu']))
            else:
                response_parts.append("レシピデータの形式が正しくありません。")
                
        except Exception as e:
            self.logger.error(f"❌ [ResponseFormatters] Error in format_web_recipes: {e}")
            response_parts.append("レシピデータの処理中にエラーが発生しました。")
        
        return response_parts
    
    def format_llm_menu(self, llm_menu: Dict[str, Any]) -> List[str]:
        """LLMメニューのフォーマット"""
        response_parts = []
        response_parts.append("🍽️ 斬新な提案")
        response_parts.append("")
        
        # 主菜
        if 'main_dish' in llm_menu and llm_menu['main_dish']:
            dish_text = self.format_dish_item(llm_menu['main_dish'], "主菜")
            response_parts.append(dish_text)
        
        # 副菜
        if 'side_dish' in llm_menu and llm_menu['side_dish']:
            dish_text = self.format_dish_item(llm_menu['side_dish'], "副菜")
            response_parts.append(dish_text)
        
        # 汁物
        if 'soup' in llm_menu and llm_menu['soup']:
            dish_text = self.format_dish_item(llm_menu['soup'], "汁物")
            response_parts.append(dish_text)
        else:
            response_parts.append("汁物:")
        
        response_parts.append("")
        return response_parts
    
    def format_rag_menu(self, rag_menu: Dict[str, Any]) -> List[str]:
        """RAGメニューのフォーマット"""
        response_parts = []
        response_parts.append("🍽️ 伝統的な提案")
        response_parts.append("")
        
        # 主菜
        if 'main_dish' in rag_menu and rag_menu['main_dish']:
            dish_text = self.format_dish_item(rag_menu['main_dish'], "主菜")
            response_parts.append(dish_text)
        
        # 副菜
        if 'side_dish' in rag_menu and rag_menu['side_dish']:
            dish_text = self.format_dish_item(rag_menu['side_dish'], "副菜")
            response_parts.append(dish_text)
        
        # 汁物
        if 'soup' in rag_menu and rag_menu['soup']:
            dish_text = self.format_dish_item(rag_menu['soup'], "汁物")
            response_parts.append(dish_text)
        else:
            response_parts.append("汁物:")
        
        response_parts.append("")
        return response_parts
    
    def format_dish_item(self, dish_data: Any, dish_type: str) -> str:
        """料理項目のフォーマット（共通処理）"""
        if isinstance(dish_data, str):
            return f"{dish_type}: {dish_data}"
        elif isinstance(dish_data, dict) and 'title' in dish_data:
            return f"{dish_type}: {dish_data['title']}"
        else:
            return f"{dish_type}:"
    
    def format_generic_result(self, service_method: str, data: Any) -> List[str]:
        """汎用結果のフォーマット"""
        response_parts = []
        response_parts.append(f"📊 **{service_method}の結果**")
        response_parts.append("")  # タイトル後の空行
        
        if isinstance(data, list):
            response_parts.append(f"取得件数: {len(data)}件")
            for i, item in enumerate(data[:3], 1):  # 上位3件のみ
                if isinstance(item, dict):
                    response_parts.append(f"{i}. {item}")
                else:
                    response_parts.append(f"{i}. {str(item)[:100]}...")
        elif isinstance(data, dict):
            response_parts.append(f"データ: {str(data)[:200]}...")
        else:
            response_parts.append(f"結果: {str(data)[:200]}...")
        
        response_parts.append("")  # セクション終了後の空行
        return response_parts
