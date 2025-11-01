# Phase 5C-3: フロントエンドUI実装（履歴パネル）

## 概要

Phase 5C-1で実装した履歴取得APIを使用して、過去の献立履歴を閲覧できるフロントエンドUIを実装します。

**注意**: Phase 5C-2（重複警告計算機能）は実装不要のためスキップします。

## 対象範囲

- `/app/Morizo-web/components/HistoryPanel.tsx` (新規作成)
- `/app/Morizo-web/components/ChatSection.tsx`

## UIイメージ

### **履歴パネル（ドロワー型）**

```
┌─────────────────────────────────┐
│ 📅 献立履歴          [✕]        │
│ ─────────────────────────────── │
│ 期間: [7日] [14日] [30日]       │
│ カテゴリ: [全て▼]              │
│                                 │
│ 📆 2024/01/15 (月)              │
│ ┌─────────────────────────────┐ │
│ │ 🍖 主菜: 鶏もも肉の唐揚げ    │ │
│ │ 🥗 副菜: ほうれん草の胡麻和え │ │
│ │ 🍲 汁物: 味噌汁              │ │
│ └─────────────────────────────┘ │
│                                 │
│ 📆 2024/01/14 (日)              │
│ ┌─────────────────────────────┐ │
│ │ 🍖 主菜: サバの味噌煮        │ │
│ │ 🥗 副菜: きゅうりの酢の物    │ │
│ │ 🍲 汁物: ワンタンスープ      │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

## 実装計画

### 1. HistoryPanelコンポーネントの作成

**修正する場所**: `/app/Morizo-web/components/HistoryPanel.tsx` (新規作成)

**実装内容**:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { authenticatedFetch } from '@/lib/auth';

interface HistoryRecipe {
  category: string | null;
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
      setHistory([]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const days = ['日', '月', '火', '水', '木', '金', '土'];
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()} (${days[date.getDay()]})`;
  };

  const getCategoryIcon = (category: string | null) => {
    if (category === 'main') return '🍖';
    if (category === 'sub') return '🥗';
    if (category === 'soup') return '🍲';
    return '🍽️';
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
        <div className="space-y-3">
          <div>
            <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">
              期間: {days}日間
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setDays(7)}
                className={`px-3 py-1 rounded text-sm ${
                  days === 7
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                7日
              </button>
              <button
                onClick={() => setDays(14)}
                className={`px-3 py-1 rounded text-sm ${
                  days === 14
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                14日
              </button>
              <button
                onClick={() => setDays(30)}
                className={`px-3 py-1 rounded text-sm ${
                  days === 30
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                30日
              </button>
            </div>
          </div>
          
          <div>
            <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">
              カテゴリ
            </label>
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
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-400">読み込み中...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            履歴がありません
          </div>
        ) : (
          <div className="space-y-4">
            {history.map((entry, index) => (
              <div key={index} className="border-b border-gray-200 dark:border-gray-700 pb-4 last:border-b-0">
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
                          {getCategoryIcon(recipe.category)}
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

### 2. ChatSectionへの統合

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

```typescript
import HistoryPanel from '@/components/HistoryPanel';

// 状態管理の追加
const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false);

// ヘッダー部分に履歴ボタンを追加（既存のUI構造に応じて）
<div className="flex items-center justify-between mb-4">
  <h2 className="text-xl font-bold">Morizo AI</h2>
  <button
    onClick={() => setIsHistoryPanelOpen(true)}
    className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
  >
    📅 履歴
  </button>
</div>

// HistoryPanelコンポーネントの表示
<HistoryPanel
  isOpen={isHistoryPanelOpen}
  onClose={() => setIsHistoryPanelOpen(false)}
/>
```

## 実装のポイント

### 1. レスポンシブ対応

- デスクトップ: 右側からスライドインするドロワー（幅: 384px / sm:w-96）
- モバイル: 全幅で表示（w-full）

### 2. フィルター機能

- 期間選択: 7日、14日、30日のボタン
- カテゴリフィルター: ドロップダウン

### 3. パフォーマンス

- 初回表示時のみAPI呼び出し
- フィルター変更時のみ再取得
- ローディング状態の表示

## テスト項目

### 単体テスト

1. **HistoryPanelコンポーネント**
   - 履歴の表示
   - フィルター機能
   - ローディング状態の表示
   - 空の状態の表示

2. **ChatSection統合**
   - 履歴ボタンの表示
   - パネルの開閉

### 統合テスト

1. **Phase 5C-1との統合**
   - API呼び出しが正しく動作すること
   - レスポンスが正しく表示されること

## 期待される効果

- ユーザーが過去の献立を確認できる
- 過去の献立を参考にできる
- 2週間分の履歴管理が可能

## モバイル対応

Webアプリの実装をモバイルアプリ（Expo）に移植可能です。
- React Nativeコンポーネントへの移植
- ナビゲーションドロワーの統合

