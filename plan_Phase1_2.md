# Phase 1-2: 在庫一覧表示 - フロントエンド実装

## 概要

Phase 1-1で実装した在庫一覧取得APIを使用して、在庫を一覧表示するフロントエンドUIを実装します。
一覧表示とフィルター機能のみを実装し、CRUD操作（編集・削除）は Phase 2-2 で実装します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**参考実装**: Phase 5C-3 履歴パネル実装

## 対象範囲

### フロントエンド
- `/app/Morizo-web/components/InventoryPanel.tsx` (新規作成 - 一覧表示のみ)
- `/app/Morizo-web/components/ChatSection.tsx` (拡張)
- `/app/Morizo-web/hooks/useModalManagement.ts` (拡張)
- `/app/Morizo-web/components/ChatInput.tsx` (拡張 - 在庫ボタン追加)

## UIイメージ

### **在庫パネル（ドロワー型）**

```
┌─────────────────────────────────┐
│ 📦 在庫管理          [✕]        │
│ ─────────────────────────────── │
│ フィルター:                     │
│ 保管場所: [全て▼] [検索🔍]     │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ アイテム名│数量│単位│場所│登録日│
│ ├─────────────────────────────┤ │
│ │ りんご    │ 5 │個  │冷蔵│01/15│
│ │ 米        │ 2 │kg  │常温│01/10│
│ │ 牛乳      │ 1 │L   │冷蔵│01/12│
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**注意**: このフェーズでは編集・削除ボタンや新規追加ボタンは表示しません（Phase 2-2で実装）。

## 実装計画

### 1. InventoryPanelコンポーネントの作成（一覧表示のみ）

**修正する場所**: `/app/Morizo-web/components/InventoryPanel.tsx` (新規作成)

**実装内容**:

```typescript
'use client';

import React, { useState, useEffect } from 'react';
import { authenticatedFetch } from '@/lib/auth';

interface InventoryItem {
  id: string;
  item_name: string;
  quantity: number;
  unit: string;
  storage_location: string | null;
  expiry_date: string | null;
  created_at: string;
  updated_at: string;
}

