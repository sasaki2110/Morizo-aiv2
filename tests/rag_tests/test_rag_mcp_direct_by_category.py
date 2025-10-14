#!/usr/bin/env python3
"""
RAG検索機能の直接テスト（3つのベクトルDB対応）

RecipeRAGClientの新しいsearch_recipes_by_category()メソッドを直接テスト
06_7_test_mcp_rag.pyのパターンを参考に実装
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ログ設定のインポート
from config.loggers import GenericLogger
from config.logging import setup_logging

# テスト対象のインポート
from mcp_servers.recipe_rag import RecipeRAGClient

async def test_rag_client_category_search():
    """RAG検索クライアントの3つのベクトルDB検索テスト"""
    logger = GenericLogger("test", "rag_category_direct", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe RAG Client Category Search...")
    
    try:
        # RAG検索クライアントの初期化
        rag_client = RecipeRAGClient()
        logger.info("✅ [TEST] RAG client initialized successfully")
        
        # 3つのベクトルストアの取得テスト
        logger.info("📋 [TEST] Testing 3 vectorstores access...")
        vectorstores = rag_client._get_vectorstores()
        assert vectorstores is not None, "Vectorstores should not be None"
        assert "main" in vectorstores, "Main vectorstore should exist"
        assert "sub" in vectorstores, "Sub vectorstore should exist"
        assert "soup" in vectorstores, "Soup vectorstore should exist"
        
        for category, vectorstore in vectorstores.items():
            assert hasattr(vectorstore, 'similarity_search'), f"{category} vectorstore should have similarity_search method"
        
        logger.info("✅ [TEST] 3 vectorstores access successful")
        
        # テスト用の在庫食材リスト
        test_ingredients = [
            "ピーマン", "鶏もも肉", "もやし", "ほうれん草", "パン", 
            "豚バラブロック", "牛すね肉", "人参", 
            "牛乳", "玉ねぎ", "ジャガイモ", "キャベツ"
        ]
        
        logger.info(f"📋 [TEST] Testing category search with ingredients: {test_ingredients}")
        
        # 3つのベクトルDBでの並列検索テスト
        results = await rag_client.search_recipes_by_category(
            ingredients=test_ingredients,
            menu_type="和食",
            limit=5
        )
        
        assert isinstance(results, dict), "Results should be a dictionary"
        assert "main" in results, "Results should have 'main' key"
        assert "sub" in results, "Results should have 'sub' key"
        assert "soup" in results, "Results should have 'soup' key"
        
        logger.info(f"✅ [TEST] Category search successful:")
        logger.info(f"  主菜: {len(results['main'])}件")
        logger.info(f"  副菜: {len(results['sub'])}件")
        logger.info(f"  汁物: {len(results['soup'])}件")
        
        # 各カテゴリの結果を検証
        for category, category_results in results.items():
            assert isinstance(category_results, list), f"{category} results should be a list"
            assert len(category_results) <= 5, f"Expected max 5 results for {category}, got {len(category_results)}"
            
            logger.info(f"📋 [TEST] {category} category results:")
            for i, result in enumerate(category_results):
                assert isinstance(result, dict), f"{category} result {i} should be a dict"
                assert "title" in result, f"{category} result {i} should have 'title' key"
                assert "category" in result, f"{category} result {i} should have 'category' key"
                
                title = result.get('title', 'N/A')
                category_name = result.get('category', 'N/A')
                main_ingredients = result.get('main_ingredients', 'N/A')
                
                logger.info(f"   📝 {category.title()} Recipe {i+1}: {title}")
                logger.info(f"      - 分類: {category_name}")
                logger.info(f"      - カテゴリ詳細: {result.get('category_detail', 'N/A')}")
                logger.info(f"      - 主材料: {main_ingredients}")
                
                print(f"{category.title()} {i+1}. {title}")
                print(f"   分類: {category_name}")
                print(f"   主材料: {main_ingredients}")
                print()
        
        # 分類の正確性を検証
        logger.info("📋 [TEST] Verifying category accuracy...")
        
        # 主菜の分類確認
        for result in results['main']:
            category = result.get('category', '')
            assert '主菜' in category, f"Main dish result should have '主菜' in category: {result.get('title', 'N/A')}"
        
        # 副菜の分類確認
        for result in results['sub']:
            category = result.get('category', '')
            assert '副菜' in category, f"Side dish result should have '副菜' in category: {result.get('title', 'N/A')}"
        
        # 汁物の分類確認
        for result in results['soup']:
            category_detail = result.get('category_detail', '')
            assert '汁もの' in category_detail or 'スープ' in category_detail or '味噌汁' in category_detail, f"Soup result should have soup-related category_detail: {result.get('title', 'N/A')}"
        
        logger.info("✅ [TEST] Category accuracy verification passed")
        
        # 重複チェック
        logger.info("📋 [TEST] Checking for duplicates across categories...")
        all_titles = []
        for category_results in results.values():
            for result in category_results:
                title = result.get('title', '')
                assert title not in all_titles, f"Duplicate recipe found: {title}"
                all_titles.append(title)
        
        logger.info("✅ [TEST] No duplicates found across categories")
        
        logger.info("🎉 [TEST] All RAG client category search tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG client category search test failed: {e}")
        return False

async def test_rag_client_traditional_search():
    """従来の単一ベクトルDB検索のテスト（互換性確認）"""
    logger = GenericLogger("test", "rag_traditional_direct", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe RAG Client Traditional Search...")
    
    try:
        # RAG検索クライアントの初期化
        rag_client = RecipeRAGClient()
        logger.info("✅ [TEST] RAG client initialized successfully")
        
        # 従来のベクトルストアの取得テスト
        logger.info("📋 [TEST] Testing traditional vectorstore access...")
        vectorstore = rag_client._get_vectorstore()
        assert vectorstore is not None, "Traditional vectorstore should not be None"
        assert hasattr(vectorstore, 'similarity_search'), "Traditional vectorstore should have similarity_search method"
        logger.info("✅ [TEST] Traditional vectorstore access successful")
        
        # テスト用の在庫食材リスト（3ベクトルDBテストと同じ食材）
        test_ingredients = [
            "ピーマン", "鶏もも肉", "もやし", "ほうれん草", "パン", 
            "豚バラブロック", "牛すね肉", "人参", 
            "牛乳", "玉ねぎ", "ジャガイモ", "キャベツ"
        ]
        
        logger.info(f"📋 [TEST] Testing traditional search with ingredients: {test_ingredients}")
        
        # 従来の検索テスト
        results = await rag_client.search_similar_recipes(
            ingredients=test_ingredients,
            menu_type="和食",
            limit=3
        )
        
        assert isinstance(results, list), "Traditional results should be a list"
        assert len(results) <= 3, f"Expected max 3 results, got {len(results)}"
        
        logger.info(f"✅ [TEST] Traditional search successful: {len(results)} results")
        
        if results:
            logger.info(f"📋 [TEST] Traditional search results:")
            for i, result in enumerate(results):
                assert isinstance(result, dict), f"Traditional result {i} should be a dict"
                assert "title" in result, f"Traditional result {i} should have 'title' key"
                assert "category" in result, f"Traditional result {i} should have 'category' key"
                
                title = result.get('title', 'N/A')
                category = result.get('category', 'N/A')
                main_ingredients = result.get('main_ingredients', 'N/A')
                
                logger.info(f"   📝 Traditional Recipe {i+1}: {title}")
                logger.info(f"      - 分類: {category}")
                logger.info(f"      - 主材料: {main_ingredients}")
                
                print(f"Traditional {i+1}. {title}")
                print(f"   分類: {category}")
                print(f"   主材料: {main_ingredients}")
                print()
        else:
            logger.warning("📋 [TEST] No traditional recipes found")
        
        logger.info("🎉 [TEST] All RAG client traditional search tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG client traditional search test failed: {e}")
        return False

async def test_rag_integration_comparison():
    """RAG統合比較テスト（3つのベクトルDB vs 従来の単一ベクトルDB）"""
    logger = GenericLogger("test", "rag_integration_comparison", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing RAG Integration Comparison...")
    
    try:
        # テスト用の在庫食材リスト
        test_ingredients = [
            "ピーマン", "鶏もも肉", "もやし", "ほうれん草", "パン", 
            "豚バラブロック", "牛すね肉", "人参", 
            "牛乳", "玉ねぎ", "ジャガイモ", "キャベツ"
        ]
        
        logger.info(f"📋 [TEST] Testing with inventory items: {test_ingredients}")
        
        # RAG検索クライアントの初期化
        rag_client = RecipeRAGClient()
        
        # 3つのベクトルDBでの検索
        logger.info("📋 [TEST] Testing 3-vector DB search...")
        category_results = await rag_client.search_recipes_by_category(
            ingredients=test_ingredients,
            menu_type="和食",
            limit=5
        )
        
        logger.info(f"✅ [TEST] 3-vector DB search completed:")
        logger.info(f"  主菜: {len(category_results['main'])}件")
        logger.info(f"  副菜: {len(category_results['sub'])}件")
        logger.info(f"  汁物: {len(category_results['soup'])}件")
        
        # 従来の単一ベクトルDBでの検索
        logger.info("📋 [TEST] Testing traditional single-vector DB search...")
        traditional_results = await rag_client.search_similar_recipes(
            ingredients=test_ingredients,
            menu_type="和食",
            limit=15  # 3つのベクトルDBの合計と同程度
        )
        
        logger.info(f"✅ [TEST] Traditional search completed: {len(traditional_results)} results")
        
        # 結果の比較
        logger.info("📋 [TEST] Comparing results...")
        
        # 3つのベクトルDBの結果を統合
        all_category_results = []
        for category_results_list in category_results.values():
            all_category_results.extend(category_results_list)
        
        logger.info(f"📊 [TEST] Comparison Results:")
        logger.info(f"  3-vector DB total: {len(all_category_results)} recipes")
        logger.info(f"  Traditional total: {len(traditional_results)} recipes")
        
        # 分類の精度比較
        category_main_count = len([r for r in all_category_results if '主菜' in r.get('category', '')])
        category_sub_count = len([r for r in all_category_results if '副菜' in r.get('category', '')])
        category_soup_count = len([r for r in all_category_results if '汁物' in r.get('category', '') or 'スープ' in r.get('category', '')])
        
        traditional_main_count = len([r for r in traditional_results if '主菜' in r.get('category', '')])
        traditional_sub_count = len([r for r in traditional_results if '副菜' in r.get('category', '')])
        traditional_soup_count = len([r for r in traditional_results if '汁物' in r.get('category', '') or 'スープ' in r.get('category', '')])
        
        logger.info(f"📊 [TEST] Category Distribution:")
        logger.info(f"  3-vector DB - 主菜: {category_main_count}, 副菜: {category_sub_count}, 汁物: {category_soup_count}")
        logger.info(f"  Traditional - 主菜: {traditional_main_count}, 副菜: {traditional_sub_count}, 汁物: {traditional_soup_count}")
        
        print(f"\n📊 Comparison Results:")
        print(f"3-vector DB total: {len(all_category_results)} recipes")
        print(f"Traditional total: {len(traditional_results)} recipes")
        print(f"\nCategory Distribution:")
        print(f"3-vector DB - 主菜: {category_main_count}, 副菜: {category_sub_count}, 汁物: {category_soup_count}")
        print(f"Traditional - 主菜: {traditional_main_count}, 副菜: {traditional_sub_count}, 汁物: {traditional_soup_count}")
        
        logger.info("🎉 [TEST] RAG integration comparison test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG integration comparison test failed: {e}")
        return False

async def main():
    """メイン実行関数"""
    print("🧪 RAG検索機能の直接テスト（3つのベクトルDB対応）を開始します...")
    print("=" * 60)
    
    # ログ設定の初期化
    setup_logging(initialize=False)
    
    passed = 0
    total = 0
    
    # 3つのベクトルDB検索のテスト
    print("\n🔍 3つのベクトルDB検索のテスト")
    total += 1
    if await test_rag_client_category_search():
        passed += 1
        print("✅ 3つのベクトルDB検索のテスト: PASSED")
    else:
        print("❌ 3つのベクトルDB検索のテスト: FAILED")
    
    # 従来の単一ベクトルDB検索のテスト
    print("\n🔍 従来の単一ベクトルDB検索のテスト")
    total += 1
    if await test_rag_client_traditional_search():
        passed += 1
        print("✅ 従来の単一ベクトルDB検索のテスト: PASSED")
    else:
        print("❌ 従来の単一ベクトルDB検索のテスト: FAILED")
    
    # 統合比較テスト
    print("\n🔗 統合比較テスト")
    total += 1
    if await test_rag_integration_comparison():
        passed += 1
        print("✅ 統合比較テスト: PASSED")
    else:
        print("❌ 統合比較テスト: FAILED")
    
    # 結果表示
    print("\n" + "=" * 60)
    print(f"📊 テスト結果: {passed}/{total} パス")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        return True
    else:
        print(f"⚠️  {total - passed}個のテストが失敗しました。")
        return False

if __name__ == "__main__":
    # テスト実行
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
