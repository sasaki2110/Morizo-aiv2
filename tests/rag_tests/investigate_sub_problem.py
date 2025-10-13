#!/usr/bin/env python3
"""
副菜分類問題調査スクリプト

副菜用ベクトルDBに混入している問題のあるデータを特定する
"""

import json
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
    """ベクトルDBを読み込む"""
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

def investigate_sub_problem():
    """副菜分類の問題を調査する"""
    print("=== 副菜分類問題調査 ===")
    
    # 副菜用ベクトルDBを読み込み
    project_root = Path(__file__).parent.parent.parent
    db_path = str(project_root / "recipe_vector_db_sub")
    
    vectorstore = load_vector_db(db_path)
    if vectorstore is None:
        print("副菜用ベクトルDBが見つかりません")
        return
    
    # 全件を取得
    all_results = vectorstore.similarity_search("", k=10000)
    print(f"副菜用ベクトルDB総件数: {len(all_results)}件")
    
    # 問題のあるカテゴリを特定
    problem_categories = [
        "おかずしょうが焼き",
        "おかずみそ炒め", 
        "おかずグラタン",
        "おかず揚げ物天ぷら",
        "おかず肉巻き",
        "汁ものスープ",
        "麺もの冷たい麺"
    ]
    
    print("\n=== 問題のあるカテゴリの詳細 ===")
    
    for category in problem_categories:
        print(f"\n--- {category} ---")
        count = 0
        
        for result in all_results:
            metadata = result.metadata
            category_detail = metadata.get('category_detail', '')
            
            if category in category_detail:
                count += 1
                title = metadata.get('title', 'Unknown')
                recipe_category = metadata.get('recipe_category', 'Unknown')
                main_ingredients = metadata.get('main_ingredients', 'Unknown')
                
                print(f"  {count}. {title}")
                print(f"     レシピ分類: {recipe_category}")
                print(f"     カテゴリ: {category_detail}")
                print(f"     主材料: {main_ingredients}")
                print()
        
        print(f"  {category}の件数: {count}件")

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
    
    # 副菜分類問題の調査
    investigate_sub_problem()

if __name__ == "__main__":
    main()
