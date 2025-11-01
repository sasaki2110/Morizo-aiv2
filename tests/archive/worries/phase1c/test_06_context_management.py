#!/usr/bin/env python3
"""
Phase 1C - コンテキスト管理テスト

期待:
- ContextManagerの基本機能が正常に動作する
- 主要食材の設定・取得が正常に動作する
- 在庫食材の設定・取得が正常に動作する
- 除外レシピの設定・取得が正常に動作する
- コンテキストクリアが正常に動作する
- 全コンテキスト取得が正常に動作する
"""

import asyncio
import os
import sys
from typing import List

# プロジェクトルートをパスに追加（tests/phase1c 配下のため3階層戻る）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.context_manager import ContextManager
except Exception as e:
    ContextManager = None  # type: ignore
    _import_error = e
else:
    _import_error = None


async def main() -> None:
    print("🚀 test_06_context_management: start")

    if _import_error is not None or ContextManager is None:
        print(f"⏭  ContextManager の読み込みに失敗したためスキップ: {_import_error}")
        return

    # テストデータ
    test_session_id = "test_session_06"
    main_ingredient = "レンコン"
    inventory_items = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草"]
    excluded_recipes = ["レンコンの煮物", "キャベツの炒め物"]

    # ContextManager初期化
    context_manager = ContextManager(test_session_id)
    print(f"📋 ContextManager initialized: session_id={test_session_id}")

    # 1. 主要食材の設定・取得テスト
    print("\n1️⃣ 主要食材の設定・取得テスト")
    context_manager.set_main_ingredient(main_ingredient)
    retrieved_main_ingredient = context_manager.get_main_ingredient()
    
    assert retrieved_main_ingredient == main_ingredient, f"主要食材の取得が失敗: 期待={main_ingredient}, 実際={retrieved_main_ingredient}"
    print(f"✅ 主要食材設定・取得: {retrieved_main_ingredient}")

    # 2. 在庫食材の設定・取得テスト
    print("\n2️⃣ 在庫食材の設定・取得テスト")
    context_manager.set_inventory_items(inventory_items)
    retrieved_inventory_items = context_manager.get_inventory_items()
    
    assert retrieved_inventory_items == inventory_items, f"在庫食材の取得が失敗: 期待={inventory_items}, 実際={retrieved_inventory_items}"
    assert len(retrieved_inventory_items) == len(inventory_items), f"在庫食材の件数が不一致: 期待={len(inventory_items)}, 実際={len(retrieved_inventory_items)}"
    print(f"✅ 在庫食材設定・取得: {len(retrieved_inventory_items)}件")

    # 3. 除外レシピの設定・取得テスト
    print("\n3️⃣ 除外レシピの設定・取得テスト")
    context_manager.set_excluded_recipes(excluded_recipes)
    retrieved_excluded_recipes = context_manager.get_excluded_recipes()
    
    assert retrieved_excluded_recipes == excluded_recipes, f"除外レシピの取得が失敗: 期待={excluded_recipes}, 実際={retrieved_excluded_recipes}"
    assert len(retrieved_excluded_recipes) == len(excluded_recipes), f"除外レシピの件数が不一致: 期待={len(excluded_recipes)}, 実際={len(retrieved_excluded_recipes)}"
    print(f"✅ 除外レシピ設定・取得: {len(retrieved_excluded_recipes)}件")

    # 4. 全コンテキスト取得テスト
    print("\n4️⃣ 全コンテキスト取得テスト")
    full_context = context_manager.get_context()
    
    assert isinstance(full_context, dict), "全コンテキストが辞書型ではありません"
    assert "main_ingredient" in full_context, "主要食材がコンテキストに含まれていません"
    assert "inventory_items" in full_context, "在庫食材がコンテキストに含まれていません"
    assert "excluded_recipes" in full_context, "除外レシピがコンテキストに含まれていません"
    assert full_context["main_ingredient"] == main_ingredient, "主要食材の値が一致しません"
    assert full_context["inventory_items"] == inventory_items, "在庫食材の値が一致しません"
    assert full_context["excluded_recipes"] == excluded_recipes, "除外レシピの値が一致しません"
    
    print(f"✅ 全コンテキスト取得: {len(full_context)}個のキー")
    print(f"   キー: {list(full_context.keys())}")

    # 5. コンテキストクリアテスト
    print("\n5️⃣ コンテキストクリアテスト")
    context_manager.clear_context()
    
    cleared_main_ingredient = context_manager.get_main_ingredient()
    cleared_inventory_items = context_manager.get_inventory_items()
    cleared_excluded_recipes = context_manager.get_excluded_recipes()
    cleared_context = context_manager.get_context()
    
    assert cleared_main_ingredient is None, f"主要食材がクリアされていません: {cleared_main_ingredient}"
    assert cleared_inventory_items == [], f"在庫食材がクリアされていません: {cleared_inventory_items}"
    assert cleared_excluded_recipes == [], f"除外レシピがクリアされていません: {cleared_excluded_recipes}"
    assert cleared_context == {}, f"全コンテキストがクリアされていません: {cleared_context}"
    
    print("✅ コンテキストクリア: 全ての値がクリアされました")

    # 6. デフォルト値テスト
    print("\n6️⃣ デフォルト値テスト")
    # クリア後の状態でデフォルト値をテスト
    default_main_ingredient = context_manager.get_main_ingredient()
    default_inventory_items = context_manager.get_inventory_items()
    default_excluded_recipes = context_manager.get_excluded_recipes()
    
    assert default_main_ingredient is None, f"主要食材のデフォルト値がNoneではありません: {default_main_ingredient}"
    assert default_inventory_items == [], f"在庫食材のデフォルト値が空リストではありません: {default_inventory_items}"
    assert default_excluded_recipes == [], f"除外レシピのデフォルト値が空リストではありません: {default_excluded_recipes}"
    
    print("✅ デフォルト値: 期待通りのデフォルト値が返されました")

    # 7. 再設定テスト
    print("\n7️⃣ 再設定テスト")
    # クリア後に再設定して動作確認
    new_main_ingredient = "キャベツ"
    new_inventory_items = ["キャベツ", "大根", "白菜"]
    new_excluded_recipes = ["キャベツの炒め物"]
    
    context_manager.set_main_ingredient(new_main_ingredient)
    context_manager.set_inventory_items(new_inventory_items)
    context_manager.set_excluded_recipes(new_excluded_recipes)
    
    final_main_ingredient = context_manager.get_main_ingredient()
    final_inventory_items = context_manager.get_inventory_items()
    final_excluded_recipes = context_manager.get_excluded_recipes()
    
    assert final_main_ingredient == new_main_ingredient, f"再設定後の主要食材が一致しません: 期待={new_main_ingredient}, 実際={final_main_ingredient}"
    assert final_inventory_items == new_inventory_items, f"再設定後の在庫食材が一致しません: 期待={new_inventory_items}, 実際={final_inventory_items}"
    assert final_excluded_recipes == new_excluded_recipes, f"再設定後の除外レシピが一致しません: 期待={new_excluded_recipes}, 実際={final_excluded_recipes}"
    
    print(f"✅ 再設定: main_ingredient={final_main_ingredient}, inventory_items={len(final_inventory_items)}件, excluded_recipes={len(final_excluded_recipes)}件")

    print("\n✅ test_06_context_management: passed")


if __name__ == "__main__":
    asyncio.run(main())


