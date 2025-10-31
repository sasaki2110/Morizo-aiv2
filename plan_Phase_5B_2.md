# Phase 5B-2: 選択確定時の情報取得

## 概要

ユーザーがレシピを選択した際に、選択したレシピの詳細情報を取得する方法を実装します。バックエンドレスポンス拡張（案1）またはフロントエンドでの情報取得（案2）のいずれかを選択して実装します。

## 背景

選択確定時に、選択したレシピの詳細情報（タイトル、食材、URL等）を`SelectedRecipeCard`コンポーネントに渡す必要があります。この情報をどのように取得するかが課題です。

## 実装方針の決定

### 案1: バックエンドレスポンス拡張（推奨）

**メリット**:
- 選択確定時に確実にレシピ情報が取得できる
- フロントエンドでの処理がシンプル
- データの整合性が保たれる

**デメリット**:
- バックエンドの修正が必要

### 案2: 選択UIから情報取得

**メリット**:
- バックエンドの修正が不要
- 既存の候補情報を活用

**デメリット**:
- 選択UIメッセージを探す処理が必要
- 候補が更新されると情報がずれる可能性

**推奨**: **案1（バックエンドレスポンス拡張）**を採用

## 実装計画（案1を採用した場合）

### 1. バックエンドレスポンスの拡張

**修正する場所**: `/app/Morizo-aiv2/core/handlers/selection_handler.py`

**修正内容**:

`process_user_selection`メソッドで、選択確定時に選択したレシピ情報も返すように拡張：

```python
async def process_user_selection(
    self,
    task_id: str,
    selection: int,
    sse_session_id: str,
    user_id: str,
    token: str,
    old_sse_session_id: str = None
) -> dict:
    """ユーザー選択を処理"""
    # ... 既存の処理 ...
    
    # 選択されたレシピを取得
    selected_recipe = await self.stage_manager.get_selected_recipe_from_task(
        task_id, selection, sse_session_id
    )
    
    # 段階を進める
    next_stage = await self.stage_manager.advance_stage(
        sse_session_id, user_id, selected_recipe
    )
    
    if next_stage == "sub":
        # 副菜提案に自動遷移
        # ... 既存の処理 ...
        return {
            "success": True,
            "message": "主菜が確定しました。副菜を提案します。",
            "requires_next_stage": True,
            "selected_recipe": {  # 新規追加
                "category": "main",
                "recipe": selected_recipe
            }
        }
    
    elif next_stage == "soup":
        # 汁物提案に自動遷移
        # ... 既存の処理 ...
        return {
            "success": True,
            "message": "副菜が確定しました。汁物を提案します。",
            "requires_next_stage": True,
            "selected_recipe": {  # 新規追加
                "category": "sub",
                "recipe": selected_recipe
            }
        }
    
    elif next_stage == "completed":
        # 完了
        # ... 既存の処理 ...
        return {
            "success": True,
            "message": "献立が完成しました。",
            "menu": {
                "main": main_recipe,
                "sub": sub_dish,
                "soup": soup
            },
            "selected_recipe": {  # 新規追加
                "category": "soup",
                "recipe": selected_recipe
            }
        }
    
    # その他の場合
    return {
        "success": True,
        "task_id": task_id,
        "selection": selection,
        "current_stage": current_stage,
        "message": f"選択肢 {selection} を受け付けました。",
        "selected_recipe": {  # 新規追加
            "category": current_stage,
            "recipe": selected_recipe
        }
    }
```

### 2. フロントエンドでの処理

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

`handleSelection`関数で、レスポンスから選択したレシピ情報を取得：

```typescript
const handleSelection = async (selection: number) => {
  // ... 既存の選択処理 ...
  
  try {
    const response = await authenticatedFetch('/api/chat/selection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
        selection: selection,
        sse_session_id: sseSessionId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    if (result.success) {
      // 選択したレシピ情報を取得
      if (result.selected_recipe) {
        const { category, recipe } = result.selected_recipe;
        
        // selectedRecipesを更新
        setSelectedRecipes(prev => ({
          ...prev,
          [category]: recipe
        }));
      }
      
      // 既存の選択処理を継続
      // ...
    }
  } catch (error) {
    // エラーハンドリング
  }
};
```

## 実装計画（案2を採用した場合）

### 1. フロントエンドでの情報取得

**修正する場所**: `/app/Morizo-web/components/ChatSection.tsx`

**修正内容**:

`handleSelection`関数で、選択UIメッセージから選択したレシピ情報を取得：

```typescript
const handleSelection = async (selection: number) => {
  // 現在の選択UIメッセージから候補を取得
  const currentSelectionMessage = chatMessages
    .find(msg => msg.type === 'ai' && msg.requiresSelection && msg.candidates);
  
  if (currentSelectionMessage && currentSelectionMessage.candidates) {
    const selectedRecipe = currentSelectionMessage.candidates[selection - 1];
    const currentStage = currentSelectionMessage.currentStage;
    
    // selectedRecipesを更新
    setSelectedRecipes(prev => ({
      ...prev,
      [currentStage]: selectedRecipe
    }));
  }
  
  // ... 既存の選択処理（API呼び出し等） ...
};
```

## 実装のポイント

### 1. データの整合性

- 選択したレシピ情報と実際の選択が一致していること
- 候補が更新されても正しい情報を取得できること

### 2. エラーハンドリング

- 選択情報が取得できない場合の処理
- 不正なデータ形式の場合の処理

### 3. パフォーマンス

- 不要な再レンダリングを避ける
- 情報取得の処理が軽量であること

## テスト項目

### 単体テスト

1. **バックエンド（案1の場合）**
   - 選択レスポンスに`selected_recipe`が含まれること
   - 各カテゴリ（main, sub, soup）で正しく返されること

2. **フロントエンド**
   - 選択確定時に`selectedRecipes`が正しく更新されること
   - 各段階で正しいレシピ情報が取得できること

### 統合テスト

1. **Phase 5B-1との統合**
   - `SelectedRecipeCard`に正しくデータが渡されること
   - 表示が正しく更新されること

## 期待される効果

- 選択確定時にレシピ情報が確実に取得できる
- Phase 5B-1で作成したコンポーネントにデータを渡せる
- 次のフェーズ（保存機能）の実装が容易になる

## 次のフェーズ

- **Phase 5B-3**: 保存機能の実装と統合

