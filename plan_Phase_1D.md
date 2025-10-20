# Phase 1D: 重複回避機能テスト

## 概要

Phase 1A〜1Cで実装した重複回避機能をテストします。履歴取得機能、除外レシピ適用、統合テストを実施し、主菜は14日間、副菜は7日間の重複回避が正しく動作することを確認します。

## 対象範囲

- 履歴取得機能のテスト
- MCPツール統合テスト
- カテゴリ別重複回避期間のテスト
- 重複回避機能の統合テスト
- パフォーマンステスト

## テスト計画

### 1. 履歴取得機能テスト

#### 1.1 基本履歴取得テスト
**テストケース**: `get_recent_recipe_titles()`の動作確認

**テスト内容**:
```python
async def test_history_get_recent_titles():
    """履歴取得機能のテスト"""
    
    # 1. 履歴にレシピを保存
    history_crud = RecipeHistoryCRUD()
    client = get_authenticated_client("test_user", "test_token")
    
    await history_crud.add_history(
        client, "test_user", "レンコンのきんぴら", "rag"
    )
    await history_crud.add_history(
        client, "test_user", "キャベツの炒め物", "web"
    )
    
    # 2. 履歴タイトルを取得
    result = await history_crud.get_recent_recipe_titles(
        client, "test_user", "main", 14
    )
    
    # 検証
    assert result["success"] == True
    assert "レンコンのきんぴら" in result["data"]
    assert "キャベツの炒め物" in result["data"]
    
    # 3. 主菜提案で重複回避を確認
    excluded_recipes = result["data"]
    proposals_result = await generate_main_dish_proposals(
        ["レンコン", "キャベツ", "大根"],
        "test_user",
        "",
        None,
        excluded_recipes
    )
    
    # 検証: 除外レシピが提案されていない
    proposed_titles = [c["title"] for c in proposals_result["data"]["candidates"]]
    assert "レンコンのきんぴら" not in proposed_titles
    assert "キャベツの炒め物" not in proposed_titles
```

#### 1.2 カテゴリ別重複回避期間テスト
**テストケース**: カテゴリ別の重複回避期間の確認

**テスト内容**:
```python
async def test_category_specific_exclusion():
    """カテゴリ別重複回避期間のテスト"""
    
    client = get_authenticated_client("test_user", "test_token")
    history_crud = RecipeHistoryCRUD()
    
    # 主菜: 14日間
    main_result = await history_crud.get_recent_recipe_titles(
        client, "test_user", "main", 14
    )
    
    # 副菜: 7日間
    sub_result = await history_crud.get_recent_recipe_titles(
        client, "test_user", "sub", 7
    )
    
    # 検証
    assert main_result["success"] == True
    assert sub_result["success"] == True
    
    # 主菜の方が期間が長いため、より多くのレシピが除外される
    # （履歴データ次第）
```

#### 1.3 期間指定テスト
**テストケース**: 異なる期間での履歴取得

**テスト内容**:
```python
async def test_different_periods():
    """異なる期間での履歴取得テスト"""
    
    client = get_authenticated_client("test_user", "test_token")
    history_crud = RecipeHistoryCRUD()
    
    # 7日間の履歴
    result_7days = await history_crud.get_recent_recipe_titles(
        client, "test_user", "main", 7
    )
    
    # 14日間の履歴
    result_14days = await history_crud.get_recent_recipe_titles(
        client, "test_user", "main", 14
    )
    
    # 検証: 14日間の方が多くのレシピが含まれる
    assert len(result_14days["data"]) >= len(result_7days["data"])
```

### 2. MCPツール統合テスト

#### 2.1 履歴取得MCPツールテスト
**テストケース**: `history_get_recent_titles()`の動作確認

**テスト内容**:
```python
async def test_history_mcp_tool():
    """履歴取得MCPツールのテスト"""
    
    # MCPツールを直接呼び出し
    result = await history_get_recent_titles(
        "test_user", "main", 14, "test_token"
    )
    
    # 検証
    assert result["success"] == True
    assert isinstance(result["data"], list)
    
    # エラーケースのテスト
    error_result = await history_get_recent_titles(
        "invalid_user", "main", 14, "invalid_token"
    )
    
    # 検証
    assert error_result["success"] == False
    assert "error" in error_result
```

#### 2.2 ToolRouter統合テスト
**テストケース**: ToolRouterでの履歴取得ツールのルーティング

