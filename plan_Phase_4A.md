# Phase 4A: バックエンドロールバック機能の実装

## 概要

Phase 4Aでは、ロールバック機能のバックエンド部分を実装します。タスクチェーンとセッション状態を適切にロールバックできるようにします。

## 実装順序

1. **4A-1**: TaskChainManagerの拡張
2. **4A-2**: SessionServiceの拡張
3. **4A-3**: Agentのロールバック処理機能

## 4A-1: TaskChainManagerの拡張

### 修正する場所

`core/models.py` - `TaskChainManager`クラスの`update_task_status()`メソッドの後

### 修正する内容

#### `rollback_to_stage()` メソッドの追加

```python
def rollback_to_stage(self, stage: str) -> Dict[str, Any]:
    """
    指定された段階までのタスクチェーンをロールバック
    
    Args:
        stage: ロールバック対象の段階（"main" または "sub"）
    
    Returns:
        Dict[str, Any]: ロールバック結果
        {
            "success": bool,
            "rolled_back_tasks": List[str],  # ロールバックされたタスクIDのリスト
            "reset_tasks": List[str],  # PENDINGに戻されたタスクIDのリスト
            "error": Optional[str]
        }
    """
```

**実装ロジック**:

1. タスクチェーンから該当する段階の提案タスクを特定
   - `method == "generate_proposals"` かつ `parameters.get("category") == stage` のタスクを探す
   
2. 該当タスクが見つかった場合：
   - 該当タスクを `COMPLETED` → `RUNNING` に戻す
   - タスクの `result` を `None` にクリア
   - `self.results` から該当タスクIDの結果を削除
   
3. 該当タスク以降のタスクを `PENDING` に戻す
   - タスクチェーン内で、該当タスクより後の位置にあるタスクすべて
   - 各タスクの `status` を `PENDING` に
   - 各タスクの `result` を `None` にクリア
   - `self.results` から該当タスクIDの結果を削除

4. ロールバック結果を返す

**エラーハンドリング**:
- 該当タスクが見つからない場合: `{"success": False, "error": "Task not found for stage: {stage}"}`
- タスクチェーンが空の場合: `{"success": False, "error": "Task chain is empty"}`

### 修正の理由

- タスクチェーンの状態を適切に管理するため
- 既存の`update_task_status()`メソッドを活用し、一貫性を保つため

### 修正の影響

- TaskChainManagerの機能が拡張される
- 既存のタスク実行フローに影響なし（ロールバック時にのみ呼び出される）
- 既存の`update_task_status()`メソッドの実装は変更なし

---

## 4A-2: SessionServiceの拡張

### 修正する場所

`services/session_service.py` - `Session`クラスの`get_menu_category()`メソッドの後

### 修正する内容

#### `rollback_stage()` メソッドの追加

```python
def rollback_stage(self, target_stage: str) -> None:
    """
    セッション状態を指定された段階にロールバック
    
    Args:
        target_stage: ロールバック先の段階（"main" または "sub"）
    """
```

**実装ロジック**:

#### `target_stage == "main"` の場合：

1. 選択履歴のクリア
   - `self.selected_main_dish = None`
   - `self.selected_sub_dish = None`
   - `self.selected_soup = None`

2. 段階の更新
   - `self.current_stage = "main"`

3. 使用済み食材のクリア
   - `self.used_ingredients = []`

4. 提案履歴のクリア
   - `self.proposed_recipes["sub"] = []`
   - `self.proposed_recipes["soup"] = []`

5. 候補情報のクリア
   - `self.candidates["sub"] = []`
   - `self.candidates["soup"] = []`

6. ログ出力
   - `self.logger.info(f"🔄 [SESSION] Rolled back to main stage")`

#### `target_stage == "sub"` の場合：

1. 選択履歴の部分クリア
   - `self.selected_sub_dish = None`
   - `self.selected_soup = None`
   - **注意**: `self.selected_main_dish` は保持

2. 段階の更新
   - `self.current_stage = "sub"`

