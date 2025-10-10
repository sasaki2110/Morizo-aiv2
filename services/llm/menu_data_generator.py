#!/usr/bin/env python3
"""
MenuDataGenerator - メニューデータ生成処理

レシピデータのJSON形式変換とメニューデータ生成を担当
"""

import json
from typing import Dict, Any, List, Optional
from config.loggers import GenericLogger
from .utils import ResponseProcessorUtils, DISH_TO_CATEGORY_MAPPING, CATEGORY_LABELS, EMOJI_MAP


class MenuDataGenerator:
    """メニューデータ生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.menu_generator")
        self.utils = ResponseProcessorUtils()
    
    def generate_menu_data_json(self, web_data: Any) -> Optional[Dict[str, Any]]:
        """
        レシピデータをJSON形式に変換
        
        Args:
            web_data: Web検索結果データ
        
        Returns:
            仕様書に準拠したJSON形式のレシピデータ
        """
        try:
            # Web検索結果の詳細ログを追加
            self.logger.info(f"🔍 [MenuDataGenerator] Web data type: {type(web_data)}")
            self.logger.info(f"📊 [MenuDataGenerator] Web data content: {json.dumps(web_data, ensure_ascii=False, indent=2)}")
            
            if not isinstance(web_data, dict):
                self.logger.warning("⚠️ [MenuDataGenerator] web_data is not a dict, skipping JSON generation")
                return None
            
            # メニュー構造を構築
            menu_data = self.build_menu_structure()
            
            # llm_menu と rag_menu からレシピを抽出
            for menu_type in ['llm_menu', 'rag_menu']:
                if menu_type not in web_data:
                    continue
                    
                menu = web_data[menu_type]
                self.extract_recipes_by_type(menu, menu_type, menu_data, web_data)
            
            # 空のセクションをチェック
            if not self.has_menu_data(menu_data):
                self.logger.warning("⚠️ [MenuDataGenerator] No recipe data found for JSON generation")
                return None
            
            # 生成されたmenu_dataの全文ログを追加
            self.logger.info(f"📋 [MenuDataGenerator] Generated menu_data: {json.dumps(menu_data, ensure_ascii=False, indent=2)}")
            self.logger.info(f"✅ [MenuDataGenerator] Menu data JSON generated successfully")
            return menu_data
            
        except Exception as e:
            self.logger.error(f"❌ [MenuDataGenerator] Error generating menu data JSON: {e}")
            return None
    
    def build_menu_structure(self) -> Dict[str, Any]:
        """
        メニュー構造を構築
        
        Returns:
            初期化されたメニューデータ構造
        """
        return {
            "innovative": {
                "title": "📝 斬新な提案",
                "recipes": {
                    "main": [],
                    "side": [],
                    "soup": []
                }
            },
            "traditional": {
                "title": "📚 伝統的な提案",
                "recipes": {
                    "main": [],
                    "side": [],
                    "soup": []
                }
            }
        }
    
    def extract_recipes_by_type(self, menu: Dict[str, Any], menu_type: str, menu_data: Dict[str, Any], web_data: Dict[str, Any]) -> None:
        """
        タイプ別レシピ抽出
        
        Args:
            menu: メニューデータ
            menu_type: メニュータイプ（llm_menu または rag_menu）
            menu_data: 構築中のメニューデータ
            web_data: 元のWebデータ
        """
        # カテゴリ別に処理
        for dish_type in ['main_dish', 'side_dish', 'soup']:
            if dish_type not in menu or 'recipes' not in menu[dish_type]:
                continue
                
            recipes = menu[dish_type]['recipes']
            if not recipes:
                continue
            
            # カテゴリマッピング
            category = DISH_TO_CATEGORY_MAPPING.get(dish_type, 'main')
            
            # 絵文字マッピング
            emoji = EMOJI_MAP.get(category, '🍽️')
            
            # レシピを変換（カテゴリ統合処理）
            category_urls = []  # カテゴリ全体のURLリスト
            
            for recipe in recipes[:2]:  # 最大2件まで
                urls = self.extract_recipe_urls(recipe)
                category_urls.extend(urls)  # 全URLを統合
            
            # カテゴリにURLがある場合は1つのレシピオブジェクトとして追加
            if category_urls:
                self.classify_and_add_recipe(category_urls, category, emoji, menu_type, web_data, menu_data)
    
    def classify_and_add_recipe(self, category_urls: List[Dict[str, str]], category: str, emoji: str, menu_type: str, web_data: Dict[str, Any], menu_data: Dict[str, Any]) -> None:
        """
        レシピ分類・追加
        
        Args:
            category_urls: カテゴリのURLリスト
            category: カテゴリ名
            emoji: 絵文字
            menu_type: メニュータイプ
            web_data: 元のWebデータ
            menu_data: 構築中のメニューデータ
        """
        # 実際の献立提案からタイトルを生成
        actual_menu_type = 'llm' if menu_type == 'llm_menu' else 'rag'
        actual_title = self.utils.extract_actual_menu_title(web_data, category, actual_menu_type)
        category_label = CATEGORY_LABELS.get(category, category)
        combined_title = f"{category_label}: {actual_title}" if actual_title else f"{category_label}:"
        
        combined_recipe = {
            "title": combined_title,
            "emoji": emoji,
            "category": category,
            "urls": category_urls
        }
        
        # innovative または traditional に分類
        target_section = self.classify_recipe(combined_recipe, menu_type)
        menu_data[target_section]["recipes"][category].append(combined_recipe)
    
    def has_menu_data(self, menu_data: Dict[str, Any]) -> bool:
        """
        メニューデータが存在するかチェック
        
        Args:
            menu_data: メニューデータ
        
        Returns:
            データが存在する場合True
        """
        for section in ['innovative', 'traditional']:
            for category in ['main', 'side', 'soup']:
                if menu_data[section]["recipes"][category]:
                    return True
        return False
    
    def extract_recipe_urls(self, recipe: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        レシピからURL情報を抽出
        
        Args:
            recipe: レシピデータ
        
        Returns:
            URL情報のリスト
        """
        urls = []
        
        try:
            # レシピのURL情報を抽出（実際の構造に応じて調整が必要）
            if 'url' in recipe:
                url = str(recipe['url'])
                title = str(recipe.get('title', 'レシピ詳細'))
                domain = self.utils.extract_domain(url)
                
                urls.append({
                    "title": title,
                    "url": url,
                    "domain": domain
                })
            
            # 複数URLがある場合の処理（必要に応じて拡張）
            
        except Exception as e:
            self.logger.error(f"❌ [MenuDataGenerator] Error extracting recipe URLs: {e}")
        
        return urls
    
    def classify_recipe(self, recipe: Dict[str, Any], menu_type: str) -> str:
        """
        レシピをinnovativeまたはtraditionalに分類
        
        Args:
            recipe: レシピデータ
            menu_type: メニュータイプ（llm_menu または rag_menu）
        
        Returns:
            'innovative' または 'traditional'
        """
        # 簡易的な分類ロジック
        # llm_menu = innovative, rag_menu = traditional
        if menu_type == 'llm_menu':
            return 'innovative'
        else:
            return 'traditional'