**テスト内容**:
```python
async def test_tool_router_history():
    """ToolRouterでの履歴取得ツールのテスト"""
    
    tool_router = ToolRouter()
    
    # サービスメソッド形式で呼び出し
    result = await tool_router.route_service_method(
        "history_service", "history_get_recent_titles",
        user_id="test_user", category="main", days=14, token="test_token"
    )
    
    # 検証
    assert result["success"] == True
    assert isinstance(result["data"], list)
```

### 3. LLM/RAG除外機能テスト

#### 3.1 LLM除外機能テスト
**テストケース**: LLM推論での除外レシピ適用

**テスト内容**:
```python
async def test_llm_exclusion():
    """LLM推論での除外レシピ適用テスト"""
    
    inventory_items = ["レンコン", "キャベツ", "大根"]
    menu_type = "和食"
    main_ingredient = "レンコン"
    excluded_recipes = ["レンコンのきんぴら", "レンコンの天ぷら"]
    
    # 実行
    result = await llm_client.generate_main_dish_candidates(
        inventory_items, menu_type, main_ingredient, excluded_recipes, count=2
    )
    
    # 検証
    assert result["success"] == True
    assert len(result["data"]["candidates"]) == 2
    
    for candidate in result["data"]["candidates"]:
        assert candidate["title"] not in excluded_recipes
        assert main_ingredient in candidate["ingredients"]
```

#### 3.2 RAG除外機能テスト
**テストケース**: RAG検索での除外レシピ適用

**テスト内容**:
```python
async def test_rag_exclusion():
    """RAG検索での除外レシピ適用テスト"""
    
    inventory_items = ["レンコン", "キャベツ", "大根"]
    menu_type = "和食"
    main_ingredient = "レンコン"
    excluded_recipes = ["レンコンのきんぴら", "レンコンの天ぷら"]
    
    # 実行
    results = await rag_client.search_main_dish_candidates(
        inventory_items, menu_type, main_ingredient, excluded_recipes, limit=3
    )
    
    # 検証
    assert len(results) == 3
    
    for result in results:
        assert result["title"] not in excluded_recipes
```

### 4. 統合テスト

#### 4.1 重複回避統合テスト
**テストケース**: 重複回避機能を含む一連の流れ

**テスト内容**:
```python
async def test_duplicate_avoidance_integration():
    """重複回避機能の統合テスト"""
    
    # 1. 履歴にレシピを保存
    history_crud = RecipeHistoryCRUD()
    client = get_authenticated_client("test_user", "test_token")
    
    await history_crud.add_history(
        client, "test_user", "レンコンのきんぴら", "rag"
    )
    
    # 2. ユーザー要求（主菜提案）
    user_request = "レンコンを使った主菜を5件提案して"
    user_id = "test_user"
    token = "test_token"
    sse_session_id = "test_session"
    
    # 3. エージェントで処理
    response = await agent.process_request(user_request, user_id, token, sse_session_id)
    
    # 4. 検証
    assert "主菜の提案（5件）" in response
    assert "レンコン使用" in response
    assert "斬新な提案（LLM推論）" in response
    assert "伝統的な提案（RAG検索）" in response
    assert "レンコン" in response  # 主要食材が表示されている
    
    # 5. 重複回避の確認（除外レシピが提案されていない）
    assert "レンコンのきんぴら" not in response
```

#### 4.2 3段階タスク構成テスト
**テストケース**: プランナーでの3段階タスク構成（在庫取得→履歴取得→主菜提案）

**テスト内容**:
```python
async def test_three_stage_task_flow():
    """3段階タスク構成のテスト"""
    
    # ユーザー要求
    user_request = "主菜を5件提案して"
    user_id = "test_user"
    token = "test_token"
    sse_session_id = "test_session"
    
    # プランナーでタスク生成
    tasks = await planner.generate_tasks(user_request)
    
    # 検証: 3段階のタスクが生成される
    assert len(tasks) == 3
    
    # task1: 在庫取得
    assert tasks[0].service == "inventory_service"
    assert tasks[0].method == "get_inventory"
    
    # task2: 履歴取得
    assert tasks[1].service == "history_service"
    assert tasks[1].method == "history_get_recent_titles"
    assert tasks[1].parameters["category"] == "main"
    assert tasks[1].parameters["days"] == 14
    
    # task3: 主菜提案
    assert tasks[2].service == "recipe_service"
    assert tasks[2].method == "generate_main_dish_proposals"
    assert tasks[2].parameters["inventory_items"] == "task1.result"
    assert tasks[2].parameters["excluded_recipes"] == "task2.result.data"
```