3. 使用済み食材の部分クリア
   - 主菜で使った食材は保持する必要があるため、実装が複雑になる
   - **実装案**: `self.used_ingredients`を主菜選択時の状態に戻す
   - **問題**: 主菜選択時の`used_ingredients`の状態は保存されていない
   - **解決策**: 主菜選択時に`used_ingredients`のスナップショットを保存する、または主菜の情報から再計算する
   - **暫定実装**: 主菜が選択されている場合、主菜の食材情報から`used_ingredients`を再計算
     ```python
     if self.selected_main_dish and "ingredients" in self.selected_main_dish:
         # 主菜の食材を在庫名にマッピングしてused_ingredientsを再構築
         inventory_items = self.context.get("inventory_items", [])
         recipe_ingredients = self.selected_main_dish["ingredients"]
         mapped_ingredients = self._map_recipe_ingredients_to_inventory(
             recipe_ingredients, inventory_items
         )
         self.used_ingredients = mapped_ingredients
     else:
         self.used_ingredients = []
     ```

4. 提案履歴の部分クリア
   - `self.proposed_recipes["soup"] = []`
   - **注意**: `self.proposed_recipes["main"]` と `self.proposed_recipes["sub"]` は保持

5. 候補情報の部分クリア
   - `self.candidates["soup"] = []`
   - **注意**: `self.candidates["main"]` と `self.candidates["sub"]` は保持

6. ログ出力
   - `self.logger.info(f"🔄 [SESSION] Rolled back to sub stage")`

**エラーハンドリング**:
- `target_stage`が"main"でも"sub"でもない場合: `ValueError`を発生

### 修正の理由

- セッション状態をロールバック時に適切に管理するため
- 段階的な選択システムと整合性を保つため

### 修正の影響

- Sessionの状態管理が拡張される
- 既存のセッション管理機能に影響なし（ロールバック時にのみ呼び出される）
- 主菜選択時の`used_ingredients`の状態管理が重要になる（副菜ロールバック時）

---

## 4A-3: Agentのロールバック処理機能

### 修正する場所1

`core/agent.py` - `TrueReactAgent`クラスの`process_user_selection()`メソッド内（`selection == 0`のチェック直後）

### 修正する内容1: `process_user_selection()`メソッドの拡張

**修正箇所**: `process_user_selection()`メソッドの先頭（`selection == 0`のチェック後）

```python
async def process_user_selection(self, task_id: str, selection: int, sse_session_id: str, user_id: str, token: str, old_sse_session_id: str = None) -> dict:
    """ユーザー選択結果の処理（自動遷移機能付き）"""
    try:
        self.logger.info(f"📥 [AGENT] Processing user selection: task_id={task_id}, selection={selection}")
        
        # Phase 1F: selection=0 の場合は追加提案要求
        if selection == 0:
            ...
            return await self._handle_additional_proposal_request(...)
        
        # Phase 4A: selection=-1 の場合はロールバック要求
        if selection == -1:
            self.logger.info(f"🔄 [AGENT] Rollback request detected (selection=-1)")
            return await self.handle_rollback_request(
                sse_session_id, user_id, token
            )
        
        # 以降、既存のロジック...
```

### 修正する場所2

`core/agent.py` - `TrueReactAgent`クラスの`_handle_additional_proposal_request()`メソッドの後

### 修正する内容2: `handle_rollback_request()`メソッドの追加

```python
async def handle_rollback_request(
    self, 
    sse_session_id: str, 
    user_id: str, 
    token: str
) -> dict:
    """
    ロールバック要求の処理
    
    Args:
        sse_session_id: SSEセッションID
        user_id: ユーザーID
        token: 認証トークン
    
    Returns:
        dict: 処理結果
        {
            "success": bool,
            "message": str,
            "rolled_back_to": Optional[str],  # "main" or "sub"
            "error": Optional[str]
        }
    """
```

**実装ロジック**:

1. セッションの取得と検証
   ```python
   session = await self.session_service.get_session(sse_session_id, user_id)
   if not session:
       return {"success": False, "error": "Session not found"}
   ```

2. 現在の段階の取得
   ```python
   current_stage = session.get_current_stage()
   self.logger.info(f"🔍 [AGENT] Current stage: {current_stage}")
   ```

3. ロールバック対象段階の判定
   - `current_stage == "sub"` → `target_stage = "main"`
   - `current_stage == "soup"` → `target_stage = "sub"`
   - `current_stage == "main"` → エラー（既に最初の段階）
   - `current_stage == "completed"` → `target_stage = "sub"`（汁物選択から副菜選定に戻る）

