#!/usr/bin/env python3
"""
Phase 1C - 確認プロセステスト（スクリプト実行型）
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.models import Task
from services.confirmation.models import AmbiguityInfo
from services.confirmation.response_parser import UserResponseParser


async def test_confirmation_process_proceed():
    """確認プロセスのテスト（指定せずに進める）"""
    
    print("🔍 確認プロセステスト開始（指定せずに進める）")
    
    # テスト用タスクを作成
    task = Task(
        id="test_task",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": None
        }
    )
    
    # 曖昧性情報を作成
    ambiguity_info = {
        "task_id": "test_task",
        "details": {
            "type": "main_ingredient_optional_selection",
            "options": [
                {"value": "specify", "label": "食材を指定する"},
                {"value": "proceed", "label": "指定せずに提案してもらう"}
            ]
        }
    }
    
    # ユーザー選択（指定せずに進める）
    user_response = "そのまま提案して"
    
    # UserResponseParserのインスタンス化
    response_parser = UserResponseParser()
    
    # 確認プロセス処理
    result = await response_parser.process_main_ingredient_confirmation(
        ambiguity_info, user_response, [task]
    )
    
    # 検証
    print("✅ 確認プロセス結果の検証（指定せずに進める）")
    assert result["is_confirmed"] == True, f"確認フラグが正しくありません: {result['is_confirmed']}"
    assert result["updated_tasks"][0].parameters["main_ingredient"] is None, f"主要食材がnullのままではありません: {result['updated_tasks'][0].parameters['main_ingredient']}"
    assert "在庫から作れる主菜を提案します" in result["message"], f"メッセージが正しくありません: {result['message']}"
    
    print("✅ 指定せずに進めるケースの検証が成功しました")
    print(f"   確認フラグ: {result['is_confirmed']}")
    print(f"   主要食材: {result['updated_tasks'][0].parameters['main_ingredient']}")
    print(f"   メッセージ: {result['message']}")
    
    return True


async def test_confirmation_process_specify():
    """確認プロセスのテスト（食材を指定する）"""
    
    print("🔍 確認プロセステスト開始（食材を指定する）")
    
    # テスト用タスクを作成
    task = Task(
        id="test_task",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": None
        }
    )
    
    # 曖昧性情報を作成
    ambiguity_info = {
        "task_id": "test_task",
        "details": {
            "type": "main_ingredient_optional_selection",
            "options": [
                {"value": "specify", "label": "食材を指定する"},
                {"value": "proceed", "label": "指定せずに提案してもらう"}
            ]
        }
    }
    
    # ユーザー選択（食材を指定する）
    user_response = "はい"
    
    # UserResponseParserのインスタンス化
    response_parser = UserResponseParser()
    
    # 確認プロセス処理
    result = await response_parser.process_main_ingredient_confirmation(
        ambiguity_info, user_response, [task]
    )
    
    # 検証
    print("✅ 確認プロセス結果の検証（食材を指定する）")
    assert result["is_confirmed"] == False, f"確認フラグが正しくありません: {result['is_confirmed']}"
    assert result["needs_follow_up"] == True, f"フォローアップが必要ではありません: {result.get('needs_follow_up')}"
    assert "どの食材を使いたいですか？" in result["message"], f"メッセージが正しくありません: {result['message']}"
    
    print("✅ 食材を指定するケースの検証が成功しました")
    print(f"   確認フラグ: {result['is_confirmed']}")
    print(f"   フォローアップ必要: {result.get('needs_follow_up')}")
    print(f"   メッセージ: {result['message']}")
    
    return True


async def test_confirmation_process_direct_ingredient():
    """確認プロセスのテスト（直接食材名を入力）"""
    
    print("🔍 確認プロセステスト開始（直接食材名を入力）")
    
    # テスト用タスクを作成
    task = Task(
        id="test_task",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": None
        }
    )
    
    # 曖昧性情報を作成
    ambiguity_info = {
        "task_id": "test_task",
        "details": {
            "type": "main_ingredient_optional_selection",
            "options": [
                {"value": "specify", "label": "食材を指定する"},
                {"value": "proceed", "label": "指定せずに提案してもらう"}
            ]
        }
    }
    
    # ユーザー選択（直接食材名を入力）
    user_response = "サバ"
    
    # UserResponseParserのインスタンス化
    response_parser = UserResponseParser()
    
    # 確認プロセス処理
    result = await response_parser.process_main_ingredient_confirmation(
        ambiguity_info, user_response, [task]
    )
    
    # 検証
    print("✅ 確認プロセス結果の検証（直接食材名を入力）")
    assert result["is_confirmed"] == True, f"確認フラグが正しくありません: {result['is_confirmed']}"
    assert result["updated_tasks"][0].parameters["main_ingredient"] == "サバ", f"主要食材が正しく設定されていません: {result['updated_tasks'][0].parameters['main_ingredient']}"
    assert "主要食材を「サバ」に設定しました" in result["message"], f"メッセージが正しくありません: {result['message']}"
    
    print("✅ 直接食材名入力ケースの検証が成功しました")
    print(f"   確認フラグ: {result['is_confirmed']}")
    print(f"   主要食材: {result['updated_tasks'][0].parameters['main_ingredient']}")
    print(f"   メッセージ: {result['message']}")
    
    return True


async def test_confirmation_process_unrecognized():
    """確認プロセスのテスト（認識できない応答）"""
    
    print("🔍 確認プロセステスト開始（認識できない応答）")
    
    # テスト用タスクを作成
    task = Task(
        id="test_task",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": None
        }
    )
    
    # 曖昧性情報を作成
    ambiguity_info = {
        "task_id": "test_task",
        "details": {
            "type": "main_ingredient_optional_selection",
            "options": [
                {"value": "specify", "label": "食材を指定する"},
                {"value": "proceed", "label": "指定せずに提案してもらう"}
            ]
        }
    }
    
    # ユーザー選択（認識できない応答）
    user_response = "これはとても長い応答で、食材名として認識されるべきではない長い文字列です。"
    
    # UserResponseParserのインスタンス化
    response_parser = UserResponseParser()
    
    # 確認プロセス処理
    result = await response_parser.process_main_ingredient_confirmation(
        ambiguity_info, user_response, [task]
    )
    
    # 検証
    print("✅ 確認プロセス結果の検証（認識できない応答）")
    assert result["is_confirmed"] == False, f"確認フラグが正しくありません: {result['is_confirmed']}"
    assert "すみません、理解できませんでした" in result["message"], f"メッセージが正しくありません: {result['message']}"
    
    print("✅ 認識できない応答ケースの検証が成功しました")
    print(f"   確認フラグ: {result['is_confirmed']}")
    print(f"   メッセージ: {result['message']}")
    
    return True


async def main() -> None:
    print("🚀 test_08_confirmation_process: start")
    
    try:
        # テスト1: 指定せずに進めるケース
        await test_confirmation_process_proceed()
        
        # テスト2: 食材を指定するケース
        await test_confirmation_process_specify()
        
        # テスト3: 直接食材名入力ケース
        await test_confirmation_process_direct_ingredient()
        
        # テスト4: 認識できない応答ケース
        await test_confirmation_process_unrecognized()
        
        print("🎉 test_08_confirmation_process: すべてのテストが成功しました")
        
    except Exception as e:
        print(f"❌ test_08_confirmation_process: テストが失敗しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())


