#!/usr/bin/env python3
"""
セッション2: Phase 1C（提案レスポンスに食材情報を含める）の単体テスト

LLM/RAG候補のingredientsとセッション保存のテスト
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_servers.recipe_llm import RecipeLLM
from mcp_servers.recipe_rag.client import RecipeRAGClient
from services.session.models.components.candidate import CandidateComponent
from services.session.candidate_manager import CandidateManager
from services.session.service import SessionService
from config.loggers import GenericLogger


class TestLLMCandidateIngredients:
    """LLM提案の候補にingredientsが含まれることのテスト"""
    
    def test_parse_candidate_response_with_ingredients(self):
        """ingredientsがある場合のパース"""
        print("\n[テスト1] LLM _parse_candidate_response() - ingredientsあり")
        
        # RecipeLLMインスタンス作成
        llm = RecipeLLM()
        
        # テストデータ（ingredientsあり）
        response_content = """
        {
            "candidates": [
                {"title": "レンコン炒め", "ingredients": ["レンコン", "にんじん", "鶏肉"]},
                {"title": "ほうれん草の胡麻和え", "ingredients": ["ほうれん草", "ごま"]}
            ]
        }
        """
        
        # テスト実行
        candidates = llm._parse_candidate_response(response_content)
        
        # 検証
        assert len(candidates) == 2, f"候補数が2であること: {len(candidates)}"
        assert candidates[0]["title"] == "レンコン炒め", f"1つ目のタイトルが正しいこと: {candidates[0]['title']}"
        assert candidates[0]["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
            f"1つ目のingredientsが正しいこと: {candidates[0]['ingredients']}"
        assert candidates[1]["title"] == "ほうれん草の胡麻和え", f"2つ目のタイトルが正しいこと: {candidates[1]['title']}"
        assert candidates[1]["ingredients"] == ["ほうれん草", "ごま"], \
            f"2つ目のingredientsが正しいこと: {candidates[1]['ingredients']}"
        
        print("✅ ingredientsがある場合のパーステストが成功しました")
        return True
    
    def test_parse_candidate_response_without_ingredients(self):
        """ingredientsがない場合のデフォルト値設定"""
        print("\n[テスト2] LLM _parse_candidate_response() - ingredientsなし（デフォルト値設定）")
        
        # RecipeLLMインスタンス作成
        llm = RecipeLLM()
        
        # テストデータ（ingredientsなし）
        response_content = """
        {
            "candidates": [
                {"title": "レンコン炒め"},
                {"title": "ほうれん草の胡麻和え"}
            ]
        }
        """
        
        # テスト実行
        candidates = llm._parse_candidate_response(response_content)
        
        # 検証
        assert len(candidates) == 2, f"候補数が2であること: {len(candidates)}"
        assert candidates[0]["title"] == "レンコン炒め", f"1つ目のタイトルが正しいこと: {candidates[0]['title']}"
        assert "ingredients" in candidates[0], f"1つ目の候補にingredientsフィールドがあること"
        assert candidates[0]["ingredients"] == [], f"1つ目のingredientsが空リストであること: {candidates[0]['ingredients']}"
        assert candidates[1]["title"] == "ほうれん草の胡麻和え", f"2つ目のタイトルが正しいこと: {candidates[1]['title']}"
        assert "ingredients" in candidates[1], f"2つ目の候補にingredientsフィールドがあること"
        assert candidates[1]["ingredients"] == [], f"2つ目のingredientsが空リストであること: {candidates[1]['ingredients']}"
        
        print("✅ ingredientsがない場合のデフォルト値設定テストが成功しました")
        return True
    
    def test_parse_candidate_response_mixed(self):
        """ingredientsがある候補とない候補が混在する場合"""
        print("\n[テスト3] LLM _parse_candidate_response() - ingredients混在")
        
        # RecipeLLMインスタンス作成
        llm = RecipeLLM()
        
        # テストデータ（ingredients混在）
        response_content = """
        {
            "candidates": [
                {"title": "レンコン炒め", "ingredients": ["レンコン", "にんじん"]},
                {"title": "ほうれん草の胡麻和え"}
            ]
        }
        """
        
        # テスト実行
        candidates = llm._parse_candidate_response(response_content)
        
        # 検証
        assert len(candidates) == 2, f"候補数が2であること: {len(candidates)}"
        assert candidates[0]["ingredients"] == ["レンコン", "にんじん"], \
            f"1つ目のingredientsが正しいこと: {candidates[0]['ingredients']}"
        assert candidates[1]["ingredients"] == [], \
            f"2つ目のingredientsが空リストであること: {candidates[1]['ingredients']}"
        
        print("✅ ingredients混在の場合のテストが成功しました")
        return True


class TestRAGCandidateIngredients:
    """RAG提案の候補にingredientsが含まれることのテスト"""
    
    async def test_search_candidates_with_ingredients(self):
        """search_candidates()でingredientsが含まれること"""
        print("\n[テスト4] RAG search_candidates() - ingredientsあり")
        
        # モックの準備
        mock_search_engine = Mock()
        mock_search_engine.search_similar_recipes = AsyncMock(return_value=[
            {
                "title": "レンコン炒め",
                "category": "main",
                "content": "レンコン、にんじん、鶏肉を使った料理です。",
                "ingredients": ["レンコン", "にんじん", "鶏肉"]  # 既にingredientsがある
            },
            {
                "title": "ほうれん草の胡麻和え",
                "category": "sub",
                "content": "ほうれん草、ごまを使った料理です。"
                # ingredientsがない（抽出される）
            }
        ])
        
        # RecipeRAGClientインスタンス作成
        rag_client = RecipeRAGClient()
        
        # _get_search_enginesをモック
        with patch.object(rag_client, '_get_search_engines', return_value={"main": mock_search_engine}):
            # _extract_ingredients_from_contentをモック
            with patch.object(rag_client, '_extract_ingredients_from_content', return_value=["ほうれん草", "ごま"]):
                # テスト実行
                results = await rag_client.search_candidates(
                    ingredients=["レンコン", "にんじん", "鶏肉"],
                    menu_type="和食",
                    category="main",
                    limit=2
                )
                
                # 検証
                assert len(results) == 2, f"結果数が2であること: {len(results)}"
                assert results[0]["title"] == "レンコン炒め", f"1つ目のタイトルが正しいこと: {results[0]['title']}"
                assert results[0]["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
                    f"1つ目のingredientsが正しいこと: {results[0]['ingredients']}"
                assert results[1]["title"] == "ほうれん草の胡麻和え", f"2つ目のタイトルが正しいこと: {results[1]['title']}"
                assert "ingredients" in results[1], f"2つ目の候補にingredientsフィールドがあること"
                assert results[1]["ingredients"] == ["ほうれん草", "ごま"], \
                    f"2つ目のingredientsが抽出されていること: {results[1]['ingredients']}"
                
                print("✅ search_candidates()でingredientsが含まれることのテストが成功しました")
                return True


class TestSessionCandidateIngredients:
    """セッション保存時にingredientsが保存されることのテスト"""
    
    def test_candidate_component_set_with_ingredients(self):
        """CandidateComponent.set()でingredientsが含まれる候補を保存できること"""
        print("\n[テスト5] CandidateComponent.set() - ingredientsあり")
        
        # ロガーのモック
        mock_logger = Mock(spec=GenericLogger)
        
        # CandidateComponentインスタンス作成
        component = CandidateComponent(mock_logger)
        
        # テストデータ（ingredientsあり）
        candidates = [
            {
                "title": "レンコン炒め",
                "source": "llm",
                "ingredients": ["レンコン", "にんじん", "鶏肉"]
            },
            {
                "title": "ほうれん草の胡麻和え",
                "source": "rag",
                "ingredients": ["ほうれん草", "ごま"]
            }
        ]
        
        # テスト実行
        component.set("main", candidates)
        
        # 検証
        saved_candidates = component.get("main")
        assert len(saved_candidates) == 2, f"保存された候補数が2であること: {len(saved_candidates)}"
        assert saved_candidates[0]["title"] == "レンコン炒め", f"1つ目のタイトルが正しいこと: {saved_candidates[0]['title']}"
        assert saved_candidates[0]["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
            f"1つ目のingredientsが保存されていること: {saved_candidates[0]['ingredients']}"
        assert saved_candidates[1]["title"] == "ほうれん草の胡麻和え", f"2つ目のタイトルが正しいこと: {saved_candidates[1]['title']}"
        assert saved_candidates[1]["ingredients"] == ["ほうれん草", "ごま"], \
            f"2つ目のingredientsが保存されていること: {saved_candidates[1]['ingredients']}"
        
        print("✅ CandidateComponent.set()でingredientsが含まれる候補を保存できることのテストが成功しました")
        return True
    
    def test_candidate_component_get_with_ingredients(self):
        """CandidateComponent.get()でingredientsが含まれる候補を取得できること"""
        print("\n[テスト6] CandidateComponent.get() - ingredientsあり")
        
        # ロガーのモック
        mock_logger = Mock(spec=GenericLogger)
        
        # CandidateComponentインスタンス作成
        component = CandidateComponent(mock_logger)
        
        # テストデータ（ingredientsあり）
        candidates = [
            {
                "title": "レンコン炒め",
                "source": "llm",
                "ingredients": ["レンコン", "にんじん", "鶏肉"]
            }
        ]
        
        # 保存
        component.set("main", candidates)
        
        # 取得
        retrieved_candidates = component.get("main")
        
        # 検証
        assert len(retrieved_candidates) == 1, f"取得された候補数が1であること: {len(retrieved_candidates)}"
        assert retrieved_candidates[0]["title"] == "レンコン炒め", f"タイトルが正しいこと: {retrieved_candidates[0]['title']}"
        assert retrieved_candidates[0]["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
            f"ingredientsが取得されていること: {retrieved_candidates[0]['ingredients']}"
        
        print("✅ CandidateComponent.get()でingredientsが含まれる候補を取得できることのテストが成功しました")
        return True
    
    def test_candidate_component_without_ingredients(self):
        """ingredientsがない候補でも保存・取得できること（既存動作確認）"""
        print("\n[テスト7] CandidateComponent - ingredientsなし（既存動作確認）")
        
        # ロガーのモック
        mock_logger = Mock(spec=GenericLogger)
        
        # CandidateComponentインスタンス作成
        component = CandidateComponent(mock_logger)
        
        # テストデータ（ingredientsなし）
        candidates = [
            {
                "title": "レンコン炒め",
                "source": "llm"
                # ingredientsフィールドなし
            }
        ]
        
        # 保存
        component.set("main", candidates)
        
        # 取得
        retrieved_candidates = component.get("main")
        
        # 検証
        assert len(retrieved_candidates) == 1, f"取得された候補数が1であること: {len(retrieved_candidates)}"
        assert retrieved_candidates[0]["title"] == "レンコン炒め", f"タイトルが正しいこと: {retrieved_candidates[0]['title']}"
        # ingredientsがない場合でも保存・取得できること（既存動作確認）
        
        print("✅ ingredientsがない候補でも保存・取得できることのテストが成功しました")
        return True


async def run_all_tests():
    """全てのテストを実行"""
    print("=" * 80)
    print("セッション2: Phase 1C（提案レスポンスに食材情報を含める）の単体テスト")
    print("=" * 80)
    
    test_llm = TestLLMCandidateIngredients()
    test_rag = TestRAGCandidateIngredients()
    test_session = TestSessionCandidateIngredients()
    
    tests = [
        ("test_parse_candidate_response_with_ingredients", test_llm.test_parse_candidate_response_with_ingredients),
        ("test_parse_candidate_response_without_ingredients", test_llm.test_parse_candidate_response_without_ingredients),
        ("test_parse_candidate_response_mixed", test_llm.test_parse_candidate_response_mixed),
        ("test_search_candidates_with_ingredients", test_rag.test_search_candidates_with_ingredients),
        ("test_candidate_component_set_with_ingredients", test_session.test_candidate_component_set_with_ingredients),
        ("test_candidate_component_get_with_ingredients", test_session.test_candidate_component_get_with_ingredients),
        ("test_candidate_component_without_ingredients", test_session.test_candidate_component_without_ingredients),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*80}")
            print(f"実行中: {test_name}")
            print('='*80)
            
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                failed += 1
                
        except AssertionError as e:
            print(f"\n❌ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"テスト結果: {passed} passed, {failed} failed (合計 {len(tests)})")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

