#!/usr/bin/env python3
"""
主要食材のベクトルDB存在確認テスト
main_targetを変更することで、任意の食材でテスト可能
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_servers.recipe_rag.client import RecipeRAGClient

async def test_ingredient_in_vector_db():
    """ベクトルDBに指定食材のレシピが存在するか確認"""
    
    # ===== ここで主要食材を変更 =====
    main_target = "鯖"  # 他の食材に変更可能: "レンコン", "鶏もも肉", "豆腐" など
    # ================================
    
    print(f"🔍 {main_target}レシピの存在確認テスト")
    print("=" * 60)
    
    rag_client = RecipeRAGClient()
    
    # ベクトルストアを直接取得
    vectorstores = rag_client._get_vectorstores()
    main_vectorstore = vectorstores["main"]
    
    # テスト1: 主要食材で単純検索（多めに取得）
    print(f"\n📋 テスト1: '{main_target}'で50件検索")
    print("-" * 60)
    
    results = main_vectorstore.similarity_search(f"{main_target} 和食", k=50)
    
    print(f"検索結果: {len(results)}件")
    
    # 主要食材を含むレシピをカウント
    target_recipes = []
    for i, result in enumerate(results[:20]):  # 上位20件を確認
        content = result.page_content
        title = result.metadata.get('title', '')
        
        # contentからタイトルを抽出（metadataになければ）
        if not title:
            parts = content.split(' | ')
            if parts:
                title = parts[0].strip()
        
        # 主要食材が含まれるかチェック（カタカナ、ひらがな、漢字の可能性）
        ingredients = content.split()
        has_target = any(main_target in ing for ing in ingredients)
        
        if has_target:
            target_recipes.append((i+1, title, content))
        
        print(f"{i+1:2d}. {title[:40]:40s} {main_target}: {'○' if has_target else '×'}")
        if i < 5:  # 上位5件は食材も表示
            print(f"    食材: {' '.join(ingredients[:10])}")
    
    print(f"\n✅ {main_target}を含むレシピ: {len(target_recipes)}件 / {len(results[:20])}件中")
    
    # テスト2: 在庫食材を含めた検索
    print(f"\n📋 テスト2: 在庫食材+{main_target}で30件検索")
    print("-" * 60)
    
    inventory = ["鶏もも肉", "玉ねぎ", "にんじん", "じゃがいも", "キャベツ", "レンコン", "サバ", "豆腐", "卵", "米"]
    # クエリ: 主要食材を2回繰り返して強調（実装と同じ）
    query = f"{main_target} {main_target} {' '.join(inventory)} 和食"
    
    print(f"クエリ: {query[:80]}...")
    
    results2 = main_vectorstore.similarity_search(query, k=30)
    
    print(f"検索結果: {len(results2)}件")
    
    target_recipes2 = []
    for i, result in enumerate(results2[:15]):  # 上位15件を確認
        content = result.page_content
        title = result.metadata.get('title', '')
        
        if not title:
            parts = content.split(' | ')
            if parts:
                title = parts[0].strip()
        
        ingredients = content.split()
        has_target = any(main_target in ing for ing in ingredients)
        
        if has_target:
            target_recipes2.append((i+1, title, content))
        
        print(f"{i+1:2d}. {title[:40]:40s} {main_target}: {'○' if has_target else '×'}")
    
    print(f"\n✅ {main_target}を含むレシピ: {len(target_recipes2)}件 / {len(results2[:15])}件中")
    
    # 主要食材レシピの詳細を表示
    if target_recipes2:
        print(f"\n📝 {main_target}を含むレシピの詳細:")
        print("-" * 60)
        for rank, title, content in target_recipes2[:5]:  # 上位5件
            ingredients = content.split()
            print(f"{rank}. {title}")
            print(f"   食材: {', '.join(ingredients[:15])}")
            print()
    else:
        print(f"\n⚠️  上位15件に{main_target}を含むレシピが見つかりませんでした")
    
    # テスト3: 表記ゆれチェック
    print(f"\n📋 テスト3: 表記ゆれチェック")
    print("-" * 60)
    
    # 主要食材の代表的な表記ゆれパターン
    variations_map = {
        "サバ": ["サバ", "さば", "鯖"],
        "レンコン": ["レンコン", "れんこん", "蓮根"],
        "鶏もも肉": ["鶏もも肉", "鶏もも", "とりもも", "鳥もも"],
        "豆腐": ["豆腐", "とうふ", "トウフ"],
        "キャベツ": ["キャベツ", "きゃべつ", "甘藍"],
    }
    
    variations = variations_map.get(main_target, [main_target])
    
    print(f"チェックする表記: {', '.join(variations)}")
    
    for variation in variations:
        results3 = main_vectorstore.similarity_search(f"{variation} 和食", k=20)
        count = 0
        for result in results3[:10]:
            content = result.page_content
            ingredients = content.split()
            if any(variation in ing for ing in ingredients):
                count += 1
        print(f"  '{variation}': {count}件 / 10件中")
    
    print("\n🏁 テスト完了")

if __name__ == "__main__":
    asyncio.run(test_ingredient_in_vector_db())
