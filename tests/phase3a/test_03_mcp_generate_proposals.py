"""
Phase 3A テスト: MCP層の汎用メソッド `generate_proposals()`
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp_servers.recipe_mcp import generate_proposals


async def test_generate_proposals_main():
    """主菜5件提案テスト"""
    result = await generate_proposals(
        inventory_items=["レンコン", "ニンジン", "牛豚合挽肉"],
        user_id="test_user",
        category="main",
        menu_type="",
        main_ingredient="レンコン",
        token="test_token"
    )
    
    print("\n=== test_generate_proposals_main ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        data = result["data"]
        print(f"Category: {data.get('category')}")
        print(f"Total: {data.get('total')}")
        print(f"LLM count: {data.get('llm_count')}")
        print(f"RAG count: {data.get('rag_count')}")
        print(f"Candidates:")
        for i, candidate in enumerate(data.get('candidates', []), 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
    
    assert result["success"], "主菜提案に失敗しました"
    assert result["data"]["category"] == "main", "カテゴリが不正です"
    assert result["data"]["total"] == 5, f"5件の候補が生成されていません: {result['data']['total']}"
    
    return result


async def test_generate_proposals_sub():
    """副菜5件提案テスト"""
    result = await generate_proposals(
        inventory_items=["ニンジン", "ピーマン", "もやし", "鶏もも肉"],
        user_id="test_user",
        category="sub",
        menu_type="",
        used_ingredients=["レンコン", "牛豚合挽肉"],  # 主菜で使った食材
        token="test_token"
    )
    
    print("\n=== test_generate_proposals_sub ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        data = result["data"]
        print(f"Category: {data.get('category')}")
        print(f"Total: {data.get('total')}")
        print(f"LLM count: {data.get('llm_count')}")
        print(f"RAG count: {data.get('rag_count')}")
        print(f"Candidates:")
        for i, candidate in enumerate(data.get('candidates', []), 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
    
    assert result["success"], "副菜提案に失敗しました"
    assert result["data"]["category"] == "sub", "カテゴリが不正です"
    # 副菜・汁物では5件に満たない場合もあるため、柔軟にチェック
    assert result["data"]["total"] > 0, "候補が生成されていません"
    
    return result


async def test_generate_proposals_soup():
    """汁物5件提案テスト"""
    result = await generate_proposals(
        inventory_items=["大根", "豆腐", "チキン"],
        user_id="test_user",
        category="soup",
        menu_type="",
        used_ingredients=["レンコン", "鶏もも肉"],  # 主菜・副菜で使った食材
        token="test_token"
    )
    
    print("\n=== test_generate_proposals_soup ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        data = result["data"]
        print(f"Category: {data.get('category')}")
        print(f"Total: {data.get('total')}")
        print(f"LLM count: {data.get('llm_count')}")
        print(f"RAG count: {data.get('rag_count')}")
        print(f"Candidates:")
        for i, candidate in enumerate(data.get('candidates', []), 1):
            print(f"  {i}. {candidate.get('title')}")
            print(f"     Ingredients: {candidate.get('ingredients', [])}")
    
    assert result["success"], "汁物提案に失敗しました"
    assert result["data"]["category"] == "soup", "カテゴリが不正です"
    # 副菜・汁物では5件に満たない場合もあるため、柔軟にチェック
    assert result["data"]["total"] > 0, "候補が生成されていません"
    
    return result


async def test_generate_proposals_integration():
    """統合テスト: LLM+RAGの統合が正しく動作すること"""
    result = await generate_proposals(
        inventory_items=["レンコン", "ニンジン", "牛豚合挽肉", "ピーマン", "もやし"],
        user_id="test_user",
        category="main",
        menu_type="",
        main_ingredient="レンコン",
        token="test_token"
    )
    
    print("\n=== test_generate_proposals_integration ===")
    print(f"Success: {result.get('success')}")
    if result.get("success"):
        data = result["data"]
        print(f"LLM candidates: {data.get('llm_count')}")
        print(f"RAG candidates: {data.get('rag_count')}")
        print(f"Total candidates: {data.get('total')}")
    
    assert result["success"], "統合提案に失敗しました"
    assert data.get("llm_count", 0) > 0, "LLM候補が生成されていません"
    assert data.get("rag_count", 0) > 0, "RAG候補が生成されていません"
    assert data.get("total") == data.get("llm_count", 0) + data.get("rag_count", 0), "統合件数が不正です"
    
    return result


async def main():
    """全テストを実行"""
    print("=" * 60)
    print("Phase 3A MCP層汎用メソッドテスト開始")
    print("=" * 60)
    
    try:
        # 主菜テスト
        await test_generate_proposals_main()
        print("\n✅ 主菜提案テスト: PASSED")
        
        # 副菜テスト
        await test_generate_proposals_sub()
        print("\n✅ 副菜提案テスト: PASSED")
        
        # 汁物テスト
        await test_generate_proposals_soup()
        print("\n✅ 汁物提案テスト: PASSED")
        
        # 統合テスト
        await test_generate_proposals_integration()
        print("\n✅ 統合テスト: PASSED")
        
        print("\n" + "=" * 60)
        print("Phase 3A MCP層汎用メソッドテスト: ALL PASSED")
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
