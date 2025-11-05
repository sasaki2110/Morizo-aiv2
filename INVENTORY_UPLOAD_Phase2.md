# Phase 2: CSVアップロード機能（フロントエンド）

## 📋 概要

CSVファイルをアップロードして在庫データを一括登録するUIを実装します。

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**推定時間**: 1-2時間

## 🎯 目標

1. `InventoryCSVUploadModal.tsx`コンポーネントの作成
2. `InventoryPanel.tsx`にCSVアップロードボタンを追加
3. ファイル選択・進捗表示・結果表示の実装
4. エラーハンドリング

## 📝 対象ファイル

- `/app/Morizo-web/components/InventoryCSVUploadModal.tsx` (新規作成)
- `/app/Morizo-web/components/InventoryPanel.tsx` (拡張)

## 🔍 実装の詳細

### 2.1 InventoryCSVUploadModalコンポーネント

**機能**:
- ファイル選択ダイアログ
- アップロード進捗表示
- 結果表示（成功件数、エラー件数、エラー詳細）

**UI要素**:
```typescript
interface CSVUploadResult {
  success: boolean;
  total: number;
  success_count: number;
  error_count: number;
  errors: Array<{
    row: number;
    item_name?: string;
    error: string;
  }>;
}
```

**実装例**:
```typescript
'use client';

import React, { useState, useRef } from 'react';
import { authenticatedFetch } from '@/lib/auth';

interface CSVUploadResult {
  success: boolean;
  total: number;
  success_count: number;
  error_count: number;
  errors: Array<{
    row: number;
    item_name?: string;
    error: string;
  }>;
}

interface InventoryCSVUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete: () => void;
}

const InventoryCSVUploadModal: React.FC<InventoryCSVUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadComplete,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<CSVUploadResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.csv')) {
        alert('CSVファイルのみアップロード可能です');
        return;
      }
      setFile(selectedFile);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert('ファイルを選択してください');
      return;
    }

    setIsUploading(true);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await authenticatedFetch('/api/inventory/upload-csv', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const result: CSVUploadResult = await response.json();
      setUploadResult(result);

      if (result.success && result.error_count === 0) {
        // 成功した場合、在庫一覧を再読み込み
        onUploadComplete();
      }
    } catch (error) {
      console.error('CSV upload failed:', error);
      alert(error instanceof Error ? error.message : 'アップロードに失敗しました');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setUploadResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">
              CSVアップロード
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              ✕
            </button>
          </div>

          {/* CSVフォーマット説明 */}
          <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              <strong>CSVフォーマット:</strong>
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              item_name,quantity,unit,storage_location,expiry_date
            </p>
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
              例: りんご,5,個,冷蔵庫,2024-02-15
            </p>
          </div>

          {/* ファイル選択 */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              CSVファイルを選択
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:text-white"
              disabled={isUploading}
            />
            {file && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                選択中のファイル: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>

          {/* アップロードボタン */}
          <div className="mb-4">
            <button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploading ? 'アップロード中...' : 'アップロード'}
            </button>
          </div>

          {/* 進捗表示 */}
          {isUploading && (
            <div className="mb-4">
              <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700">
                <div className="bg-blue-600 h-2.5 rounded-full animate-pulse" style={{ width: '100%' }}></div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 text-center">
                アップロード中...
              </p>
            </div>
          )}

          {/* 結果表示 */}
          {uploadResult && (
            <div className="mt-4">
              <div className={`p-4 rounded-lg ${uploadResult.success && uploadResult.error_count === 0 ? 'bg-green-50 dark:bg-green-900' : 'bg-yellow-50 dark:bg-yellow-900'}`}>
                <h3 className="font-bold text-gray-800 dark:text-white mb-2">
                  {uploadResult.success && uploadResult.error_count === 0 ? '✅ アップロード成功' : '⚠️ 部分成功'}
                </h3>
                <div className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                  <p>総件数: {uploadResult.total}</p>
                  <p>成功件数: {uploadResult.success_count}</p>
                  {uploadResult.error_count > 0 && (
                    <p className="text-red-600 dark:text-red-400">エラー件数: {uploadResult.error_count}</p>
                  )}
                </div>
              </div>

              {/* エラー詳細 */}
              {uploadResult.errors && uploadResult.errors.length > 0 && (
                <div className="mt-4">
                  <h4 className="font-bold text-gray-800 dark:text-white mb-2">エラー詳細:</h4>
                  <div className="max-h-60 overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="text-left py-2 text-gray-600 dark:text-gray-400">行</th>
                          <th className="text-left py-2 text-gray-600 dark:text-gray-400">アイテム名</th>
                          <th className="text-left py-2 text-gray-600 dark:text-gray-400">エラー</th>
                        </tr>
                      </thead>
                      <tbody>
                        {uploadResult.errors.map((error, index) => (
                          <tr key={index} className="border-b border-gray-200 dark:border-gray-700">
                            <td className="py-2 text-gray-800 dark:text-white">{error.row}</td>
                            <td className="py-2 text-gray-600 dark:text-gray-400">{error.item_name || '-'}</td>
                            <td className="py-2 text-red-600 dark:text-red-400">{error.error}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 閉じるボタン */}
          <div className="mt-6">
            <button
              onClick={handleClose}
              className="w-full px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InventoryCSVUploadModal;
```

### 2.2 InventoryPanel.tsxの拡張

**追加内容**:
- CSVアップロードボタン
- CSVアップロードモーダルの表示制御

**実装例**:
```typescript
// InventoryPanel.tsx に追加

import InventoryCSVUploadModal from '@/components/InventoryCSVUploadModal';

// 状態管理に追加
const [isCSVUploadModalOpen, setIsCSVUploadModalOpen] = useState(false);

// ボタン追加（新規追加ボタンの近く）
<div className="mt-4 space-y-2">
  <button
    onClick={handleAddNew}
    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
  >
    + 新規追加
  </button>
  <button
    onClick={() => setIsCSVUploadModalOpen(true)}
    className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
  >
    📄 CSVアップロード
  </button>
</div>

// モーダル追加（既存のInventoryEditModalの下）
{isCSVUploadModalOpen && (
  <InventoryCSVUploadModal
    isOpen={isCSVUploadModalOpen}
    onClose={() => setIsCSVUploadModalOpen(false)}
    onUploadComplete={loadInventory}
  />
)}
```

## 🧪 テスト項目

- [x] CSVファイルの選択とアップロード
- [x] 進捗表示の動作
- [x] 成功・エラーメッセージの表示
- [x] エラー詳細の表示
- [x] アップロード後の在庫一覧の再読み込み

## 📊 成功基準

- [ ] CSVファイルを選択してアップロードできる
- [ ] 進捗表示が動作する
- [ ] 成功・エラーメッセージが表示される
- [ ] エラー詳細が正しく表示される
- [ ] アップロード後に在庫一覧が更新される

## 🔄 実装順序

1. `InventoryCSVUploadModal.tsx`コンポーネントの作成
2. `InventoryPanel.tsx`にCSVアップロードボタンを追加
3. モーダルの表示制御を実装
4. 動作確認とUI調整

