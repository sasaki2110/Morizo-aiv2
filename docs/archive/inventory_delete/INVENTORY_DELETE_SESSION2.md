# セッション2: Phase 1B + Phase 1C（献立提案と提案レスポンス）

## 概要

献立提案でも食材情報を保存し、提案レスポンスに食材情報を含める機能を実装します。

## 目的

- 献立提案で採用したレシピの`ingredients`を履歴保存時にDBへ保存
- 提案レスポンスに`ingredients`を含める
- セッション保存時に`ingredients`を含める

## 実装範囲

**Phase 1B**: 献立提案での食材保持と保存  
**Phase 1C**: 提案レスポンスに食材情報を含める

## 修正ファイル

### Phase 1B
- `api/routes/recipe.py`
- `api/models/requests.py` (RecipeItemモデル)

### Phase 1C
- `services/llm/service_handlers.py` (RecipeServiceHandler)
- `mcp_servers/recipe_mcp.py` (generate_proposals)
- `mcp_servers/recipe_llm.py`
- `mcp_servers/recipe_rag/client.py`

## 実装内容

### Phase 1B: 献立提案での食材保持と保存

#### 1. RecipeItemモデルの拡張

**ファイル**: `api/models/requests.py`

**変更内容**:
- `ingredients`フィールドを追加（Optional[List[str]]）
- 既存のリクエストは影響なし（Optionalのため）

**修正箇所**:
```python
class RecipeItem(BaseModel):
    """個別レシピアイテム"""
    title: str = Field(
        ..., 
        description="レシピのタイトル", 
        min_length=1, 
        max_length=255
    )
    category: str = Field(
        ..., 
        description="レシピのカテゴリ",
        pattern="^(main_dish|side_dish|soup)$"
    )
    menu_source: str = Field(
        ..., 
        description="メニューの出典",
        pattern="^(llm_menu|rag_menu|manual)$"
    )
    url: Optional[str] = Field(
        None, 
        description="レシピのURL（Web検索から採用した場合）"
    )
    ingredients: Optional[List[str]] = Field(None, description="利用食材リスト")  # 新規追加
```

#### 2. api/routes/recipe.py の adopt_recipe() の修正

**ファイル**: `api/routes/recipe.py`

**変更内容**:
- リクエストから`ingredients`を取得
- `crud.add_history()`に`ingredients`を渡す

**修正箇所**:
```python
for i, recipe in enumerate(request.recipes):
    try:
        logger.info(f"🔍 [API] Processing recipe {i+1}/{len(request.recipes)}: {recipe.title}")
        
        # menu_source → source のマッピング
        db_source = db_source_mapping.get(recipe.menu_source)
        if not db_source:
            logger.error(f"❌ [API] Invalid menu_source for recipe {i+1}: {recipe.menu_source}")
            failed_recipes.append(f"Recipe {i+1}: Invalid menu_source '{recipe.menu_source}'")
            continue
        
        logger.info(f"🔍 [API] Mapped source for recipe {i+1}: {recipe.menu_source} → {db_source}")
        
        # 新規追加: ingredientsを取得
        ingredients = recipe.ingredients if recipe.ingredients else None
        
        # RecipeHistoryCRUD.add_history()を呼び出し
        result = await crud.add_history(
            client=client,
            user_id=user_id,
            title=recipe.title,
            source=db_source,
            url=recipe.url,
            ingredients=ingredients  # 新規追加
        )
        
        # ... 既存の処理
```

### Phase 1C: 提案レスポンスに食材情報を含める

#### 1. レシピ候補にingredientsを含める

**確認事項**:
- 既存の候補情報に`ingredients`が含まれているか確認
- 含まれていない場合は追加実装

**確認対象ファイル**:
- `mcp_servers/recipe_llm.py`: `_parse_candidate_response()`で`ingredients`を抽出
- `mcp_servers/recipe_rag/client.py`: 検索結果に`ingredients`を含める（既に実装済みの可能性あり）