#### 4.3 エラーハンドリングテスト
**テストケース**: 履歴取得エラー時の動作

**テスト内容**:
```python
async def test_history_error_handling():
    """履歴取得エラー時のテスト"""
    
    # 無効なユーザーIDで履歴取得
    result = await history_get_recent_titles(
        "invalid_user", "main", 14, "invalid_token"
    )
    
    # 検証: エラーが適切に処理される
    assert result["success"] == False
    assert "error" in result
    assert result["data"] == []  # 空のリストが返される
    
    # 主菜提案は除外レシピなしで実行される
    proposals_result = await generate_main_dish_proposals(
        ["レンコン", "キャベツ", "大根"],
        "invalid_user",
        "",
        None,
        []  # 空の除外リスト
    )
    
    # 検証: 主菜提案は正常に実行される
    assert proposals_result["success"] == True
    assert proposals_result["data"]["excluded_count"] == 0
```

### 5. パフォーマンステスト

#### 5.1 履歴取得パフォーマンステスト
**テストケース**: 履歴取得のレスポンス時間

**テスト内容**:
```python
async def test_history_performance():
    """履歴取得のパフォーマンステスト"""
    
    import time
    
    client = get_authenticated_client("test_user", "test_token")
    history_crud = RecipeHistoryCRUD()
    
    # 実行時間測定
    start_time = time.time()
    
    result = await history_crud.get_recent_recipe_titles(
        client, "test_user", "main", 14
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 検証（1秒以内）
    assert execution_time < 1.0
    assert result["success"] == True
    print(f"History retrieval time: {execution_time:.3f} seconds")
```

#### 5.2 重複回避統合パフォーマンステスト
**テストケース**: 重複回避機能を含む統合処理のレスポンス時間

**テスト内容**:
```python
async def test_duplicate_avoidance_performance():
    """重複回避機能の統合パフォーマンステスト"""
    
    import time
    
    # テストデータ
    user_request = "レンコンを使った主菜を5件提案して"
    user_id = "test_user"
    token = "test_token"
    sse_session_id = "test_session"
    
    # 実行時間測定
    start_time = time.time()
    
    response = await agent.process_request(user_request, user_id, token, sse_session_id)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 検証（6秒以内 - 履歴取得が追加されるため少し長め）
    assert execution_time < 6.0
    assert "主菜の提案（5件）" in response
    print(f"Duplicate avoidance integration time: {execution_time:.2f} seconds")
```

## テスト実行計画

### 実行順序
1. **履歴取得機能テスト** → 基本機能が動作することを確認
2. **MCPツール統合テスト** → MCPツールが正しく動作することを確認
3. **LLM/RAG除外機能テスト** → 除外機能が正しく動作することを確認
4. **統合テスト** → 全体の流れが動作することを確認
5. **パフォーマンステスト** → 性能要件を満たすことを確認

### テスト環境
- **開発環境**: ローカル開発環境
- **テストデータ**: サンプル在庫データ + 履歴データ
- **認証**: テスト用トークン
- **データベース**: テスト用データベース

### 成功基準
- すべての単体テストが成功
- 統合テストが成功
- 履歴取得が1秒以内
- 重複回避統合処理が6秒以内
- エラーハンドリングが適切に動作
- 重複回避機能が正しく動作

## 制約事項
- Phase 1A〜1Cが完成している必要がある
- テスト用の履歴データが必要
- 認証トークンの設定が必要

## 期待される効果
- 重複回避機能の品質保証
- ユーザー体験の向上確認（同じレシピを短期間に繰り返し見ない）
- システムの安定性確認
- Phase 2以降の基盤確立

### To-dos

- [ ] 履歴取得機能のテストを実装・実行
- [ ] MCPツール統合テストを実装・実行
- [ ] LLM/RAG除外機能テストを実装・実行
- [ ] 重複回避統合テストを実装・実行
- [ ] 3段階タスク構成テストを実装・実行
- [ ] エラーハンドリングテストを実装・実行
- [ ] パフォーマンステストを実装・実行
- [ ] テスト結果の分析とレポート作成
- [ ] Phase 1Dの完了確認
