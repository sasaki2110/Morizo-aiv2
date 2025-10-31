# Phase 5A: バックエンド実装（DB保存機能）

## 概要

選択したレシピ（主菜・副菜・汁物）をDBに永続化する機能を実装します。フロントエンドのUIを意識したAPI設計を行い、セッションから選択済みレシピを取得してDBに保存します。

## 対象範囲

- `/app/Morizo-aiv2/api/routes/menu.py` (新規作成)
- `/app/Morizo-aiv2/api/models.py` (リクエスト/レスポンスモデルの追加)

## 実装計画

### 1. エンドポイント設計

#### **エンドポイント**: `POST /api/menu/save`

**リクエスト**:
```json
{
  "sse_session_id": "session_xxx"
}
```

**レスポンス**:
```json
{
  "success": true,
  "message": "2つのレシピが履歴に保存されました",
  "saved_recipes": [
    {
      "category": "main",
      "title": "主菜: 鶏もも肉の唐揚げ",
      "history_id": "uuid-xxx"
    },
    {
      "category": "sub",
      "title": "副菜: ほうれん草の胡麻和え",
      "history_id": "uuid-yyy"
    }
  ],
  "total_saved": 2
}
```

### 2. データモデルの追加

**修正する場所**: `/app/Morizo-aiv2/api/models.py`

**追加する内容**:
```python
class MenuSaveRequest(BaseModel):
    """献立保存リクエスト"""
    sse_session_id: str

class SavedMenuRecipe(BaseModel):
    """保存されたレシピ情報"""
    category: str  # "main", "sub", "soup"
    title: str
    history_id: str

class MenuSaveResponse(BaseModel):
    """献立保存レスポンス"""
    success: bool
    message: str
    saved_recipes: List[SavedMenuRecipe]
    total_saved: int
```

### 3. エンドポイント実装

**修正する場所**: `/app/Morizo-aiv2/api/routes/menu.py` (新規作成)

**実装内容**:

#### 3.1 基本構造

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List
from config.loggers import GenericLogger
from ..models import MenuSaveRequest, MenuSaveResponse, SavedMenuRecipe
from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
from mcp_servers.utils import get_authenticated_client
from services.session.service import session_service

router = APIRouter()
logger = GenericLogger("api", "menu")
```

#### 3.2 メイン処理

```python
@router.post("/menu/save", response_model=MenuSaveResponse)
async def save_menu(request: MenuSaveRequest, http_request: Request):
    """献立をDBに保存するエンドポイント"""
    try:
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        
        # 2. セッションから選択済みレシピを取得
        selected_recipes = await session_service.get_selected_recipes(request.sse_session_id)
        
        if not selected_recipes:
            return MenuSaveResponse(
                success=False,
                message="保存するレシピがありません",
                saved_recipes=[],
                total_saved=0
            )
        
        # 3. 認証済みSupabaseクライアントの作成
        client = get_authenticated_client(user_id, token)
        
        # 4. 各レシピをDBに保存
        crud = RecipeHistoryCRUD()
        saved_recipes = []
        failed_count = 0
        
        category_prefix_map = {
            "main": "主菜: ",
            "sub": "副菜: ",
            "soup": "汁物: "
        }
        
        source_mapping = {
            "llm": "web",
            "rag": "rag",
            "web": "web"
        }
        
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
                
                # DBに保存
                result = await crud.add_history(
                    client=client,
                    user_id=user_id,
                    title=prefixed_title,
                    source=db_source,
                    url=url
                )
                
                if result.get("success"):
                    history_id = result.get("data", {}).get("id")
                    saved_recipes.append(SavedMenuRecipe(
                        category=category,
                        title=prefixed_title,
                        history_id=history_id
                    ))
                else:
                    failed_count += 1
                    logger.error(f"❌ [API] Failed to save {category}: {result.get('error')}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ [API] Error saving {category}: {e}")
        
        # 5. レスポンスの生成
        total_saved = len(saved_recipes)
        if total_saved == 0:
            message = "レシピの保存に失敗しました"
            success = False
        elif failed_count > 0:
            message = f"{total_saved}つのレシピが保存されました（{failed_count}つ失敗）"
            success = True
        else:
            message = f"{total_saved}つのレシピが履歴に保存されました"
            success = True
        
        return MenuSaveResponse(
            success=success,
            message=message,
            saved_recipes=saved_recipes,
            total_saved=total_saved
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in save_menu: {e}")
        raise HTTPException(status_code=500, detail="献立保存処理でエラーが発生しました")
```

### 4. ルーター登録

**修正する場所**: `/app/Morizo-aiv2/main.py` または ルーター登録ファイル

**修正する内容**:
```python
from api.routes import menu

app.include_router(menu.router, tags=["menu"])
```

## 実装のポイント

### 1. セッションからのレシピ取得

- `session_service.get_selected_recipes(sse_session_id)`を使用
- 返り値: `{"main": {...}, "sub": {...}, "soup": {...}}`
- `None`のカテゴリは保存しない（未選択のため）

### 2. タイトルプレフィックスの追加

- `"主菜: "`, `"副菜: "`, `"汁物: "`をタイトルに追加
- 既存の`get_recent_recipe_titles()`との互換性を保つため

### 3. source のマッピング

- `"llm"` → `"web"` (LLM推論で生成したレシピはWeb検索でレシピ取得)
- `"rag"` → `"rag"` (RAG検索で生成したレシピ)
- その他 → `"web"` (デフォルト)

### 4. エラーハンドリング

- セッションが見つからない場合
- レシピが存在しない場合
- DB保存に失敗した場合
- 認証エラーの場合

## テスト項目

### 単体テスト

1. **正常系**
   - 主菜のみ選択時の保存
   - 主菜+副菜選択時の保存
   - 全3件選択時の保存
   - 各レシピが正しく保存されること

2. **異常系**
   - セッションが見つからない場合
   - レシピが存在しない場合
   - 認証エラーの場合
   - DB保存エラーの場合

### 統合テスト

1. **Phase 5Bとの統合テスト**
   - フロントエンドから保存リクエストを送信
   - 保存成功時のレスポンス確認
   - 保存失敗時のレスポンス確認

## 期待される効果

- 選択したレシピがDBに永続化される
- 次回アクセス時も履歴が残る
- 重複回避機能（2週間分の履歴）が正しく機能する
- Phase 5Bでフロントエンドから呼び出し可能

## 次のフェーズ

- **Phase 5B**: フロントエンド実装（選択履歴表示UI + 保存機能）

