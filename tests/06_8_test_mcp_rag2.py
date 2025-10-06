#!/usr/bin/env python3
"""
RAG検索献立形式化機能の単体試験

新しく追加したconvert_rag_results_to_menu_format()メソッドの動作確認
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
from mcp_servers.recipe_rag import RecipeRAGClient

async def test_rag_menu_format_conversion():
    """RAG検索結果の献立形式変換テスト"""
    # ログ設定（初期化は既にメイン関数で実行済み）
    from config.logging import setup_logging
    setup_logging(initialize=False)
    
    logger = GenericLogger("test", "rag_menu_format", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing RAG Menu Format Conversion...")
    
    try:
        # RAG検索クライアントの初期化
        rag_client = RecipeRAGClient()
        logger.info("✅ [TEST] RAG client initialized successfully")
        
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
        
        # Step 1: RAG検索を実行してレシピを取得
        logger.info("🔍 [TEST] Step 1: Executing RAG search...")
        rag_results = await rag_client.search_similar_recipes(
            ingredients=test_inventory_items,
            menu_type="和食",
            limit=10  # 多めに取得して献立構成に使用
        )
        
        assert isinstance(rag_results, list), "RAG results should be a list"
        assert len(rag_results) > 0, "RAG search should return at least one result"
        logger.info(f"✅ [TEST] RAG search completed: {len(rag_results)} recipes found")
        
        # RAG検索結果の詳細ログ出力
        logger.info("=" * 60)
        logger.info("📋 [TEST] RAG SEARCH RESULTS DETAILS:")
        logger.info("=" * 60)
        for i, recipe in enumerate(rag_results, 1):
            title = recipe.get("title", "N/A")
            category = recipe.get("category", "N/A")
            main_ingredients = recipe.get("main_ingredients", "N/A")
            content = recipe.get("content", "N/A")
            
            logger.info(f"   📝 Recipe {i}: {title}")
            logger.info(f"      - 分類: {category}")
            logger.info(f"      - 主材料: {main_ingredients}")
            logger.info(f"      - 内容: {content[:100]}..." if len(content) > 100 else f"      - 内容: {content}")
            logger.info("")
        logger.info("=" * 60)
        
        # Step 2: 献立形式に変換
        logger.info("🔄 [TEST] Step 2: Converting to menu format...")
        logger.info("📋 [TEST] Input for conversion:")
        logger.info(f"   - RAG Results Count: {len(rag_results)}")
        logger.info(f"   - Inventory Items: {test_inventory_items}")
        logger.info(f"   - Menu Type: 和食")
        
        menu_result = await rag_client.convert_rag_results_to_menu_format(
            rag_results=rag_results,
            inventory_items=test_inventory_items,
            menu_type="和食"
        )
        
        # Step 3: 結果の構造を検証
        logger.info("🔍 [TEST] Step 3: Validating menu format structure...")
        
        # 基本構造の確認
        assert isinstance(menu_result, dict), "Menu result should be a dictionary"
        assert "candidates" in menu_result, "Menu result should have 'candidates' key"
        assert "selected" in menu_result, "Menu result should have 'selected' key"
        
        candidates = menu_result["candidates"]
        selected = menu_result["selected"]
        
        # 変換結果の詳細ログ出力
        logger.info("=" * 60)
        logger.info("🔄 [TEST] MENU FORMAT CONVERSION RESULTS:")
        logger.info("=" * 60)
        
        # candidatesの確認
        assert isinstance(candidates, list), "Candidates should be a list"
        logger.info(f"📊 [TEST] Found {len(candidates)} menu candidates")
        
        # selectedの確認
        assert isinstance(selected, dict), "Selected should be a dictionary"
        
        # 献立構成の確認
        required_categories = ["main_dish", "side_dish", "soup"]
        logger.info("🍽️ [TEST] SELECTED MENU DETAILS:")
        for category in required_categories:
            assert category in selected, f"Selected should have '{category}' key"
            
            dish = selected[category]
            assert isinstance(dish, dict), f"{category} should be a dictionary"
            assert "title" in dish, f"{category} should have 'title' key"
            assert "ingredients" in dish, f"{category} should have 'ingredients' key"
            
            title = dish["title"]
            ingredients = dish["ingredients"]
            
            assert isinstance(title, str), f"{category} title should be a string"
            assert isinstance(ingredients, list), f"{category} ingredients should be a list"
            
            logger.info(f"   🍽️ {category}: {title}")
            logger.info(f"      - 食材: {ingredients}")
            logger.info("")
        
        # Step 4: 食材重複回避の確認
        logger.info("🔍 [TEST] Step 4: Checking ingredient overlap avoidance...")
        
        all_used_ingredients = set()
        overlap_found = False
        
        for category in required_categories:
            dish = selected[category]
            ingredients = set(dish["ingredients"])
            
            # 重複チェック
            overlap = all_used_ingredients & ingredients
            if overlap:
                overlap_found = True
                logger.warning(f"⚠️ [TEST] Ingredient overlap found in {category}: {overlap}")
            
            all_used_ingredients.update(ingredients)
        
        if not overlap_found:
            logger.info("✅ [TEST] No ingredient overlap found - good!")
        else:
            logger.warning("⚠️ [TEST] Some ingredient overlap detected")
        
        # Step 5: 在庫食材活用の確認
        logger.info("🔍 [TEST] Step 5: Checking inventory ingredient utilization...")
        
        inventory_set = set(test_inventory_items)
        used_inventory = all_used_ingredients & inventory_set
        
        logger.info(f"📊 [TEST] Inventory ingredients used: {len(used_inventory)}/{len(inventory_set)}")
        logger.info(f"📊 [TEST] Used inventory items: {list(used_inventory)}")
        
        utilization_rate = len(used_inventory) / len(inventory_set) if inventory_set else 0
        logger.info(f"📊 [TEST] Inventory utilization rate: {utilization_rate:.2%}")
        
        # Step 6: 候補の詳細確認
        logger.info("🔍 [TEST] Step 6: Checking menu candidates...")
        logger.info("📋 [TEST] ALL MENU CANDIDATES:")
        logger.info("=" * 60)
        
        for i, candidate in enumerate(candidates):
            logger.info(f"   📋 Candidate {i+1}:")
            for category in required_categories:
                if category in candidate:
                    dish = candidate[category]
                    title = dish.get("title", "N/A")
                    ingredients = dish.get("ingredients", [])
                    logger.info(f"      {category}: {title} ({ingredients})")
                else:
                    logger.info(f"      {category}: Not available")
            logger.info("")
        logger.info("=" * 60)
        
        # 最終結果のログ出力
        logger.info("🎉 [TEST] RAG Menu Format Conversion test passed!")
        logger.info("=" * 60)
        logger.info("📊 [TEST] FINAL RESULTS SUMMARY:")
        logger.info(f"   🍽️ Selected Menu:")
        logger.info(f"      Main Dish: {selected['main_dish']['title']}")
        logger.info(f"      Side Dish: {selected['side_dish']['title']}")
        logger.info(f"      Soup: {selected['soup']['title']}")
        logger.info(f"   📋 Total Candidates: {len(candidates)}")
        logger.info(f"   🥬 Inventory Utilization: {utilization_rate:.2%}")
        logger.info(f"   🔄 Ingredient Overlap: {'None' if not overlap_found else 'Detected'}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG Menu Format Conversion test failed: {e}")
        import traceback
        logger.error(f"❌ [TEST] Traceback: {traceback.format_exc()}")
        logger.error("=" * 60)
        logger.error("❌ [TEST] TEST FAILED - Check error details above")
        logger.error("=" * 60)
        return False

async def test_rag_menu_format_edge_cases():
    """RAG献立形式変換のエッジケーステスト"""
    # ログ設定（初期化は既にメイン関数で実行済み）
    from config.logging import setup_logging
    setup_logging(initialize=False)
    
    logger = GenericLogger("test", "rag_menu_format_edge", initialize_logging=False)
    
    logger.info("🧪 [TEST] Testing RAG Menu Format Edge Cases...")
    
    try:
        rag_client = RecipeRAGClient()
        
        # エッジケース1: 空のRAG結果
        logger.info("📋 [TEST] Edge Case 1: Empty RAG results")
        empty_result = await rag_client.convert_rag_results_to_menu_format(
            rag_results=[],
            inventory_items=["牛乳", "卵"],
            menu_type="和食"
        )
        
        assert isinstance(empty_result, dict), "Empty result should be a dictionary"
        assert "candidates" in empty_result, "Empty result should have 'candidates' key"
        assert "selected" in empty_result, "Empty result should have 'selected' key"
        logger.info("✅ [TEST] Empty RAG results handled correctly")
        
        # エッジケース2: 最小在庫食材
        logger.info("📋 [TEST] Edge Case 2: Minimal inventory")
        minimal_inventory = ["牛乳"]
        
        rag_results = await rag_client.search_similar_recipes(
            ingredients=minimal_inventory,
            menu_type="和食",
            limit=5
        )
        
        if rag_results:
            minimal_result = await rag_client.convert_rag_results_to_menu_format(
                rag_results=rag_results,
                inventory_items=minimal_inventory,
                menu_type="和食"
            )
            
            assert isinstance(minimal_result, dict), "Minimal result should be a dictionary"
            logger.info("✅ [TEST] Minimal inventory handled correctly")
        
        logger.info("🎉 [TEST] RAG Menu Format Edge Cases test passed!")
        logger.info("=" * 60)
        logger.info("📊 [TEST] EDGE CASES SUMMARY:")
        logger.info("   ✅ Empty RAG results handled correctly")
        logger.info("   ✅ Minimal inventory handled correctly")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ [TEST] RAG Menu Format Edge Cases test failed: {e}")
        logger.error("=" * 60)
        logger.error("❌ [TEST] EDGE CASES TEST FAILED - Check error details above")
        logger.error("=" * 60)
        return False

async def main():
    """メイン実行関数"""
    print("🧪 RAG検索献立形式化機能の単体試験を開始します...")
    print("=" * 60)
    
    # ログ設定の初期化
    setup_logging(initialize=True)
    
    # メインロガーの設定
    main_logger = GenericLogger("test", "rag_menu_format_main", initialize_logging=False)
    main_logger.info("🚀 [TEST] Starting RAG Menu Format Conversion Tests")
    main_logger.info("=" * 60)
    
    # ログファイルへの出力を強制
    import logging
    root_logger = logging.getLogger('morizo_ai')
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    passed = 0
    total = 0
    
    # 献立形式変換テスト
    print("\n🔄 RAG献立形式変換テスト")
    main_logger.info("🔄 [TEST] Starting RAG Menu Format Conversion Test")
    main_logger.info("=" * 60)
    
    # ログファイルへの出力を強制
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    total += 1
    if await test_rag_menu_format_conversion():
        passed += 1
        print("✅ RAG献立形式変換テスト: PASSED")
        main_logger.info("✅ [TEST] RAG Menu Format Conversion Test: PASSED")
    else:
        print("❌ RAG献立形式変換テスト: FAILED")
        main_logger.error("❌ [TEST] RAG Menu Format Conversion Test: FAILED")
    
    # ログファイルへの出力を強制
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    # エッジケーステスト
    print("\n🔍 RAG献立形式エッジケーステスト")
    main_logger.info("🔍 [TEST] Starting RAG Menu Format Edge Cases Test")
    main_logger.info("=" * 60)
    
    # ログファイルへの出力を強制
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    total += 1
    if await test_rag_menu_format_edge_cases():
        passed += 1
        print("✅ RAG献立形式エッジケーステスト: PASSED")
        main_logger.info("✅ [TEST] RAG Menu Format Edge Cases Test: PASSED")
    else:
        print("❌ RAG献立形式エッジケーステスト: FAILED")
        main_logger.error("❌ [TEST] RAG Menu Format Edge Cases Test: FAILED")
    
    # ログファイルへの出力を強制
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    # 結果表示
    print("\n" + "=" * 60)
    print(f"📊 テスト結果: {passed}/{total} パス")
    
    main_logger.info("=" * 60)
    main_logger.info(f"📊 [TEST] FINAL TEST RESULTS: {passed}/{total} PASSED")
    
    # 最終的なログファイルへの出力を強制
    for handler in root_logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        main_logger.info("🎉 [TEST] ALL TESTS PASSED SUCCESSFULLY!")
        main_logger.info("=" * 60)
        
        # 最終的なログファイルへの出力を強制
        for handler in root_logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        return True
    else:
        print(f"⚠️  {total - passed}個のテストが失敗しました。")
        main_logger.error(f"⚠️ [TEST] {total - passed} TESTS FAILED")
        main_logger.info("=" * 60)
        
        # 最終的なログファイルへの出力を強制
        for handler in root_logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        return False

if __name__ == "__main__":
    # テスト実行
    success = asyncio.run(main())
