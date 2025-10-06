#!/usr/bin/env python3
"""
Recipe RAG クライアント

レシピRAG検索のメインクライアント
各機能モジュールを統合して提供
"""

import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI
from dotenv import load_dotenv
import logging

# ロガーの設定
from config.loggers import GenericLogger
logger = GenericLogger("mcp", "recipe_rag", initialize_logging=False)

# ルートロガーを取得してハンドラーを設定
root_logger = logging.getLogger('morizo_ai')
if not root_logger.handlers:
    from config.logging import setup_logging
    setup_logging(initialize=False)  # ローテーションなし

# 機能モジュールのインポート
from .search import RecipeSearchEngine
from .menu_format import MenuFormatter
from .llm_solver import LLMConstraintSolver


class RecipeRAGClient:
    """レシピRAG検索クライアント"""
    
    def __init__(self):
        """初期化"""
        load_dotenv()
        
        # 環境変数からChromaDBのパスを取得
        self.vector_db_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "./recipe_vector_db")
        
        # 環境変数から埋め込みモデルを取得
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self._vectorstore = None
        
        # LLMクライアントの初期化
        self.llm_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.llm_client = AsyncOpenAI()
        
        # 機能モジュールの初期化
        self._search_engine = None
        self._menu_formatter = None
        self._llm_solver = None
    
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
    
    def _get_search_engine(self) -> RecipeSearchEngine:
        """検索エンジンの取得（遅延初期化）"""
        if self._search_engine is None:
            vectorstore = self._get_vectorstore()
            self._search_engine = RecipeSearchEngine(vectorstore)
        return self._search_engine
    
    def _get_menu_formatter(self) -> MenuFormatter:
        """メニューフォーマッターの取得（遅延初期化）"""
        if self._menu_formatter is None:
            llm_solver = self._get_llm_solver()
            self._menu_formatter = MenuFormatter(llm_solver)
        return self._menu_formatter
    
    def _get_llm_solver(self) -> LLMConstraintSolver:
        """LLM制約解決エンジンの取得（遅延初期化）"""
        if self._llm_solver is None:
            self._llm_solver = LLMConstraintSolver(self.llm_client, self.llm_model)
        return self._llm_solver
    
    async def search_similar_recipes(
        self,
        ingredients: List[str],
        menu_type: str = "和食",
        excluded_recipes: List[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在庫食材に基づく類似レシピ検索
        
        Args:
            ingredients: 在庫食材リスト
            menu_type: メニュータイプ
            excluded_recipes: 除外するレシピタイトル
            limit: 検索結果の最大件数
        
        Returns:
            検索結果のリスト
        """
        search_engine = self._get_search_engine()
        return await search_engine.search_similar_recipes(
            ingredients, menu_type, excluded_recipes, limit
        )
    
    async def convert_rag_results_to_menu_format(
        self,
        rag_results: List[Dict[str, Any]],
        inventory_items: List[str],
        menu_type: str = "和食"
    ) -> Dict[str, Any]:
        """
        RAG検索結果を献立形式に変換
        
        Args:
            rag_results: RAG検索結果のリスト
            inventory_items: 在庫食材リスト
            menu_type: 献立のタイプ
        
        Returns:
            献立形式の辞書
        """
        menu_formatter = self._get_menu_formatter()
        return await menu_formatter.convert_rag_results_to_menu_format(
            rag_results, inventory_items, menu_type
        )
