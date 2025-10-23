#!/usr/bin/env python3
"""
Phase 2A-2 - レスポンスフォーマッターのテスト
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.llm.response_formatters import ResponseFormatters


def test_format_selection_request():
    """選択要求フォーマットのテスト"""
    print("🔍 選択要求フォーマットのテスト")
    
    formatter = ResponseFormatters()
    candidates = [
        {
            "title": "レンコンのきんぴら",
            "ingredients": ["レンコン", "ごま油", "醤油"],
            "cooking_time": "15分",
            "category": "和食"
        },
        {
            "title": "レンコンの天ぷら",
            "ingredients": ["レンコン", "天ぷら粉", "油"],
            "cooking_time": "20分",
            "category": "和食"
        },
        {
            "title": "レンコンのサラダ",
            "ingredients": ["レンコン", "マヨネーズ", "塩"],
            "cooking_time": "10分",
            "category": "洋食"
        }
    ]
    
    result = formatter.format_selection_request(candidates, "main_dish_proposal_0")
    
    assert result["requires_selection"] is True
    assert result["task_id"] == "main_dish_proposal_0"
    assert "以下の5件から選択してください:" in result["message"]
    assert "1. レンコンのきんぴら" in result["message"]
    assert "2. レンコンの天ぷら" in result["message"]
    assert "3. レンコンのサラダ" in result["message"]
    assert "番号を選択してください（1-5）:" in result["message"]
    assert len(result["candidates"]) == 3
    
    print("✅ 選択要求フォーマットのテスト成功")


def test_format_selection_request_with_minimal_data():
    """最小限のデータでの選択要求フォーマットのテスト"""
    print("🔍 最小限のデータでの選択要求フォーマットのテスト")
    
    formatter = ResponseFormatters()
    candidates = [
        {
            "title": "シンプルなレシピ"
        }
    ]
    
    result = formatter.format_selection_request(candidates, "main_dish_proposal_0")
    
    assert result["requires_selection"] is True
    assert result["task_id"] == "main_dish_proposal_0"
    assert "1. シンプルなレシピ" in result["message"]
    assert "不明なレシピ" not in result["message"]
    
    print("✅ 最小限のデータでの選択要求フォーマットのテスト成功")


def test_format_selection_request_empty_candidates():
    """空の候補リストでの選択要求フォーマットのテスト"""
    print("🔍 空の候補リストでの選択要求フォーマットのテスト")
    
    formatter = ResponseFormatters()
    candidates = []
    
    result = formatter.format_selection_request(candidates, "main_dish_proposal_0")
    
    assert result["requires_selection"] is True
    assert result["task_id"] == "main_dish_proposal_0"
    assert "以下の5件から選択してください:" in result["message"]
    assert "番号を選択してください（1-5）:" in result["message"]
    assert len(result["candidates"]) == 0
    
    print("✅ 空の候補リストでの選択要求フォーマットのテスト成功")


def test_format_selection_result():
    """選択結果フォーマットのテスト"""
    print("🔍 選択結果フォーマットのテスト")
    
    formatter = ResponseFormatters()
    result = formatter.format_selection_result(3, "main_dish_proposal_0")
    
    assert result["success"] is True
    assert result["task_id"] == "main_dish_proposal_0"
    assert result["selection"] == 3
    assert result["message"] == "選択肢 3 を受け付けました。"
    
    print("✅ 選択結果フォーマットのテスト成功")


def test_format_selection_result_edge_cases():
    """選択結果フォーマットの境界値テスト"""
    print("🔍 選択結果フォーマットの境界値テスト")
    
    formatter = ResponseFormatters()
    
    # 最小値
    result1 = formatter.format_selection_result(1, "main_dish_proposal_0")
    assert result1["selection"] == 1
    assert "選択肢 1 を受け付けました。" in result1["message"]
    
    # 最大値
    result2 = formatter.format_selection_result(5, "main_dish_proposal_0")
    assert result2["selection"] == 5
    assert "選択肢 5 を受け付けました。" in result2["message"]
    
    print("✅ 選択結果フォーマットの境界値テスト成功")


def main():
    """メイン関数"""
    print("🚀 Phase 2A-2 レスポンスフォーマッターのテスト開始")
    
    tests = [
        test_format_selection_request,
        test_format_selection_request_with_minimal_data,
        test_format_selection_request_empty_candidates,
        test_format_selection_result,
        test_format_selection_result_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: テストが失敗しました: {e}")
            failed += 1
    
    print(f"\n📊 テスト結果: {passed}件成功, {failed}件失敗")
    
    if failed == 0:
        print("🎉 すべてのテストが成功しました！")
        return True
    else:
        print("❌ 一部のテストが失敗しました")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
