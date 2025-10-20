# Phase 1C: 統合テスト

## 概要

Phase 1A（基本機能実装）とPhase 1B（プランナー・タスク設計拡張）を統合し、ユーザー要求から主菜5件提案までの一連の流れをテストします。主要食材指定・未指定の両方のケースを検証します。

## 対象範囲

- Phase 1A + Phase 1Bの統合テスト
- ユーザー要求から5件提案までの一連の流れ確認
- 主要食材指定・未指定の両方のケース
- 曖昧性検出・確認プロセスの動作確認
- エラーハンドリングの確認

## テスト計画

### 1. 基本機能テスト

#### 1.1 LLM推論テスト
**テストケース**: `generate_main_dish_candidates()`の動作確認

**テスト内容**:
```python
async def test_llm_main_dish_generation():
    """LLM推論で主菜2件生成のテスト"""
    
    # テストデータ
    inventory_items = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草"]
    menu_type = "和食"
    main_ingredient = "レンコン"
    
    # 実行
    result = await llm_client.generate_main_dish_candidates(
        inventory_items, menu_type, main_ingredient, count=2
    )
    
    # 検証
    assert result["success"] == True
    assert len(result["data"]["candidates"]) == 2
    
    for candidate in result["data"]["candidates"]:
        assert "title" in candidate
        assert "ingredients" in candidate
        assert main_ingredient in candidate["ingredients"]  # 主要食材が含まれている
```

#### 1.2 RAG検索テスト
**テストケース**: `search_main_dish_candidates()`の動作確認

**テスト内容**:
```python
async def test_rag_main_dish_search():
    """RAG検索で主菜3件検索のテスト"""
    
    # テストデータ
    inventory_items = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草"]
    menu_type = "和食"
    main_ingredient = "レンコン"
    
    # 実行
    results = await rag_client.search_main_dish_candidates(
        inventory_items, menu_type, main_ingredient, limit=3
    )
    
    # 検証
    assert len(results) == 3
    
    for result in results:
        assert "title" in result
        assert "ingredients" in result
```

#### 1.3 MCP統合テスト
**テストケース**: `generate_main_dish_proposals()`の動作確認

**テスト内容**:
```python
async def test_mcp_integration():
    """LLM + RAG統合のテスト"""
    
    # テストデータ
    inventory_items = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草"]
    user_id = "test_user"
    menu_type = "和食"
    main_ingredient = "レンコン"
    
    # 実行
    result = await generate_main_dish_proposals(
        inventory_items, user_id, menu_type, main_ingredient
    )
    
    # 検証
    assert result["success"] == True
    assert result["data"]["total"] == 5
    assert result["data"]["llm_count"] == 2
    assert result["data"]["rag_count"] == 3
    assert result["data"]["main_ingredient"] == main_ingredient
```

### 2. プランナー・タスク設計テスト

#### 2.1 プランナープロンプトテスト
**テストケース**: プランナーが主菜提案要求を正しく認識するか

**テスト内容**:
```python
async def test_planner_main_dish_recognition():
    """プランナーの主菜提案要求認識テスト"""
    
    # テストケース
    test_cases = [
        "主菜を5件提案して",
        "レンコンを使った主菜を教えて",
        "メインを提案して",
        "キャベツで主菜を作って"
    ]
    
    for user_request in test_cases:
        # プランナーでタスク生成
        tasks = await planner.generate_tasks(user_request)
        
        # 検証
        assert len(tasks) >= 2  # 在庫取得 + 主菜提案
        assert any(task.method == "generate_main_dish_proposals" for task in tasks)
```

#### 2.2 動的タスク構築テスト
**テストケース**: 動的タスク構築機能の動作確認

**テスト内容**:
```python
async def test_dynamic_task_building():
    """動的タスク構築のテスト"""
    
    # テストデータ
    inventory_items = ["レンコン", "キャベツ", "大根"]
    user_id = "test_user"
    main_ingredient = "レンコン"
    
    # 動的タスク構築
    task_builder = DynamicTaskBuilder(task_chain_manager)
    
    # 在庫取得タスク
    inventory_task = task_builder.add_inventory_task(user_id)
    
    # 主菜提案タスク
    main_dish_task = task_builder.add_main_dish_proposal_task(
        inventory_items, user_id, main_ingredient
    )
    
    # 検証
    assert inventory_task.service == "inventory_service"
    assert inventory_task.method == "get_inventory"
    assert main_dish_task.service == "recipe_service"
    assert main_dish_task.method == "generate_main_dish_proposals"
    assert main_dish_task.parameters["main_ingredient"] == main_ingredient
```

