# Phase 2-2: 在庫CRUD操作 - フロントエンド実装

## 概要

Phase 2-1で実装したCRUD操作APIを使用して、在庫アイテムの作成・更新・削除を行うフロントエンドUIを実装します。
Phase 1-2で作成したInventoryPanelコンポーネントに、編集モーダルとCRUD操作機能を追加します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**前提**: Phase 1-2, Phase 2-1完了  
**参考実装**: Phase 5C-3 履歴パネル実装

## 対象範囲

### フロントエンド
- `/app/Morizo-web/components/InventoryPanel.tsx` (拡張 - CRUD操作ボタンと機能追加)
- `/app/Morizo-web/components/InventoryEditModal.tsx` (新規作成)

## UIイメージ

### **編集モーダル（新規追加・編集共通）**

```
┌─────────────────────────────┐
│ 在庫編集          [✕]        │
│ ─────────────────────────── │
│ アイテム名*:                 │
│ [りんご                   ]  │
│                              │
│ 数量*:                       │
│ [5                        ]  │
│                              │
│ 単位*:                       │
│ [個▼]                       │
│   (個, kg, g, L, ml, etc.)   │
│                              │
│ 保管場所:                    │
│ [冷蔵庫▼]                   │
│   (冷蔵庫, 冷凍庫, 常温倉庫,  │
│    野菜室, その他)            │
│                              │
│ 賞味期限:                    │
│ [2024/01/20        ] [📅]    │
│                              │
│ [キャンセル] [保存]          │
└─────────────────────────────┘
```

### **更新後の在庫パネル（編集・削除ボタン追加）**

```
┌─────────────────────────────────┐
│ 📦 在庫管理          [✕]        │
│ ─────────────────────────────── │
│ フィルター:                     │
│ 保管場所: [全て▼] [検索🔍]     │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ アイテム名│数量│単位│場所│登録日│[操作]│
│ ├─────────────────────────────┤ │
│ │ りんご    │ 5 │個  │冷蔵│01/15│[編集][削除]│
│ │ 米        │ 2 │kg  │常温│01/10│[編集][削除]│
│ └─────────────────────────────┘ │
│ [+ 新規追加]                     │
└─────────────────────────────────┘
```

## 実装計画

### 1. InventoryEditModalコンポーネントの作成

**修正する場所**: `/app/Morizo-web/components/InventoryEditModal.tsx` (新規作成)

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

interface InventoryEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  item: InventoryItem | null; // nullの場合は新規作成
  onSave: () => void;
}

