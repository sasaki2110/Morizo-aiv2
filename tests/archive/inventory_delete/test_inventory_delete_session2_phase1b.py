#!/usr/bin/env python3
"""
セッション2: Phase 1B（献立提案での食材保持と保存）の単体テスト

RecipeItemモデルとapi/routes/recipe.pyのadopt_recipe()のテスト
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import RecipeItem, RecipeAdoptionRequest, RecipeAdoptionResponse
from api.routes.recipe import adopt_recipe
from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
from fastapi import Request, HTTPException


class TestRecipeItem:
    """RecipeItemモデルの単体テスト"""
    
    def test_recipe_item_with_ingredients(self):
        """ingredientsがある場合のリクエスト"""
        print("\n[テスト1] RecipeItemモデル - ingredientsあり")
        
        # テストデータ作成
        recipe_item = RecipeItem(
            title="レンコン炒め",
            category="main_dish",
            menu_source="llm_menu",
            url="https://example.com/recipe1",
            ingredients=["レンコン", "にんじん", "鶏肉"]
        )
        
        # 検証
        assert recipe_item.title == "レンコン炒め", f"タイトルが正しいこと: {recipe_item.title}"
        assert recipe_item.category == "main_dish", f"カテゴリが正しいこと: {recipe_item.category}"
        assert recipe_item.menu_source == "llm_menu", f"menu_sourceが正しいこと: {recipe_item.menu_source}"
        assert recipe_item.url == "https://example.com/recipe1", f"URLが正しいこと: {recipe_item.url}"
        assert recipe_item.ingredients == ["レンコン", "にんじん", "鶏肉"], \
            f"ingredientsが正しいこと: {recipe_item.ingredients}"
        
        print("✅ ingredientsがある場合のリクエストテストが成功しました")
        return True
    
    def test_recipe_item_without_ingredients(self):
        """ingredientsがない場合のリクエスト（既存動作確認）"""
        print("\n[テスト2] RecipeItemモデル - ingredientsなし")
        
        # テストデータ作成（ingredientsなし）
        recipe_item = RecipeItem(
            title="レンコン炒め",
            category="main_dish",
            menu_source="llm_menu",
            url="https://example.com/recipe1"
            # ingredientsフィールドなし
        )
        
        # 検証
        assert recipe_item.title == "レンコン炒め", f"タイトルが正しいこと: {recipe_item.title}"
        assert recipe_item.category == "main_dish", f"カテゴリが正しいこと: {recipe_item.category}"
        assert recipe_item.menu_source == "llm_menu", f"menu_sourceが正しいこと: {recipe_item.menu_source}"
        assert recipe_item.url == "https://example.com/recipe1", f"URLが正しいこと: {recipe_item.url}"
        assert recipe_item.ingredients is None, \
            f"ingredientsがNoneであること: {recipe_item.ingredients}"
        
        print("✅ ingredientsがない場合のリクエストテストが成功しました")
        return True
    
    def test_recipe_item_with_empty_ingredients(self):
        """ingredientsが空リストの場合"""
        print("\n[テスト3] RecipeItemモデル - ingredientsが空リスト")
        
        # テストデータ作成（ingredientsが空リスト）
        recipe_item = RecipeItem(
            title="レンコン炒め",
            category="main_dish",
            menu_source="llm_menu",
            url="https://example.com/recipe1",
            ingredients=[]  # 空リスト
        )
        
        # 検証
        assert recipe_item.title == "レンコン炒め", f"タイトルが正しいこと: {recipe_item.title}"
        assert recipe_item.ingredients == [], \
            f"ingredientsが空リストであること: {recipe_item.ingredients}"
        
        print("✅ ingredientsが空リストの場合のテストが成功しました")
        return True


class TestAdoptRecipe:
    """api/routes/recipe.pyのadopt_recipe()の単体テスト"""
    
    async def test_adopt_recipe_with_ingredients(self):
        """ingredientsがある場合の保存"""
        print("\n[テスト4] adopt_recipe() - ingredientsあり")
        
        # モックの準備
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer test-token"
        mock_request.state.user_info = {"user_id": "test-user-id"}
        
        # モッククライアント
        mock_client = Mock()
        
        # RecipeHistoryCRUDのモック
        mock_crud = Mock(spec=RecipeHistoryCRUD)
        mock_crud.add_history = AsyncMock(return_value={
            "success": True,
            "data": {"id": "test-history-id-1"}
        })
        
        # get_authenticated_clientのモック
        with patch('api.routes.recipe.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.recipe.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成
                adoption_request = RecipeAdoptionRequest(
                    recipes=[
                        RecipeItem(
                            title="レンコン炒め",
                            category="main_dish",
                            menu_source="llm_menu",
                            url="https://example.com/recipe1",
                            ingredients=["レンコン", "にんじん", "鶏肉"]
                        )
                    ],
                    token="test-token"
                )
                
                # テスト実行
                response = await adopt_recipe(adoption_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 1, f"保存数が1であること: {response.total_saved}"
                assert len(response.saved_recipes) == 1, f"保存レシピ数が1であること: {len(response.saved_recipes)}"
                
                # add_historyがingredientsと共に呼ばれたことを確認
                mock_crud.add_history.assert_called_once()
                call_kwargs = mock_crud.add_history.call_args[1]
                assert call_kwargs["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
                    f"ingredientsが渡されていること: {call_kwargs.get('ingredients')}"
                assert call_kwargs["title"] == "レンコン炒め", \
                    f"タイトルが正しいこと: {call_kwargs.get('title')}"
                assert call_kwargs["source"] == "web", \
                    f"sourceが正しくマッピングされていること: {call_kwargs.get('source')}"
                
                print("✅ ingredientsがある場合の保存テストが成功しました")
                return True
    
    async def test_adopt_recipe_without_ingredients(self):
        """ingredientsがない場合の既存動作確認"""
        print("\n[テスト5] adopt_recipe() - ingredientsなし")
        
        # モックの準備
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer test-token"
        mock_request.state.user_info = {"user_id": "test-user-id"}
        
        # モッククライアント
        mock_client = Mock()
        
        # RecipeHistoryCRUDのモック
        mock_crud = Mock(spec=RecipeHistoryCRUD)
        mock_crud.add_history = AsyncMock(return_value={
            "success": True,
            "data": {"id": "test-history-id-2"}
        })
        
        # get_authenticated_clientのモック
        with patch('api.routes.recipe.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.recipe.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成（ingredientsなし）
                adoption_request = RecipeAdoptionRequest(
                    recipes=[
                        RecipeItem(
                            title="レンコン炒め",
                            category="main_dish",
                            menu_source="llm_menu",
                            url="https://example.com/recipe1"
                            # ingredientsフィールドなし
                        )
                    ],
                    token="test-token"
                )
                
                # テスト実行
                response = await adopt_recipe(adoption_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 1, f"保存数が1であること: {response.total_saved}"
                
                # add_historyがingredients=Noneで呼ばれたことを確認
                mock_crud.add_history.assert_called_once()
                call_kwargs = mock_crud.add_history.call_args[1]
                assert call_kwargs.get("ingredients") is None, \
                    f"ingredientsがNoneであること: {call_kwargs.get('ingredients')}"
                assert call_kwargs["title"] == "レンコン炒め", \
                    f"タイトルが正しいこと: {call_kwargs.get('title')}"
                
                print("✅ ingredientsがない場合の既存動作確認が成功しました")
                return True
    
    async def test_adopt_recipe_with_empty_ingredients(self):
        """ingredientsが空リストの場合"""
        print("\n[テスト6] adopt_recipe() - ingredientsが空リスト")
        
        # モックの準備
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer test-token"
        mock_request.state.user_info = {"user_id": "test-user-id"}
        
        # モッククライアント
        mock_client = Mock()
        
        # RecipeHistoryCRUDのモック
        mock_crud = Mock(spec=RecipeHistoryCRUD)
        mock_crud.add_history = AsyncMock(return_value={
            "success": True,
            "data": {"id": "test-history-id-3"}
        })
        
        # get_authenticated_clientのモック
        with patch('api.routes.recipe.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.recipe.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成（ingredientsが空リスト）
                adoption_request = RecipeAdoptionRequest(
                    recipes=[
                        RecipeItem(
                            title="レンコン炒め",
                            category="main_dish",
                            menu_source="llm_menu",
                            url="https://example.com/recipe1",
                            ingredients=[]  # 空リスト
                        )
                    ],
                    token="test-token"
                )
                
                # テスト実行
                response = await adopt_recipe(adoption_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 1, f"保存数が1であること: {response.total_saved}"
                
                # add_historyがingredients=Noneで呼ばれたことを確認（空リストはNoneに変換される）
                mock_crud.add_history.assert_called_once()
                call_kwargs = mock_crud.add_history.call_args[1]
                assert call_kwargs.get("ingredients") is None, \
                    f"空リストがNoneに変換されていること: {call_kwargs.get('ingredients')}"
                
                print("✅ ingredientsが空リストの場合のテストが成功しました")
                return True
    
    async def test_adopt_recipe_multiple_recipes_with_ingredients(self):
        """複数レシピでingredientsがある場合"""
        print("\n[テスト7] adopt_recipe() - 複数レシピでingredientsあり")
        
        # モックの準備
        mock_request = Mock(spec=Request)
        mock_request.headers.get.return_value = "Bearer test-token"
        mock_request.state.user_info = {"user_id": "test-user-id"}
        
        # モッククライアント
        mock_client = Mock()
        
        # RecipeHistoryCRUDのモック
        mock_crud = Mock(spec=RecipeHistoryCRUD)
        mock_crud.add_history = AsyncMock(side_effect=[
            {"success": True, "data": {"id": "test-history-id-main"}},
            {"success": True, "data": {"id": "test-history-id-sub"}},
            {"success": True, "data": {"id": "test-history-id-soup"}}
        ])
        
        # get_authenticated_clientのモック
        with patch('api.routes.recipe.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.recipe.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成（3つのレシピ）
                adoption_request = RecipeAdoptionRequest(
                    recipes=[
                        RecipeItem(
                            title="レンコン炒め",
                            category="main_dish",
                            menu_source="llm_menu",
                            ingredients=["レンコン", "にんじん", "鶏肉"]
                        ),
                        RecipeItem(
                            title="ほうれん草の胡麻和え",
                            category="side_dish",
                            menu_source="rag_menu",
                            ingredients=["ほうれん草", "ごま"]
                        ),
                        RecipeItem(
                            title="味噌汁",
                            category="soup",
                            menu_source="llm_menu",
                            ingredients=["味噌", "豆腐", "わかめ"]
                        )
                    ],
                    token="test-token"
                )
                
                # テスト実行
                response = await adopt_recipe(adoption_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 3, f"保存数が3であること: {response.total_saved}"
                assert len(response.saved_recipes) == 3, f"保存レシピ数が3であること: {len(response.saved_recipes)}"
                
                # add_historyが3回呼ばれたことを確認
                assert mock_crud.add_history.call_count == 3, \
                    f"add_historyが3回呼ばれたこと: {mock_crud.add_history.call_count}"
                
                # 各呼び出しのingredientsを確認
                call_args_list = mock_crud.add_history.call_args_list
                assert call_args_list[0][1]["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
                    f"1つ目のレシピのingredientsが正しいこと: {call_args_list[0][1].get('ingredients')}"
                assert call_args_list[1][1]["ingredients"] == ["ほうれん草", "ごま"], \
                    f"2つ目のレシピのingredientsが正しいこと: {call_args_list[1][1].get('ingredients')}"
                assert call_args_list[2][1]["ingredients"] == ["味噌", "豆腐", "わかめ"], \
                    f"3つ目のレシピのingredientsが正しいこと: {call_args_list[2][1].get('ingredients')}"
                
                print("✅ 複数レシピでingredientsがある場合のテストが成功しました")
                return True


async def run_all_tests():
    """全てのテストを実行"""
    print("=" * 80)
    print("セッション2: Phase 1B（献立提案での食材保持と保存）の単体テスト")
    print("=" * 80)
    
    test_recipe_item = TestRecipeItem()
    test_adopt_recipe = TestAdoptRecipe()
    
    tests = [
        ("test_recipe_item_with_ingredients", test_recipe_item.test_recipe_item_with_ingredients),
        ("test_recipe_item_without_ingredients", test_recipe_item.test_recipe_item_without_ingredients),
        ("test_recipe_item_with_empty_ingredients", test_recipe_item.test_recipe_item_with_empty_ingredients),
        ("test_adopt_recipe_with_ingredients", test_adopt_recipe.test_adopt_recipe_with_ingredients),
        ("test_adopt_recipe_without_ingredients", test_adopt_recipe.test_adopt_recipe_without_ingredients),
        ("test_adopt_recipe_with_empty_ingredients", test_adopt_recipe.test_adopt_recipe_with_empty_ingredients),
        ("test_adopt_recipe_multiple_recipes_with_ingredients", test_adopt_recipe.test_adopt_recipe_multiple_recipes_with_ingredients),
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

