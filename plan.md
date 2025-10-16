## **プランモードでの履歴管理機能実装プラン**

### **実装範囲**
- 採用レシピの特定機能
- レシピ履歴の保存機能
- 2週間重複回避機能

### **実装プラン**

#### **Phase 1: 採用通知API** ✅ **完了**
- 新しいエンドポイント `/api/recipe/adopt` の追加 ✅
- リクエストモデル `RecipeAdoptionRequest` の作成 ✅
- レスポンスモデル `RecipeAdoptionResponse` の作成 ✅
- フロントエンドからの採用通知受信 ✅
- menu_source → source マッピング機能 ✅

**実装詳細:**
- `api/models/requests.py`: `RecipeAdoptionRequest`クラス追加
- `api/models/responses.py`: `RecipeAdoptionResponse`クラス追加
- `api/routes/recipe.py`: `/api/recipe/adopt` POSTエンドポイント実装
- `api/routes/__init__.py`: recipeルーター登録
- `main.py`: FastAPIアプリにrecipeルーター追加
- `api/models/__init__.py`: 新モデルのエクスポート

**エンドポイント仕様:**
```
POST /api/recipe/adopt
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "牛乳と卵のフレンチトースト",
  "category": "main_dish",
  "menu_source": "llm_menu",
  "url": "https://cookpad.com/recipe/12345"
}

Response:
{
  "success": true,
  "message": "レシピが履歴に保存されました",
  "history_id": "uuid-string"
}
```

#### **Phase 2: 履歴保存機能**
- 既存の `recipe_history_crud.py` を活用
- 採用されたレシピの保存処理
- ユーザー別の履歴管理

#### **Phase 3: 重複回避機能**
- 2週間以内のレシピ除外ロジック
- 既存の `excluded_recipes` パラメータとの連携
- 献立提案時の自動除外

### **技術的詳細**
- 既存の認証システムを活用
- 既存のデータベース構造を拡張
- 既存のAPI設計パターンに準拠

