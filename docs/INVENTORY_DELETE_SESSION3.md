# セッション3: Phase 2A（食材集約API）

## 概要

1日分のレシピから利用食材を集約するAPIを実装します。

## 目的

- 指定日付のレシピ履歴から利用食材を集約
- 在庫情報とマッチングして削除候補リストを返す

## 実装範囲

**Phase 2A**: 1日分のレシピから利用食材を集約するAPI

## 修正ファイル

- `api/routes/recipe.py` (新規エンドポイント)
- `api/models/responses.py` (新規レスポンスモデル)

## 実装内容

### 1. レスポンスモデルの追加

**ファイル**: `api/models/responses.py`

**追加内容**:
```python
class IngredientDeleteCandidate(BaseModel):
    """削除候補食材"""
    inventory_id: str = Field(..., description="在庫ID")
    item_name: str = Field(..., description="食材名")
    current_quantity: float = Field(..., description="現在の数量")
    unit: str = Field(..., description="単位")

class IngredientDeleteCandidatesResponse(BaseModel):
    """削除候補食材レスポンス"""
    success: bool
    date: str
    candidates: List[IngredientDeleteCandidate]
```

### 2. エンドポイントの実装

**ファイル**: `api/routes/recipe.py`

**エンドポイント**: `GET /api/recipe/ingredients/delete-candidates/{date}`

**実装詳細**:
```python
@router.get("/recipe/ingredients/delete-candidates/{date}", response_model=IngredientDeleteCandidatesResponse)
async def get_ingredient_delete_candidates(
    date: str,  # YYYY-MM-DD形式
    http_request: Request
):
    """指定日付のレシピから利用食材の削除候補を取得"""
    try:
        logger.info(f"🔍 [API] Ingredient delete candidates request received: date={date}")
        
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
        
        # 3. 日付の検証と変換
        from datetime import datetime
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, datetime.min.time())
            end_datetime = datetime.combine(date_obj, datetime.max.time())
        except ValueError:
            logger.error(f"❌ [API] Invalid date format: {date}")
            raise HTTPException(status_code=400, detail="日付の形式が不正です（YYYY-MM-DD形式で指定してください）")
        
        # 4. 指定日付のレシピ履歴を取得
        crud = RecipeHistoryCRUD()
        result = client.table("recipe_historys")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("cooked_at", start_datetime.isoformat())\
            .lte("cooked_at", end_datetime.isoformat())\
            .execute()
        
        logger.info(f"🔍 [API] Retrieved {len(result.data)} recipe histories for date: {date}")
        
        # 5. 各レシピのingredientsを集約（重複除去）
        all_ingredients = []
        for recipe in result.data:
            ingredients = recipe.get("ingredients")
            if ingredients:
                if isinstance(ingredients, list):
                    all_ingredients.extend(ingredients)
                elif isinstance(ingredients, str):
                    # JSON文字列の場合
                    import json
                    try:
                        ingredients_list = json.loads(ingredients)
                        if isinstance(ingredients_list, list):
                            all_ingredients.extend(ingredients_list)
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ [API] Failed to parse ingredients JSON: {ingredients}")
        
        # 重複除去（順序を保持）
        unique_ingredients = list(dict.fromkeys(all_ingredients))
        logger.info(f"🔍 [API] Aggregated {len(unique_ingredients)} unique ingredients")
        
        # 6. 在庫一覧を取得
        from mcp_servers.inventory_crud import InventoryCRUD
        inventory_crud = InventoryCRUD()
        inventory_result = await inventory_crud.get_all_items(client, user_id)
        
        if not inventory_result.get("success"):
            logger.error(f"❌ [API] Failed to get inventory list: {inventory_result.get('error')}")
            raise HTTPException(status_code=500, detail="在庫情報の取得に失敗しました")
        
        inventory_items = inventory_result.get("data", [])
        logger.info(f"🔍 [API] Retrieved {len(inventory_items)} inventory items")
        
        # 7. 食材名でマッチングして削除候補リストを作成
        # 食材名の正規化用（既存のIngredientMapperComponentを活用）
        from services.session.models.components.ingredient_mapper import IngredientMapperComponent
        from config.loggers import GenericLogger
        ingredient_mapper = IngredientMapperComponent(GenericLogger("api", "ingredient_mapper"))
        
        candidates = []
        matched_inventory_ids = set()  # 重複防止用
        
        for ingredient_name in unique_ingredients:
            # 在庫名を正規化してインデックスを作成
            inventory_normalized = {}
            for inv_item in inventory_items:
                normalized = ingredient_mapper.normalize_ingredient_name(inv_item.get("item_name", ""))
                if normalized not in inventory_normalized:
                    inventory_normalized[normalized] = []
                inventory_normalized[normalized].append(inv_item)
            
            # レシピ食材を在庫名にマッピング
            normalized_ingredient = ingredient_mapper.normalize_ingredient_name(ingredient_name)
            
            matched = False
            for inv_item in inventory_items:
                normalized_inv = ingredient_mapper.normalize_ingredient_name(inv_item.get("item_name", ""))
                
                # 完全一致または部分一致をチェック
                if normalized_ingredient == normalized_inv or \
                   normalized_ingredient in normalized_inv or \
                   normalized_inv in normalized_ingredient:
                    inv_id = inv_item.get("id")
                    # 重複防止
                    if inv_id not in matched_inventory_ids:
                        candidates.append(IngredientDeleteCandidate(
                            inventory_id=inv_id,
                            item_name=inv_item.get("item_name", ""),
                            current_quantity=float(inv_item.get("quantity", 0)),
                            unit=inv_item.get("unit", "個")
                        ))
                        matched_inventory_ids.add(inv_id)
                        matched = True
            
            if not matched:
                logger.debug(f"⚠️ [API] Ingredient '{ingredient_name}' not found in inventory")
        
        logger.info(f"✅ [API] Created {len(candidates)} delete candidates")
        
        return IngredientDeleteCandidatesResponse(
            success=True,
            date=date,
            candidates=candidates
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in get_ingredient_delete_candidates: {e}")
        raise HTTPException(status_code=500, detail="削除候補の取得処理でエラーが発生しました")
```

