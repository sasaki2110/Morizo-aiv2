#!/usr/bin/env python3
"""
RAG検索結果のingredientsフィールドが空になる問題の調査スクリプト
問題: RAG検索結果で"ingredients": []が空になっている
原因調査: ベクトルDBの構造と検索結果の取得方法を確認
"""

import asyncio
import json
import os
import sys
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_servers.recipe_llm import RecipeLLM
from mcp_servers.recipe_rag.client import RecipeRAGClient
from config.loggers import GenericLogger

# ロガーの設定
logger = GenericLogger("test", "main_dish_proposals", initialize_logging=False)

async def test_rag_ingredients_issue():
    """RAG検索結果のingredientsフィールドが空になる問題の調査"""
    
    print("🔍 RAG検索結果のingredientsフィールド問題調査")
    print("=" * 50)
    
    # クライアントの初期化
    llm_client = RecipeLLM()
    rag_client = RecipeRAGClient()
    
    # テスト用の在庫食材
    inventory_items = [
        "鶏もも肉", "玉ねぎ", "にんじん", "じゃがいも", "キャベツ", 
        "レンコン", "サバ", "豆腐", "卵", "米"
    ]
    
    # テストケース1: 主要食材指定なし
    print("\n📋 テストケース1: 主要食材指定なし")
    print("-" * 30)
    
    # LLMで2件生成
    llm_result1 = await llm_client.generate_main_dish_candidates(
        inventory_items=inventory_items,
        menu_type="和食",
        main_ingredient=None,
        excluded_recipes=None,
        count=2
    )
    
    # RAGで3件検索
    rag_result1 = await rag_client.search_main_dish_candidates(
        ingredients=inventory_items,
        menu_type="和食",
        main_ingredient=None,
        excluded_recipes=None,
        limit=3
    )
    
    print(f"✅ LLM結果1: {json.dumps(llm_result1, ensure_ascii=False, indent=2)}")
    print(f"✅ RAG結果1: {json.dumps(rag_result1, ensure_ascii=False, indent=2)}")
    
    # テストケース2: 主要食材指定あり
    main_target = "サバ"

    print("\n📋 テストケース2: 主要食材指定あり（" + main_target + "）")
    print("-" * 30)

    
    # LLMで2件生成（ターゲット指定）
    llm_result2 = await llm_client.generate_main_dish_candidates(
        inventory_items=inventory_items,
        menu_type="和食",
        main_ingredient=main_target,
        excluded_recipes=None,
        count=2
    )
    
    # RAGで3件検索（ターゲット指定）
    rag_result2 = await rag_client.search_main_dish_candidates(
        ingredients=inventory_items,
        menu_type="和食",
        main_ingredient=main_target,
        excluded_recipes=None,
        limit=3
    )
    
    print(f"✅ LLM結果2: {json.dumps(llm_result2, ensure_ascii=False, indent=2)}")
    print(f"✅ RAG結果2: {json.dumps(rag_result2, ensure_ascii=False, indent=2)}")
    
    # テストケース3: 除外レシピ指定あり
    print("\n📋 テストケース3: 除外レシピ指定あり")
    print("-" * 30)
    
    excluded_recipes = ["レンコン炒め", "レンコンサラダ"]
    
    # LLMで2件生成（除外レシピ指定）
    llm_result3 = await llm_client.generate_main_dish_candidates(
        inventory_items=inventory_items,
        menu_type="和食",
        main_ingredient=main_target,
        excluded_recipes=excluded_recipes,
        count=2
    )
    
    # RAGで3件検索（除外レシピ指定）
    rag_result3 = await rag_client.search_main_dish_candidates(
        ingredients=inventory_items,
        menu_type="和食",
        main_ingredient=main_target,
        excluded_recipes=excluded_recipes,
        limit=3
    )
    
    print(f"✅ LLM結果3: {json.dumps(llm_result3, ensure_ascii=False, indent=2)}")
    print(f"✅ RAG結果3: {json.dumps(rag_result3, ensure_ascii=False, indent=2)}")
    
    # 結果の分析
    print("\n📊 結果分析")
    print("=" * 50)
    
    test_cases = [
        ("主要食材指定なし", llm_result1, rag_result1),
        (main_target + "指定", llm_result2, rag_result2),
        ("除外レシピ指定", llm_result3, rag_result3)
    ]
    
    for i, (case_name, llm_result, rag_result) in enumerate(test_cases, 1):
        print(f"\nテストケース{i}: {case_name}")
        print(f"  LLM結果: {'成功' if llm_result.get('success') else '失敗'}")
        if llm_result.get('success'):
            llm_candidates = llm_result['data']['candidates']
            print(f"    - LLM生成数: {len(llm_candidates)}")
            for j, candidate in enumerate(llm_candidates, 1):
                print(f"      {j}. {candidate['title']}")
                print(f"         食材: {candidate.get('ingredients', [])}")
        else:
            print(f"    - エラー: {llm_result.get('error')}")
        
        print(f"  RAG結果: {'成功' if rag_result else '失敗'}")
        if rag_result:
            print(f"    - RAG検索数: {len(rag_result)}")
            for j, recipe in enumerate(rag_result, 1):
                print(f"      {j}. {recipe['title']}")
                print(f"         食材: {recipe.get('ingredients', [])}")
        else:
            print(f"    - エラー: RAG検索結果なし")
    
    print("\n🏁 テスト完了")

if __name__ == "__main__":
    asyncio.run(test_rag_ingredients_issue())
