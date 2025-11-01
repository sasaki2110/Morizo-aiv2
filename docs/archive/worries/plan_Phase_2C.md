# Phase 2C: 統合テストと品質保証

## 概要

Phase 2Cでは、Phase 2A（バックエンド基盤）とPhase 2B（フロントエンド連携）で実装した機能の統合テストと品質保証を実施します。エンドツーエンドテスト、パフォーマンステスト、ユーザー体験テストを実行し、Phase 2の完成度を確認します。

## 対象範囲

- エンドツーエンドテスト
- パフォーマンステスト
- ユーザー体験テスト
- エラーハンドリングテスト
- セキュリティテスト
- 品質保証レポート

## テスト計画

### 1. エンドツーエンドテスト

#### 1.1 基本フローテスト
**テストケース**: `test_basic_selection_flow()`

**テスト内容**:
```python
async def test_basic_selection_flow():
    """基本的な選択フローのテスト"""
    
    # 1. 主菜提案リクエスト
    user_request = "レンコンを使った主菜を5件提案して"
    user_id = "test_user"
    token = "test_token"
    sse_session_id = "test_session"
    
    # 2. エージェントで処理開始
    response = await agent.process_request(user_request, user_id, token, sse_session_id)
    
    # 3. 選択要求の確認
    assert response["requires_selection"] == True
    assert len(response["candidates"]) == 5
    assert response["task_id"] is not None
    
    # 4. ユーザー選択（3番を選択）
    selection_result = await agent.process_user_selection(
        response["task_id"], 3
    )
    
    # 5. 選択結果の確認
    assert selection_result["success"] == True
    assert "副菜の提案" in selection_result["response"]
    
    print("✅ 基本的な選択フローが正常に動作しました")
```

**修正する場所**: `tests/phase2c/test_basic_selection_flow.py`

**修正する内容**: 基本的な選択フローのテスト実装

**修正の理由**: エンドツーエンドでの動作確認のため

**修正の影響**: テストファイルの新規作成

#### 1.2 再提案フローテスト
**テストケース**: `test_reproposal_flow()`

**テスト内容**:
```python
async def test_reproposal_flow():
    """再提案フローのテスト"""
    
    # 1. 主菜提案
    user_request = "レンコンを使った主菜を5件提案して"
    response = await agent.process_request(user_request, "test_user", "test_token", "test_session")
    
    # 2. 再提案リクエスト
    reproposal_request = "他を提案して"
    reproposal_response = await agent.process_request(
        reproposal_request, "test_user", "test_token", "test_session"
    )
    
    # 3. 再提案の確認
    assert reproposal_response["requires_selection"] == True
    assert len(reproposal_response["candidates"]) == 5
    
    # 4. 既に提案したレシピが除外されていることを確認
    original_titles = [c["title"] for c in response["candidates"]]
    new_titles = [c["title"] for c in reproposal_response["candidates"]]
    
    # 重複がないことを確認（完全に重複しない場合もある）
    overlap = set(original_titles) & set(new_titles)
    assert len(overlap) < 3, f"Too many overlapping recipes: {overlap}"
    
    print("✅ 再提案フローが正常に動作しました")
```

**修正する場所**: `tests/phase2c/test_reproposal_flow.py`

**修正する内容**: 再提案フローのテスト実装

**修正の理由**: 再提案機能の動作確認のため

**修正の影響**: テストファイルの新規作成

#### 1.3 エラーハンドリングテスト
**テストケース**: `test_error_handling()`

**テスト内容**:
```python
async def test_error_handling():
    """エラーハンドリングのテスト"""
    
    # 1. 無効な選択（範囲外）
    invalid_selection_result = await agent.process_user_selection(
        "invalid_task_id", 6  # 無効な選択
    )
    
    assert invalid_selection_result["success"] == False
    assert "error" in invalid_selection_result
    
    # 2. 存在しないタスクID
    nonexistent_task_result = await agent.process_user_selection(
        "nonexistent_task_id", 1
    )
    
    assert nonexistent_task_result["success"] == False
    assert "error" in nonexistent_task_result
    
    # 3. タイムアウトしたコンテキスト
    # コンテキストを意図的に古くする
    old_context = {
        "paused_at": time.time() - 7200,  # 2時間前
        "candidates": [],
        "task_id": "old_task_id"
    }
    
    await context_manager.save_context_for_resume("old_task_id", old_context)
    
    timeout_result = await agent.process_user_selection(
        "old_task_id", 1
    )
    
    assert timeout_result["success"] == False
    assert "expired" in timeout_result["error"].lower()
    
    print("✅ エラーハンドリングが正常に動作しました")
```

**修正する場所**: `tests/phase2c/test_error_handling.py`

**修正する内容**: エラーハンドリングのテスト実装