**実装内容**（必要に応じて）:

**mcp_servers/recipe_llm.py**:
```python
def _parse_candidate_response(self, response_content: str) -> List[Dict[str, Any]]:
    """LLMレスポンスを解析して候補を抽出（汎用版）"""
    try:
        import json
        import re
        
        # JSON部分を抽出
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            candidates = data.get("candidates", [])
            
            # ingredientsが含まれていることを確認
            for candidate in candidates:
                if "ingredients" not in candidate:
                    candidate["ingredients"] = []  # デフォルト値
            
            return candidates
        
        return []
    except Exception as e:
        self.logger.error(f"❌ [LLM] Failed to parse candidate response: {e}")
        return []
```

**mcp_servers/recipe_rag/client.py**:
- 既に`ingredients`を含めているか確認
- 含まれていない場合は追加実装

#### 2. セッション保存時にingredientsを含める

**ファイル**: `services/llm/service_handlers.py`

**変更内容**:
- `set_candidates()`で`ingredients`も保存

**修正箇所**:
```python
# Phase 3C-3: 候補情報をセッションに保存（詳細情報）
if sse_session_id and session_service:
    session = await session_service.get_session(sse_session_id, user_id=None)
    if session:
        current_stage = session.get_current_stage()
        category = current_stage  # "main", "sub", "soup"
        await session_service.set_candidates(sse_session_id, category, candidates_with_urls)
        # デバッグログ: 保存する候補のsourceとingredientsを確認
        for i, candidate in enumerate(candidates_with_urls):
            self.logger.debug(f"🔍 [RecipeServiceHandler] Saving candidate {i+1}: title='{candidate.get('title', 'N/A')}', source='{candidate.get('source', 'N/A')}', ingredients={candidate.get('ingredients', [])}")
        self.logger.info(f"💾 [RecipeServiceHandler] Saved {len(candidates_with_urls)} {category} candidates to session")
```

## テスト項目

### Phase 1B テスト

1. **RecipeItemモデルのテスト**
   - `ingredients`がある場合のリクエスト
   - `ingredients`がない場合のリクエスト（既存動作確認）

2. **api/routes/recipe.py の adopt_recipe() のテスト**
   - `ingredients`がある場合の保存
   - `ingredients`がない場合の既存動作確認

### Phase 1C テスト

1. **レシピ候補にingredientsが含まれること**
   - LLM提案の候補に`ingredients`が含まれること
   - RAG提案の候補に`ingredients`が含まれること

2. **セッション保存時にingredientsが保存されること**
   - セッションから候補情報を取得した際に`ingredients`が含まれること

### 統合テスト

1. **献立提案→履歴保存のフロー**
   - 献立提案→採用→履歴保存
   - DBに`ingredients`が保存されていることを確認

2. **提案レスポンスにingredientsが含まれること**
   - 提案レスポンスに`ingredients`が含まれることを確認

## デグレード防止チェックリスト

- [ ] 既存の`adopt_recipe()`呼び出しが動作することを確認
- [ ] `ingredients`がnullの場合でも既存動作を維持
- [ ] 既存の提案レスポンスが正常に動作することを確認
- [ ] 既存のセッション保存機能が正常に動作することを確認

## 完了条件

- 献立提案→履歴保存→DB確認が成功
- 提案レスポンスに食材情報が含まれること
- セッション保存時に食材情報が保存されること
- 既存機能に影響がないことを確認
- テストが成功すること

## 所要時間

中規模（2-3時間想定）

## 実装後の確認事項

1. **DB確認**
   - 献立提案で保存したレシピ履歴に`ingredients`が保存されていること

2. **既存機能の動作確認**
   - 献立提案が正常に動作すること
   - 提案レスポンスが正常に動作すること
   - セッション保存が正常に動作すること

3. **新機能の動作確認**
   - 提案レスポンスに`ingredients`が含まれること
   - セッション保存時に`ingredients`が保存されること