## テスト項目

### 単体テスト

1. **日付の検証**
   - 正常系: 有効な日付形式（YYYY-MM-DD）
   - 異常系: 無効な日付形式
   - 異常系: 日付が未来

2. **レシピ履歴の取得**
   - 正常系: 指定日付のレシピが存在する場合
   - 正常系: 指定日付のレシピが存在しない場合（空リストを返す）
   - 異常系: `ingredients`がnullのレシピがある場合

3. **食材の集約**
   - 正常系: 複数のレシピから食材を集約
   - 正常系: 重複食材の除去
   - 異常系: `ingredients`がJSON文字列の場合

4. **在庫とのマッチング**
   - 正常系: 在庫に存在する食材のマッチング
   - 正常系: 在庫に存在しない食材の処理（候補に含めない）
   - 正常系: 表記ゆれ（「レンコン」と「れんこん」など）のマッチング

### 統合テスト

1. **エンドツーエンドテスト**
   - 段階提案→履歴保存→食材集約APIの呼び出し
   - 献立提案→履歴保存→食材集約APIの呼び出し

## デグレード防止チェックリスト

- [ ] 既存のレシピ履歴取得APIが動作することを確認
- [ ] 既存の在庫取得APIが動作することを確認
- [ ] エラーハンドリングが適切であることを確認

## 完了条件

- APIが正常に動作し、テストが成功
- 指定日付のレシピから利用食材を集約できること
- 在庫情報とマッチングして削除候補リストを返せること

## 所要時間

小規模（1-2時間想定）

## 実装後の確認事項

1. **API動作確認**
   - エンドポイントが正常に動作すること
   - レスポンス形式が正しいこと
   - エラーハンドリングが適切であること

2. **データ確認**
   - 指定日付のレシピから食材が正しく集約されること
   - 在庫情報と正しくマッチングされること
   - 表記ゆれが正しく処理されること

