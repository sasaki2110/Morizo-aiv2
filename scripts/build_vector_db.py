#!/usr/bin/env python3
"""
レシピベクトルDB構築スクリプト

このスクリプトは、me2you/recipe_data.jsonlからレシピデータを読み込み、
前処理を行ってChromaDBベクトルデータベースを構築します。

使用方法:
    python scripts/build_vector_db.py

前提条件:
    - me2you/recipe_data.jsonlが存在すること
    - OpenAI APIキーが設定されていること
    - 必要な依存関係がインストールされていること
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# LangChain関連のインポート
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 調味料キーワードリスト（検索対象外）
SEASONING_KEYWORDS = [
    # 基本調味料
    '醤油', 'しょうゆ', '砂糖', '塩', '胡椒', 'こしょう', '酒', 'みりん', '酢',
    # 油類
    '油', 'ごま油', 'サラダ油', 'バター', 'マーガリン', 'オリーブオイル',
    # 発酵調味料
    '味噌', 'みそ', 'だし', 'コンソメ', 'ブイヨン',
    # ソース類
    'ケチャップ', 'マヨネーズ', 'マスタード', 'ウスターソース', 'オイスターソース',
    # 香辛料
    'わさび', 'からし', 'しょうが', 'にんにく', 'ねぎ', 'みつば', 'しそ', '大葉',
    # その他
    '片栗粉', '小麦粉', 'パン粉', 'ベーキングパウダー', '重曹'
]

def load_recipe_data(file_path: str) -> List[Dict[str, Any]]:
    """
    レシピデータをJSONLファイルから読み込む
    
    Args:
        file_path: JSONLファイルのパス
        
    Returns:
        レシピデータのリスト
    """
    recipes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    recipe = json.loads(line.strip())
                    recipes.append(recipe)
                except json.JSONDecodeError as e:
                    logger.warning(f"行 {line_num} のJSON解析に失敗: {e}")
                    continue
                    
        logger.info(f"レシピデータ読み込み完了: {len(recipes)}件")
        return recipes
        
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"ファイル読み込みエラー: {e}")
        sys.exit(1)

def extract_recipe_info(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    レシピデータから必要な情報を抽出する
    
    Args:
        recipe_data: 元のレシピデータ
        
    Returns:
        抽出されたレシピ情報
    """
    text = recipe_data.get('text', '')
    
    # タイトルの抽出
    title_start = text.find('(title)')
    title_end = text.find('(ingredientText)')
    title = ''
    if title_start != -1 and title_end != -1:
        title = text[title_start + 7:title_end].strip()
    
    # 食材リストの抽出
    ingredient_start = text.find('(ingredientText)')
    ingredient_end = text.find('[回答]')
    ingredients_text = ''
    if ingredient_start != -1 and ingredient_end != -1:
        ingredients_text = text[ingredient_start + 16:ingredient_end].strip()
    
    # 分類情報の抽出
    answer_start = text.find('[回答]')
    category = ''
    main_ingredients = []
    if answer_start != -1:
        answer_text = text[answer_start + 4:].strip()
        try:
            # JSON部分を抽出
            json_start = answer_text.find('{')
            json_end = answer_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_text = answer_text[json_start:json_end]
                answer_data = json.loads(json_text)
                category = answer_data.get('レシピ分類', '')
                main_ingredients = answer_data.get('主材料', [])
        except json.JSONDecodeError:
            logger.warning(f"分類情報のJSON解析に失敗: {title}")
    
    return {
        'title': title,
        'ingredients_text': ingredients_text,
        'category': category,
        'main_ingredients': main_ingredients,
        'original_text': text
    }

