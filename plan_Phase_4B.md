# Phase 4B: フロントエンド連携

## 概要

Phase 4Bでは、ロールバック機能のフロントエンド部分を実装します。ユーザーが「戻る」ボタンで前の段階に戻れるUIを追加します。

## 実装順序

1. **4B-1**: 戻るボタンの追加（SelectionOptions.tsx）
2. **4B-2**: ロールバック要求の送信（ChatSection.tsx）
3. **4B-3**: 統合テスト

## 4B-1: 戻るボタンの追加

### 修正する場所

`Morizo-web/components/SelectionOptions.tsx`

### 修正する内容

#### 「戻る」ボタンの追加

**実装箇所**: 選択肢の表示領域の上部または下部に「戻る」ボタンを追加

**実装条件**:
- 主菜選択時（`currentStage === "main"`）: 「戻る」ボタンを表示しない（最初の段階のため）
- 副菜選択時（`currentStage === "sub"`）: 「戻る」ボタンを表示（主菜選定に戻る）
- 汁物選択時（`currentStage === "soup"`）: 「戻る」ボタンを表示（副菜選定に戻る）

**UIデザイン**:
```tsx
{currentStage !== "main" && (
  <button
    onClick={handleRollback}
    className="rollback-button"
    style={{
      marginTop: "1rem",
      padding: "0.5rem 1rem",
      backgroundColor: "#f0f0f0",
      border: "1px solid #ccc",
      borderRadius: "4px",
      cursor: "pointer"
    }}
  >
    ← 前の段階に戻る
  </button>
)}
```

**実装ロジック**:

1. `handleRollback`関数の追加
   ```tsx
   const handleRollback = async () => {
     try {
       // ロールバック要求を送信（selection=-1）
       const response = await fetch('/api/chat/selection', {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           'Authorization': `Bearer ${token}`
         },
         body: JSON.stringify({
           task_id: taskId,  // 現在のタスクID
           selection: -1,    // ロールバック要求を示す値
           sse_session_id: sseSessionId
         })
       });
       
       const result = await response.json();
       
       if (result.success) {
         // ロールバック成功時の処理
         // 状態を更新して、前の段階の選択画面に戻る
         // または、親コンポーネントに通知
         onRollback?.(result.rolled_back_to);
       } else {
         // エラー処理
         console.error('Rollback failed:', result.error);
         alert('ロールバックに失敗しました: ' + result.error);
       }
     } catch (error) {
       console.error('Rollback error:', error);
       alert('ロールバック中にエラーが発生しました');
     }
   };
   ```

2. `onRollback`コールバックの追加（親コンポーネントから受け取る）
   ```tsx
   interface SelectionOptionsProps {
     // ... 既存のprops
     onRollback?: (rolledBackTo: string) => void;
   }
   ```

3. ロールバック成功時の状態更新
   - `currentStage`を更新する必要があるため、親コンポーネント（ChatSection）に通知

### 修正の理由

- ユーザーが視覚的に戻る操作を行えるようにするため
- 選択に満足できない場合に、前の段階に戻れるようにするため

### 修正の影響

- UIに新しいボタンが追加される
- 既存の選択機能に影響なし（追加のみ）
- 親コンポーネント（ChatSection）との連携が必要

---

## 4B-2: ロールバック要求の送信

### 修正する場所

`Morizo-web/components/ChatSection.tsx`

### 修正する内容

#### ロールバック要求の処理と状態管理

**実装箇所1**: `handleSelection`関数の拡張または新しい`handleRollback`関数の追加

**実装ロジック**:

1. `handleRollback`関数の追加
   ```tsx
   const handleRollback = async (taskId: string) => {
     try {
       const response = await fetch('/api/chat/selection', {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           'Authorization': `Bearer ${token}`
         },
         body: JSON.stringify({
           task_id: taskId,
           selection: -1,
           sse_session_id: sseSessionId
         })
       });
       
       const result = await response.json();
       
       if (result.success) {
         // ロールバック成功時の処理
         const rolledBackTo = result.rolled_back_to;
         
         // セッション状態を更新
         // currentStageを更新
         setCurrentStage(rolledBackTo);
         
         // 選択履歴を更新
         if (rolledBackTo === "main") {
           // 主菜選定に戻った場合
           setSelectedMainDish(null);
           setSelectedSubDish(null);
           setSelectedSoup(null);
         } else if (rolledBackTo === "sub") {
           // 副菜選定に戻った場合
           setSelectedSubDish(null);
           setSelectedSoup(null);
         }
         
         // UIを更新（メッセージを追加など）
         addMessage({
           role: 'assistant',
           content: result.message || `段階${rolledBackTo === "main" ? "主菜" : "副菜"}選定に戻りました。`
         });
         
         // 必要に応じて、前の段階の選択画面を再表示
         // または、チャットを再読み込み
       } else {
         console.error('Rollback failed:', result.error);
         addMessage({
           role: 'assistant',
           content: `ロールバックに失敗しました: ${result.error}`
         });
       }
     } catch (error) {
       console.error('Rollback error:', error);
       addMessage({
         role: 'assistant',
         content: 'ロールバック中にエラーが発生しました'
       });
     }
   };
   ```

