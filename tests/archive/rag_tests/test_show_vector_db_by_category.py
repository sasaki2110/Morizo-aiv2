#!/usr/bin/env python3
"""
ベクトルDB内容表示テスト

3つのベクトルDB（主菜・副菜・汁物）の内容を検証・表示するテストスクリプト

使用方法:
    python tests/rag_tests/test_show_vector_db_by_category.py

前提条件:
    - 3つのベクトルDBが構築済みであること
    - OpenAI APIキーが設定されていること
"""

import os
import sys
from pathlib import Path
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

def show_db_contents(db_path: str, db_name: str, limit: int = 20):
    """
    ベクトルDBの内容を表示する
    
    Args:
        db_path: ベクトルDBのパス
        db_name: 表示名
        limit: 表示件数
    """
    print(f"\n=== {db_name} ({db_path}) ===")
    
    vectorstore = load_vector_db(db_path)
    if vectorstore is None:
        print("ベクトルDBが見つかりません")
        return
    
    try:
        # 全件数を取得（適当な検索で全件取得）
        all_results = vectorstore.similarity_search("", k=10000)  # 最大10000件に拡張
        
        print(f"件数: {len(all_results)}件")
        print()
        
        # 指定件数まで表示
        for i, result in enumerate(all_results[:limit], 1):
            metadata = result.metadata
            title = metadata.get('title', 'Unknown')
            recipe_category = metadata.get('recipe_category', 'Unknown')
            category_detail = metadata.get('category_detail', 'Unknown')
            main_ingredients = metadata.get('main_ingredients', 'Unknown')
            
            print(f"{i}. {title}")
            print(f"   レシピ分類: {recipe_category}")
            print(f"   カテゴリ: {category_detail}")
            print(f"   主材料: {main_ingredients}")
            print()
            
    except Exception as e:
        logger.error(f"内容表示エラー: {e}")

def show_db_statistics(db_path: str, db_name: str):
    """
    ベクトルDBの統計情報を表示する
    
    Args:
        db_path: ベクトルDBのパス
        db_name: 表示名
    """
    print(f"\n=== {db_name} 統計情報 ===")
    
    vectorstore = load_vector_db(db_path)
    if vectorstore is None:
        print("ベクトルDBが見つかりません")
        return
    
    try:
        # 全件数を取得
        all_results = vectorstore.similarity_search("", k=10000)  # 最大10000件に拡張
        
        print(f"総件数: {len(all_results)}件")
        
        # レシピ分類別の統計
        category_counts = {}
        category_detail_counts = {}
        
        for result in all_results:
            metadata = result.metadata
            recipe_category = metadata.get('recipe_category', 'Unknown')
            category_detail = metadata.get('category_detail', 'Unknown')
            
            # レシピ分類の統計
            if recipe_category in category_counts:
                category_counts[recipe_category] += 1
            else:
                category_counts[recipe_category] = 1
            
            # カテゴリの統計
            if category_detail in category_detail_counts:
                category_detail_counts[category_detail] += 1
            else:
                category_detail_counts[category_detail] = 1
        
        print("\nレシピ分類別統計:")
        for category, count in sorted(category_counts.items()):
            print(f"  {category}: {count}件")
        
        print("\nカテゴリ別統計:")
        for category, count in sorted(category_detail_counts.items()):
            if category:  # 空文字列は除外
                print(f"  {category}: {count}件")
        
    except Exception as e:
        logger.error(f"統計情報表示エラー: {e}")

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
    
    # パスの設定
    project_root = Path(__file__).parent.parent.parent
    
    # 3つのベクトルDBの内容を表示
    databases = [
        (str(project_root / "recipe_vector_db_main"), "主菜用ベクトルDB"),
        (str(project_root / "recipe_vector_db_sub"), "副菜用ベクトルDB"),
        (str(project_root / "recipe_vector_db_soup"), "汁物用ベクトルDB")
    ]
    
    print("=== ベクトルDB内容表示テスト ===")
    
    # 統計情報を表示
    for db_path, db_name in databases:
        show_db_statistics(db_path, db_name)
    
    # 詳細内容を表示
    for db_path, db_name in databases:
        show_db_contents(db_path, db_name, limit=20)
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    main()