def preprocess_recipes(recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    レシピデータを前処理してベクトル化用のデータに変換する
    
    Args:
        recipes: 元のレシピデータのリスト
        
    Returns:
        前処理済みレシピデータのリスト
    """
    processed_recipes = []
    
    for i, recipe in enumerate(recipes):
        try:
            # レシピ情報を抽出
            recipe_info = extract_recipe_info(recipe)
            
            # 基本的な検証
            if not recipe_info['title'] or not recipe_info['category']:
                logger.warning(f"レシピ {i+1}: タイトルまたは分類が空です")
                continue
            
            # 食材リストを正規化
            ingredients = normalize_ingredients(recipe_info['ingredients_text'])
            
            # 結合テキストを作成（ベクトル化用）
            combined_text = create_combined_text(
                recipe_info['title'],
                ingredients,
                recipe_info['category']
            )
            
            # 前処理済みデータを作成
            processed_recipe = {
                'id': f"recipe_{i+1:04d}",
                'title': recipe_info['title'],
                'ingredients': ingredients,
                'combined_text': combined_text,
                'metadata': {
                    'title': recipe_info['title'],  # タイトルをメタデータに追加
                    'recipe_category': recipe_info['category'],
                    'main_ingredients': ', '.join(recipe_info['main_ingredients'][:3]),  # リストを文字列に変換
                    'original_index': i
                }
            }
            
            processed_recipes.append(processed_recipe)
            
        except Exception as e:
            logger.error(f"レシピ {i+1} の前処理に失敗: {e}")
            continue
    
    logger.info(f"前処理完了: {len(processed_recipes)}件")
    return processed_recipes

def normalize_ingredients(ingredients_text: str) -> List[str]:
    """
    食材リストを正規化する
    
    Args:
        ingredients_text: 食材テキスト
        
    Returns:
        正規化された食材リスト
    """
    if not ingredients_text:
        return []
    
    # 基本的な正規化
    ingredients = []
    
    # 改行やスペースで分割
    lines = ingredients_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 食材名を抽出（分量情報を除去）
        # 例: "牛乳50cc" → "牛乳"
        ingredient = extract_ingredient_name(line)
        if ingredient:
            ingredients.append(ingredient)
    
    # 重複を除去
    ingredients = list(set(ingredients))
    
    # 調味料を除外
    ingredients = filter_seasonings(ingredients)
    
    return ingredients

def extract_ingredient_name(ingredient_line: str) -> str:
    """
    食材行から食材名を抽出する
    
    Args:
        ingredient_line: 食材行（例: "牛乳50cc"）
        
    Returns:
        食材名（例: "牛乳"）
    """
    # 基本的な抽出ロジック
    # 数字や単位を除去
    import re
    
    # 数字と単位を除去
    ingredient = re.sub(r'\d+[a-zA-Z]*', '', ingredient_line)
    ingredient = re.sub(r'[（）()]', '', ingredient)
    ingredient = ingredient.strip()
    
    # 空文字列や短すぎる場合は除外
    if len(ingredient) < 2:
        return ''
    
    return ingredient

def filter_seasonings(ingredients: List[str]) -> List[str]:
    """
    調味料を除外して食材のみを抽出する
    
    Args:
        ingredients: 食材リスト
        
    Returns:
        調味料を除外した食材リスト
    """
    filtered = []
    for ingredient in ingredients:
        # 調味料かどうかをチェック
        is_seasoning = any(keyword in ingredient for keyword in SEASONING_KEYWORDS)
        if not is_seasoning:
            filtered.append(ingredient)
    
    logger.info(f"調味料除外: {len(ingredients)} → {len(filtered)} (除外: {len(ingredients) - len(filtered)})")
    return filtered

def create_combined_text(title: str, ingredients: List[str], category: str) -> str:
    """
    ベクトル化用の結合テキストを作成する（食材のみ）
    
    Args:
        title: レシピタイトル（使用しない）
        ingredients: 食材リスト（調味料除外済み）
        category: レシピ分類（使用しない）
        
    Returns:
        食材のみの結合テキスト
    """
    # 食材リストを文字列に変換（調味料は既に除外済み）
    ingredients_str = ' '.join(ingredients)
    
    # 余分なスペースを除去
    ingredients_str = ' '.join(ingredients_str.split())
    
    return ingredients_str

def build_vector_database(processed_recipes: List[Dict[str, Any]], output_dir: str):
    """
    ベクトルデータベースを構築する
    
    Args:
        processed_recipes: 前処理済みレシピデータ
        output_dir: 出力ディレクトリ
    """
    try:
        logger.info("ベクトルデータベース構築開始...")
        
        # OpenAI Embeddingsの初期化
        embeddings = OpenAIEmbeddings()
        
        # テキストとメタデータを準備
        texts = [recipe['combined_text'] for recipe in processed_recipes]
        metadatas = [recipe['metadata'] for recipe in processed_recipes]
        
        # ChromaDBベクトルストアを作成
        vectorstore = Chroma.from_texts(
            texts=texts,
            metadatas=metadatas,
            embedding=embeddings,
            persist_directory=output_dir
        )
        
        # 永続化
        vectorstore.persist()
        
        logger.info(f"ベクトルデータベース構築完了: {len(processed_recipes)}件")
        logger.info(f"出力先: {output_dir}")
        
        return vectorstore
        
    except Exception as e:
        logger.error(f"ベクトルデータベース構築エラー: {e}")
        raise

def main():
    """メイン処理"""
    # .envファイルの読み込み
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
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
    recipe_data_path = project_root / "me2you" / "recipe_data.jsonl"
    output_dir = project_root / "recipe_vector_db"
    
    logger.info("=== レシピベクトルDB構築開始 ===")
    logger.info(f"元データ: {recipe_data_path}")
    logger.info(f"出力先: {output_dir}")
    
    # 1. レシピデータの読み込み
    logger.info("ステップ1: レシピデータの読み込み")
    recipes = load_recipe_data(str(recipe_data_path))
    
    # 2. 前処理
    logger.info("ステップ2: レシピデータの前処理")
    processed_recipes = preprocess_recipes(recipes)
    
    # 3. ベクトルデータベース構築
    logger.info("ステップ3: ベクトルデータベース構築")
    vectorstore = build_vector_database(processed_recipes, str(output_dir))
    
    # 4. 完了報告
    logger.info("=== レシピベクトルDB構築完了 ===")
    logger.info(f"処理件数: {len(processed_recipes)}件")
    logger.info(f"出力先: {output_dir}")
    
    # 5. 簡単なテスト
    logger.info("ステップ4: 動作確認テスト")
    try:
        test_results = vectorstore.similarity_search("牛乳", k=3)
        logger.info(f"テスト検索結果: {len(test_results)}件")
        for i, result in enumerate(test_results):
            # メタデータの詳細を表示
            metadata = result.metadata
            title = metadata.get('title', 'Unknown')
            category = metadata.get('recipe_category', 'Unknown')
            logger.info(f"  {i+1}. {title} ({category})")
    except Exception as e:
        logger.warning(f"テスト検索に失敗: {e}")

if __name__ == "__main__":
    main()