2. `SelectionOptions`コンポーネントへの`onRollback`プロップの追加
   ```tsx
   {showSelection && (
     <SelectionOptions
       candidates={candidates}
       taskId={currentTaskId}
       onSelect={handleSelection}
       onRollback={handleRollback}  // 追加
       currentStage={currentStage}
       sseSessionId={sseSessionId}
     />
   )}
   ```

3. 状態管理の拡張
   - `currentStage`の状態管理を適切に更新
   - 選択履歴の状態管理を更新

**実装箇所2**: `handleSelection`関数の拡張（オプション）

- `selection === -1`の場合に`handleRollback`を呼び出すように拡張することも可能
- ただし、`SelectionOptions`から直接`handleRollback`を呼ぶ方が明確

### 修正の理由

- フロントエンドからロールバック要求を送信するため
- ロールバック後の状態を適切に管理するため
- UIとの整合性を保つため

### 修正の影響

- 既存のAPI呼び出し処理に影響なし（新しい関数を追加）
- 既存の選択処理（`handleSelection`）に影響なし
- 状態管理が拡張される

---

## 4B-3: 統合テスト

### 修正する場所

テストファイル（新規作成または既存の拡張）

**新規作成の場合**: `Morizo-web/__tests__/rollback.test.tsx` または既存のテストファイルに追加

### 修正する内容

#### ロールバック機能のエンドツーエンドテスト

**テストケース1: 副菜選択から主菜選定へのロールバック**

1. 主菜選択画面を表示
2. 主菜を選択 → 副菜選択画面に遷移
3. 「戻る」ボタンをクリック
4. 主菜選択画面に戻ることを確認
5. 選択履歴がクリアされていることを確認

**テストケース2: 汁物選択から副菜選定へのロールバック**

1. 主菜選択画面を表示
2. 主菜を選択 → 副菜選択画面に遷移
3. 副菜を選択 → 汁物選択画面に遷移
4. 「戻る」ボタンをクリック
5. 副菜選択画面に戻ることを確認
6. 汁物の選択履歴がクリアされていることを確認
7. 主菜の選択履歴は保持されていることを確認

**テストケース3: ロールバックエラーハンドリング**

1. 主菜選択画面（最初の段階）で「戻る」ボタンが表示されないことを確認
2. ロールバックAPI呼び出しがエラーになった場合の処理を確認

**実装例**:
```tsx
describe('Rollback Functionality', () => {
  test('should rollback from sub dish selection to main dish selection', async () => {
    // テストの実装
  });
  
  test('should rollback from soup selection to sub dish selection', async () => {
    // テストの実装
  });
  
  test('should not show rollback button on main dish selection', () => {
    // テストの実装
  });
});
```

### 修正の理由

- ロールバック機能が正常に動作することを確認するため
- UIとバックエンドの統合が正しく機能することを確認するため
- エッジケースやエラーハンドリングを確認するため

### 修正の影響

- テストカバレッジが向上する
- 既存のテストに影響なし（新規テストファイルの場合）

---

## 期待される効果

- ユーザーが視覚的に「戻る」ボタンをクリックして前の段階に戻れる
- 選択に満足できない場合に、柔軟に献立作成をやり直せる
- ユーザー体験が向上する

## 技術的な考慮事項

### UIの状態管理

- ロールバック後、UIの状態を適切に更新する必要がある
- `currentStage`の状態管理が重要
- 選択履歴の表示も更新する必要がある

### API連携

- ロールバック要求は既存の`/api/chat/selection`エンドポイントを使用
- `selection=-1`を特別な値として扱う必要がある
- バックエンド（Phase 4A）との整合性を保つ必要がある

### エラーハンドリング

- API呼び出しが失敗した場合のエラーメッセージ表示
- ネットワークエラーの処理
- ロールバック後の状態更新が失敗した場合の処理

## 実装の制約事項

- Phase 4Aが完成してからPhase 4Bを開始
- 既存のPhase 1-3の機能を破壊しない
- 既存の選択機能（`selection >= 1`）に影響しない

