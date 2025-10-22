#!/usr/bin/env python3
"""
Phase 1C - LLM主菜2件生成 テスト

期待:
- success が True
- candidates が 2 件
- 各 candidate が title / ingredients を持つ
- 指定主要食材が ingredients に含まれる
"""

import asyncio
import os
import sys
from typing import List

from dotenv import load_dotenv

# プロジェクトルートをパスに追加（tests/phase1c 配下のため3階層戻る）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # 実体を利用
    from mcp_servers.recipe_llm import RecipeLLM
except Exception as e:  # 実行環境での import 失敗を検知
    RecipeLLM = None  # type: ignore
    _import_error = e
else:
    _import_error = None


async def main() -> None:
    print("🚀 test_01_llm_main_dish_generation: start")

    # .env の読み込み
    load_dotenv()

    if _import_error is not None or RecipeLLM is None:
        print(f"⏭  RecipeLLM の読み込みに失敗したためスキップ: {_import_error}")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("⏭  OPENAI_API_KEY 未設定のためスキップ（.env を設定してください）")
        return

    # テストデータ
    #inventory_items: List[str] = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草"]
    #menu_type = "和食"
    #main_ingredient = "レンコン"
    inventory_items: List[str] = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草","鯖"]
    menu_type = "和食"
    main_ingredient = "鯖"

    # 実行
    llm_client = RecipeLLM()
    result = await llm_client.generate_main_dish_candidates(
        inventory_items=inventory_items,
        menu_type=menu_type,
        main_ingredient=main_ingredient,
        count=2,
    )

    # 可視化
    print("📥 result:", result)

    # 検証
    assert result["success"] is True
    assert len(result["data"]["candidates"]) == 2
    for candidate in result["data"]["candidates"]:
        assert "title" in candidate
        assert "ingredients" in candidate
        # 主要食材が含まれていること（プロンプト仕様）
        assert main_ingredient in candidate["ingredients"], "主要食材がingredientsに含まれていません"


if __name__ == "__main__":
    asyncio.run(main())


