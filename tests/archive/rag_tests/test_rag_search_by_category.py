#!/usr/bin/env python3
"""
食材ベース検索テスト

3つのベクトルDB（主菜・副菜・汁物）に対して食材ベースの検索を実行し、
検索結果を検証・表示するテストスクリプト

使用方法:
    python tests/rag_tests/test_rag_search_by_category.py

前提条件:
    - 3つのベクトルDBが構築済みであること
    - OpenAI APIキーが設定されていること
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_vector_db(db_path: str):
    """
    ベクトルDBを読み込む
    
    Args:
        db_path: ベクトルDBのパス
        
    Returns:
        ChromaDBオブジェクト
    """
    try:
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        embeddings = OpenAIEmbeddings(model=embedding_model)
        
        vectorstore = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )
        
        return vectorstore
    except Exception as e:
        logger.error(f"ベクトルDB読み込みエラー ({db_path}): {e}")
        return None

def search_by_ingredients(vectorstore, ingredients: List[str], k: int = 20) -> List[Dict[str, Any]]:
    """
    食材リストでベクトル検索を実行する
    
    Args:
        vectorstore: ChromaDBオブジェクト
        ingredients: 食材リスト
        k: 取得件数
        
    Returns:
        検索結果のリスト
    """
    try:
        # 食材を結合して検索クエリを作成
        search_query = ' '.join(ingredients)
        
        # ベクトル検索を実行
        results = vectorstore.similarity_search(search_query, k=k)
        
        # 結果を辞書形式に変換
        search_results = []
        for result in results:
            metadata = result.metadata
            search_results.append({
                'title': metadata.get('title', 'Unknown'),
                'main_ingredients': metadata.get('main_ingredients', 'Unknown'),
                'recipe_category': metadata.get('recipe_category', 'Unknown'),
                'category_detail': metadata.get('category_detail', 'Unknown'),
                'page_content': result.page_content
            })
        
        return search_results
        
    except Exception as e:
        logger.error(f"食材ベース検索エラー: {e}")
        return []

def display_search_results(results: List[Dict[str, Any]], category_name: str, limit: int = 20):
    """
    検索結果を整形して表示する
    
    Args:
        results: 検索結果のリスト
        category_name: カテゴリ名
        limit: 表示件数
    """
    print(f"\n=== {category_name}検索結果 ===")
    print(f"件数: {len(results)}件")
    print()
    
    # 指定件数まで表示
    for i, result in enumerate(results[:limit], 1):
        title = result.get('title', 'Unknown')
        main_ingredients = result.get('main_ingredients', 'Unknown')
        recipe_category = result.get('recipe_category', 'Unknown')
        category_detail = result.get('category_detail', 'Unknown')
        
        print(f"{i}. {title}")
        print(f"   主材料: {main_ingredients}")
        print(f"   レシピ分類: {recipe_category}")
        print(f"   カテゴリ: {category_detail}")
        print()

def test_ingredient_search():
    """食材ベース検索テストを実行する"""
    print("=== 食材ベース検索テスト ===")
    
    # テスト用食材リスト
    inventory_items = [
        'ピーマン', '鶏もも肉', 'もやし', 'ほうれん草', 'パン', 
        '豚バラブロック', 'ほうれん草', '牛すね肉', '人参', 
        '牛乳', '牛乳', '牛乳', '玉ねぎ', 'ジャガイモ', 'キャベツ'
    ]
    
    print(f"テスト食材: {', '.join(inventory_items)}")
    print()
    
    # パスの設定
    project_root = Path(__file__).parent.parent.parent
    
    # 3つのベクトルDBの検索
    databases = [
        (str(project_root / "recipe_vector_db_main"), "主菜用ベクトルDB"),
        (str(project_root / "recipe_vector_db_sub"), "副菜用ベクトルDB"),
        (str(project_root / "recipe_vector_db_soup"), "汁物用ベクトルDB")
    ]
    
    for db_path, db_name in databases:
        print(f"--- {db_name} 検索中 ---")
        
        # ベクトルDBを読み込み
        vectorstore = load_vector_db(db_path)
        if vectorstore is None:
            print(f"{db_name}が見つかりません。スキップします。")
            continue
        
        # 食材ベース検索を実行
        results = search_by_ingredients(vectorstore, inventory_items, k=20)
        
        # 結果を表示
        display_search_results(results, db_name, limit=20)
        
        print(f"{db_name}検索完了")
        print()

def main():
    """メイン処理"""
    # .envファイルの読み込み
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    env_path = project_root / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f".envファイルを読み込みました: {env_path}")
    else:
        logger.warning(f".envファイルが見つかりません: {env_path}")
    
    # OpenAI APIキーの確認
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEYが設定されていません。.envファイルを確認してください。")
        sys.exit(1)
    
    # 食材ベース検索テストを実行
    test_ingredient_search()
    
    print("=== テスト完了 ===")

if __name__ == "__main__":
    main()
