# Phase 3C-2: 段階判定機能

## 概要

現在の段階（main/sub/soup）を判定し、次の段階を決定する機能を実装します。

## 対象範囲

- `core/agent.py`

## 実装計画

**修正する場所**: `core/agent.py`

**修正する内容**:

```python
async def _get_current_stage(self, task_id: str, sse_session_id: str, user_id: str) -> str:
    """現在の段階を取得"""
    try:
        session = await self.session_service.get_session(sse_session_id, user_id)
        if not session:
            return "main"
        
        return session.current_stage
    except Exception as e:
        self.logger.error(f"❌ [AGENT] Failed to get current stage: {e}")
        return "main"

async def _advance_stage(self, sse_session_id: str, user_id: str, selected_recipe: Dict) -> str:
    """
    段階を進める
    
    Returns:
        次の段階の名前
    """
    try:
        session = await self.session_service.get_session(sse_session_id, user_id)
        if not session:
            return "main"
        
        # 選択したレシピを保存
        if session.current_stage == "main":
            session.selected_main_dish = selected_recipe
            session.current_stage = "sub"
            # 使用済み食材を記録
            session.used_ingredients.extend(selected_recipe.get("ingredients", []))
            # カテゴリ判定
            menu_type = selected_recipe.get("menu_type", "")
            if any(x in menu_type for x in ["洋食", "western", "西洋"]):
                session.menu_category = "western"
            elif any(x in menu_type for x in ["中華", "chinese"]):
                session.menu_category = "chinese"
            else:
                session.menu_category = "japanese"
        
        elif session.current_stage == "sub":
            session.selected_sub_dish = selected_recipe
            session.current_stage = "soup"
            # 使用済み食材を記録
            session.used_ingredients.extend(selected_recipe.get("ingredients", []))
        
        elif session.current_stage == "soup":
            session.selected_soup = selected_recipe
            session.current_stage = "completed"
        
        return session.current_stage
        
    except Exception as e:
        self.logger.error(f"❌ [AGENT] Failed to advance stage: {e}")
        return "main"
```

**修正の理由**: 段階判定が必要

**修正の影響**: 既存のエージェント処理に新規メソッドを追加

---

## テスト

### 単体試験

#### 段階判定機能のテスト
**テストファイル**: `tests/phase3c2/test_01_stage_management.py`

**テスト項目**:
- `_get_current_stage()`が正しい段階を返すこと
- `_advance_stage()`が次の段階に進めること
- 主菜選択後、段階が"sub"に進むこと
- 副菜選択後、段階が"soup"に進むこと
- 汁物選択後、段階が"completed"に進むこと
- 使用済み食材が正しく記録されること
- カテゴリ判定が正しく動作すること

**テスト例**:
```python
async def test_advance_stage_main_to_sub():
    """主菜選択後、段階がsubに進むテスト"""
    selected_recipe = {
        "title": "レンコンのきんぴら",
        "ingredients": ["レンコン", "ニンジン"]
    }
    
    next_stage = await agent._advance_stage(sse_session_id, user_id, selected_recipe)
    
    assert next_stage == "sub"
    
    # セッションを確認
    session = await session_service.get_session(sse_session_id, user_id)
    assert session.current_stage == "sub"
    assert session.selected_main_dish == selected_recipe
    assert session.used_ingredients == ["レンコン", "ニンジン"]

async def test_advance_stage_sub_to_soup():
    """副菜選択後、段階がsoupに進むテスト"""
    selected_recipe = {
        "title": "ほうれん草の胡麻和え",
        "ingredients": ["ほうれん草", "ごま"]
    }
    
    next_stage = await agent._advance_stage(sse_session_id, user_id, selected_recipe)
    
    assert next_stage == "soup"
    
    session = await session_service.get_session(sse_session_id, user_id)
    assert session.current_stage == "soup"
    assert session.used_ingredients == ["レンコン", "ニンジン", "ほうれん草", "ごま"]

async def test_category_detection():
    """カテゴリ判定テスト"""
    western_recipe = {"title": "スパゲッティ", "menu_type": "洋食"}
    next_stage = await agent._advance_stage(sse_session_id, user_id, western_recipe)
    
    session = await session_service.get_session(sse_session_id, user_id)
    assert session.menu_category == "western"
```

---

## 期待される効果

- 現在の段階を判定できる
- 次の段階に自動的に進める
- 選択したレシピをセッションに保存

