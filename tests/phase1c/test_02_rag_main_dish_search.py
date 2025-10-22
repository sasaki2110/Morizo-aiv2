#!/usr/bin/env python3
"""
Phase 1C - RAG主菜3件検索 テスト

期待:
- 結果が3件
- 各 result が title / ingredients を持つ
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
    from mcp_servers.recipe_rag.client import RecipeRAGClient
except Exception as e:
    RecipeRAGClient = None  # type: ignore
    _import_error = e
else:
    _import_error = None


async def main() -> None:
    print("🚀 test_02_rag_main_dish_search: start")

    load_dotenv()

    if _import_error is not None or RecipeRAGClient is None:
        print(f"⏭  RecipeRAGClient の読み込みに失敗したためスキップ: {_import_error}")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("⏭  OPENAI_API_KEY 未設定のためスキップ（.env を設定してください）")
        return

    # ベクトルDBの存在確認（無ければスキップ）
    main_dir = os.getenv("CHROMA_PERSIST_DIRECTORY_MAIN", "./recipe_vector_db_main")
    sub_dir = os.getenv("CHROMA_PERSIST_DIRECTORY_SUB", "./recipe_vector_db_sub")
    soup_dir = os.getenv("CHROMA_PERSIST_DIRECTORY_SOUP", "./recipe_vector_db_soup")
    if not (os.path.isdir(main_dir) and os.path.isdir(sub_dir) and os.path.isdir(soup_dir)):
        print(f"⏭  ベクトルDBが見つかりません: main={main_dir}, sub={sub_dir}, soup={soup_dir}")
        print("    インデックスを作成してから再実行してください。")
        return

    # テストデータ
    inventory_items: List[str] = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草", "鶏もも肉"]
    menu_type = "和食"
    main_ingredient = "鶏もも肉"

    # 実行
    rag_client = RecipeRAGClient()
    results = await rag_client.search_main_dish_candidates(
        ingredients=inventory_items,
        menu_type=menu_type,
        main_ingredient=main_ingredient,
        limit=3,
    )

    # 可視化
    print("📥 results (count=", len(results), "):")
    for i, r in enumerate(results, 1):
        print(f"  {i}. title={r.get('title')} | source={r.get('source')} | site={r.get('site')}")

    # 検証
    assert len(results) == 3, f"期待3件だが {len(results)} 件"
    for item in results:
        assert "title" in item, "titleがありません"
        assert "ingredients" in item, "ingredientsがありません"


if __name__ == "__main__":
    asyncio.run(main())


