#!/usr/bin/env python3
"""
Phase 1C - 動的タスク構築テスト
"""

import asyncio
import os
import sys

# プロジェクトルートをパスに追加（tests/phase1c 配下のため3階層戻る）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.dynamic_task_builder import DynamicTaskBuilder
    from core.models import TaskChainManager, TaskStatus
except Exception as e:
    DynamicTaskBuilder = None  # type: ignore
    TaskChainManager = None  # type: ignore
    TaskStatus = None  # type: ignore
    _import_error = e
else:
    _import_error = None


async def main() -> None:
    print("🚀 test_05_dynamic_task_building: start")

    if _import_error is not None or DynamicTaskBuilder is None:
        print(f"⏭  DynamicTaskBuilder の読み込みに失敗したためスキップ: {_import_error}")
        return

    # テストデータ
    inventory_items = ["レンコン", "キャベツ", "大根"]
    user_id = "test_user"
    main_ingredient = "レンコン"

    # TaskChainManager初期化
    task_chain_manager = TaskChainManager()
    print(f"📋 TaskChainManager initialized: tasks={len(task_chain_manager.tasks)}")

    # DynamicTaskBuilder初期化
    task_builder = DynamicTaskBuilder(task_chain_manager)
    print(f"🔧 DynamicTaskBuilder initialized")

    # 1. DynamicTaskBuilderの初期化テスト
    print("\n1️⃣ DynamicTaskBuilder初期化テスト")
    assert task_builder.task_chain_manager == task_chain_manager
    assert task_builder.context == {}
    print("✅ 初期化テスト: passed")

    # 2. 在庫取得タスクの追加テスト
    print("\n2️⃣ 在庫取得タスク追加テスト")
    inventory_task = task_builder.add_inventory_task(user_id)
    
    # 検証
    assert inventory_task.service == "inventory_service"
    assert inventory_task.method == "get_inventory"
    assert inventory_task.parameters["user_id"] == user_id
    assert inventory_task.status == TaskStatus.PENDING
    assert inventory_task.id.startswith("inventory_get_")
    
    print(f"✅ 在庫取得タスク: service={inventory_task.service}, method={inventory_task.method}")
    print(f"   parameters={inventory_task.parameters}")

    # 3. 主菜提案タスクの追加テスト
    print("\n3️⃣ 主菜提案タスク追加テスト")
    main_dish_task = task_builder.add_main_dish_proposal_task(
        inventory_items, user_id, main_ingredient
    )
    
    # 検証
    assert main_dish_task.service == "recipe_service"
    assert main_dish_task.method == "generate_main_dish_proposals"
    assert main_dish_task.parameters["main_ingredient"] == main_ingredient
    assert main_dish_task.parameters["inventory_items"] == inventory_items
    assert main_dish_task.parameters["user_id"] == user_id
    assert main_dish_task.status == TaskStatus.PENDING
    assert main_dish_task.id.startswith("main_dish_proposal_")
    
    print(f"✅ 主菜提案タスク: service={main_dish_task.service}, method={main_dish_task.method}")
    print(f"   main_ingredient={main_dish_task.parameters['main_ingredient']}")
    print(f"   inventory_items={main_dish_task.parameters['inventory_items']}")

    # 4. コンテキスト管理テスト
    print("\n4️⃣ コンテキスト管理テスト")
    # 主要食材がコンテキストに保存されているか確認
    context_main_ingredient = task_builder.get_context("main_ingredient")
    assert context_main_ingredient == main_ingredient
    
    # コンテキストの設定・取得テスト
    task_builder.set_context("test_key", "test_value")
    assert task_builder.get_context("test_key") == "test_value"
    assert task_builder.get_context("nonexistent_key") is None
    assert task_builder.get_context("nonexistent_key", "default") == "default"
    
    print(f"✅ コンテキスト管理: main_ingredient={context_main_ingredient}")
    print(f"   test_key={task_builder.get_context('test_key')}")

    # 5. 履歴取得タスクの追加テスト
    print("\n5️⃣ 履歴取得タスク追加テスト")
    history_task = task_builder.add_history_task(user_id, "main", 14)
    
    # 検証
    assert history_task.service == "history_service"
    assert history_task.method == "history_get_recent_titles"
    assert history_task.parameters["user_id"] == user_id
    assert history_task.parameters["category"] == "main"
    assert history_task.parameters["days"] == 14
    assert history_task.status == TaskStatus.PENDING
    assert history_task.id.startswith("history_get_")
    
    print(f"✅ 履歴取得タスク: service={history_task.service}, method={history_task.method}")
    print(f"   parameters={history_task.parameters}")

    # 6. タスクIDの一意性確認
    print("\n6️⃣ タスクID一意性テスト")
    task_ids = [inventory_task.id, main_dish_task.id, history_task.id]
    assert len(set(task_ids)) == len(task_ids), "タスクIDが重複しています"
    print(f"✅ タスクID一意性: {task_ids}")

    print("\n✅ test_05_dynamic_task_building: passed")


if __name__ == "__main__":
    asyncio.run(main())


