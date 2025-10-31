# Phase 5C-1: バックエンドAPI拡張（履歴取得）

## 概要

過去に保存した献立履歴を取得するバックエンドAPIを実装します。日付別にグループ化し、カテゴリフィルターに対応します。

## 対象範囲

- `/app/Morizo-aiv2/api/routes/menu.py`
- `/app/Morizo-aiv2/api/models.py` (レスポンスモデルの追加)

## 実装計画

### 1. エンドポイント設計

#### **エンドポイント**: `GET /api/menu/history`

**リクエスト**:
```
GET /api/menu/history?days=14&category=main
```

**クエリパラメータ**:
- `days`: 取得期間（デフォルト: 14）
- `category`: カテゴリフィルター（"main", "sub", "soup", または未指定で全件）

**レスポンス**:
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-15",
      "recipes": [
        {
          "category": "main",
          "title": "主菜: 鶏もも肉の唐揚げ",
          "source": "web",
          "url": "...",
          "history_id": "uuid-xxx"
        },
        {
          "category": "sub",
          "title": "副菜: ほうれん草の胡麻和え",
          "source": "rag",
          "url": null,
          "history_id": "uuid-yyy"
        },
        {
          "category": "soup",
          "title": "汁物: 味噌汁",
          "source": "web",
          "url": "...",
          "history_id": "uuid-zzz"
        }
      ]
    },
    {
      "date": "2024-01-14",
      "recipes": [...]
    }
  ]
}
```

### 2. データモデルの追加

**修正する場所**: `/app/Morizo-aiv2/api/models.py`

**追加する内容**:
```python
class HistoryRecipe(BaseModel):
    """履歴レシピ情報"""
    category: Optional[str]  # "main", "sub", "soup", None
    title: str
    source: str
    url: Optional[str]
    history_id: str

class HistoryEntry(BaseModel):
    """履歴エントリ（日付単位）"""
    date: str
    recipes: List[HistoryRecipe]

class MenuHistoryResponse(BaseModel):
    """献立履歴レスポンス"""
    success: bool
    data: List[HistoryEntry]
```

### 3. エンドポイント実装

**修正する場所**: `/app/Morizo-aiv2/api/routes/menu.py`

**実装内容**:

```python
@router.get("/menu/history", response_model=MenuHistoryResponse)
async def get_menu_history(
    days: int = 14,
    category: Optional[str] = None,  # "main", "sub", "soup" or None
    http_request: Request = None
):
    """献立履歴を取得するエンドポイント"""
    try:
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        client = get_authenticated_client(user_id, token)
        
        # 2. 履歴を取得
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # recipe_historysテーブルから取得
        result = client.table("recipe_historys")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("cooked_at", cutoff_date.isoformat())\
            .order("cooked_at", desc=True)\
            .execute()
        
        # 3. 日付ごとにグループ化
        history_by_date = {}
        category_prefix_map = {
            "main": "主菜: ",
            "sub": "副菜: ",
            "soup": "汁物: "
        }
        
        for item in result.data:
            # cooked_atから日付を取得
            cooked_at_str = item["cooked_at"]
            if "Z" in cooked_at_str:
                cooked_at = datetime.fromisoformat(cooked_at_str.replace("Z", "+00:00"))
            else:
                cooked_at = datetime.fromisoformat(cooked_at_str)
            
            date_key = cooked_at.date().isoformat()
            
            if date_key not in history_by_date:
                history_by_date[date_key] = []
            
            # カテゴリを判定（タイトルのプレフィックスから）
            title = item["title"]
            recipe_category = None
            for cat, prefix in category_prefix_map.items():
                if title.startswith(prefix):
                    recipe_category = cat
                    break
            
            # カテゴリフィルター適用
            if category and recipe_category != category:
                continue
            
            history_by_date[date_key].append({
                "category": recipe_category,
                "title": title,
                "source": item.get("source", "web"),
                "url": item.get("url"),
                "history_id": item["id"]
            })
        
        # 4. 日付順にソート（最新順）
        sorted_history = sorted(
            [{"date": date, "recipes": recipes} for date, recipes in history_by_date.items()],
            key=lambda x: x["date"],
            reverse=True
        )
        
        # 5. レスポンスを生成
        return MenuHistoryResponse(
            success=True,
            data=sorted_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in get_menu_history: {e}")
        raise HTTPException(status_code=500, detail="履歴取得処理でエラーが発生しました")
```

## 実装のポイント

### 1. 日付別グループ化

- `cooked_at`フィールドから日付を抽出
- 同じ日付のレシピをまとめる
- 日付順にソート（最新順）

### 2. カテゴリ判定

- タイトルのプレフィックス（「主菜: 」「副菜: 」「汁物: 」）からカテゴリを判定
- プレフィックスがない場合は`category`を`None`とする

### 3. カテゴリフィルター

- クエリパラメータ`category`でフィルタリング
- `category`が未指定の場合は全カテゴリを返す

### 4. エラーハンドリング

- 認証エラー
- データベースエラー
- 日付パースエラー

## テスト項目

### 単体テスト

1. **正常系**
   - 全カテゴリ取得（`category`未指定）
   - 特定カテゴリ取得（`category=main`等）
   - 期間指定（`days=7, 14, 30`）
   - 日付別グループ化が正しく動作すること

2. **異常系**
   - 認証エラー
   - データベースエラー
   - 無効なクエリパラメータ

### 統合テスト

1. **Phase 5Aとの統合**
   - 保存したレシピが履歴に正しく表示されること
   - 日付が正しくグループ化されること

## 期待される効果

- 過去の献立履歴を取得できる
- 日付別に整理されたデータが提供される
- カテゴリフィルターで絞り込みが可能
- 次のフェーズ（重複警告計算、フロントエンドUI）の実装基盤となる

## 次のフェーズ

- **Phase 5C-2**: 重複警告計算機能

