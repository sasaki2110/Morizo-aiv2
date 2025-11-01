#!/usr/bin/env python3
"""
Phase 1C - 曖昧性検出テスト（スクリプト実行型）
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.models import Task
from services.confirmation.ambiguity_detector import AmbiguityDetector


async def test_ambiguity_detection():
    """曖昧性検出のテスト（柔軟な選択肢提示）"""
    
    print("🔍 曖昧性検出テスト開始")
    
    # 主要食材未指定のタスクを作成
    task = Task(
        id="test_task",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": None  # 未指定
        }
    )
    
    # AmbiguityDetectorのインスタンス化
    ambiguity_detector = AmbiguityDetector()
    
    # 曖昧性検出
    ambiguity_info = await ambiguity_detector.check_main_dish_ambiguity(task, "test_user")
    
    # 検証
    print("✅ 曖昧性検出結果の検証")
    assert ambiguity_info is not None, "曖昧性情報が検出されませんでした"
    assert ambiguity_info.is_ambiguous == True, "曖昧性フラグが正しく設定されていません"
    assert ambiguity_info.details["type"] == "main_ingredient_optional_selection", f"曖昧性タイプが正しくありません: {ambiguity_info.details['type']}"
    assert len(ambiguity_info.details["options"]) == 2, f"選択肢の数が正しくありません: {len(ambiguity_info.details['options'])}"
    
    # メッセージの検証
    expected_message = "なにか主な食材を指定しますか？それとも今の在庫から作れる主菜を提案しましょうか？"
    assert ambiguity_info.details["message"] == expected_message, f"メッセージが正しくありません: {ambiguity_info.details['message']}"
    
    # 選択肢の検証
    options = ambiguity_info.details["options"]
    assert options[0]["value"] == "specify", f"1番目の選択肢のvalueが正しくありません: {options[0]['value']}"
    assert options[0]["label"] == "食材を指定する", f"1番目の選択肢のlabelが正しくありません: {options[0]['label']}"
    assert options[1]["value"] == "proceed", f"2番目の選択肢のvalueが正しくありません: {options[1]['value']}"
    assert options[1]["label"] == "指定せずに提案してもらう", f"2番目の選択肢のlabelが正しくありません: {options[1]['label']}"
    
    # タスク情報の検証
    assert ambiguity_info.task_id == "test_task", f"タスクIDが正しくありません: {ambiguity_info.task_id}"
    assert ambiguity_info.tool_name == "recipe_service_generate_main_dish_proposals", f"ツール名が正しくありません: {ambiguity_info.tool_name}"
    assert ambiguity_info.ambiguity_type == "main_ingredient_optional_selection", f"曖昧性タイプが正しくありません: {ambiguity_info.ambiguity_type}"
    
    print("✅ すべての検証が成功しました")
    print(f"   曖昧性タイプ: {ambiguity_info.ambiguity_type}")
    print(f"   メッセージ: {ambiguity_info.details['message']}")
    print(f"   選択肢数: {len(ambiguity_info.details['options'])}")
    
    return True


async def test_no_ambiguity_detection():
    """曖昧性が検出されないケースのテスト"""
    
    print("🔍 曖昧性なしケースのテスト開始")
    
    # 主要食材が指定されたタスクを作成
    task = Task(
        id="test_task_no_ambiguity",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": "レンコン"  # 指定済み
        }
    )
    
    # AmbiguityDetectorのインスタンス化
    ambiguity_detector = AmbiguityDetector()
    
    # 曖昧性検出
    ambiguity_info = await ambiguity_detector.check_main_dish_ambiguity(task, "test_user")
    
    # 検証（曖昧性が検出されないことを確認）
    assert ambiguity_info is None, "主要食材が指定されている場合は曖昧性が検出されるべきではありません"
    
    print("✅ 曖昧性なしケースの検証が成功しました")
    
    return True


async def main() -> None:
    print("🚀 test_07_ambiguity_detection: start")
    
    try:
        # テスト1: 曖昧性検出テスト
        await test_ambiguity_detection()
        
        # テスト2: 曖昧性なしケースのテスト
        await test_no_ambiguity_detection()
        
        print("🎉 test_07_ambiguity_detection: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_07_ambiguity_detection: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())


