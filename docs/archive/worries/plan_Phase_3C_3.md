# Phase 3C-3: 自動遷移機能

## 概要

次の段階のリクエストを生成し、自動的にタスクチェーンを実行します。

## 対象範囲

- `core/agent.py`

## 実装計画

**修正する場所**: `core/agent.py` - `process_user_selection()`メソッド

**修正する内容**:

```python
async def process_user_selection(
    self, task_id: str, selection: int, sse_session_id: str, user_id: str, token: str
) -> dict:
    """ユーザー選択結果の処理（自動遷移機能付き）"""
    
    try:
        # 選択されたレシピの情報を取得
        selected_recipe = await self._get_selected_recipe_from_task(task_id, selection)
        
        # 段階を進める
        next_stage = await self._advance_stage(sse_session_id, user_id, selected_recipe)
        
        # 次の段階に応じた処理
        if next_stage == "sub":
            # 副菜提案に自動遷移
            next_request = await self._generate_sub_dish_request(
                selected_recipe, sse_session_id, user_id
            )
            result = await self.process_request(next_request, user_id, token, sse_session_id, False)
            return result
        
        elif next_stage == "soup":
            # 汁物提案に自動遷移
            next_request = await self._generate_soup_request(
                selected_recipe, sse_session_id, user_id
            )
            result = await self.process_request(next_request, user_id, token, sse_session_id, False)
            return result
        
        elif next_stage == "completed":
            # 完了
            return {
                "success": True,
                "message": "献立が完成しました。",
                "menu": {
                    "main": selected_recipe,
                    "sub": await self._get_selected_sub_dish(sse_session_id, user_id),
                    "soup": await self._get_selected_soup(sse_session_id, user_id)
                }
            }
        
    except Exception as e:
        self.logger.error(f"❌ [AGENT] Failed to process user selection: {e}")
        return {"success": False, "error": str(e)}

async def _generate_sub_dish_request(
    self, main_dish: Dict, sse_session_id: str, user_id: str
) -> str:
    """
    副菜提案用のリクエストを生成
    
    例: "副菜を5件提案して"（主菜で使った食材を除外）
    """
    session = await self.session_service.get_session(sse_session_id, user_id)
    if not session:
        return "副菜を5件提案して"
    
    used_ingredients = session.used_ingredients
    main_ingredient_text = f"（主菜で使った食材: {', '.join(used_ingredients)} は除外して）"
    
    return f"主菜で使っていない食材で副菜を5件提案して。{main_ingredient_text}"

async def _generate_soup_request(
    self, sub_dish: Dict, sse_session_id: str, user_id: str
) -> str:
    """
    汁物提案用のリクエストを生成
    
    例: "汁物を5件提案して"（和食なら味噌汁、洋食ならスープ）
    """
    session = await self.session_service.get_session(sse_session_id, user_id)
    if not session:
        return "汁物を5件提案して"
    
    used_ingredients = session.used_ingredients
    menu_category = session.menu_category
    
    soup_type = "味噌汁" if menu_category == "japanese" else "スープ"
    used_ingredients_text = f"（主菜・副菜で使った食材: {', '.join(used_ingredients)} は除外して）"
    
    return f"{soup_type}を5件提案して。{used_ingredients_text}"
```

**修正の理由**: 段階的選択の自動遷移が必要

**修正の影響**: 既存の`process_user_selection()`を拡張

---

## テスト

### 結合試験

#### 自動遷移機能のテスト
**テストファイル**: `tests/phase3c3/test_01_auto_transition.py`

**テストシナリオ**:

**シナリオ1: 主菜選択後の副菜遷移**
1. サーバーを起動
2. 主菜提案リクエストを送信 → 5件の主菜が返される
3. ユーザーが主菜を選択
4. 自動的に副菜提案リクエストが生成される
5. 副菜5件が返される

**シナリオ2: 副菜選択後の汁物遷移**
1. 副菜を選択
2. 自動的に汁物提案リクエストが生成される
3. 汁物5件が返される（カテゴリに応じて味噌汁orスープ）

**シナリオ3: 汁物選択後の完了**
1. 汁物を選択
2. 献立完成のメッセージが返される
3. 選択した主菜・副菜・汁物の履歴が確認できる

**テスト例**:
```python
async def test_auto_transition_main_to_sub():
    """主菜選択後の副菜自動遷移テスト"""
    # 1. 主菜提案を送信
    response1 = await agent.process_request(
        "レンコンの主菜を5件提案して",
        user_id, token, sse_session_id, False
    )
    assert "candidates" in response1
    
    # 2. ユーザーが主菜を選択
    task_id = response1["task_id"]
    selection_response = await agent.process_user_selection(
        task_id, 1, sse_session_id, user_id, token
    )
    
    # 3. 自動的に副菜提案が開始される
    assert "candidates" in selection_response
    assert "副菜" in selection_response.get("response", "")
```

### エンドツーエンドテスト

**テストシナリオ**: 完全な段階的選択フロー
1. 在庫確認
2. 主菜提案 → 選択
3. 副菜提案 → 選択（主菜で使った食材を除外）
4. 汁物提案 → 選択（主菜・副菜で使った食材を除外）
5. 献立完成

**期待される動作**:
- 各段階で5件の候補が提案される
- 使い残し食材を最大化して活用
- カテゴリ連動（和食→和食→味噌汁、洋食→洋食→スープ）

---

## 期待される効果

- 主菜選択後、自動的に副菜提案に遷移
- 副菜選択後、自動的に汁物提案に遷移
- ユーザー体験が向上

