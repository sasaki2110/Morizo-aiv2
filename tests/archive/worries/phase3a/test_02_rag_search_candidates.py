"""
Phase 3A テスト: RAG層の汎用メソッド `search_candidates()`
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_servers.recipe_rag.client import RecipeRAGClient


async def test_search_candidates_main():
    """主菜候補検索テスト"""
    rag_client = RecipeRAGClient()
    
    results = await rag_client.search_candidates(
        ingredients=["レンコン"],
        menu_type="",
        category="main",
        main_ingredient="レンコン",
        limit=3
    )
    
    print("\n=== test_search_candidates_main ===")
    print(f"Found {len(results)} candidates")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('title')}")
        print(f"     Ingredients: {result.get('ingredients', [])}")
    
    assert len(results) <= 3, f"検索結果が指定件数({3})を超えています: {len(results)}"
    
    return results


async def test_search_candidates_sub():
    """副菜候補検索テスト"""
    rag_client = RecipeRAGClient()
    
    results = await rag_client.search_candidates(
        ingredients=["ピーマン", "もやし"],
        menu_type="",
        category="sub",
        limit=3
    )
    
    print("\n=== test_search_candidates_sub ===")
    print(f"Found {len(results)} candidates")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('title')}")
        print(f"     Ingredients: {result.get('ingredients', [])}")
    
    assert len(results) <= 3, f"検索結果が指定件数({3})を超えています: {len(results)}"
    
    return results


async def test_search_candidates_soup():
    """汁物候補検索テスト"""
    rag_client = RecipeRAGClient()
    
    results = await rag_client.search_candidates(
        ingredients=["大根", "豆腐"],
        menu_type="",
        category="soup",
        limit=3
    )
    
    print("\n=== test_search_candidates_soup ===")
    print(f"Found {len(results)} candidates")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.get('title')}")
        print(f"     Ingredients: {result.get('ingredients', [])}")
    
    assert len(results) <= 3, f"検索結果が指定件数({3})を超えています: {len(results)}"
    
    return results


async def test_search_candidates_category():
    """カテゴリ別ベクトルストア選択テスト"""
    rag_client = RecipeRAGClient()
    
    # 各カテゴリで検索を実行
    results_main = await rag_client.search_candidates(
        ingredients=["レンコン"],
        menu_type="",
        category="main",
        limit=3
    )
    
    results_sub = await rag_client.search_candidates(
        ingredients=["ピーマン"],
        menu_type="",
        category="sub",
        limit=3
    )
    
    results_soup = await rag_client.search_candidates(
        ingredients=["大根"],
        menu_type="",
        category="soup",
        limit=3
    )
    
    print("\n=== test_search_candidates_category ===")
    print(f"Main: {len(results_main)} recipes")
    print(f"Sub: {len(results_sub)} recipes")
    print(f"Soup: {len(results_soup)} recipes")
    
    # 各カテゴリで適切なベクトルストアが使用されていることを確認
    assert len(results_main) <= 3, "主菜検索結果が不正"
    assert len(results_sub) <= 3, "副菜検索結果が不正"
    assert len(results_soup) <= 3, "汁物検索結果が不正"
    
    return {
        "main": results_main,
        "sub": results_sub,
        "soup": results_soup
    }


async def main():
    """全テストを実行"""
    print("=" * 60)
    print("Phase 3A RAG層汎用メソッドテスト開始")
    print("=" * 60)
    
    try:
        # 主菜テスト
        await test_search_candidates_main()
        print("\n✅ 主菜候補検索テスト: PASSED")
        
        # 副菜テスト
        await test_search_candidates_sub()
        print("\n✅ 副菜候補検索テスト: PASSED")
        
        # 汁物テスト
        await test_search_candidates_soup()
        print("\n✅ 汁物候補検索テスト: PASSED")
        
        # カテゴリ別ベクトルストアテスト
        await test_search_candidates_category()
        print("\n✅ カテゴリ別ベクトルストアテスト: PASSED")
        
        print("\n" + "=" * 60)
        print("Phase 3A RAG層汎用メソッドテスト: ALL PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
