# セッション5: Phase 4（フロントエンド実装）

## 概要

食材削除UIコンポーネントを実装します。

## 目的

- レシピ履歴表示に食材削除ボタンを追加
- 食材削除コンポーネントを実装
- 削除済み表示を実装

## 実装範囲

**Phase 4**: フロントエンド実装

## 実装内容

### 1. レシピ履歴表示に食材削除ボタンを追加

**実装内容**:
- 1日分のまとめに「食材削除」ボタンを追加
- `ingredients_deleted = True`の場合は「削除済み」と表示し、グレーアウト
- ボタンクリックで食材削除コンポーネントを開く

**UI要件**:
- ボタンの配置: 1日分のレシピ履歴のまとめの右上または下部
- 削除済みの場合: 「削除済み」と表示し、グレーアウト（クリック不可）
- 削除未済みの場合: 「食材削除」と表示し、クリック可能

### 2. 食材削除コンポーネント

**実装内容**:
- 削除候補食材リストを表示
- プルダウンで処理を選択（無処理・削除・数量減）
- 数量減の場合のみ変更後数量を入力
- 削除実行ボタン

**UI要件**:
- モーダルまたはダイアログ形式で表示
- 削除候補食材リスト（テーブル形式）:
  - **処理（選択）**: プルダウンで「無処理・削除・数量減」を選択
  - 無処理: 処理を行わない（APIに送信しない）
  - 削除: 数量を0に設定して削除
  - 数量減: 変更後数量を入力して数量を減らす
  - **アイテム名（表示）**: 食材名を表示
  - **変更前数量（表示）**: 現在の数量と単位を表示
  - **変更後数量（入力）**: 「数量減」選択時のみ活性化される入力フィールド
- 削除実行ボタン: 選択された処理を実行（「無処理」は除外）
- キャンセルボタン: モーダルを閉じる

**API呼び出し**:
1. 食材削除候補取得: `GET /api/recipe/ingredients/delete-candidates/{date}`
2. 食材削除実行: `POST /api/recipe/ingredients/delete`

### 3. 削除済み表示

**実装内容**:
- レシピ履歴取得時に`ingredients_deleted`フラグを確認
- フラグが`true`の場合は「削除済み」と表示し、グレーアウト

**UI要件**:
- 削除済みの場合: ボタンをグレーアウトし、「削除済み」と表示
- クリック不可にする

## 実装詳細

### コンポーネント構成

```
RecipeHistoryList
  └─ HistoryEntry (1日分のまとめ)
      ├─ RecipeList (レシピリスト)
      └─ IngredientDeleteButton (食材削除ボタン)
          └─ IngredientDeleteModal (食材削除モーダル)
              ├─ IngredientDeleteCandidateList (削除候補リスト)
              └─ IngredientDeleteActions (削除実行ボタン等)
```

### 主要なコンポーネント

#### IngredientDeleteButton

```typescript
interface IngredientDeleteButtonProps {
  date: string; // YYYY-MM-DD形式
  ingredientsDeleted: boolean;
  onDeleteClick: () => void;
}

// 削除済みの場合はグレーアウト、クリック不可
// 削除未済みの場合はクリック可能
```

#### IngredientDeleteModal

```typescript
interface IngredientDeleteModalProps {
  date: string;
  isOpen: boolean;
  onClose: () => void;
  onDeleteComplete: () => void;
}

// モーダル内で削除候補を取得・表示
// 削除実行処理
```

#### IngredientDeleteCandidateList

```typescript
type ActionType = 'none' | 'delete' | 'reduce';

interface IngredientDeleteCandidate {
  inventory_id: string;
  item_name: string;
  current_quantity: number;
  unit: string;
}

interface CandidateAction {
  inventory_id: string;
  action: ActionType;
  new_quantity?: number; // 数量減の場合のみ
}

interface IngredientDeleteCandidateListProps {
  candidates: IngredientDeleteCandidate[];
  actions: Map<string, CandidateAction>; // inventory_id -> CandidateAction
  onActionChange: (inventoryId: string, action: ActionType, newQuantity?: number) => void;
}

// プルダウン（処理選択）と数量入力フィールド（数量減の場合のみ活性化）
```

## テスト項目

### UIテスト

1. **食材削除ボタンの表示**
   - 削除済みの場合: 「削除済み」と表示し、グレーアウト
   - 削除未済みの場合: 「食材削除」と表示し、クリック可能

2. **食材削除モーダルの表示**
   - ボタンクリックでモーダルが開くこと
   - 削除候補食材リストが表示されること

3. **食材削除コンポーネントの動作**
   - プルダウンで「無処理・削除・数量減」を選択できること
   - 「数量減」選択時のみ変更後数量入力欄が活性化されること
   - 「無処理」を選択したアイテムはAPIに送信されないこと
   - 「削除」を選択したアイテムは数量0として送信されること
   - 「数量減」を選択したアイテムは入力された数量で送信されること
   - 削除実行ボタンで処理が実行されること
   - 削除完了後、モーダルが閉じること

### 統合テスト

1. **エンドツーエンドテスト**
   - レシピ履歴表示→食材削除ボタンクリック→削除候補取得→削除実行→削除完了

2. **削除済み表示の確認**
   - 食材削除実行後、ボタンが「削除済み」と表示され、グレーアウトされること

## デグレード防止チェックリスト

- [ ] 既存のレシピ履歴表示が正常に動作すること
- [ ] 既存のレシピ履歴取得APIが正常に動作すること
- [ ] 食材削除機能がない場合でも既存動作を維持すること

## 完了条件

- UIが正常に動作し、エンドツーエンドテストが成功
- 食材削除ボタンが正しく表示されること
- 食材削除コンポーネントが正常に動作すること
- 削除済み表示が正しく動作すること

## 所要時間

中規模（2-3時間想定）

## 実装後の確認事項

1. **UI動作確認**
   - 食材削除ボタンが正しく表示されること
   - モーダルが正しく開閉されること
   - 削除候補リストが正しく表示されること

2. **機能動作確認**
   - 削除候補取得APIが正常に呼び出されること
   - 削除実行APIが正常に呼び出されること
   - 削除完了後、UIが正しく更新されること

3. **エラーハンドリング確認**
   - API呼び出し失敗時のエラー表示が適切であること
   - ネットワークエラー時の処理が適切であること

## 注意事項

1. **API呼び出しのエラーハンドリング**
   - 削除候補取得失敗時: エラーメッセージを表示
   - 削除実行失敗時: エラーメッセージを表示し、成功した分は反映

2. **ローディング状態の表示**
   - API呼び出し中はローディング表示
   - 削除実行中はローディング表示

3. **確認ダイアログ**
   - 削除実行前に確認ダイアログを表示（オプション）

4. **レスポンシブ対応**
   - モバイル端末でも使いやすいUI