4. セッション状態のロールバック
   ```python
   try:
       session.rollback_stage(target_stage)
       self.logger.info(f"✅ [AGENT] Session rolled back to {target_stage}")
   except ValueError as e:
       return {"success": False, "error": str(e)}
   ```

5. タスクチェーンのロールバック（オプション）
   - **注意**: `process_user_selection()`が呼ばれる時点では、タスクチェーンは既に完了している可能性が高い
   - タスクチェーンの管理方法を確認する必要がある
   - **暫定実装**: タスクチェーンのロールバックはスキップし、次回のリクエスト時に新規タスクチェーンが生成されることを期待
   - **将来の拡張**: セッションにタスクチェーンを保存し、ロールバック時に再利用する

6. レスポンスの生成
   ```python
   if target_stage == "main":
       message = "主菜選定に戻りました。主菜を選び直してください。"
   elif target_stage == "sub":
       message = "副菜選定に戻りました。副菜を選び直してください。"
   
   return {
       "success": True,
       "message": message,
       "rolled_back_to": target_stage
   }
   ```

**エラーハンドリング**:
- セッションが見つからない場合
- 現在の段階が無効な場合（例: "main"からロールバックしようとした場合）
- `rollback_stage()`でエラーが発生した場合

### 修正の理由

- ユーザーのロールバック要求を処理するため
- タスクチェーンとセッション状態を同期してロールバックするため
- 段階的選択システムと整合性を保つため

### 修正の影響

- `process_user_selection()`の機能が拡張される（`selection == -1`の場合の処理が追加）
- 既存の選択処理に影響なし（ロールバック要求時のみ新機能が動作）
- 既存の`_handle_additional_proposal_request()`の実装は変更なし

---

## 4A-4: プランナーの拡張（オプション）

### 修正する場所

`services/llm/prompt_manager.py` - プランナープロンプトビルダー

### 修正する内容

プランナープロンプトにロールバック処理の説明を追加（必要に応じて）

**実装判断基準**:
- プランナーがユーザーの「戻る」要求を理解し、適切に処理できる場合は不要
- プランナーが「戻る」要求を誤解したり、不適切なタスクを生成する場合は実装

### 修正の理由

- プランナーがロールバック要求を適切に理解できるようにするため（必要に応じて）

### 修正の影響

- プランナーのプロンプトが拡張される
- 既存のタスク生成に影響なし

**注意**: この項目はオプションです。Phase 4A-1〜4A-3の実装完了後、必要に応じて検討してください。

---

## テスト計画

### 4A-1のテスト

- `rollback_to_stage("main")`で主菜提案タスクがロールバックされることを確認
- `rollback_to_stage("sub")`で副菜提案タスクがロールバックされることを確認
- 該当タスクが見つからない場合のエラーハンドリングを確認

### 4A-2のテスト

- `rollback_stage("main")`で主菜選定に戻り、副菜・汁物の選択がクリアされることを確認
- `rollback_stage("sub")`で副菜選定に戻り、汁物の選択がクリアされることを確認
- `used_ingredients`が適切に更新されることを確認

### 4A-3のテスト

- `selection=-1`でロールバック要求が検出されることを確認
- 副菜選択時（`current_stage="sub"`）にロールバックすると主菜選定に戻ることを確認
- 汁物選択時（`current_stage="soup"`）にロールバックすると副菜選定に戻ることを確認
- 主菜選択時（`current_stage="main"`）にロールバックするとエラーになることを確認

---

## 技術的な考慮事項

### タスクチェーンの管理

- `process_user_selection()`が呼ばれる時点では、タスクチェーンは既に完了している
- ロールバック後の再実行は、次回のリクエスト時に新規タスクチェーンが生成されることを期待
- 将来的には、セッションにタスクチェーンを保存し、ロールバック時に再利用する方法を検討

### セッション状態の整合性

- ロールバック時、セッション状態が不整合にならないように注意
- `used_ingredients`の管理が特に重要（主菜選択時の状態を保持する必要がある）

### エラーハンドリング

- ロールバック対象タスクが見つからない場合の処理
- セッション状態が不整合な場合の処理
- 無効な段階へのロールバック要求の処理

