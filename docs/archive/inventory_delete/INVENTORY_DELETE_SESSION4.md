# セッション4: Phase 2B + Phase 3（在庫更新とフラグ更新）

## 概要

在庫更新APIとレシピ履歴の`ingredients_deleted`フラグ更新を実装します。

## 目的

- 複数の食材を一括で削除（数量を0に設定）するAPIを実装
- 食材削除時にレシピ履歴の`ingredients_deleted`フラグを更新

## 実装範囲

**Phase 2B**: 在庫更新API（食材削除用）  
**Phase 3**: レシピ履歴のingredients_deletedフラグ更新

## 修正ファイル

### Phase 2B
- `api/routes/recipe.py` (新規エンドポイント)
- `api/models/requests.py` (新規リクエストモデル)
- `api/models/responses.py` (新規レスポンスモデル)

### Phase 3
- `mcp_servers/recipe_history_crud.py`
- `api/routes/recipe.py`

## 実装内容

### Phase 2B: 在庫更新API（食材削除用）

#### 1. リクエスト/レスポンスモデルの追加

**ファイル**: `api/models/requests.py`

**追加内容**:
```python
class IngredientDeleteItem(BaseModel):
    """削除対象食材アイテム"""
    item_name: str = Field(..., description="食材名")
    quantity: float = Field(0, description="更新後の数量（0で削除）")
    inventory_id: Optional[str] = Field(None, description="在庫ID（指定がある場合）")

class IngredientDeleteRequest(BaseModel):
    """食材削除リクエスト"""
    date: str = Field(..., description="日付（YYYY-MM-DD形式）")
    ingredients: List[IngredientDeleteItem] = Field(..., description="削除対象食材リスト")
```

**ファイル**: `api/models/responses.py`

**追加内容**:
```python
class IngredientDeleteResponse(BaseModel):
    """食材削除レスポンス"""
    success: bool
    deleted_count: int
    updated_count: int
    failed_items: List[str]
```

#### 2. エンドポイントの実装

**ファイル**: `api/routes/recipe.py`

**エンドポイント**: `POST /api/recipe/ingredients/delete`

**実装詳細**:
```python
@router.post("/recipe/ingredients/delete", response_model=IngredientDeleteResponse)
async def delete_ingredients(
    request: IngredientDeleteRequest,
    http_request: Request
):
    """指定された食材を在庫から削除（数量を0に設定）"""
    try:
        logger.info(f"🔍 [API] Ingredient delete request received: date={request.date}, ingredients={len(request.ingredients)}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 2. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 3. 在庫一覧を取得
        from mcp_servers.inventory_crud import InventoryCRUD
        inventory_crud = InventoryCRUD()
        inventory_result = await inventory_crud.get_all_items(client, user_id)
        
        if not inventory_result.get("success"):
            logger.error(f"❌ [API] Failed to get inventory list: {inventory_result.get('error')}")
            raise HTTPException(status_code=500, detail="在庫情報の取得に失敗しました")
        
        inventory_items = inventory_result.get("data", [])
        logger.info(f"🔍 [API] Retrieved {len(inventory_items)} inventory items")
        
        # 4. 食材名の正規化用
        from services.session.models.components.ingredient_mapper import IngredientMapperComponent
        from config.loggers import GenericLogger
        ingredient_mapper = IngredientMapperComponent(GenericLogger("api", "ingredient_mapper"))
        
        # 5. リクエストの食材名で在庫を検索して更新
        deleted_count = 0
        updated_count = 0
        failed_items = []
        
        for ingredient_item in request.ingredients:
            try:
                item_name = ingredient_item.item_name
                target_quantity = ingredient_item.quantity
                inventory_id = ingredient_item.inventory_id
                
                # 在庫IDが指定されている場合は直接更新
                if inventory_id:
                    result = await inventory_crud.update_item_by_id(
                        client=client,
                        user_id=user_id,
                        item_id=inventory_id,
                        quantity=target_quantity
                    )
                    
                    if result.get("success"):
                        if target_quantity == 0:
                            deleted_count += 1
                        else:
                            updated_count += 1
                        logger.info(f"✅ [API] Updated inventory item: {inventory_id}, quantity={target_quantity}")
                    else:
                        failed_items.append(f"{item_name} (ID: {inventory_id})")
                        logger.error(f"❌ [API] Failed to update inventory item: {inventory_id}")
                else:
                    # 食材名で検索（複数在庫がある場合はすべて更新）
                    matched_items = []
                    normalized_item_name = ingredient_mapper.normalize_ingredient_name(item_name)
                    
                    for inv_item in inventory_items:
                        normalized_inv = ingredient_mapper.normalize_ingredient_name(inv_item.get("item_name", ""))
                        if normalized_item_name == normalized_inv or \
                           normalized_item_name in normalized_inv or \
                           normalized_inv in normalized_item_name:
                            matched_items.append(inv_item)
                    
                    if not matched_items:
                        failed_items.append(f"{item_name} (在庫に存在しません)")
                        logger.warning(f"⚠️ [API] Inventory item not found: {item_name}")
                        continue
                    
                    # すべてのマッチした在庫を更新
                    for inv_item in matched_items:
                        inv_id = inv_item.get("id")
                        result = await inventory_crud.update_item_by_id(
                            client=client,
                            user_id=user_id,
                            item_id=inv_id,
                            quantity=target_quantity
                        )
                        
                        if result.get("success"):
                            if target_quantity == 0:
                                deleted_count += 1
                            else:
                                updated_count += 1
                            logger.info(f"✅ [API] Updated inventory item: {inv_id}, quantity={target_quantity}")
                        else:
                            failed_items.append(f"{item_name} (ID: {inv_id})")
                            logger.error(f"❌ [API] Failed to update inventory item: {inv_id}")
                            
            except Exception as e:
                failed_items.append(f"{ingredient_item.item_name} (エラー: {str(e)})")
                logger.error(f"❌ [API] Error processing ingredient: {ingredient_item.item_name}, error: {e}")
        
        # 6. レシピ履歴のingredients_deletedフラグを更新
        crud = RecipeHistoryCRUD()
        update_result = await crud.update_ingredients_deleted(
            client=client,
            user_id=user_id,
            date=request.date,
            deleted=True
        )
        
        if not update_result.get("success"):
            logger.warning(f"⚠️ [API] Failed to update ingredients_deleted flag: {update_result.get('error')}")
        
        logger.info(f"✅ [API] Ingredient delete completed: deleted={deleted_count}, updated={updated_count}, failed={len(failed_items)}")
        
        return IngredientDeleteResponse(
            success=True,
            deleted_count=deleted_count,
            updated_count=updated_count,
            failed_items=failed_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in delete_ingredients: {e}")
        raise HTTPException(status_code=500, detail="食材削除処理でエラーが発生しました")
```