#### 2.3 コンテキスト管理テスト
**テストケース**: コンテキスト管理機能の動作確認

**テスト内容**:
```python
async def test_context_management():
    """コンテキスト管理のテスト"""
    
    # コンテキストマネージャー初期化
    context_manager = ContextManager("test_session")
    
    # 主要食材設定
    context_manager.set_main_ingredient("レンコン")
    assert context_manager.get_main_ingredient() == "レンコン"
    
    # 在庫食材設定
    inventory_items = ["レンコン", "キャベツ", "大根"]
    context_manager.set_inventory_items(inventory_items)
    assert context_manager.get_inventory_items() == inventory_items
    
    # コンテキストクリア
    context_manager.clear_context()
    assert context_manager.get_main_ingredient() is None
    assert context_manager.get_inventory_items() == []
```

### 3. 曖昧性検出・確認プロセステスト

#### 3.1 曖昧性検出テスト
**テストケース**: 主要食材未指定時の柔軟な選択肢提示

**テスト内容**:
```python
async def test_ambiguity_detection():
    """曖昧性検出のテスト（柔軟な選択肢提示）"""
    
    # 主要食材未指定のタスク
    task = Task(
        id="test_task",
        service="recipe_service",
        method="generate_main_dish_proposals",
        parameters={
            "inventory_items": ["レンコン", "キャベツ", "大根"],
            "main_ingredient": None  # 未指定
        }
    )
    
    # 曖昧性検出
    ambiguity_info = await ambiguity_detector.check_main_dish_ambiguity(task, "test_user")
    
    # 検証
    assert ambiguity_info is not None
    assert ambiguity_info.is_ambiguous == True
    assert ambiguity_info.details["type"] == "main_ingredient_optional_selection"
    assert ambiguity_info.details["message"] == "なにか主な食材を指定しますか？それとも今の在庫から作れる主菜を提案しましょうか？"
    assert len(ambiguity_info.details["options"]) == 2
```

#### 3.2 確認プロセステスト
**テストケース**: 主要食材選択の確認プロセス（柔軟な選択肢対応）

**テスト内容**:
```python
async def test_confirmation_process_proceed():
    """確認プロセスのテスト（指定せずに進める）"""
    
    # 曖昧性情報
    ambiguity_info = AmbiguityInfo(
        is_ambiguous=True,
        task_id="test_task",
        details={
            "type": "main_ingredient_optional_selection",
            "options": [
                {"value": "specify", "label": "食材を指定する"},
                {"value": "proceed", "label": "指定せずに提案してもらう"}
            ]
        }
    )
    
    # ユーザー選択（指定せずに進める）
    user_response = "そのまま提案して"
    
    # 確認プロセス処理
    result = await response_parser.process_main_ingredient_confirmation(
        ambiguity_info, user_response, {"original_tasks": [task]}
    )
    
    # 検証
    assert result.is_confirmed == True
    assert result.updated_tasks[0].parameters["main_ingredient"] is None  # null のまま
    assert "在庫から作れる主菜を提案します" in result.message

async def test_confirmation_process_specify():
    """確認プロセスのテスト（食材を指定する）"""
    
    # 曖昧性情報
    ambiguity_info = AmbiguityInfo(
        is_ambiguous=True,
        task_id="test_task",
        details={
            "type": "main_ingredient_optional_selection",
            "options": [
                {"value": "specify", "label": "食材を指定する"},
                {"value": "proceed", "label": "指定せずに提案してもらう"}
            ]
        }
    )
    
    # ユーザー選択（食材を指定）
    user_response = "サバで"
    
    # 確認プロセス処理
    result = await response_parser.process_main_ingredient_confirmation(
        ambiguity_info, user_response, {"original_tasks": [task]}
    )
    
    # 検証
    assert result.is_confirmed == True
    assert result.updated_tasks[0].parameters["main_ingredient"] == "サバ"
    assert "主要食材を「サバ」に設定しました" in result.message
```

### 4. 統合テスト

#### 4.1 主要食材指定ケース
**テストケース**: 主要食材が指定された場合の一連の流れ

