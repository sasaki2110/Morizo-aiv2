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

## 期待される効果

- 主菜選択後、自動的に副菜提案に遷移
- 副菜選択後、自動的に汁物提案に遷移
- ユーザー体験が向上

