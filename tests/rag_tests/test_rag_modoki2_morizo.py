#!/usr/bin/env python3
"""
修正後ロジックのテストスクリプト
parts[0]から食材を抽出する実際のデータ構造での処理を検証
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def extract_ingredients_fixed_logic(content: str) -> str:
    """
    修正後ロジック：parts[0]から食材を抽出
    実際のデータ構造: "食材1 食材2 食材3"
    """
    parts = content.split(' | ')
    if len(parts) > 0:
        return parts[0]  # 食材部分を抽出
    else:
        return ""  # 空の場合は空文字列

def calculate_match_score_fixed_logic(recipe_ingredients: str, normalized_ingredients: list) -> tuple[float, list]:
    """
    修正後ロジックでのマッチングスコア計算
    """
    if not recipe_ingredients or not normalized_ingredients:
        return 0.0, []
    
    recipe_words = recipe_ingredients.split()
    matched_count = 0
    total_inventory = len(normalized_ingredients)
    matched_items = []
    
    for inventory_item in normalized_ingredients:
        # 完全マッチ
        if inventory_item in recipe_words:
            matched_count += 1
            matched_items.append(f"{inventory_item}(完全)")
        else:
            # 部分マッチ（在庫食材がレシピ食材に含まれる）
            for word in recipe_words:
                if inventory_item in word or word in inventory_item:
                    matched_count += 0.5
                    matched_items.append(f"{inventory_item}(部分:{word})")
                    break
    
    # スコア計算: マッチした食材数 / 在庫食材数
    match_score = matched_count / total_inventory if total_inventory > 0 else 0.0
    
    return match_score, matched_items

async def test_fixed_logic():
    """修正後ロジックでのテスト"""
    try:
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        
        print("=== 修正後ロジックテスト ===")
        
        # morizo_ai.logと同じ条件
        inventory_items = [
            'ピーマン', '鶏もも肉', 'もやし', 'ほうれん草', 'パン', 
            '豚バラブロック', 'ほうれん草', '牛すね肉', '人参', 
            '牛乳', '牛乳', '牛乳', '玉ねぎ', 'ジャガイモ', 'キャベツ'
        ]
        menu_type = "和食"
        
        print(f"在庫食材: {inventory_items}")
        print(f"メニュータイプ: {menu_type}")
        print()
        
        # RAGクライアント初期化
        client = RecipeRAGClient()
        vectorstore = client._get_vectorstore()
        
        # 食材の正規化
        normalized_ingredients = list(set(inventory_items))
        print(f"正規化後の食材: {normalized_ingredients}")
        
        # クエリ生成
        query = f"{' '.join(normalized_ingredients)} {menu_type}"
        print(f"生成されたクエリ: '{query}'")
        
        # ベクトル検索
        print("\n=== ベクトル検索実行 ===")
        vector_results = vectorstore.similarity_search(query, k=40)
        print(f"ベクトル検索結果: {len(vector_results)}件")
        
        if not vector_results:
            print("⚠️ ベクトル検索結果が0件です")
            return
        
        # 修正後ロジックでの処理
        print("\n=== 修正後ロジックでの処理 ===")
        print("実際のデータ構造: '食材1 食材2 食材3'")
        print("抽出ロジック: parts[0]から食材を抽出")
        print()
        
        valid_recipes = []
        invalid_recipes = []
        
        for i, result in enumerate(vector_results[:10]):  # 最初の10件をテスト
            print(f"\n--- レシピ {i+1} ---")
            
            metadata = result.metadata
            content = result.page_content
            title = metadata.get('title', 'Unknown')
            
            print(f"タイトル: {title}")
            print(f"コンテンツ: {content}")
            
            # 修正後ロジックで食材抽出
            recipe_ingredients = extract_ingredients_fixed_logic(content)
            print(f"抽出されたレシピ食材: '{recipe_ingredients}'")
            
            if recipe_ingredients:
                # マッチングスコア計算
                match_score, matched_items = calculate_match_score_fixed_logic(
                    recipe_ingredients, normalized_ingredients
                )
                
                print(f"レシピ食材単語: {recipe_ingredients.split()}")
                print(f"マッチした食材: {matched_items}")
                print(f"マッチングスコア: {match_score:.3f}")
                print(f"閾値(0.05)通過: {'✅' if match_score >= 0.05 else '❌'}")
                
                if match_score >= 0.05:
                    valid_recipes.append({
                        'title': title,
                        'score': match_score,
                        'ingredients': recipe_ingredients,
                        'matched_items': matched_items
                    })
                else:
                    invalid_recipes.append({
                        'title': title,
                        'score': match_score,
                        'reason': 'スコア不足'
                    })
            else:
                print("⚠️ 食材抽出失敗")
                invalid_recipes.append({
                    'title': title,
                    'score': 0.0,
                    'reason': '食材抽出失敗'
                })
        
        # 結果のまとめ
        print("\n=== 修正後ロジックの結果 ===")
        print(f"有効なレシピ: {len(valid_recipes)}件")
        print(f"無効なレシピ: {len(invalid_recipes)}件")
        
        if valid_recipes:
            print("\n有効なレシピ一覧:")
            for i, recipe in enumerate(valid_recipes):
                print(f"{i+1}. {recipe['title']} (スコア: {recipe['score']:.3f})")
                print(f"   食材: {recipe['ingredients']}")
                print(f"   マッチ: {recipe['matched_items']}")
        
        if invalid_recipes:
            print("\n無効なレシピ一覧:")
            for i, recipe in enumerate(invalid_recipes):
                print(f"{i+1}. {recipe['title']} (スコア: {recipe['score']:.3f}, 理由: {recipe['reason']})")
        
        # 修正前との比較
        print("\n=== 修正前との比較 ===")
        print("修正前ロジック（parts[1]）: 有効レシピ 0件")
        print(f"修正後ロジック（parts[0]）: 有効レシピ {len(valid_recipes)}件")
        
        if len(valid_recipes) > 0:
            print("✅ 修正後ロジックで正常に動作することを確認")
            print("→ 本番ソースの修正が必要")
        else:
            print("⚠️ 修正後ロジックでも有効なレシピが0件")
            print("→ 他の問題が存在する可能性")
        
        return {
            'valid_recipes': len(valid_recipes),
            'invalid_recipes': len(invalid_recipes),
            'total_tested': len(vector_results[:10]),
            'valid_recipe_details': valid_recipes
        }
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン処理"""
    print("修正後ロジックテスト開始")
    print("=" * 60)
    
    # 環境変数読み込み
    load_dotenv()
    
    # 非同期テスト実行
    result = asyncio.run(test_fixed_logic())
    
    print("\n" + "=" * 60)
    print("テスト完了")
    
    if result:
        print(f"有効なレシピ: {result['valid_recipes']}件")
        print(f"無効なレシピ: {result['invalid_recipes']}件")
        print(f"テスト対象: {result['total_tested']}件")
        
        if result['valid_recipes'] > 0:
            print("✅ 修正後ロジックで有効なレシピが取得できています")
            print("→ 本番ソースの修正が必要")
            
            # 上位3件の詳細表示
            if result['valid_recipe_details']:
                print("\n上位レシピの詳細:")
                for i, recipe in enumerate(result['valid_recipe_details'][:3]):
                    print(f"{i+1}. {recipe['title']}")
                    print(f"   スコア: {recipe['score']:.3f}")
                    print(f"   マッチ食材: {recipe['matched_items']}")
        else:
            print("⚠️ 修正後ロジックでも有効なレシピが0件")
            print("→ 他の問題が存在する可能性")

if __name__ == "__main__":
    main()
