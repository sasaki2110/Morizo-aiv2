#!/usr/bin/env python3
"""
セッション1: Phase 1A（段階提案での食材保持と保存）の単体テスト

RecipeHistoryCRUD.add_history()とapi/routes/menu.pyのsave_menu()のテスト
"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
from api.routes.menu import save_menu
from api.models import MenuSaveRequest, MenuSaveResponse
from fastapi import Request, HTTPException


class TestRecipeHistoryCRUD:
    """RecipeHistoryCRUD.add_history()の単体テスト"""
    
    async def test_add_history_with_ingredients(self):
        """ingredientsがある場合の保存テスト"""
        print("\n[テスト1] RecipeHistoryCRUD.add_history() - ingredientsあり")
        
        # モッククライアントの作成
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()
        
        # モックのチェーン設定
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(
            data=[{
                "id": "test-history-id-1",
                "user_id": "test-user-id",
                "title": "テストレシピ",
                "source": "web",
                "ingredients": ["レンコン", "にんじん", "鶏肉"]
            }]
        )
        
        # CRUDインスタンス作成
        crud = RecipeHistoryCRUD()
        
        # テスト実行
        ingredients = ["レンコン", "にんじん", "鶏肉"]
        result = await crud.add_history(
            client=mock_client,
            user_id="test-user-id",
            title="テストレシピ",
            source="web",
            ingredients=ingredients
        )
        
        # 検証
        assert result["success"] == True, f"保存が成功していること: {result}"
        assert result["data"]["id"] == "test-history-id-1", f"IDが正しいこと: {result['data']['id']}"
        assert result["data"]["ingredients"] == ingredients, f"ingredientsが保存されていること: {result['data']['ingredients']}"
        
        # モックの呼び出し確認
        mock_client.table.assert_called_once_with("recipe_historys")
        mock_table.insert.assert_called_once()
        
        # insertに渡されたデータを確認
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["ingredients"] == ingredients, f"ingredientsがinsertに渡されていること: {call_args}"
        
        print("✅ ingredientsがある場合の保存テストが成功しました")
        return True
    
    async def test_add_history_without_ingredients(self):
        """ingredientsがない場合の既存動作確認"""
        print("\n[テスト2] RecipeHistoryCRUD.add_history() - ingredientsなし")
        
        # モッククライアントの作成
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        
        # モックのチェーン設定
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(
            data=[{
                "id": "test-history-id-2",
                "user_id": "test-user-id",
                "title": "テストレシピ2",
                "source": "web"
            }]
        )
        
        # CRUDインスタンス作成
        crud = RecipeHistoryCRUD()
        
        # テスト実行（ingredientsなし）
        result = await crud.add_history(
            client=mock_client,
            user_id="test-user-id",
            title="テストレシピ2",
            source="web"
        )
        
        # 検証
        assert result["success"] == True, f"保存が成功していること: {result}"
        assert result["data"]["id"] == "test-history-id-2", f"IDが正しいこと: {result['data']['id']}"
        
        # モックの呼び出し確認
        mock_client.table.assert_called_once_with("recipe_historys")
        mock_table.insert.assert_called_once()
        
        # insertに渡されたデータを確認（ingredientsが含まれていないこと）
        call_args = mock_table.insert.call_args[0][0]
        assert "ingredients" not in call_args, f"ingredientsがinsertに渡されていないこと: {call_args}"
        
        print("✅ ingredientsがない場合の既存動作確認が成功しました")
        return True
    
    async def test_add_history_with_empty_ingredients(self):
        """ingredientsが空リストの場合の処理"""
        print("\n[テスト3] RecipeHistoryCRUD.add_history() - ingredientsが空リスト")
        
        # モッククライアントの作成
        mock_client = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        
        # モックのチェーン設定
        mock_client.table.return_value = mock_table
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(
            data=[{
                "id": "test-history-id-3",
                "user_id": "test-user-id",
                "title": "テストレシピ3",
                "source": "web"
            }]
        )
        
        # CRUDインスタンス作成
        crud = RecipeHistoryCRUD()
        
        # テスト実行（ingredientsが空リスト）
        result = await crud.add_history(
            client=mock_client,
            user_id="test-user-id",
            title="テストレシピ3",
            source="web",
            ingredients=[]  # 空リスト
        )
        
        # 検証
        assert result["success"] == True, f"保存が成功していること: {result}"
        
        # モックの呼び出し確認
        mock_client.table.assert_called_once_with("recipe_historys")
        mock_table.insert.assert_called_once()
        
        # insertに渡されたデータを確認（空リストの場合はingredientsが含まれないこと）
        call_args = mock_table.insert.call_args[0][0]
        # 空リストはfalsyなので、if ingredients: の条件でFalseになり、ingredientsは含まれない
        assert "ingredients" not in call_args, f"空リストの場合はingredientsがinsertに渡されないこと: {call_args}"
        
        print("✅ ingredientsが空リストの場合の処理が成功しました")
        return True


class TestMenuSave:
    """api/routes/menu.pyのsave_menu()の単体テスト"""
    
    async def test_save_menu_with_ingredients(self):
        """選択済みレシピにingredientsがある場合"""
        print("\n[テスト4] save_menu() - ingredientsあり")
        
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
            "data": {"id": "test-history-id-main"}
        })
        
        # get_authenticated_clientのモック
        with patch('api.routes.menu.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.menu.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成
                menu_request = MenuSaveRequest(
                    recipes={
                        "main": {
                            "title": "レンコン炒め",
                            "source": "web",
                            "url": "https://example.com/recipe1",
                            "ingredients": ["レンコン", "にんじん", "鶏肉"]
                        }
                    }
                )
                
                # テスト実行
                response = await save_menu(menu_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 1, f"保存数が1であること: {response.total_saved}"
                assert len(response.saved_recipes) == 1, f"保存レシピ数が1であること: {len(response.saved_recipes)}"
                
                # add_historyがingredientsと共に呼ばれたことを確認
                mock_crud.add_history.assert_called_once()
                call_kwargs = mock_crud.add_history.call_args[1]
                assert call_kwargs["ingredients"] == ["レンコン", "にんじん", "鶏肉"], \
                    f"ingredientsが渡されていること: {call_kwargs.get('ingredients')}"
                
                print("✅ ingredientsがある場合のsave_menu()テストが成功しました")
                return True
    
    async def test_save_menu_without_ingredients(self):
        """選択済みレシピにingredientsがない場合"""
        print("\n[テスト5] save_menu() - ingredientsなし")
        
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
            "data": {"id": "test-history-id-main"}
        })
        
        # get_authenticated_clientのモック
        with patch('api.routes.menu.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.menu.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成（ingredientsなし）
                menu_request = MenuSaveRequest(
                    recipes={
                        "main": {
                            "title": "レンコン炒め",
                            "source": "web",
                            "url": "https://example.com/recipe1"
                            # ingredientsフィールドなし
                        }
                    }
                )
                
                # テスト実行
                response = await save_menu(menu_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 1, f"保存数が1であること: {response.total_saved}"
                
                # add_historyがingredients=Noneで呼ばれたことを確認
                mock_crud.add_history.assert_called_once()
                call_kwargs = mock_crud.add_history.call_args[1]
                assert call_kwargs.get("ingredients") is None, \
                    f"ingredientsがNoneであること: {call_kwargs.get('ingredients')}"
                
                print("✅ ingredientsがない場合のsave_menu()テストが成功しました")
                return True
    
    async def test_save_menu_with_empty_ingredients(self):
        """選択済みレシピにingredientsが空リストの場合"""
        print("\n[テスト6] save_menu() - ingredientsが空リスト")
        
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
            "data": {"id": "test-history-id-main"}
        })
        
        # get_authenticated_clientのモック
        with patch('api.routes.menu.get_authenticated_client', return_value=mock_client):
            with patch('api.routes.menu.RecipeHistoryCRUD', return_value=mock_crud):
                # リクエストデータ作成（ingredientsが空リスト）
                menu_request = MenuSaveRequest(
                    recipes={
                        "main": {
                            "title": "レンコン炒め",
                            "source": "web",
                            "url": "https://example.com/recipe1",
                            "ingredients": []  # 空リスト
                        }
                    }
                )
                
                # テスト実行
                response = await save_menu(menu_request, mock_request)
                
                # 検証
                assert response.success == True, f"保存が成功していること: {response.success}"
                assert response.total_saved == 1, f"保存数が1であること: {response.total_saved}"
                
                # add_historyがingredients=Noneで呼ばれたことを確認（空リストはNoneに変換される）
                mock_crud.add_history.assert_called_once()
                call_kwargs = mock_crud.add_history.call_args[1]
                assert call_kwargs.get("ingredients") is None, \
                    f"空リストがNoneに変換されていること: {call_kwargs.get('ingredients')}"
                
                print("✅ ingredientsが空リストの場合のsave_menu()テストが成功しました")
                return True


async def run_all_tests():
    """全てのテストを実行"""
    print("=" * 80)
    print("セッション1: Phase 1A（段階提案での食材保持と保存）の単体テスト")
    print("=" * 80)
    
    test_crud = TestRecipeHistoryCRUD()
    test_menu = TestMenuSave()
    
    tests = [
        ("test_add_history_with_ingredients", test_crud.test_add_history_with_ingredients),
        ("test_add_history_without_ingredients", test_crud.test_add_history_without_ingredients),
        ("test_add_history_with_empty_ingredients", test_crud.test_add_history_with_empty_ingredients),
        ("test_save_menu_with_ingredients", test_menu.test_save_menu_with_ingredients),
        ("test_save_menu_without_ingredients", test_menu.test_save_menu_without_ingredients),
        ("test_save_menu_with_empty_ingredients", test_menu.test_save_menu_with_empty_ingredients),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*80}")
            print(f"実行中: {test_name}")
            print('='*80)
            
            result = await test_func()
            
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

