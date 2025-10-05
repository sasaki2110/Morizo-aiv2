#!/usr/bin/env python3
"""
RAG検索機能の単体試験

埋め込みサービスとRAG検索クライアントの動作確認
morizo_ai.logにログ出力
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 認証ユーティリティのインポート
sys.path.append(os.path.join(os.path.dirname(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("test_util", os.path.join(os.path.dirname(__file__), "00_1_test_util.py"))
test_util = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_util)

# MCPクライアントのインポート
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "mcp_servers"))
from client import MCPClient
from config.loggers import GenericLogger
from config.logging import setup_logging

# テスト対象のインポート
from mcp_servers.recipe_embeddings import RecipeEmbeddingsService
from mcp_servers.recipe_rag import RecipeRAGClient

async def test_embeddings_service():
    """埋め込みサービスのテスト"""
    logger = GenericLogger("test", "rag_embeddings", initialize_logging=True)
    
    logger.info("🧪 [TEST] Testing Recipe Embeddings Service...")
    
    try:
        # 埋め込みサービスの初期化
        embeddings_service = RecipeEmbeddingsService()
        logger.info("✅ [TEST] Embeddings service initialized successfully")
        
        # レシピテキストの埋め込み生成テスト
        recipe_text = "牛乳と卵のフレンチトースト 牛乳 卵 パン その他"
        logger.info(f"📋 [TEST] Testing recipe text embedding: {recipe_text}")
        
        embedding = await embeddings_service.generate_recipe_embedding(recipe_text)
        
        # 埋め込みベクトルの検証
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) == 1536, f"Expected 1536 dimensions, got {len(embedding)}"
        assert all(isinstance(x, float) for x in embedding), "All elements should be floats"
        
        logger.info(f"✅ [TEST] Recipe embedding generated successfully: {len(embedding)} dimensions")
        
        # 食材リストの埋め込み生成テスト
        ingredients = ["牛乳", "卵", "パン"]
        logger.info(f"📋 [TEST] Testing ingredients embedding: {ingredients}")
        
        ingredients_embedding = await embeddings_service.generate_ingredients_embedding(ingredients)
        
        assert isinstance(ingredients_embedding, list), "Ingredients embedding should be a list"
        assert len(ingredients_embedding) == 1536, f"Expected 1536 dimensions, got {len(ingredients_embedding)}"
        
        logger.info(f"✅ [TEST] Ingredients embedding generated successfully: {len(ingredients_embedding)} dimensions")
        
        # クエリの埋め込み生成テスト
        query = "牛乳を使ったレシピ"
        logger.info(f"📋 [TEST] Testing query embedding: {query}")
        
        query_embedding = await embeddings_service.generate_query_embedding(query)
        
        assert isinstance(query_embedding, list), "Query embedding should be a list"
        assert len(query_embedding) == 1536, f"Expected 1536 dimensions, got {len(query_embedding)}"
        
        logger.info(f"✅ [TEST] Query embedding generated successfully: {len(query_embedding)} dimensions")
        
        logger.info("🎉 [TEST] All embeddings service tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] Embeddings service test failed: {e}")
        return False

async def test_rag_client():
    """RAG検索クライアントのテスト"""
    logger = GenericLogger("test", "rag_client", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing Recipe RAG Client...")
    
    try:
        # RAG検索クライアントの初期化
        rag_client = RecipeRAGClient()
        logger.info("✅ [TEST] RAG client initialized successfully")
        
        # ベクトルストアの取得テスト
        logger.info("📋 [TEST] Testing vectorstore access...")
        vectorstore = rag_client._get_vectorstore()
        assert vectorstore is not None, "Vectorstore should not be None"
        assert hasattr(vectorstore, 'similarity_search'), "Vectorstore should have similarity_search method"
        logger.info("✅ [TEST] Vectorstore access successful")
        
        # 類似レシピ検索テスト
        ingredients = ["牛乳", "卵"]
        logger.info(f"📋 [TEST] Testing similar recipe search with ingredients: {ingredients}")
        
        results = await rag_client.search_similar_recipes(
            ingredients=ingredients,
            menu_type="和食",
            limit=3
        )
        
        assert isinstance(results, list), "Results should be a list"
        assert len(results) <= 3, f"Expected max 3 results, got {len(results)}"
        
        logger.info(f"✅ [TEST] Similar recipe search successful: {len(results)} results")
        
        if results:
            logger.info(f"📋 [TEST] Similar recipe search results:")
            for i, result in enumerate(results):
                assert isinstance(result, dict), f"Result {i} should be a dict"
                assert "title" in result, f"Result {i} should have 'title' key"
                assert "category" in result, f"Result {i} should have 'category' key"
                
                title = result.get('title', 'N/A')
                category = result.get('category', 'N/A')
                main_ingredients = result.get('main_ingredients', 'N/A')
                
                logger.info(f"   📝 Recipe {i+1}: {title}")
                logger.info(f"      - 分類: {category}")
                logger.info(f"      - 主材料: {main_ingredients}")
        else:
            logger.warning("📋 [TEST] No similar recipes found")
        
        # クエリベース検索テスト
        query = "牛乳を使ったレシピ"
        logger.info(f"📋 [TEST] Testing query-based search: {query}")
        
        query_results = await rag_client.search_by_query(query, limit=3)
        
        assert isinstance(query_results, list), "Query results should be a list"
        assert len(query_results) <= 3, f"Expected max 3 results, got {len(query_results)}"
        
        logger.info(f"✅ [TEST] Query-based search successful: {len(query_results)} results")
        
        if query_results:
            logger.info(f"📋 [TEST] Query-based search results:")
            for i, result in enumerate(query_results):
                assert isinstance(result, dict), f"Query result {i} should be a dict"
                assert "title" in result, f"Query result {i} should have 'title' key"
                
                title = result.get('title', 'N/A')
                category = result.get('category', 'N/A')
                main_ingredients = result.get('main_ingredients', 'N/A')
                
                logger.info(f"   📝 Query Recipe {i+1}: {title}")
                logger.info(f"      - 分類: {category}")
                logger.info(f"      - 主材料: {main_ingredients}")
        else:
            logger.warning("📋 [TEST] No query-based recipes found")
        
        # 除外レシピ機能テスト
        excluded_recipes = ["フレンチトースト"]
        logger.info(f"📋 [TEST] Testing excluded recipes functionality: {excluded_recipes}")
        
        excluded_results = await rag_client.search_similar_recipes(
            ingredients=ingredients,
            excluded_recipes=excluded_recipes,
            limit=5
        )
        
        # 除外レシピが結果に含まれていないことを確認
        excluded_found = False
        for result in excluded_results:
            title = result.get("title", "")
            if "フレンチトースト" in title:
                excluded_found = True
                break
        
        assert not excluded_found, "Excluded recipes should not appear in results"
        logger.info("✅ [TEST] Excluded recipes functionality working correctly")
        
        if excluded_results:
            logger.info(f"📋 [TEST] Excluded recipes search results:")
            for i, result in enumerate(excluded_results):
                title = result.get('title', 'N/A')
                category = result.get('category', 'N/A')
                logger.info(f"   📝 Excluded Recipe {i+1}: {title} ({category})")
        else:
            logger.warning("📋 [TEST] No recipes found after exclusion")
        
        logger.info("🎉 [TEST] All RAG client tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG client test failed: {e}")
        return False

async def test_rag_integration():
    """RAG統合テスト"""
    logger = GenericLogger("test", "rag_integration", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing RAG Integration...")
    
    try:
        # テスト用の在庫食材リスト
        test_inventory_items = [
            "牛乳",
            "卵",
            "パン",
            "バター",
            "ほうれん草",
            "胡麻",
            "白菜",
            "ハム",
            "小麦粉"
        ]
        
        logger.info(f"📋 [TEST] Testing with inventory items: {test_inventory_items}")
        
        # 埋め込みサービスとRAG検索の統合テスト
        embeddings_service = RecipeEmbeddingsService()
        rag_client = RecipeRAGClient()
        
        # レシピテキストの埋め込み生成
        recipe_text = "牛乳と卵のフレンチトースト 牛乳 卵 パン その他"
        embedding = await embeddings_service.generate_recipe_embedding(recipe_text)
        logger.info(f"✅ [TEST] Recipe embedding generated: {len(embedding)} dimensions")
        
        # 在庫食材に基づくレシピ検索
        results = await rag_client.search_similar_recipes(
            ingredients=test_inventory_items,
            menu_type="和食",
            limit=5
        )
        
        logger.info(f"✅ [TEST] Recipe search completed: {len(results)} results")
        
        if results:
            logger.info(f"📋 [TEST] Integration test recipe search results:")
            for i, result in enumerate(results, 1):
                title = result.get("title", "タイトル不明")
                category = result.get("category", "分類不明")
                main_ingredients = result.get("main_ingredients", "主材料不明")
                
                logger.info(f"   📝 Integration Recipe {i}: {title}")
                logger.info(f"      - 分類: {category}")
                logger.info(f"      - 主材料: {main_ingredients}")
                
                print(f"{i}. {title}")
                print(f"   分類: {category}")
                print(f"   主材料: {main_ingredients}")
                print()
        else:
            logger.warning("📋 [TEST] No recipes found in integration test")
        
        logger.info("🎉 [TEST] RAG integration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG integration test failed: {e}")
        return False

async def main():
    """メイン実行関数"""
    print("🧪 RAG検索機能の単体試験を開始します...")
    print("=" * 60)
    
    # ログ設定の初期化
    setup_logging(initialize=False)
    
    passed = 0
    total = 0
    
    # 埋め込みサービスのテスト
    print("\n📝 埋め込みサービスのテスト")
    total += 1
    if await test_embeddings_service():
        passed += 1
        print("✅ 埋め込みサービスのテスト: PASSED")
    else:
        print("❌ 埋め込みサービスのテスト: FAILED")
    
    # RAG検索クライアントのテスト
    print("\n🔍 RAG検索クライアントのテスト")
    total += 1
    if await test_rag_client():
        passed += 1
        print("✅ RAG検索クライアントのテスト: PASSED")
    else:
        print("❌ RAG検索クライアントのテスト: FAILED")
    
    # 統合テスト
    print("\n🔗 統合テスト")
    total += 1
    if await test_rag_integration():
        passed += 1
        print("✅ 統合テスト: PASSED")
    else:
        print("❌ 統合テスト: FAILED")
    
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