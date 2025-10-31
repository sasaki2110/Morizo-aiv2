# Phase 5B: フロントエンド実装（選択履歴表示UI + 保存機能）

## 概要

ユーザーに選択状況を視覚的に表示し、任意のタイミングで献立を保存できるUIを実装します。Phase 5Aで実装したバックエンドAPIを呼び出してDBに保存します。

## 対象範囲

- `/app/Morizo-web/components/ChatSection.tsx`
- `/app/Morizo-web/components/SelectedRecipeCard.tsx` (新規作成)

## UIイメージ

### **1. 主菜選択後の表示**

```
┌─────────────────────────────────────┐
│ ✅ 主菜が確定しました                  │
│ ───────────────────────────────────│
│ 🍖 主菜: 鶏もも肉の唐揚げ            │
│ 食材: 鶏もも肉、片栗粉、にんにく...   │
│                                     │
│ [詳細を見る] [献立を保存]            │
└─────────────────────────────────────┘
```

### **2. 副菜選択後の表示**

```
┌─────────────────────────────────────┐
│ ✅ 副菜が確定しました                  │
│ ───────────────────────────────────│
│ 現在の献立:                          │
│                                     │
│ 🍖 主菜: 鶏もも肉の唐揚げ            │
│ 🥗 副菜: ほうれん草の胡麻和え         │
│                                     │
│ [詳細を見る] [献立を保存]            │
└─────────────────────────────────────┘
```

### **3. 汁物選択後の表示（完了）**

```
┌─────────────────────────────────────┐
│ 🎉 献立が完成しました！               │
│ ───────────────────────────────────│
│                                     │
│ 📅 今日の献立                        │
│                                     │
│ 🍖 主菜: 鶏もも肉の唐揚げ            │
│   食材: 鶏もも肉、片栗粉...          │
│                                     │
│ 🥗 副菜: ほうれん草の胡麻和え         │
│   食材: ほうれん草、ごま...          │
│                                     │
│ 🍲 汁物: 味噌汁                      │
│   食材: わかめ、豆腐...              │
│                                     │
│ [詳細を見る] [献立を保存]            │
└─────────────────────────────────────┘
```

## 実装計画

### 1. SelectedRecipeCardコンポーネントの作成

**修正する場所**: `/app/Morizo-web/components/SelectedRecipeCard.tsx` (新規作成)

**実装内容**:

```typescript
'use client';

import React from 'react';
import { RecipeCandidate } from '@/types/menu';

interface SelectedRecipeCardProps {
  main?: RecipeCandidate;
  sub?: RecipeCandidate;
  soup?: RecipeCandidate;
  onSave?: () => void;
  onViewDetails?: (recipe: RecipeCandidate) => void;
  isSaving?: boolean;
  savedMessage?: string;
}

const SelectedRecipeCard: React.FC<SelectedRecipeCardProps> = ({
  main,
  sub,
  soup,
  onSave,
  onViewDetails,
  isSaving = false,
  savedMessage
}) => {
  const isComplete = main && sub && soup;
  const stage = main && !sub ? 'main' : main && sub && !soup ? 'sub' : 'completed';
  
  const getTitle = () => {
    if (isComplete) return '🎉 献立が完成しました！';
    if (sub) return '✅ 副菜が確定しました';
    if (main) return '✅ 主菜が確定しました';
    return '';
  };
  
  return (
    <div className="mt-6 p-6 bg-green-50 dark:bg-green-900/20 rounded-lg border-2 border-green-500">
      <h3 className="text-lg font-bold text-gray-800 dark:text-white mb-4">
        {getTitle()}
      </h3>
      
      {isComplete && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            📅 今日の献立
          </p>
        </div>
      )}
      
      <div className="space-y-3">
        {main && (
          <div className="p-3 bg-white dark:bg-gray-800 rounded-lg">
            <div className="flex items-start">
              <span className="text-2xl mr-2">🍖</span>
              <div className="flex-1">
                <p className="font-medium text-gray-800 dark:text-white">
                  主菜: {main.title}
                </p>
                {main.ingredients && main.ingredients.length > 0 && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    食材: {main.ingredients.join(', ')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        
        {sub && (
          <div className="p-3 bg-white dark:bg-gray-800 rounded-lg">
            <div className="flex items-start">
              <span className="text-2xl mr-2">🥗</span>
              <div className="flex-1">
                <p className="font-medium text-gray-800 dark:text-white">
                  副菜: {sub.title}
                </p>
                {sub.ingredients && sub.ingredients.length > 0 && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    食材: {sub.ingredients.join(', ')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        
        {soup && (
          <div className="p-3 bg-white dark:bg-gray-800 rounded-lg">
            <div className="flex items-start">
              <span className="text-2xl mr-2">🍲</span>
              <div className="flex-1">
                <p className="font-medium text-gray-800 dark:text-white">
                  汁物: {soup.title}
                </p>
                {soup.ingredients && soup.ingredients.length > 0 && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    食材: {soup.ingredients.join(', ')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-4 flex flex-col sm:flex-row gap-3">
        {onSave && (
          <button
            onClick={onSave}
            disabled={isSaving}
            className="px-6 py-3 rounded-lg font-medium transition-colors duration-200 bg-green-600 hover:bg-green-700 text-white disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isSaving ? '保存中...' : '献立を保存'}
          </button>
        )}
      </div>
      
      {savedMessage && (
        <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-sm text-blue-800 dark:text-blue-300">
          {savedMessage}
        </div>
      )}
    </div>
  );
};

export default SelectedRecipeCard;
```

