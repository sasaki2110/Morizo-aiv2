"""
Phase 3A テスト: LLM層の汎用メソッド `generate_candidates()`
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_servers.recipe_llm import RecipeLLM


async def test_generate_candidates_main():
    """主菜候補生成テスト"""
    llm_client = RecipeLLM()
    
    result = await llm_client.generate_candidates(
        inventory_items=["レンコン", "ニンジン", "牛豚合挽肉"],
        menu_type="",
        category="main",
        main_ingredient="レンコン",
        count=2
    )
    
    print("\n=== test_generate_candidates_main ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        candidates = result["data"]["candidates"]
        print(f"Generated {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
    
    assert result["success"], "主菜候補生成に失敗しました"
    assert len(result["data"]["candidates"]) == 2, "2件の候補が生成されていません"
    
    return result


async def test_generate_candidates_sub():
    """副菜候補生成テスト"""
    llm_client = RecipeLLM()
    
    result = await llm_client.generate_candidates(
        inventory_items=["ニンジン", "ピーマン", "もやし", "鶏もも肉"],
        menu_type="",
        category="sub",
        used_ingredients=["レンコン", "牛豚合挽肉"],  # 主菜で使った食材
        count=2
    )
    
    print("\n=== test_generate_candidates_sub ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        candidates = result["data"]["candidates"]
        print(f"Generated {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
            
            # 副菜候補に主菜で使った食材が含まれていないことを確認
            ingredients = candidate.get('ingredients', [])
            for used in ["レンコン", "牛豚合挽肉"]:
                assert used not in ingredients, f"副菜に使用済み食材({used})が含まれています"
    
    assert result["success"], "副菜候補生成に失敗しました"
    assert len(result["data"]["candidates"]) == 2, "2件の候補が生成されていません"
    
    return result


async def test_generate_candidates_soup():
    """汁物候補生成テスト"""
    llm_client = RecipeLLM()
    
    result = await llm_client.generate_candidates(
        inventory_items=["ニンジン", "大根", "豆腐", "チキン"],
        menu_type="",
        category="soup",
        used_ingredients=["レンコン", "鶏もも肉"],  # 主菜・副菜で使った食材
        count=2
    )
    
    print("\n=== test_generate_candidates_soup ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        candidates = result["data"]["candidates"]
        print(f"Generated {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
            
            # 汁物候補に既に使った食材が含まれていないことを確認
            ingredients = candidate.get('ingredients', [])
            for used in ["レンコン", "鶏もも肉"]:
                assert used not in ingredients, f"汁物に使用済み食材({used})が含まれています"
    
    assert result["success"], "汁物候補生成に失敗しました"
    assert len(result["data"]["candidates"]) == 2, "2件の候補が生成されていません"
    
    return result


async def test_generate_candidates_excluded():
    """除外レシピのテスト"""
    llm_client = RecipeLLM()
    
    result = await llm_client.generate_candidates(
        inventory_items=["レンコン", "ニンジン", "牛豚合挽肉"],
        menu_type="",
        category="main",
        main_ingredient="レンコン",
        excluded_recipes=["レンコンの肉巻き", "レンコンサラダ"],
        count=2
    )
    
    print("\n=== test_generate_candidates_excluded ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        candidates = result["data"]["candidates"]
        print(f"Generated {len(candidates)} candidates:")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
            
            # 除外レシピが含まれていないことを確認
            title = candidate.get('title', '')
            assert "レンコンの肉巻き" not in title, "除外レシピが生成されました"
            assert "レンコンサラダ" not in title, "除外レシピが生成されました"
    
    assert result["success"], "主菜候補生成に失敗しました"
    
    return result


async def main():
    """全テストを実行"""
    print("=" * 60)
    print("Phase 3A LLM層汎用メソッドテスト開始")
    print("=" * 60)
    
    try:
        # 主菜テスト
        await test_generate_candidates_main()
        print("\n✅ 主菜候補生成テスト: PASSED")
        
        # 副菜テスト
        await test_generate_candidates_sub()
        print("\n✅ 副菜候補生成テスト: PASSED")
        
        # 汁物テスト
        await test_generate_candidates_soup()
        print("\n✅ 汁物候補生成テスト: PASSED")
        
        # 除外レシピテスト
        await test_generate_candidates_excluded()
        print("\n✅ 除外レシピテスト: PASSED")
        
        print("\n" + "=" * 60)
        print("Phase 3A LLM層汎用メソッドテスト: ALL PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