**テスト内容**:
```python
async def test_main_ingredient_specified_flow():
    """主要食材指定ケースの統合テスト"""
    
    # ユーザー要求
    user_request = "レンコンを使った主菜を5件提案して"
    user_id = "test_user"
    token = "test_token"
    sse_session_id = "test_session"
    
    # エージェントで処理
    response = await agent.process_request(user_request, user_id, token, sse_session_id)
    
    # 検証
    assert "主菜の提案（5件）" in response
    assert "レンコン使用" in response
    assert "斬新な提案（LLM推論）" in response
    assert "伝統的な提案（RAG検索）" in response
    assert "レンコン" in response  # 主要食材が表示されている
```

#### 4.2 主要食材未指定ケース
**テストケース**: 主要食材が未指定の場合の一連の流れ

**テスト内容**:
```python
async def test_main_ingredient_unspecified_flow():
    """主要食材未指定ケースの統合テスト"""
    
    # ユーザー要求
    user_request = "主菜を5件提案して"
    user_id = "test_user"
    token = "test_token"
    sse_session_id = "test_session"
    
    # エージェントで処理
    response = await agent.process_request(user_request, user_id, token, sse_session_id)
    
    # 検証（曖昧性検出が発動）
    assert "なにか主な食材を指定しますか？" in response
    assert "在庫から作れる主菜を提案しましょうか" in response
```

#### 4.3 エラーハンドリングテスト
**テストケース**: エラー時の動作確認

**テスト内容**:
```python
async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    # 無効な在庫データ
    user_request = "主菜を5件提案して"
    user_id = "test_user"
    token = "invalid_token"  # 無効なトークン
    sse_session_id = "test_session"
    
    # エージェントで処理
    response = await agent.process_request(user_request, user_id, token, sse_session_id)
    
    # 検証
    assert "エラー" in response or "失敗" in response
```

### 5. パフォーマンステスト

#### 5.1 レスポンス時間テスト
**テストケース**: レスポンス時間の確認

**テスト内容**:
```python
async def test_response_time():
    """レスポンス時間のテスト"""
    
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
    
    # 検証（5秒以内）
    assert execution_time < 5.0
    print(f"Execution time: {execution_time:.2f} seconds")
```

#### 5.2 並列処理テスト
**テストケース**: LLMとRAGの並列処理確認

**テスト内容**:
```python
async def test_parallel_processing():
    """並列処理のテスト"""
    
    import time
    
    # テストデータ
    inventory_items = ["レンコン", "キャベツ", "大根", "白菜", "ほうれん草"]
    menu_type = "和食"
    main_ingredient = "レンコン"
    
    # 並列実行
    start_time = time.time()
    
    llm_task = llm_client.generate_main_dish_candidates(
        inventory_items, menu_type, main_ingredient, count=2
    )
    rag_task = rag_client.search_main_dish_candidates(
        inventory_items, menu_type, main_ingredient, limit=3
    )
    
    llm_result, rag_result = await asyncio.gather(llm_task, rag_task)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 検証
    assert llm_result["success"] == True
    assert len(rag_result) == 3
    assert execution_time < 3.0  # 並列処理により高速化
```

## テスト実行計画

### 実行順序
1. **Phase 1Aの基本機能テスト** → 基本機能が動作することを確認
2. **Phase 1Bのプランナー・タスク設計テスト** → プランナー機能が動作することを確認
3. **統合テスト** → 全体の流れが動作することを確認
4. **パフォーマンステスト** → 性能要件を満たすことを確認

### テスト環境
- **開発環境**: ローカル開発環境
- **テストデータ**: サンプル在庫データ
- **認証**: テスト用トークン
- **データベース**: テスト用データベース

### 成功基準
- すべての単体テストが成功
- 統合テストが成功
- レスポンス時間が5秒以内
- エラーハンドリングが適切に動作
- ユーザー体験が向上

## 制約事項
- Phase 1AとPhase 1Bが完成している必要がある
- テスト用の在庫データが必要
- 認証トークンの設定が必要

## 期待される効果
- 主菜5件提案機能の品質保証
- ユーザー体験の向上確認
- システムの安定性確認
- Phase 2以降の基盤確立

### To-dos

- [ ] Phase 1Aの基本機能テストを実装・実行
- [ ] Phase 1Bのプランナー・タスク設計テストを実装・実行
- [ ] 主要食材指定ケースの統合テストを実装・実行
- [ ] 主要食材未指定ケースの統合テストを実装・実行
- [ ] エラーハンドリングテストを実装・実行
- [ ] パフォーマンステストを実装・実行
- [ ] テスト結果の分析とレポート作成
- [ ] Phase 1Cの完了確認
