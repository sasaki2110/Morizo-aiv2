# Phase 5C: 過去履歴閲覧機能

## 概要

過去に保存した献立履歴（2週間分）を閲覧し、重複警告を視覚的に確認できる機能を実装します。フロントエンドUIとして履歴パネル（ドロワー型）を実装します。

## 背景

### worries.mdの要件

- **主菜・副菜**: 2週間程度重複を避けたい
- **汁物**: 昨日と同じでなければ、ある程度重複しても良い
- 過去の献立を参考にしたい

### 既存機能

- `get_recent_recipe_titles()`: 過去14日間のレシピタイトルを取得（重複回避用）
- `recipe_historys`テーブル: 保存済みレシピの履歴

## UIイメージ

### **履歴パネル（ドロワー型）**

```
┌─────────────────────────────────┐
│ 📅 献立履歴          [✕]        │
│ ─────────────────────────────── │
│ [フィルター] [期間] [閉じる]     │
│                                 │
│ 📆 2024/01/15 (月)              │
│ ┌─────────────────────────────┐ │
│ │ 🍖 主菜: 鶏もも肉の唐揚げ    │ │
│ │ 🥗 副菜: ほうれん草の胡麻和え │ │
│ │ 🍲 汁物: 味噌汁              │ │
│ │ [詳細] [再提案]              │ │
│ └─────────────────────────────┘ │
│                                 │
│ 📆 2024/01/14 (日)              │
│ ┌─────────────────────────────┐ │
│ │ 🍖 主菜: サバの味噌煮        │ │
│ │ ⚠️ 重複警告（13日前に使用）  │ │
│ │ 🥗 副菜: きゅうりの酢の物    │ │
│ │ 🍲 汁物: ワンタンスープ      │ │
│ └─────────────────────────────┘ │
│                                 │
│ 📆 2024/01/13 (土) ...          │
│                                 │
│ [さらに表示]                     │
└─────────────────────────────────┘
```

## 実装計画

### 1. バックエンドAPIの拡張

**修正する場所**: `/app/Morizo-aiv2/api/routes/menu.py` または新規エンドポイント

**追加するエンドポイント**: `GET /api/menu/history`

**リクエスト**:
```
GET /api/menu/history?days=14&category=main
```

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

**実装内容**:

```python
@router.get("/menu/history")
async def get_menu_history(
    days: int = 14,
    category: Optional[str] = None,  # "main", "sub", "soup" or None
    http_request: Request = None
):
    """献立履歴を取得するエンドポイント"""
    try:
        # 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        client = get_authenticated_client(user_id, token)
        
        # 履歴を取得
        from datetime import datetime, timedelta
        from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
        
        crud = RecipeHistoryCRUD()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # recipe_historysテーブルから取得
        result = client.table("recipe_historys")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("cooked_at", cutoff_date.isoformat())\
            .order("cooked_at", desc=True)\
            .execute()
        
        # 日付ごとにグループ化
        history_by_date = {}
        category_prefix_map = {
            "main": "主菜: ",
            "sub": "副菜: ",
            "soup": "汁物: "
        }
        
        for item in result.data:
            # cooked_atから日付を取得
            cooked_at = datetime.fromisoformat(item["cooked_at"].replace("Z", "+00:00"))
            date_key = cooked_at.date().isoformat()
            
            if date_key not in history_by_date:
                history_by_date[date_key] = []
            
            # カテゴリを判定
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
                "source": item.get("source"),
                "url": item.get("url"),
                "history_id": item["id"]
            })
        
        # 日付順にソート
        sorted_history = sorted(
            [{"date": date, "recipes": recipes} for date, recipes in history_by_date.items()],
            key=lambda x: x["date"],
            reverse=True
        )
        
        return {
            "success": True,
            "data": sorted_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in get_menu_history: {e}")
        raise HTTPException(status_code=500, detail="履歴取得処理でエラーが発生しました")
```

### 2. 重複警告の計算

**修正する場所**: バックエンドAPIまたはフロントエンド

**実装内容**: 各レシピに対して、過去14日間（主菜・副菜）または昨日（汁物）の重複をチェック

```python
# バックエンドで重複警告を計算
def calculate_duplicate_warning(recipe, all_history):
    """重複警告を計算"""
    category = recipe["category"]
    title = recipe["title"]
    
    if category in ["main", "sub"]:
        # 主菜・副菜は14日前の重複をチェック
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=14)
        
        for hist in all_history:
            if hist["category"] == category and hist["title"] == title:
                hist_date = datetime.fromisoformat(hist["date"])
                if hist_date >= cutoff_date:
                    days_ago = (datetime.now() - hist_date).days
                    return f"{days_ago}日前に使用"
    elif category == "soup":
        # 汁物は昨日の重複をチェック
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        
        for hist in all_history:
            if hist["category"] == category and hist["title"] == title:
                hist_date = datetime.fromisoformat(hist["date"])
                if hist_date.date() == yesterday.date():
                    return "昨日使用"
    
    return None
```