**修正の理由**: エラー処理の動作確認のため

**修正の影響**: テストファイルの新規作成

### 2. パフォーマンステスト

#### 2.1 選択処理のパフォーマンステスト
**テストケース**: `test_selection_performance()`

**テスト内容**:
```python
async def test_selection_performance():
    """選択処理のパフォーマンステスト"""
    
    import time
    
    # 1. 主菜提案の時間測定
    start_time = time.time()
    
    response = await agent.process_request(
        "レンコンを使った主菜を5件提案して",
        "test_user", "test_token", "test_session"
    )
    
    proposal_time = time.time() - start_time
    
    # 2. 選択処理の時間測定
    start_time = time.time()
    
    selection_result = await agent.process_user_selection(
        response["task_id"], 3
    )
    
    selection_time = time.time() - start_time
    
    # 3. パフォーマンス検証
    assert proposal_time < 6.0, f"Proposal time too slow: {proposal_time:.2f}s"
    assert selection_time < 2.0, f"Selection time too slow: {selection_time:.2f}s"
    
    print(f"✅ パフォーマンステスト成功")
    print(f"   提案時間: {proposal_time:.2f}秒")
    print(f"   選択時間: {selection_time:.2f}秒")
```

**修正する場所**: `tests/phase2c/test_selection_performance.py`

**修正する内容**: パフォーマンステストの実装

**修正の理由**: 性能要件の確認のため

**修正の影響**: テストファイルの新規作成

#### 2.2 並行処理テスト
**テストケース**: `test_concurrent_selections()`

**テスト内容**:
```python
async def test_concurrent_selections():
    """並行選択処理のテスト"""
    
    import asyncio
    
    # 複数のユーザーが同時に選択を行う
    async def user_selection(user_id, selection):
        response = await agent.process_request(
            "レンコンを使った主菜を5件提案して",
            user_id, f"token_{user_id}", f"session_{user_id}"
        )
        
        result = await agent.process_user_selection(
            response["task_id"], selection
        )
        
        return result
    
    # 5人のユーザーが同時に選択
    tasks = [
        user_selection(f"user_{i}", i + 1) 
        for i in range(5)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # すべての結果が成功することを確認
    for i, result in enumerate(results):
        assert result["success"] == True, f"User {i} selection failed"
    
    print("✅ 並行選択処理が正常に動作しました")
```

**修正する場所**: `tests/phase2c/test_concurrent_selections.py`

**修正する内容**: 並行処理テストの実装

**修正の理由**: 並行処理の動作確認のため

**修正の影響**: テストファイルの新規作成

### 3. ユーザー体験テスト

#### 3.1 UI/UXテスト
**テストケース**: `test_ui_ux()`

**テスト内容**:
```python
async def test_ui_ux():
    """UI/UXのテスト"""
    
    # 1. 選択肢の表示品質
    response = await agent.process_request(
        "レンコンを使った主菜を5件提案して",
        "test_user", "test_token", "test_session"
    )
    
    candidates = response["candidates"]
    
    # 選択肢の品質確認
    for i, candidate in enumerate(candidates):
        assert candidate["title"], f"Candidate {i} has no title"
        assert candidate["ingredients"], f"Candidate {i} has no ingredients"
        assert len(candidate["ingredients"]) > 0, f"Candidate {i} has empty ingredients"
        
        # タイトルの長さチェック
        assert len(candidate["title"]) <= 50, f"Candidate {i} title too long: {candidate['title']}"
        
        # 食材の数チェック
        assert len(candidate["ingredients"]) <= 10, f"Candidate {i} has too many ingredients"
    
    # 2. 選択肢の多様性確認
    titles = [c["title"] for c in candidates]
    assert len(set(titles)) == len(titles), "Duplicate titles found"
    
    # 3. 食材の多様性確認
    all_ingredients = []
    for candidate in candidates:
        all_ingredients.extend(candidate["ingredients"])
    
    unique_ingredients = set(all_ingredients)
    assert len(unique_ingredients) >= 3, "Not enough ingredient variety"
    
    print("✅ UI/UXテストが成功しました")
```

**修正する場所**: `tests/phase2c/test_ui_ux.py`

**修正する内容**: UI/UXテストの実装

**修正の理由**: ユーザー体験の品質確認のため

**修正の影響**: テストファイルの新規作成

#### 3.2 アクセシビリティテスト
**テストケース**: `test_accessibility()`

