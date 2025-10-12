#!/usr/bin/env python3
"""
morizo_ai.logと同等の条件でRAG検索テスト
和食指定での検索結果と主菜・副菜・汁物の分類を確認
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_morizo_like_rag():
    """morizo_ai.logと同等の条件でRAG検索テスト（詳細デバッグ版）"""
    try:
        from mcp_servers.recipe_rag.client import RecipeRAGClient
        from mcp_servers.recipe_rag.search import RecipeSearchEngine
        
        print("=== morizo_ai.log同等RAG検索テスト（詳細デバッグ版） ===")
        
        # morizo_ai.logと同じ条件
        inventory_items = [
            'ピーマン', '鶏もも肉', 'もやし', 'ほうれん草', 'パン', 
            '豚バラブロック', 'ほうれん草', '牛すね肉', '人参', 
            '牛乳', '牛乳', '牛乳', '玉ねぎ', 'ジャガイモ', 'キャベツ'
        ]
        menu_type = "和食"
        user_id = "user123"
        
        print(f"在庫食材: {inventory_items}")
        print(f"メニュータイプ: {menu_type}")
        print(f"ユーザーID: {user_id}")
        print()
        
        # RAGクライアント初期化
        client = RecipeRAGClient()
        
        # 1. 検索エンジンを直接取得して詳細テスト
        print("=== 検索エンジン直接テスト ===")
        search_engine = client._get_search_engine()
        vectorstore = client._get_vectorstore()
        
        # 食材の正規化（RAGクライアントと同じ処理）
        normalized_ingredients = list(set(inventory_items))
        print(f"正規化後の食材: {normalized_ingredients}")
        
        # クエリ生成（RAGクライアントと同じ処理）
        query = f"{' '.join(normalized_ingredients)} {menu_type}"
        print(f"生成されたクエリ: '{query}'")
        
        # ベクトル検索（RAGクライアントと同じ処理）
        print("\n=== ベクトル検索実行 ===")
        vector_results = vectorstore.similarity_search(query, k=40)  # limit * 4 = 10 * 4
        print(f"ベクトル検索結果: {len(vector_results)}件")
        
        if vector_results:
            print("ベクトル検索で取得されたレシピ（最初の5件）:")
            for i, result in enumerate(vector_results[:5]):
                title = result.metadata.get("title", "Unknown")
                print(f"{i+1}. {title}")
        else:
            print("⚠️ ベクトル検索結果が0件です")
        
        # 2. 部分マッチングテスト（RAGクライアントと同じ処理）
        print("\n=== 部分マッチングテスト ===")
        
        # 部分マッチングの詳細デバッグ
        print("部分マッチングの詳細デバッグ:")
        print(f"在庫食材: {normalized_ingredients}")
        print(f"閾値: 0.05")
        print()
        
        # ベクトル検索結果の最初の5件を詳細分析
        print("ベクトル検索結果の詳細分析（最初の5件）:")
        for i, result in enumerate(vector_results[:5]):
            print(f"\n--- レシピ {i+1} ---")
            
            # メタデータとコンテンツの表示
            metadata = result.metadata
            content = result.page_content
            
            print(f"タイトル: {metadata.get('title', 'Unknown')}")
            print(f"コンテンツ: {content}")
            
            # レシピ食材の抽出
            parts = content.split(' | ')
            print(f"分割結果: {parts}")
            
            if len(parts) > 1:
                recipe_ingredients = parts[1]
                print(f"抽出されたレシピ食材: '{recipe_ingredients}'")
                
                # マッチングスコア計算の詳細
                if recipe_ingredients:
                    recipe_words = recipe_ingredients.split()
                    print(f"レシピ食材単語: {recipe_words}")
                    
                    matched_count = 0
                    matched_items = []
                    unmatched_items = []
                    
                    for inventory_item in normalized_ingredients:
                        # 完全マッチ
                        if inventory_item in recipe_words:
                            matched_count += 1
                            matched_items.append(f"{inventory_item}(完全)")
                        else:
                            # 部分マッチ
                            partial_match = False
                            for word in recipe_words:
                                if inventory_item in word or word in inventory_item:
                                    matched_count += 0.5
                                    matched_items.append(f"{inventory_item}(部分:{word})")
                                    partial_match = True
                                    break
                            if not partial_match:
                                unmatched_items.append(inventory_item)
                    
                    match_score = matched_count / len(normalized_ingredients)
                    print(f"マッチした食材: {matched_items}")
                    print(f"マッチしなかった食材: {unmatched_items}")
                    print(f"マッチ数: {matched_count}")
                    print(f"マッチングスコア: {match_score:.3f}")
                    print(f"閾値(0.05)通過: {'✅' if match_score >= 0.05 else '❌'}")
                else:
                    print("⚠️ レシピ食材が空です")
            else:
                print("⚠️ コンテンツの分割に失敗しました")
        
        # 実際の部分マッチング実行
        print("\n=== 部分マッチング実行 ===")
        partial_results = await search_engine.search_recipes_by_partial_match(
            ingredients=inventory_items,
            menu_type=menu_type,
            excluded_recipes=None,
            limit=10,
            min_match_score=0.05  # RAGクライアントと同じ閾値
        )
        
        print(f"部分マッチング結果: {len(partial_results)}件")
        
        if partial_results:
            print("部分マッチングで取得されたレシピ:")
            for i, result in enumerate(partial_results):
                title = result.get("title", "Unknown")
                match_score = result.get("match_score", 0.0)
                matched_ingredients = result.get("matched_ingredients", [])
                print(f"{i+1}. {title} (スコア: {match_score:.3f}, マッチ食材: {matched_ingredients})")
        else:
            print("⚠️ 部分マッチング結果が0件です")
        
        # 3. RAGクライアント経由の検索（元の処理）
        print("\n=== RAGクライアント経由検索 ===")
        rag_results = await client.search_similar_recipes(
            ingredients=inventory_items,
            menu_type=menu_type,
            excluded_recipes=None,
            limit=10
        )
        
        print(f"RAGクライアント検索結果: {len(rag_results)}件")
        
        if rag_results:
            print("RAGクライアントで取得されたレシピ:")
            for i, result in enumerate(rag_results):
                title = result.get("title", "Unknown")
                category = result.get("category", "Unknown")
                print(f"{i+1}. {title} (カテゴリ: {category})")
        else:
            print("⚠️ RAGクライアント検索結果が0件です")
        
        # 4. 献立形式に変換
        print("\n=== 献立形式変換 ===")
        menu_result = await client.convert_rag_results_to_menu_format(
            rag_results=rag_results,
            inventory_items=inventory_items,
            menu_type=menu_type
        )
        
        print(f"変換結果: {menu_result}")
        
        # 5. 分類結果の詳細表示
        print("\n=== 分類結果詳細 ===")
        selected_menu = menu_result.get("selected", {})
        
        print("主菜 (main_dish):")
        main_dish = selected_menu.get("main_dish", {})
        if main_dish.get("title"):
            print(f"  - {main_dish['title']}")
            print(f"  - 食材: {main_dish.get('ingredients', [])}")
        else:
            print("  - なし")
        
        print("\n副菜 (side_dish):")
        side_dish = selected_menu.get("side_dish", {})
        if side_dish.get("title"):
            print(f"  - {side_dish['title']}")
            print(f"  - 食材: {side_dish.get('ingredients', [])}")
        else:
            print("  - なし")
        
        print("\n汁物 (soup):")
        soup = selected_menu.get("soup", {})
        if soup.get("title"):
            print(f"  - {soup['title']}")
            print(f"  - 食材: {soup.get('ingredients', [])}")
        else:
            print("  - なし")
        
        # 6. test_rag_search.pyとの比較テスト
        print("\n=== test_rag_search.py同等テスト ===")
        print("test_rag_search.pyと同じ方法で直接ベクトル検索")
        
        # 食材のみのクエリ（test_rag_search.pyと同じ）
        simple_query = ' '.join(normalized_ingredients)
        print(f"シンプルクエリ: '{simple_query}'")
        
        simple_results = vectorstore.similarity_search(simple_query, k=5)
        print(f"シンプル検索結果: {len(simple_results)}件")
        
        if simple_results:
            print("シンプル検索で取得されたレシピ:")
            for i, result in enumerate(simple_results):
                title = result.metadata.get("title", "Unknown")
                print(f"{i+1}. {title}")
        
        # 7. 和食指定なしでの検索テスト
        print("\n=== 和食指定なしでの検索テスト ===")
        rag_results_no_menu_type = await client.search_similar_recipes(
            ingredients=inventory_items,
            menu_type="",  # 空文字で指定なし
            excluded_recipes=None,
            limit=10
        )
        
        print(f"和食指定なしの検索結果: {len(rag_results_no_menu_type)}件")
        
        if rag_results_no_menu_type:
            print("和食指定なしで取得されたレシピ:")
            for i, result in enumerate(rag_results_no_menu_type[:5]):
                title = result.get("title", "Unknown")
                print(f"{i+1}. {title}")
        
        # 8. 結果のまとめ
        print("\n=== 結果のまとめ ===")
        print(f"ベクトル検索（食材+和食）: {len(vector_results)}件")
        print(f"部分マッチング（食材+和食）: {len(partial_results)}件")
        print(f"RAGクライアント（食材+和食）: {len(rag_results)}件")
        print(f"シンプル検索（食材のみ）: {len(simple_results)}件")
        print(f"RAGクライアント（食材のみ）: {len(rag_results_no_menu_type)}件")
        
        return {
            "vector_search": len(vector_results),
            "partial_match": len(partial_results),
            "rag_client_with_menu": len(rag_results),
            "simple_search": len(simple_results),
            "rag_client_without_menu": len(rag_results_no_menu_type),
            "menu_result": menu_result
        }
        
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """メイン処理"""
    print("morizo_ai.log同等RAG検索テスト開始")
    print("=" * 60)
    
    # 環境変数読み込み
    load_dotenv()
    
    # 非同期テスト実行
    result = asyncio.run(test_morizo_like_rag())
    
    print("\n" + "=" * 60)
    print("テスト完了")
    
    if result:
        print(f"ベクトル検索（食材+和食）: {result['vector_search']}件")
        print(f"部分マッチング（食材+和食）: {result['partial_match']}件")
        print(f"RAGクライアント（食材+和食）: {result['rag_client_with_menu']}件")
        print(f"シンプル検索（食材のみ）: {result['simple_search']}件")
        print(f"RAGクライアント（食材のみ）: {result['rag_client_without_menu']}件")
        
        # 問題の特定
        if result['vector_search'] > 0 and result['partial_match'] == 0:
            print("⚠️ 部分マッチングフィルタが原因で検索結果が0件になっています")
        elif result['vector_search'] == 0:
            print("⚠️ ベクトル検索自体が0件です（和食指定が原因の可能性）")
        elif result['simple_search'] > 0 and result['rag_client_with_menu'] == 0:
            print("⚠️ RAGクライアントの処理に問題があります")
        else:
            print("✅ 各段階で検索結果が取得できています")

if __name__ == "__main__":
    main()