### 3. フロントエンド実装

**修正する場所**: `/app/Morizo-web/components/HistoryPanel.tsx` (新規作成)

**実装内容**:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { authenticatedFetch } from '@/lib/auth';

interface HistoryRecipe {
  category: string;
  title: string;
  source: string;
  url?: string;
  history_id: string;
  duplicate_warning?: string;
}

interface HistoryEntry {
  date: string;
  recipes: HistoryRecipe[];
}

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const HistoryPanel: React.FC<HistoryPanelProps> = ({ isOpen, onClose }) => {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [days, setDays] = useState(14);
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen, days, categoryFilter]);

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const url = `/api/menu/history?days=${days}${categoryFilter ? `&category=${categoryFilter}` : ''}`;
      const response = await authenticatedFetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        setHistory(result.data);
      }
    } catch (error) {
      console.error('History load failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const days = ['日', '月', '火', '水', '木', '金', '土'];
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()} (${days[date.getDay()]})`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-white dark:bg-gray-800 shadow-xl z-50 overflow-y-auto">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-800 dark:text-white">
            📅 献立履歴
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>
        
        {/* フィルター */}
        <div className="space-y-2">
          <div>
            <label className="text-sm text-gray-600 dark:text-gray-400">
              期間: {days}日間
            </label>
            <input
              type="range"
              min="7"
              max="30"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
            >
              <option value="">全て</option>
              <option value="main">主菜</option>
              <option value="sub">副菜</option>
              <option value="soup">汁物</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="p-4">
        {isLoading ? (
          <div className="text-center py-8">読み込み中...</div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            履歴がありません
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((entry, index) => (
              <div key={index} className="border-b border-gray-200 dark:border-gray-700 pb-4">
                <h3 className="text-sm font-bold text-gray-600 dark:text-gray-400 mb-2">
                  📆 {formatDate(entry.date)}
                </h3>
                <div className="space-y-2">
                  {entry.recipes.map((recipe, recipeIndex) => (
                    <div
                      key={recipeIndex}
                      className={`p-3 rounded-lg ${
                        recipe.duplicate_warning
                          ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                          : 'bg-gray-50 dark:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-start">
                        <span className="text-xl mr-2">
                          {recipe.category === 'main' ? '🍖' : recipe.category === 'sub' ? '🥗' : '🍲'}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-800 dark:text-white">
                            {recipe.title.replace(/^(主菜|副菜|汁物):\s*/, '')}
                          </p>
                          {recipe.duplicate_warning && (
                            <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                              ⚠️ 重複警告（{recipe.duplicate_warning}）
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPanel;
```

### 4. ChatSectionへの統合

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正する内容**:

```typescript
import HistoryPanel from '@/components/HistoryPanel';

const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false);

// ヘッダー部分に履歴ボタンを追加
<button
  onClick={() => setIsHistoryPanelOpen(true)}
  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
>
  📅 履歴
</button>

<HistoryPanel
  isOpen={isHistoryPanelOpen}
  onClose={() => setIsHistoryPanelOpen(false)}
/>
```

## 実装のポイント

### 1. 重複警告の計算

- **主菜・副菜**: 過去14日間の重複をチェック
- **汁物**: 昨日の重複をチェック
- バックエンドまたはフロントエンドで計算（パフォーマンスを考慮）

### 2. レスポンシブ対応

- デスクトップ: サイドバー型またはドロワー型
- モバイル: ドロワー型（右からスライドイン）

### 3. パフォーマンス

- 初期表示は14日分をデフォルト
- 「さらに表示」で過去の履歴を読み込み
- 仮想スクロールの検討（履歴が多い場合）

### 4. フィルター機能

- 期間選択（7日、14日、30日、全期間）
- カテゴリフィルター（主菜、副菜、汁物）
- 重複警告のみ表示

## テスト項目

### 単体テスト

1. **バックエンドAPI**
   - 履歴取得の正常系
   - フィルター機能
   - エラーハンドリング

2. **フロントエンドコンポーネント**
   - 履歴パネルの表示
   - フィルター機能
   - 重複警告の表示

### 統合テスト

1. **Phase 5A/Bとの統合**
   - 保存した履歴が正しく表示される
   - 重複警告が正しく表示される

## 期待される効果

- ユーザーが過去の献立を確認できる
- 重複を視覚的に確認できる
- 過去の献立を参考にできる
- 2週間分の履歴管理が可能

## モバイル対応

Phase 5Bと同様に、Webアプリの実装をモバイルアプリ（Expo）に移植可能です。
- React Nativeコンポーネントへの移植
- ナビゲーションドロワーの統合