### 2. ChatSectionの拡張

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正する内容**:

#### 2.1 状態管理の追加

```typescript
const [selectedRecipes, setSelectedRecipes] = useState<{
  main?: RecipeCandidate;
  sub?: RecipeCandidate;
  soup?: RecipeCandidate;
}>({});
const [isSavingMenu, setIsSavingMenu] = useState(false);
const [savedMessage, setSavedMessage] = useState<string>('');
```

#### 2.2 選択確定時の処理

`handleSelection`関数内で、選択確定時に`selectedRecipes`を更新：

```typescript
const handleSelection = async (selection: number) => {
  // ... 既存の選択処理 ...
  
  // 選択確定後、セッションから選択済みレシピを取得
  // バックエンドのレスポンスから選択済みレシピ情報を取得するか、
  // 別途APIで取得する必要がある
  // 暫定的に、選択UIから直接レシピ情報を取得
};
```

#### 2.3 保存機能の実装

```typescript
const handleSaveMenu = async () => {
  if (!selectedRecipes.main && !selectedRecipes.sub && !selectedRecipes.soup) {
    alert('保存するレシピがありません');
    return;
  }
  
  setIsSavingMenu(true);
  setSavedMessage('');
  
  try {
    // 現在のSSEセッションIDを取得（ChatSectionの状態から）
    const currentSseSessionId = chatMessages
      .find(msg => msg.sseSessionId)?.sseSessionId || '';
    
    if (!currentSseSessionId) {
      throw new Error('セッション情報が取得できません');
    }
    
    const response = await authenticatedFetch('/api/menu/save', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sse_session_id: currentSseSessionId
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (result.success) {
      setSavedMessage(result.message || `${result.total_saved}つのレシピが保存されました`);
    } else {
      throw new Error(result.message || '保存に失敗しました');
    }
  } catch (error) {
    console.error('Menu save failed:', error);
    alert('献立の保存に失敗しました。もう一度お試しください。');
  } finally {
    setIsSavingMenu(false);
  }
};
```

#### 2.4 UI表示の追加

チャットメッセージの表示部分に、選択済みレシピのカードを表示：

```typescript
{/* 選択済みレシピの表示 */}
{(selectedRecipes.main || selectedRecipes.sub || selectedRecipes.soup) && (
  <div className="mt-4">
    <SelectedRecipeCard
      main={selectedRecipes.main}
      sub={selectedRecipes.sub}
      soup={selectedRecipes.soup}
      onSave={handleSaveMenu}
      isSaving={isSavingMenu}
      savedMessage={savedMessage}
    />
  </div>
)}
```

### 3. 選択確定時のレシピ情報取得

**問題**: 選択確定時に、選択したレシピの詳細情報を取得する必要がある

**解決策**:
- **案1**: バックエンドの選択レスポンスに選択したレシピの詳細情報を含める
- **案2**: 選択UI（SelectionOptions）から選択したレシピの情報を取得
- **案3**: セッションから選択済みレシピを取得するAPIを別途作成

**推奨**: 案1または案2を使用

#### 案1: バックエンドレスポンスの拡張

`selection_handler.py`の`process_user_selection`で、選択確定時に選択したレシピ情報も返す：

```python
return {
    "success": True,
    "message": "主菜が確定しました。",
    "selected_recipe": selected_recipe,  # 選択したレシピの詳細情報
    "current_stage": "sub"
}
```

#### 案2: 選択UIから情報取得

`handleSelection`で、選択した候補のインデックスからレシピ情報を取得：

```typescript
const handleSelection = async (selection: number) => {
  // 現在の選択UIメッセージから候補を取得
  const currentSelectionMessage = chatMessages
    .find(msg => msg.requiresSelection && msg.candidates);
  
  if (currentSelectionMessage && currentSelectionMessage.candidates) {
    const selectedRecipe = currentSelectionMessage.candidates[selection - 1];
    const currentStage = currentSelectionMessage.currentStage;
    
    // selectedRecipesを更新
    setSelectedRecipes(prev => ({
      ...prev,
      [currentStage]: selectedRecipe
    }));
  }
  
  // ... 既存の選択処理 ...
};
```

## 実装のポイント

### 1. 段階的な表示

- 主菜選択後: 主菜のみ表示
- 副菜選択後: 主菜+副菜を表示
- 汁物選択後: 全3件を表示

### 2. 保存ボタンの表示

- 各段階で「献立を保存」ボタンを表示
- 保存済みの場合は「保存済み」表示（任意）

### 3. レスポンシブ対応

- Tailwind CSSのブレークポイントを使用
- モバイル表示にも対応

### 4. エラーハンドリング

- 保存失敗時のエラーメッセージ表示
- ネットワークエラー時の処理

## テスト項目

### 単体テスト

1. **SelectedRecipeCardコンポーネント**
   - 主菜のみ表示
   - 主菜+副菜表示
   - 全3件表示
   - 保存ボタンの動作

2. **保存機能**
   - 保存成功時の処理
   - 保存失敗時の処理
   - エラーハンドリング

### 統合テスト

1. **Phase 5Aとの統合**
   - バックエンドAPIの呼び出し
   - レスポンスの処理
   - エラー時の処理

## 期待される効果

- ユーザーが選択状況を視覚的に確認できる
- ユーザーが任意のタイミングで保存できる
- 献立完成時の確認UIが提供される
- 段階的な選択の進行状況が把握できる

## 次のフェーズ

- **Phase 5C**: 過去履歴閲覧機能

