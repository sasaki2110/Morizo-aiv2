# Phase 3D: フロントエンド対応

## 概要

段階的選択のUI改善を行います。

## 対象範囲

- `/app/Morizo-web/components/SelectionOptions.tsx`
- `/app/Morizo-web/components/ChatSection.tsx`

## 実装計画

### 1. 段階表示の追加

**修正する場所**: `SelectionOptions.tsx`

**修正する内容**:
- 現在の段階（主菜/副菜/汁物）を表示
- 使い残し食材を表示
- カテゴリ表示（和食/洋食/中華）

```typescript
interface SelectionOptionsProps {
  candidates: RecipeCandidate[];
  onSelect: (selection: number) => void;
  taskId: string;
  currentStage: 'main' | 'sub' | 'soup';  // 新規追加
  usedIngredients?: string[];  // 新規追加
  menuCategory?: 'japanese' | 'western' | 'chinese';  // 新規追加
  isLoading?: boolean;
}
```

**修正の理由**: 段階情報を表示するため

**修正の影響**: 既存のPropsにオプショナルフィールドを追加

---

### 2. 選択履歴の表示

**修正する場所**: `ChatSection.tsx`

**修正する内容**:
- 選択した主菜・副菜・汁物を履歴として表示
- 最終的な献立の確認UI

```typescript
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  type: 'text' | 'ai' | 'selection';
  requiresSelection?: boolean;
  candidates?: RecipeCandidate[];
  taskId?: string;
  selectedRecipe?: {  // 新規追加
    main?: RecipeCandidate;
    sub?: RecipeCandidate;
    soup?: RecipeCandidate;
  };
}
```

**修正の理由**: 選択履歴を表示するため

**修正の影響**: 既存のメッセージ型に新規フィールドを追加

---

## テスト

### 結合試験

#### フロントエンドUIテスト
**テストファイル**: `tests/phase3d/test_01_frontend_ui.py`

**テストシナリオ**:

**シナリオ1: 段階表示の確認**
1. サーバーを起動
2. 主菜提案リクエストを送信
3. フロントエンドで段階表示が確認できる
4. 使い残し食材リストが表示される

**シナリオ2: 選択履歴の確認**
1. 主菜を選択
2. 副菜を選択
3. 汁物を選択
4. 選択履歴UIに主菜・副菜・汁物が表示される

**シナリオ3: 段階遷移の確認**
1. 主菜選択後、段階表示が"副菜"に変わる
2. 副菜選択後、段階表示が"汁物"に変わる
3. 汁物選択後、完了メッセージが表示される

**手動テスト項目**:
- ブラウザで`localhost:3000`にアクセス
- 主菜提案 → 段階表示が"主菜"であることを確認
- 副菜提案 → 段階表示が"副菜"であることを確認
- 汁物提案 → 段階表示が"汁物"であることを確認
- 選択履歴に各レシピが表示されることを確認

---

## 期待される効果

- 段階情報がわかりやすくなる
- 選択履歴を確認できる
- ユーザー体験が向上

