#!/usr/bin/env python3
"""
Phase 1C - プランナー認識テスト
"""

import asyncio
import os
import sys
import json

from dotenv import load_dotenv

# プロジェクトルートをパスに追加（tests/phase1c 配下のため3階層戻る）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.planner import ActionPlanner
except Exception as e:
    ActionPlanner = None  # type: ignore
    _import_error = e
else:
    _import_error = None

async def main() -> None:
    print("🚀 test_04_planner_main_dish_recognition: start")

    load_dotenv()

    if _import_error is not None or ActionPlanner is None:
        print(f"⏭  ActionPlanner の読み込みに失敗したためスキップ: {_import_error}")
        return

    # 前提: LLMService が内部で OPENAI_API_KEY を参照するため、未設定ならスキップ
    if not os.getenv("OPENAI_API_KEY"):
        print("⏭  OPENAI_API_KEY 未設定のためスキップ（.env を設定してください）")
        return

    planner = ActionPlanner()

    test_cases = [
        "主菜を5件提案して",
        "レンコンを使った主菜を教えて",
        "メインを提案して",
        "キャベツで主菜を作って",
    ]

    for user_request in test_cases:
        tasks = await planner.plan(user_request, user_id="test_user")
        print(f"📝 request= {user_request} -> tasks={len(tasks)}")
        for t in tasks:
            print(f"   - {t.service}.{t.method}")
        assert len(tasks) >= 2  # 在庫取得 + 主菜提案 など
        assert any(t.method in ("generate_main_dish_proposals", "search_menu_from_rag", "generate_menu_plan") for t in tasks), "主菜提案に関わるタスクが含まれていません"

        # 完全形式のJSON出力（id/description/service/method/parameters/dependencies）
        normalized = []
        for t in tasks:
            normalized.append({
                "id": getattr(t, "id", None),
                "description": getattr(t, "description", None),
                "service": getattr(t, "service", None),
                "method": getattr(t, "method", None),
                "parameters": getattr(t, "parameters", {}),
                "dependencies": getattr(t, "dependencies", []),
            })
        print("\n📦 tasks (full):")
        print(json.dumps({"tasks": normalized}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())


