# フロントエンド API仕様書

## レシピ採用通知API

### エンドポイント
```
POST /api/recipe/adopt
```

### 認証
- **必須**: `Authorization: Bearer <token>` ヘッダー
- またはリクエストボディに `token` フィールドを含める

### リクエスト仕様

#### Content-Type
```
Content-Type: application/json
```

#### リクエストボディ
```typescript
interface RecipeAdoptionRequest {
  recipes: RecipeItem[];
  token?: string; // オプション（ヘッダーで認証する場合は不要）
}

interface RecipeItem {
  title: string;           // レシピのタイトル（1-255文字）
  category: "main_dish" | "side_dish" | "soup";  // レシピのカテゴリ
  menu_source: "llm_menu" | "rag_menu" | "manual";  // メニューの出典
  url?: string;           // レシピのURL（オプション）
}
```

#### フィールド詳細

| フィールド | 型 | 必須 | 説明 |
|-----------|----|----|------|
| `recipes` | `RecipeItem[]` | ✅ | 採用されたレシピのリスト（1-3個） |
| `token` | `string` | ❌ | 認証トークン（ヘッダーで認証する場合は不要） |

| RecipeItemフィールド | 型 | 必須 | 説明 |
|---------------------|----|----|------|
| `title` | `string` | ✅ | レシピのタイトル（1-255文字） |
| `category` | `string` | ✅ | `"main_dish"`, `"side_dish"`, `"soup"` のいずれか |
| `menu_source` | `string` | ✅ | `"llm_menu"`, `"rag_menu"`, `"manual"` のいずれか |
| `url` | `string` | ❌ | レシピのURL（Web検索から採用した場合） |

### レスポンス仕様

#### 成功時（200 OK）
```typescript
interface RecipeAdoptionResponse {
  success: boolean;
  message: string;
  saved_recipes: SavedRecipe[];
  total_saved: number;
}

interface SavedRecipe {
  title: string;
  category: string;
  history_id: string;
}
```

#### エラー時

##### バリデーションエラー（422 Unprocessable Entity）
```json
{
  "detail": "バリデーションエラー: [詳細]",
  "status_code": 422,
  "timestamp": "2025-10-16T09:43:37.690608",
  "error_type": "validation_error"
}
```

##### 認証エラー（401 Unauthorized）
```json
{
  "detail": "認証が必要です",
  "status_code": 401,
  "timestamp": "2025-10-16T09:43:37.690608",
  "error_type": "authentication_error"
}
```

##### 内部サーバーエラー（500 Internal Server Error）
```json
{
  "detail": "レシピ採用処理でエラーが発生しました",
  "status_code": 500,
  "timestamp": "2025-10-16T09:43:37.690608",
  "error_type": "internal_error"
}
```

## 使用例

### 基本的な使用例

```javascript
// 複数レシピの採用通知
const response = await fetch('/api/recipe/adopt', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${userToken}`
  },
  body: JSON.stringify({
    recipes: [
      {
        title: "牛乳と卵のフレンチトースト",
        category: "main_dish",
        menu_source: "llm_menu",
        url: "https://cookpad.com/recipe/12345"
      },
      {
        title: "ほうれん草の胡麻和え",
        category: "side_dish",
        menu_source: "rag_menu",
        url: "https://example.com/recipe/67890"
      },
      {
        title: "手作りスープ",
        category: "soup",
        menu_source: "manual"
      }
    ]
  })
});