interface InventoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const InventoryPanel: React.FC<InventoryPanelProps> = ({ isOpen, onClose }) => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [storageLocationFilter, setStorageLocationFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadInventory();
    }
  }, [isOpen]);

  const loadInventory = async () => {
    setIsLoading(true);
    try {
      const response = await authenticatedFetch('/api/inventory/list');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        setInventory(result.data);
      }
    } catch (error) {
      console.error('Inventory load failed:', error);
      setInventory([]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
  };

  // フィルター適用
  const filteredInventory = inventory.filter(item => {
    const matchesStorage = !storageLocationFilter || item.storage_location === storageLocationFilter;
    const matchesSearch = !searchQuery || 
      item.item_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStorage && matchesSearch;
  });

  // 保管場所の一意リストを取得
  const storageLocations = Array.from(new Set(
    inventory.map(item => item.storage_location).filter(Boolean) as string[]
  ));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-white dark:bg-gray-800 shadow-xl z-50 overflow-y-auto">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-800 dark:text-white">
            📦 在庫管理
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
              保管場所
            </label>
            <select
              value={storageLocationFilter}
              onChange={(e) => setStorageLocationFilter(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
            >
              <option value="">全て</option>
              {storageLocations.map(location => (
                <option key={location} value={location}>{location}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">
              検索
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="アイテム名で検索..."
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
            />
          </div>
        </div>
      </div>
      
      <div className="p-4">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600 dark:text-gray-400">読み込み中...</p>
          </div>
        ) : filteredInventory.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            {inventory.length === 0 ? '在庫がありません' : '該当する在庫がありません'}
          </div>
        ) : (
          <div className="space-y-2">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">アイテム名</th>
                  <th className="text-right py-2 text-gray-600 dark:text-gray-400">数量</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">単位</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">場所</th>
                  <th className="text-left py-2 text-gray-600 dark:text-gray-400">登録日</th>
                </tr>
              </thead>
              <tbody>
                {filteredInventory.map((item) => (
                  <tr key={item.id} className="border-b border-gray-200 dark:border-gray-700">
                    <td className="py-2 text-gray-800 dark:text-white">{item.item_name}</td>
                    <td className="py-2 text-right text-gray-800 dark:text-white">{item.quantity}</td>
                    <td className="py-2 text-gray-600 dark:text-gray-400">{item.unit}</td>
                    <td className="py-2 text-gray-600 dark:text-gray-400">{item.storage_location || '-'}</td>
                    <td className="py-2 text-gray-600 dark:text-gray-400">{formatDate(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default InventoryPanel;
```

**修正の理由**:
- 履歴ビューアーと同様のドロワー型UIで統一
- テーブル形式で在庫情報を一覧表示
- フィルター機能（保管場所、検索）を実装
- CRUD操作ボタンは Phase 2-2 で実装

**修正の影響**:
- 新規コンポーネントのみ追加（既存機能への影響なし）

---

### 2. useModalManagementフックの拡張

**修正する場所**: `/app/Morizo-web/hooks/useModalManagement.ts`

**修正内容**:

```typescript
import { useState } from 'react';
import { RecipeCandidate } from '@/types/menu';

/**
 * モーダル管理フック
 * レシピ詳細モーダル、レシピ一覧モーダル、履歴パネル、在庫パネルの状態を管理
 */
export function useModalManagement() {
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<RecipeCandidate | null>(null);
  const [isListModalOpen, setIsListModalOpen] = useState(false);
  const [listModalCandidates, setListModalCandidates] = useState<RecipeCandidate[]>([]);
  const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false);
  const [isInventoryPanelOpen, setIsInventoryPanelOpen] = useState(false); // 追加

  // ... 既存の関数 ...

  const closeInventoryPanel = () => {
    setIsInventoryPanelOpen(false);
  };

  const openInventoryPanel = () => {
    setIsInventoryPanelOpen(true);
  };

  return {
    // 詳細モーダル
    isDetailModalOpen,
    selectedRecipe,
    handleViewDetails,
    closeDetailModal,
    // 一覧モーダル
    isListModalOpen,
    listModalCandidates,
    handleViewList,
    closeListModal,
    // 履歴パネル
    isHistoryPanelOpen,
    openHistoryPanel,
    closeHistoryPanel,
    // 在庫パネル (追加)
    isInventoryPanelOpen,
    openInventoryPanel,
    closeInventoryPanel,
  };
}
```

**修正の理由**:
- 在庫パネルの開閉状態を管理
- 既存パターンに合わせた実装

**修正の影響**:
- 既存の戻り値は変更なし（拡張のみ）

---

### 3. ChatSectionへの統合

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

```typescript
import InventoryPanel from '@/components/InventoryPanel';

// useModalManagementから取得
const {
  // ... 既存のプロパティ ...
  isInventoryPanelOpen,
  openInventoryPanel,
  closeInventoryPanel,
} = useModalManagement();

// ... 既存のコード ...

// InventoryPanelコンポーネントの追加
<InventoryPanel
  isOpen={isInventoryPanelOpen}
  onClose={closeInventoryPanel}
/>
```

**修正の理由**:
- 履歴パネルと同様に在庫パネルを表示

**修正の影響**:
- 新規コンポーネントのインポートと表示のみ（既存機能への影響なし）

---

### 4. ChatInputへの在庫ボタン追加

**修正する場所**: `/app/Morizo-web/components/ChatInput.tsx`

**修正内容**:
- 履歴ボタンと同様に在庫ボタンを追加
- `onOpenInventory`プロパティの追加（履歴の`onOpenHistory`と同様）

**修正の理由**:
- ユーザーが在庫パネルにアクセスできるようにする

**修正の影響**:
- 新規ボタンの追加のみ（既存機能への影響なし）

---

## 実装のポイント

### 1. レスポンシブ対応

- デスクトップ: 右側からスライドインするドロワー（幅: 384px / sm:w-96）
- モバイル: 全幅で表示（w-full）

### 2. フィルター機能

- 保管場所フィルター: ドロップダウン（実際に使用されている保管場所のみ表示）
- 検索機能: アイテム名の部分一致検索

### 3. データ管理

- 一覧表示時のみAPI呼び出し
- ローディング状態の表示

### 4. エラーハンドリング

- API呼び出し失敗時のエラーログ出力
- 空の状態の表示

### 5. ユーザビリティ

- テーブル形式での見やすい表示
- ダークモード対応

## テスト項目

### 単体テスト

1. **InventoryPanelコンポーネント**
   - 在庫一覧の表示
   - フィルター機能（保管場所、検索）
   - ローディング状態の表示
   - 空の状態の表示

2. **useModalManagementフック**
   - 在庫パネルの開閉状態管理

### 統合テスト

1. **フロントエンド ↔ バックエンド連携**
   - API呼び出しが正しく動作すること
   - レスポンスが正しく表示されること

2. **ChatSection統合**
   - 在庫ボタンの表示
   - パネルの開閉

## 期待される効果

- ユーザーが在庫を視覚的に確認できる
- 履歴ビューアーと統一されたUI/UX
- Phase 2-2（CRUD操作）の実装基盤が整う

## 実装順序

1. useModalManagementフックの拡張
2. InventoryPanelコンポーネントの作成
3. ChatSectionへの統合
4. ChatInputへの在庫ボタン追加

## 次のフェーズ

- **Phase 2-1**: CRUD操作のバックエンド実装
- **Phase 2-2**: CRUD操作のフロントエンド実装