### Phase 3: レシピ履歴のingredients_deletedフラグ更新

#### 1. RecipeHistoryCRUD.update_ingredients_deleted()の追加

**ファイル**: `mcp_servers/recipe_history_crud.py`

**追加内容**:
```python
async def update_ingredients_deleted(
    self,
    client: Client,
    user_id: str,
    date: str,  # YYYY-MM-DD形式
    deleted: bool = True
) -> Dict[str, Any]:
    """指定日付のレシピ履歴のingredients_deletedフラグを更新"""
    try:
        self.logger.info(f"✏️ [CRUD] Updating ingredients_deleted flag for date: {date}")
        
        from datetime import datetime
        # 日付の検証と変換
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = datetime.combine(date_obj, datetime.max.time())
        except ValueError:
            return {"success": False, "error": "Invalid date format (YYYY-MM-DD required)"}
        
        # 指定日付のレシピ履歴を取得
        result = client.table("recipe_historys")\
            .select("id")\
            .eq("user_id", user_id)\
            .gte("cooked_at", start_datetime.isoformat())\
            .lte("cooked_at", end_datetime.isoformat())\
            .execute()
        
        if not result.data:
            self.logger.warning(f"⚠️ [CRUD] No recipe histories found for date: {date}")
            return {"success": True, "data": [], "updated_count": 0}
        
        # ingredients_deletedフラグを更新
        update_result = client.table("recipe_historys")\
            .update({"ingredients_deleted": deleted})\
            .eq("user_id", user_id)\
            .gte("cooked_at", start_datetime.isoformat())\
            .lte("cooked_at", end_datetime.isoformat())\
            .execute()
        
        updated_count = len(update_result.data) if update_result.data else 0
        self.logger.info(f"✅ [CRUD] Updated {updated_count} recipe histories")
        
        return {"success": True, "data": update_result.data, "updated_count": updated_count}
        
    except Exception as e:
        self.logger.error(f"❌ [CRUD] Failed to update ingredients_deleted flag: {e}")
        return {"success": False, "error": str(e)}
```

## テスト項目

### Phase 2B テスト

1. **単一食材の削除**
   - 在庫ID指定での削除
   - 食材名指定での削除（複数在庫がある場合）

2. **複数食材の一括削除**
   - 複数の食材を一度に削除
   - 一部の食材削除に失敗した場合の処理

3. **数量更新**
   - 数量を0以外に更新する場合

4. **エラーハンドリング**
   - 在庫に存在しない食材の処理
   - 無効な在庫IDの処理

### Phase 3 テスト

1. **フラグ更新**
   - 指定日付のレシピ履歴が存在する場合
   - 指定日付のレシピ履歴が存在しない場合
   - 複数のレシピ履歴がある場合

2. **エラーハンドリング**
   - 無効な日付形式の処理

### 統合テスト

1. **食材削除→フラグ更新のフロー**
   - 食材削除成功時にフラグが更新されること
   - 食材削除失敗時でもフラグ更新は試行されること

## デグレード防止チェックリスト

- [ ] 既存の在庫更新APIが動作することを確認
- [ ] 既存のレシピ履歴取得APIが動作することを確認
- [ ] `ingredients_deleted`がnullの場合でも既存動作を維持
- [ ] エラーハンドリングが適切であることを確認

## 完了条件

- 食材削除APIが正常に動作し、テストが成功
- レシピ履歴の`ingredients_deleted`フラグが正しく更新されること
- 既存機能に影響がないことを確認

## 所要時間

中規模（2-3時間想定）

## 実装後の確認事項

1. **API動作確認**
   - エンドポイントが正常に動作すること
   - 在庫が正しく更新されること
   - フラグが正しく更新されること

2. **データ確認**
   - 在庫の数量が正しく更新されること
   - レシピ履歴の`ingredients_deleted`フラグが正しく更新されること

3. **エラーハンドリング確認**
   - 在庫に存在しない食材の処理が適切であること
   - 一部の食材削除に失敗しても、成功した分は反映されること