const result = await response.json();
console.log(result);
// {
//   "success": true,
//   "message": "3つのレシピが履歴に保存されました",
//   "saved_recipes": [
//     {
//       "title": "牛乳と卵のフレンチトースト",
//       "category": "main_dish",
//       "history_id": "2b965888-cb32-43a3-ac92-3fe4b546f328"
//     },
//     {
//       "title": "ほうれん草の胡麻和え",
//       "category": "side_dish",
//       "history_id": "d9e6ad69-c34e-43cd-9b55-18f14223f577"
//     },
//     {
//       "title": "手作りスープ",
//       "category": "soup",
//       "history_id": "f0e3b264-ee0d-4127-9553-9f6a3f8fabb1"
//     }
//   ],
//   "total_saved": 3
// }
```

### 単一レシピの採用通知

```javascript
const response = await fetch('/api/recipe/adopt', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${userToken}`
  },
  body: JSON.stringify({
    recipes: [
      {
        title: "単一レシピテスト",
        category: "main_dish",
        menu_source: "llm_menu",
        url: "https://test.com/recipe/999"
      }
    ]
  })
});
```

## フロントエンド実装ガイド

### 1. レシピ選択時の処理

```javascript
// ユーザーがレシピを選択した時の処理
function onRecipeSelected(selectedRecipes) {
  // selectedRecipes: [
  //   { title: "レシピ1", category: "main_dish", menu_source: "llm_menu", url: "..." },
  //   { title: "レシピ2", category: "side_dish", menu_source: "rag_menu", url: "..." },
  //   { title: "レシピ3", category: "soup", menu_source: "manual" }
  // ]
  
  adoptRecipes(selectedRecipes);
}

async function adoptRecipes(recipes) {
  try {
    const response = await fetch('/api/recipe/adopt', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getUserToken()}`
      },
      body: JSON.stringify({ recipes })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    if (result.success) {
      // 成功時の処理
      showSuccessMessage(result.message);
      console.log(`${result.total_saved}つのレシピが保存されました`);
      
      // 保存されたレシピのIDを取得
      result.saved_recipes.forEach(recipe => {
        console.log(`保存されたレシピ: ${recipe.title} (ID: ${recipe.history_id})`);
      });
    } else {
      // 失敗時の処理
      showErrorMessage(result.message);
    }
  } catch (error) {
    console.error('レシピ採用エラー:', error);
    showErrorMessage('レシピの保存に失敗しました');
  }
}
```

### 2. エラーハンドリング

```javascript
async function adoptRecipes(recipes) {
  try {
    const response = await fetch('/api/recipe/adopt', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getUserToken()}`
      },
      body: JSON.stringify({ recipes })
    });

    const result = await response.json();

    switch (response.status) {
      case 200:
        // 成功
        showSuccessMessage(result.message);
        break;
        
      case 401:
        // 認証エラー
        showErrorMessage('ログインが必要です');
        redirectToLogin();
        break;
        
      case 422:
        // バリデーションエラー
        showErrorMessage('入力内容に問題があります');
        console.error('バリデーションエラー:', result.detail);
        break;
        
      case 500:
        // サーバーエラー
        showErrorMessage('サーバーエラーが発生しました');
        console.error('サーバーエラー:', result.detail);
        break;
        
      default:
        showErrorMessage('予期しないエラーが発生しました');
    }
  } catch (error) {
    console.error('ネットワークエラー:', error);
    showErrorMessage('ネットワークエラーが発生しました');
  }
}
```

### 3. ローディング状態の管理

```javascript
function adoptRecipes(recipes) {
  // ローディング状態を開始
  setLoading(true);
  disableRecipeSelection();

  fetch('/api/recipe/adopt', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getUserToken()}`
    },
    body: JSON.stringify({ recipes })
  })
  .then(response => response.json())
  .then(result => {
    if (result.success) {
      showSuccessMessage(result.message);
    } else {
      showErrorMessage(result.message);
    }
  })
  .catch(error => {
    console.error('エラー:', error);
    showErrorMessage('レシピの保存に失敗しました');
  })
  .finally(() => {
    // ローディング状態を終了
    setLoading(false);
    enableRecipeSelection();
  });
}
```

## 注意事項

### 1. menu_source の値について

- `llm_menu`: LLM推論で生成されたメニュー
- `rag_menu`: RAG検索で生成されたメニュー  
- `manual`: 手動で入力されたメニュー（将来の機能）

### 2. レシピ数の制限

- 最小: 1個
- 最大: 3個（主菜・副菜・汁物）

### 3. 認証トークン

- ヘッダーでの認証を推奨
- リクエストボディの `token` フィールドはオプション

### 4. URL フィールド

- Web検索からレシピを取得した場合は必須
- 手動入力の場合は省略可能

## テスト用のサンプルデータ

```javascript
// テスト用のサンプルデータ
const sampleRecipes = [
  {
    title: "牛乳と卵のフレンチトースト",
    category: "main_dish",
    menu_source: "llm_menu",
    url: "https://cookpad.com/recipe/12345"
  },
  {
    title: "ほうれん草の胡麻和え",
    category: "side_dish",
    menu_source: "rag_menu",
    url: "https://example.com/recipe/67890"
  },
  {
    title: "手作りスープ",
    category: "soup",
    menu_source: "manual"
  }
];
```

---

**更新日**: 2025-10-16  
**バージョン**: 1.0  
**実装状況**: ✅ 完了