**テスト内容**:
```python
async def test_accessibility():
    """アクセシビリティのテスト"""
    
    # 1. キーボードナビゲーションの確認
    response = await agent.process_request(
        "レンコンを使った主菜を5件提案して",
        "test_user", "test_token", "test_session"
    )
    
    candidates = response["candidates"]
    
    # 各選択肢に適切なラベルがあることを確認
    for i, candidate in enumerate(candidates):
        assert candidate["title"], f"Missing title for candidate {i}"
        
        # 食材情報が適切に表示されることを確認
        ingredients_text = ", ".join(candidate["ingredients"])
        assert len(ingredients_text) > 0, f"Empty ingredients for candidate {i}"
        
        # 調理時間が適切に表示されることを確認（オプション）
        if "cooking_time" in candidate:
            assert candidate["cooking_time"], f"Empty cooking time for candidate {i}"
    
    # 2. エラーメッセージの確認
    error_response = await agent.process_user_selection(
        "invalid_task_id", 6
    )
    
    assert error_response["success"] == False
    assert error_response["error"], "Missing error message"
    assert len(error_response["error"]) > 0, "Empty error message"
    
    print("✅ アクセシビリティテストが成功しました")
```

**修正する場所**: `tests/phase2c/test_accessibility.py`

**修正する内容**: アクセシビリティテストの実装

**修正の理由**: アクセシビリティ要件の確認のため

**修正の影響**: テストファイルの新規作成

### 4. セキュリティテスト

#### 4.1 認証・認可テスト
**テストケース**: `test_security()`

**テスト内容**:
```python
async def test_security():
    """セキュリティのテスト"""
    
    # 1. 無効なトークンでのアクセス
    invalid_token_response = await agent.process_request(
        "レンコンを使った主菜を5件提案して",
        "test_user", "invalid_token", "test_session"
    )
    
    assert invalid_token_response["success"] == False
    assert "unauthorized" in invalid_token_response["error"].lower()
    
    # 2. 他のユーザーのタスクへのアクセス
    # ユーザーAがタスクを作成
    user_a_response = await agent.process_request(
        "レンコンを使った主菜を5件提案して",
        "user_a", "token_a", "session_a"
    )
    
    # ユーザーBがユーザーAのタスクにアクセス
    user_b_response = await agent.process_user_selection(
        user_a_response["task_id"], 1
    )
    
    assert user_b_response["success"] == False
    assert "unauthorized" in user_b_response["error"].lower()
    
    # 3. SQLインジェクション対策の確認
    malicious_request = "'; DROP TABLE users; --"
    malicious_response = await agent.process_request(
        malicious_request,
        "test_user", "test_token", "test_session"
    )
    
    # エラーが適切に処理されることを確認
    assert malicious_response["success"] == False
    assert "error" in malicious_response
    
    print("✅ セキュリティテストが成功しました")
```

**修正する場所**: `tests/phase2c/test_security.py`

**修正する内容**: セキュリティテストの実装

**修正の理由**: セキュリティ要件の確認のため

**修正の影響**: テストファイルの新規作成

### 5. 品質保証レポート

#### 5.1 テスト結果の集計
**修正する場所**: `tests/phase2c/test_report.py`

**修正する内容**:
```python
class TestReportGenerator:
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.error_logs = []
    
    def generate_report(self):
        """品質保証レポートの生成"""
        report = {
            "test_summary": self.test_results,
            "performance_metrics": self.performance_metrics,
            "error_logs": self.error_logs,
            "recommendations": self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self):
        """改善提案の生成"""
        recommendations = []
        
        # パフォーマンス改善提案
        if self.performance_metrics.get("proposal_time", 0) > 5.0:
            recommendations.append("主菜提案の処理時間を改善する必要があります")
        
        if self.performance_metrics.get("selection_time", 0) > 1.5:
            recommendations.append("選択処理の処理時間を改善する必要があります")
        
        # エラーハンドリング改善提案
        if len(self.error_logs) > 10:
            recommendations.append("エラーハンドリングの改善が必要です")
        
        return recommendations
```

**修正の理由**: 品質保証レポートの生成のため

**修正の影響**: テストファイルの新規作成

## 実装順序

1. **エンドツーエンドテスト** → 基本機能の確認
2. **パフォーマンステスト** → 性能要件の確認
3. **ユーザー体験テスト** → UX品質の確認
4. **エラーハンドリングテスト** → エラー処理の確認
5. **セキュリティテスト** → セキュリティ要件の確認
6. **品質保証レポート** → 総合評価

## 期待される効果

- Phase 2の完成度が確認できる
- 品質問題の早期発見
- パフォーマンス要件の確認
- Phase 3以降の実装指針の確立

## 制約事項

- 既存のテスト環境を利用
- テストデータの準備が必要
- 本番環境でのテストは実施しない

## 成功基準

- すべてのエンドツーエンドテストが成功
- パフォーマンス要件を満たす
- ユーザー体験テストが成功
- セキュリティテストが成功
- 品質保証レポートが完成

## 次のステップ

Phase 2C完了後、Phase 3（副菜・汁物の段階的選択）の実装に進みます。