const InventoryEditModal: React.FC<InventoryEditModalProps> = ({
  isOpen,
  onClose,
  item,
  onSave,
}) => {
  const [itemName, setItemName] = useState('');
  const [quantity, setQuantity] = useState<number>(0);
  const [unit, setUnit] = useState('個');
  const [storageLocation, setStorageLocation] = useState('冷蔵庫');
  const [expiryDate, setExpiryDate] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (item) {
      // 編集モード
      setItemName(item.item_name);
      setQuantity(item.quantity);
      setUnit(item.unit);
      setStorageLocation(item.storage_location || '冷蔵庫');
      setExpiryDate(item.expiry_date ? item.expiry_date.split('T')[0] : '');
    } else {
      // 新規作成モード
      setItemName('');
      setQuantity(0);
      setUnit('個');
      setStorageLocation('冷蔵庫');
      setExpiryDate('');
    }
  }, [item, isOpen]);

  const handleSave = async () => {
    if (!itemName.trim()) {
      alert('アイテム名を入力してください');
      return;
    }
    
    if (quantity <= 0) {
      alert('数量は0より大きい値が必要です');
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        item_name: itemName.trim(),
        quantity: quantity,
        unit: unit,
        storage_location: storageLocation || null,
        expiry_date: expiryDate || null,
      };

      let response;
      if (item) {
        // 更新
        response = await authenticatedFetch(`/api/inventory/update/${item.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
      } else {
        // 新規作成
        response = await authenticatedFetch('/api/inventory/add', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      if (result.success) {
        onSave();
      } else {
        throw new Error(result.error || '保存に失敗しました');
      }
    } catch (error) {
      console.error('Inventory save failed:', error);
      alert(error instanceof Error ? error.message : '保存に失敗しました');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const units = ['個', 'kg', 'g', 'L', 'ml', '本', 'パック', '袋'];
  const storageLocations = ['冷蔵庫', '冷凍庫', '常温倉庫', '野菜室', 'その他'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">
              {item ? '在庫編集' : '新規追加'}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            {/* アイテム名 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                アイテム名 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={itemName}
                onChange={(e) => setItemName(e.target.value)}
                placeholder="例: りんご"
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
                required
              />
            </div>

            {/* 数量 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                数量 <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
                required
              />
            </div>

            {/* 単位 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                単位 <span className="text-red-500">*</span>
              </label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
              >
                {units.map(u => (
                  <option key={u} value={u}>{u}</option>
                ))}
              </select>
            </div>

            {/* 保管場所 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                保管場所
              </label>
              <select
                value={storageLocation}
                onChange={(e) => setStorageLocation(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
              >
                {storageLocations.map(loc => (
                  <option key={loc} value={loc}>{loc}</option>
                ))}
              </select>
            </div>

            {/* 賞味期限 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                賞味期限
              </label>
              <input
                type="date"
                value={expiryDate}
                onChange={(e) => setExpiryDate(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          {/* ボタン */}
          <div className="flex gap-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              キャンセル
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {isSaving ? '保存中...' : '保存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InventoryEditModal;
```

**修正の理由**:
- 新規追加と編集を同一モーダルで処理
- バリデーション機能の実装
- ユーザーフレンドリーなフォーム設計

**修正の影響**:
- 新規コンポーネントのみ追加（既存機能への影響なし）

---

### 2. InventoryPanelコンポーネントの拡張（CRUD操作機能追加）

**修正する場所**: `/app/Morizo-web/components/InventoryPanel.tsx` (既存ファイルを拡張)

**修正内容**:

Phase 1-2で作成したファイルに以下を追加：

```typescript
import InventoryEditModal from '@/components/InventoryEditModal';

// 状態追加
const [editingItem, setEditingItem] = useState<InventoryItem | null>(null);
const [isEditModalOpen, setIsEditModalOpen] = useState(false);
const [isDeleting, setIsDeleting] = useState<string | null>(null);

// 関数追加
const handleAddNew = () => {
  setEditingItem(null);
  setIsEditModalOpen(true);
};

const handleEdit = (item: InventoryItem) => {
  setEditingItem(item);
  setIsEditModalOpen(true);
};

const handleDelete = async (itemId: string, itemName: string) => {
  if (!confirm(`「${itemName}」を削除しますか？`)) {
    return;
  }
  
  setIsDeleting(itemId);
  try {
    const response = await authenticatedFetch(`/api/inventory/delete/${itemId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    if (result.success) {
      await loadInventory(); // 一覧を再読み込み
    }
  } catch (error) {
    console.error('Inventory delete failed:', error);
    alert('削除に失敗しました');
  } finally {
    setIsDeleting(null);
  }
};

const handleEditModalClose = () => {
  setIsEditModalOpen(false);
  setEditingItem(null);
};

const handleEditModalSave = async () => {
  await loadInventory(); // 一覧を再読み込み
  handleEditModalClose();
};

// テーブルに操作列を追加
<th className="text-center py-2 text-gray-600 dark:text-gray-400">操作</th>

// テーブル行に編集・削除ボタンを追加
<td className="py-2">
  <div className="flex gap-2 justify-center">
    <button
      onClick={() => handleEdit(item)}
      className="px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs"
    >
      編集
    </button>
    <button
      onClick={() => handleDelete(item.id, item.item_name)}
      disabled={isDeleting === item.id}
      className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-xs disabled:opacity-50"
    >
      {isDeleting === item.id ? '削除中...' : '削除'}
    </button>
  </div>
</td>

// 新規追加ボタンを追加
<div className="mt-4">
  <button
    onClick={handleAddNew}
    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
  >
    + 新規追加
  </button>
</div>

// 編集モーダルの表示
{isEditModalOpen && (
  <InventoryEditModal
    isOpen={isEditModalOpen}
    onClose={handleEditModalClose}
    item={editingItem}
    onSave={handleEditModalSave}
  />
)}
```

**修正の理由**:
- CRUD操作機能を追加
- 編集・削除ボタンを配置
- 新規追加ボタンを配置
- 編集モーダルとの連携

**修正の影響**:
- 既存の一覧表示機能には影響なし（拡張のみ）

---

## 実装のポイント

### 1. モーダル管理

- 新規作成と編集を同一モーダルで処理
- `item`プロパティが`null`の場合は新規作成、存在する場合は編集

### 2. バリデーション

- アイテム名の必須チェック
- 数量の正の値チェック
- クライアント側でのバリデーション実装

### 3. エラーハンドリング

- API呼び出し失敗時のエラーメッセージ表示
- 削除確認ダイアログの実装
- ローディング状態の表示

### 4. データ更新

- CRUD操作後は一覧を再読み込み
- モーダル閉鎖時に一覧を更新

### 5. ユーザビリティ

- 編集・削除ボタンの明確な配置
- 新規追加ボタンの配置
- ダークモード対応

## テスト項目

### 単体テスト

1. **InventoryEditModalコンポーネント**
   - 新規作成モードの表示
   - 編集モードの表示（既存データの読み込み）
   - バリデーション（必須項目、数量の正負）
   - 保存処理（新規作成・更新）
   - キャンセル処理

2. **InventoryPanelコンポーネント（拡張部分）**
   - 編集ボタンの動作
   - 削除ボタンの動作
   - 新規追加ボタンの動作
   - 編集モーダルとの連携
   - 削除後の一覧再読み込み

### 統合テスト

1. **フロントエンド ↔ バックエンド連携**
   - 新規作成が正しく動作すること
   - 更新が正しく動作すること
   - 削除が正しく動作すること
   - 一覧再読み込みが正しく動作すること

2. **エラーハンドリング**
   - バリデーションエラーの表示
   - ネットワークエラーの処理
   - APIエラーの処理

3. **ユーザーフロー**
   - 新規追加 → 一覧表示 → 編集 → 削除 の一連の流れが動作すること

## 期待される効果

- ユーザーが在庫のCRUD操作を簡単に実行できる
- 履歴ビューアーと統一されたUI/UX
- 在庫管理の利便性が向上

## 実装順序

1. InventoryEditModalコンポーネントの作成
2. InventoryPanelコンポーネントの拡張（CRUD操作機能追加）

## 次のフェーズ

- なし（実装完了）

