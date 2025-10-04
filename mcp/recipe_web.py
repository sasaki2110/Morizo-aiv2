"""
Morizo AI v2 - Recipe Web Search Module

This module provides web search functionality for recipe retrieval using Google Search API.
"""

import os
import re
from typing import List, Dict, Any
from googleapiclient.discovery import build
from dotenv import load_dotenv
from config.loggers import GenericLogger

# 環境変数の読み込み
load_dotenv()

# ロガーの初期化
logger = GenericLogger("mcp", "recipe_web", initialize_logging=False)


class GoogleSearchClient:
    """Google Search APIを使用したレシピ検索クライアント"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        
        if not self.api_key or not self.engine_id:
            raise ValueError("GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID are required")
        
        self.service = build("customsearch", "v1", developerKey=self.api_key)
        
        # 対応サイトの定義
        self.recipe_sites = {
            'cookpad.com': 'Cookpad',
            'kurashiru.com': 'クラシル',
            'recipe.rakuten.co.jp': '楽天レシピ',
            'delishkitchen.tv': 'デリッシュキッチン'
        }
    
    async def search_recipes(self, recipe_title: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """レシピ検索を実行（複数サイト対応）"""
        logger.info(f"🔍 [WEB] Searching recipes for: {recipe_title}")
        
        try:
            # 検索クエリを構築
            query = self._build_recipe_query(recipe_title)
            
            result = self.service.cse().list(
                q=query,
                cx=self.engine_id,
                num=num_results,
                lr='lang_ja'  # 日本語に限定
            ).execute()
            
            # 結果を解析・整形
            recipes = self._parse_search_results(result.get('items', []))
            
            logger.info(f"✅ [WEB] Found {len(recipes)} recipes")
            return recipes
            
        except Exception as e:
            logger.error(f"❌ [WEB] Search error: {e}")
            return []
    
    def _build_recipe_query(self, recipe_title: str) -> str:
        """レシピ検索用のクエリを構築"""
        # 複数サイトを対象とした検索クエリ
        sites_query = " OR ".join([f"site:{site}" for site in self.recipe_sites.keys()])
        return f"({sites_query}) {recipe_title} レシピ"
    
    def _parse_search_results(self, items: List[Dict]) -> List[Dict[str, Any]]:
        """検索結果を解析・整形"""
        recipes = []
        
        for item in items:
            # サイト名を特定
            site_name = self._identify_site(item.get('link', ''))
            
            recipe = {
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'description': item.get('snippet', ''),
                'site': site_name,
                'source': self.recipe_sites.get(site_name, 'Unknown')
            }
            
            recipes.append(recipe)
        
        return recipes
    
    def _identify_site(self, url: str) -> str:
        """URLからサイト名を特定"""
        for site in self.recipe_sites.keys():
            if site in url:
                return site
        return 'other'


def prioritize_recipes(recipes: List[Dict]) -> List[Dict]:
    """レシピを優先順位でソート"""
    priority_order = ['cookpad.com', 'kurashiru.com', 'recipe.rakuten.co.jp', 'delishkitchen.tv']
    
    def get_priority(recipe):
        site = recipe.get('site', '')
        try:
            return priority_order.index(site)
        except ValueError:
            return len(priority_order)
    
    return sorted(recipes, key=get_priority)


def filter_recipe_results(recipes: List[Dict]) -> List[Dict]:
    """レシピ結果をフィルタリング"""
    filtered = []
    
    for recipe in recipes:
        # 基本的な検証
        if recipe.get('title') and recipe.get('url'):
            # レシピサイトかどうかを確認
            if recipe.get('site') in ['cookpad.com', 'kurashiru.com', 'recipe.rakuten.co.jp', 'delishkitchen.tv']:
                filtered.append(recipe)
    
    return filtered


# グローバルインスタンス
search_client = GoogleSearchClient()
