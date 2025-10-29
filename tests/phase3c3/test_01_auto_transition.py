#!/usr/bin/env python3
"""
Phase 3C-3: 自動遷移機能の結合テスト

主菜選択後の副菜自動遷移、
副菜選択後の汁物自動遷移、
汁物選択後の完了のテスト
"""

import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

print("=" * 80)
print("Phase 3C-3: 自動遷移機能の結合テスト")
print("=" * 80)


async def test_session_methods():
    """セッションの新規メソッド（set_candidates, get_candidates）のテスト"""
    print("\n[テスト1] セッションメソッドのテスト")
    
    from services.session_service import session_service
    
    try:
        # セッションを作成
        session = await session_service.create_session("test_user", "test_session_001")
        print("✅ セッション作成成功")
        
        # 候補情報を設定
        candidates = [
            {"title": "レンコンのきんぴら", "ingredients": ["レンコン", "人参"]},
            {"title": "ひじきの煮物", "ingredients": ["ひじき", "人参"]}
        ]
        session.set_candidates("main", candidates)
        print(f"✅ 候補情報を設定: {len(candidates)}件")
        
        # 候補情報を取得
        retrieved = session.get_candidates("main")
        print(f"✅ 候補情報を取得: {len(retrieved)}件")
        
        assert len(retrieved) == 2
        assert retrieved[0]["title"] == "レンコンのきんぴら"
        print("✅ セッションメソッドのテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ セッションメソッドのテスト失敗: {e}")
        return False


async def test_advance_stage():
    """段階進行のテスト"""
    print("\n[テスト2] 段階進行のテスト")
    
    from core.agent import TrueReactAgent
    from services.session_service import session_service
    
    agent = TrueReactAgent()
    user_id = "test_user"
    sse_session_id = "test_session_002"
    
    try:
        # セッションを作成
        session = await session_service.create_session(user_id, sse_session_id)
        print("✅ セッション作成成功")
        
        # 主菜を選択
        selected_recipe = {
            "title": "レンコンのきんぴら",
            "ingredients": ["レンコン", "人参"],
            "menu_type": "和食"
        }
        
        next_stage = await agent._advance_stage(sse_session_id, user_id, selected_recipe)
        print(f"✅ 段階進行: {next_stage}")
        
        # セッションの状態を確認
        session = await session_service.get_session(sse_session_id, user_id)
        assert session.current_stage == "sub"
        assert session.selected_main_dish is not None
        assert len(session.used_ingredients) > 0
        
        print(f"✅ 使用済み食材: {session.used_ingredients}")
        print("✅ 段階進行のテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 段階進行のテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_selected_recipe():
    """選択レシピ取得のテスト"""
    print("\n[テスト3] 選択レシピ取得のテスト")
    
    from core.agent import TrueReactAgent
    from services.session_service import session_service
    
    agent = TrueReactAgent()
    user_id = "test_user"
    sse_session_id = "test_session_003"
    
    try:
        # セッションを作成
        session = await session_service.create_session(user_id, sse_session_id)
        print("✅ セッション作成成功")
        
        # 候補情報を設定
        candidates = [
            {"title": "レンコンのきんぴら", "ingredients": ["レンコン", "人参"]},
            {"title": "ひじきの煮物", "ingredients": ["ひじき", "人参"]},
            {"title": "ほうれん草の胡麻和え", "ingredients": ["ほうれん草", "ごま"]}
        ]
        session.set_candidates("main", candidates)
        print(f"✅ 候補情報を設定: {len(candidates)}件")
        
        # 選択レシピを取得（selection=1）
        selected_recipe = await agent._get_selected_recipe_from_task(
            sse_session_id, 1, sse_session_id
        )
        print(f"✅ 選択レシピ: {selected_recipe.get('title', 'Unknown')}")
        
        assert selected_recipe["title"] == "レンコンのきんぴら"
        print("✅ 選択レシピ取得のテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 選択レシピ取得のテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_generate_requests():
    """リクエスト生成のテスト"""
    print("\n[テスト4] リクエスト生成のテスト")
    
    from core.agent import TrueReactAgent
    from services.session_service import session_service
    
    agent = TrueReactAgent()
    user_id = "test_user"
    sse_session_id = "test_session_004"
    
    try:
        # セッションを作成し、主菜を選択済みにする
        session = await session_service.create_session(user_id, sse_session_id)
        session.set_selected_recipe("main", {
            "title": "レンコンのきんぴら",
            "ingredients": ["レンコン", "人参"]
        })
        print("✅ 主菜選択済み状態を作成")
        
        # 副菜提案リクエストを生成
        sub_request = await agent._generate_sub_dish_request(
            {"title": "テスト"}, sse_session_id, user_id
        )
        print(f"✅ 副菜リクエスト: {sub_request}")
        assert "副菜" in sub_request or "使っていない食材" in sub_request
        
        # 汁物提案リクエストを生成
        soup_request = await agent._generate_soup_request(
            {"title": "テスト"}, sse_session_id, user_id
        )
        print(f"✅ 汁物リクエスト: {soup_request}")
        assert "味噌汁" in soup_request or "スープ" in soup_request
        
        print("✅ リクエスト生成のテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ リクエスト生成のテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_selected_recipes():
    """選択済みレシピ取得のテスト"""
    print("\n[テスト5] 選択済みレシピ取得のテスト")
    
    from core.agent import TrueReactAgent
    from services.session_service import session_service
    
    agent = TrueReactAgent()
    user_id = "test_user"
    sse_session_id = "test_session_005"
    
    try:
        # セッションを作成し、全段階を選択済みにする
        session = await session_service.create_session(user_id, sse_session_id)
        session.set_selected_recipe("main", {"title": "主菜1"})
        session.set_selected_recipe("sub", {"title": "副菜1"})
        session.set_selected_recipe("soup", {"title": "汁物1"})
        print("✅ 全段階選択済み状態を作成")
        
        # 選択済みレシピを取得
        sub_dish = await agent._get_selected_sub_dish(sse_session_id, user_id)
        soup = await agent._get_selected_soup(sse_session_id, user_id)
        
        print(f"✅ 副菜: {sub_dish}")
        print(f"✅ 汁物: {soup}")
        
        assert sub_dish is not None
        assert soup is not None
        
        print("✅ 選択済みレシピ取得のテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 選択済みレシピ取得のテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """全テストを実行"""
    import asyncio
    
    print("\n" + "=" * 80)
    print("全テストの実行開始")
    print("=" * 80)
    
    results = []
    
    results.append(await test_session_methods())
    results.append(await test_advance_stage())
    results.append(await test_get_selected_recipe())
    results.append(await test_generate_requests())
    results.append(await test_get_selected_recipes())
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("テスト結果サマリー")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"成功: {passed}/{total}")
    print(f"失敗: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ 全テスト成功！")
        return 0
    else:
        print("\n❌ 一部のテストが失敗しました")
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
