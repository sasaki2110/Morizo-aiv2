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

## 期待される効果

- 段階情報がわかりやすくなる
- 選択履歴を確認できる
- ユーザー体験が向上

