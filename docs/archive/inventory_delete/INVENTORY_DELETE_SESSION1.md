# セッション1: Phase 1A（段階提案での食材保持と保存）

## 概要

段階提案で選択したレシピの食材情報をDBに保存する機能を実装します。

## 目的

- 段階提案（主菜→副菜→汁物）で選択したレシピの`ingredients`を履歴保存時にDBへ保存
- 既存機能への影響を最小限に抑える

## 実装範囲

**Phase 1A**: 段階提案での食材保持と保存

## 修正ファイル

- `mcp_servers/recipe_history_crud.py`
- `api/routes/menu.py`

## 実装内容

### 1. RecipeHistoryCRUD.add_history()の拡張

**ファイル**: `mcp_servers/recipe_history_crud.py`

**変更内容**:
- `ingredients`パラメータを追加（Optional[List[str]]）
- DB保存時に`ingredients`をJSONB形式で保存
- 既存の呼び出し元は影響なし（Optionalのため）

**修正箇所**:
```python
async def add_history(
    self, 
    client: Client, 
    user_id: str, 
    title: str, 
    source: str,
    url: Optional[str] = None,
    ingredients: Optional[List[str]] = None  # 新規追加
) -> Dict[str, Any]:
    """レシピ履歴を1件追加"""
    try:
        self.logger.info(f"📝 [CRUD] Adding recipe history: {title}")
        
        # データ準備
        data = {
            "user_id": user_id,
            "title": title,
            "source": source
        }
        
        if url:
            data["url"] = url
        
        # 新規追加: ingredientsをJSONB形式で保存
        if ingredients:
            data["ingredients"] = ingredients
        
        # データベースに挿入
        result = client.table("recipe_historys").insert(data).execute()
        
        if result.data:
            self.logger.info(f"✅ [CRUD] Recipe history added successfully: {result.data[0]['id']}")
            return {"success": True, "data": result.data[0]}
        else:
            raise Exception("No data returned from insert")
            
    except Exception as e:
        self.logger.error(f"❌ [CRUD] Failed to add recipe history: {e}")
        return {"success": False, "error": str(e)}
```

### 2. api/routes/menu.py の save_menu() の修正

**ファイル**: `api/routes/menu.py`

**変更内容**:
- 選択済みレシピから`ingredients`を取得
- `crud.add_history()`に`ingredients`を渡す
- `ingredients`がない場合でも既存動作を維持

**修正箇所**:
```python
for category in ["main", "sub", "soup"]:
    recipe = selected_recipes.get(category)
    if not recipe:
        continue  # 未選択のレシピはスキップ
    
    try:
        # タイトルにプレフィックスを追加
        original_title = recipe.get("title", "")
        prefixed_title = f"{category_prefix_map[category]}{original_title}"
        
        # source のマッピング
        recipe_source = recipe.get("source", "web")
        db_source = source_mapping.get(recipe_source, "web")
        
        # URLの取得
        url = recipe.get("url")
        
        # 新規追加: ingredientsを取得
        ingredients = recipe.get("ingredients", [])
        if not ingredients:
            ingredients = None  # 空リストの場合はNoneに
        
        logger.info(f"🔍 [API] Saving {category}: title='{prefixed_title}', source={recipe_source}→{db_source}, ingredients={ingredients}")
        
        # DBに保存
        result = await crud.add_history(
            client=client,
            user_id=user_id,
            title=prefixed_title,
            source=db_source,
            url=url,
            ingredients=ingredients  # 新規追加
        )
        
        # ... 既存の処理
```

## テスト項目

### 単体テスト

1. **RecipeHistoryCRUD.add_history()のテスト**
   - `ingredients`がある場合の保存
   - `ingredients`がない場合の既存動作確認
   - `ingredients`が空リストの場合の処理

2. **api/routes/menu.py の save_menu() のテスト**
   - 選択済みレシピに`ingredients`がある場合
   - 選択済みレシピに`ingredients`がない場合
   - 選択済みレシピに`ingredients`が空リストの場合

### 統合テスト

1. **段階提案→履歴保存のフロー**
   - 主菜選択→副菜選択→汁物選択→履歴保存
   - DBに`ingredients`が保存されていることを確認

2. **既存機能への影響確認**
   - `ingredients`がない場合でも既存動作を維持
   - 既存のレシピ履歴取得APIが動作することを確認

## デグレード防止チェックリスト

- [ ] 既存の`add_history()`呼び出しが動作することを確認
- [ ] `ingredients`がnullの場合でも既存動作を維持
- [ ] 既存のレシピ履歴取得APIが動作することを確認
- [ ] 既存のフロントエンドが動作することを確認

## 完了条件

- 段階提案→履歴保存→DB確認が成功
- 既存機能に影響がないことを確認
- テストが成功すること

## 所要時間

中規模（2-3時間想定）

## 実装後の確認事項

1. **DB確認**
   - `recipe_historys`テーブルに`ingredients`カラムが追加されていること
   - 履歴保存時に`ingredients`がJSONB形式で保存されていること

2. **既存機能の動作確認**
   - 段階提案が正常に動作すること
   - 履歴保存が正常に動作すること
   - レシピ履歴取得が正常に動作すること

3. **新機能の動作確認**
   - 選択済みレシピに`ingredients`がある場合、DBに保存されること
   - 選択済みレシピに`ingredients`がない場合、既存動作が維持されること

