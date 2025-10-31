# Phase 5B-3: 保存機能の実装と統合

## 概要

Phase 5B-1で作成した`SelectedRecipeCard`コンポーネントを`ChatSection`に統合し、Phase 5Aで実装したバックエンドAPIを呼び出して献立を保存する機能を実装します。

## 対象範囲

- `/app/Morizo-web/components/ChatSection.tsx`

## 実装計画

### 1. ChatSectionの状態管理追加

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

```typescript
import SelectedRecipeCard from '@/components/SelectedRecipeCard';

// 状態管理の追加
const [selectedRecipes, setSelectedRecipes] = useState<{
  main?: RecipeCandidate;
  sub?: RecipeCandidate;
  soup?: RecipeCandidate;
}>({});
const [isSavingMenu, setIsSavingMenu] = useState(false);
const [savedMessage, setSavedMessage] = useState<string>('');
```

### 2. 保存機能の実装

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

```typescript
const handleSaveMenu = async () => {
  if (!selectedRecipes.main && !selectedRecipes.sub && !selectedRecipes.soup) {
    alert('保存するレシピがありません');
    return;
  }
  
  setIsSavingMenu(true);
  setSavedMessage('');
  
  try {
    // 現在のSSEセッションIDを取得
    const currentSseSessionId = chatMessages
      .find(msg => msg.sseSessionId)?.sseSessionId || '';
    
    if (!currentSseSessionId || currentSseSessionId === 'unknown') {
      throw new Error('セッション情報が取得できません');
    }
    
    // Phase 5Aで実装したAPIを呼び出し
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
      
      // 保存成功後、メッセージをクリア（任意）
      setTimeout(() => {
        setSavedMessage('');
      }, 5000);
    } else {
      throw new Error(result.message || '保存に失敗しました');
    }
  } catch (error) {
    console.error('Menu save failed:', error);
    alert('献立の保存に失敗しました。もう一度お試しください。');
    setSavedMessage('');
  } finally {
    setIsSavingMenu(false);
  }
};
```

### 3. UI統合

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

チャットメッセージの表示部分に、選択済みレシピのカードを表示：

```typescript
{/* チャットメッセージの表示 */}
{chatMessages.map((message, index) => (
  // ... 既存のメッセージ表示 ...
))}

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

### 4. 選択確定時の処理（Phase 5B-2との連携）

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

`handleSelection`関数で、Phase 5B-2で実装した選択情報取得処理と連携：

```typescript
const handleSelection = async (selection: number) => {
  // ... 既存の選択処理（API呼び出し等） ...
  
  // Phase 5B-2で実装した選択情報取得処理
  // （バックエンドレスポンス拡張の場合）
  if (result.selected_recipe) {
    const { category, recipe } = result.selected_recipe;
    setSelectedRecipes(prev => ({
      ...prev,
      [category]: recipe
    }));
  }
  
  // または（フロントエンドでの情報取得の場合）
  // 選択UIメッセージから取得する処理
};
```

## 実装のポイント

### 1. 段階的な表示

- 主菜選択後: 主菜のみ表示 + 保存ボタン
- 副菜選択後: 主菜+副菜を表示 + 保存ボタン
- 汁物選択後: 全3件を表示 + 保存ボタン

### 2. 保存ボタンの状態管理

- 保存中: ボタンを無効化し、「保存中...」表示
- 保存成功: 成功メッセージを表示（5秒後に自動で消える）
- 保存失敗: エラーメッセージを表示

### 3. セッションIDの取得

- 現在のチャットセッションからSSEセッションIDを取得
- セッションIDが見つからない場合のエラーハンドリング

### 4. エラーハンドリング

- ネットワークエラー
- APIエラー（401, 500等）
- セッション情報の欠落

## テスト項目

### 単体テスト

1. **保存機能**
   - 保存成功時の処理
   - 保存失敗時の処理
   - エラーハンドリング

2. **UI統合**
   - 選択済みレシピのカード表示
   - 保存ボタンの動作
   - メッセージの表示

### 統合テスト

1. **Phase 5Aとの統合**
   - バックエンドAPIの呼び出し
   - レスポンスの処理
   - エラー時の処理

2. **Phase 5B-1との統合**
   - `SelectedRecipeCard`コンポーネントへのデータ渡し
   - 表示の更新

3. **Phase 5B-2との統合**
   - 選択確定時の情報取得
   - `selectedRecipes`の更新

## 期待される効果

- ユーザーが任意のタイミングで献立を保存できる
- 保存成功/失敗のフィードバックが提供される
- 段階的な選択の進行状況が把握できる

## 次のフェーズ

- **Phase 5C-1**: バックエンドAPI拡張（履歴取得）

