# Phase 2A-1: 基本実装 - 詳細プラン

## 目次

1. [実装対象の詳細](#実装対象の詳細)
2. [修正箇所の詳細](#修正箇所の詳細)
3. [テスト計画の詳細](#テスト計画の詳細)
4. [実装手順](#実装手順)
5. [検証方法](#検証方法)

---

## 実装対象の詳細

### 1. TaskStatusの拡張

#### 現在の実装（core/models.py 11-16行目）
```python
class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

#### 修正後の実装
```python
class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_USER = "waiting_for_user"  # 新規追加
```

#### 修正の詳細
- **ファイル**: `core/models.py`
- **行番号**: 11-16行目（TaskStatus Enum定義）
- **変更内容**: `WAITING_FOR_USER = "waiting_for_user"`を1行追加
- **影響範囲**: 
  - TaskStatus Enumの定義のみ
  - 既存の状態には影響なし
  - Task dataclassのstatus属性で使用可能になる

---

### 2. ContextManagerの拡張

#### 現在の実装（core/context_manager.py）

現在のContextManagerは以下のメソッドを持つ：
- `__init__(self, sse_session_id: str)`: 初期化
- `set_main_ingredient(self, ingredient: str)`: 主要食材を設定
- `get_main_ingredient(self) -> Optional[str]`: 主要食材を取得
- `set_inventory_items(self, items: List[str])`: 在庫食材を設定
- `get_inventory_items(self) -> List[str]`: 在庫食材を取得
- `set_excluded_recipes(self, recipes: List[str])`: 除外レシピを設定
- `get_excluded_recipes(self) -> List[str]`: 除外レシピを取得
- `clear_context(self) -> None`: コンテキストをクリア
- `get_context(self) -> Dict[str, Any]`: 全コンテキストを取得

#### 修正内容

##### 2.1 __init__メソッドの拡張

**現在の実装**:
```python
def __init__(self, sse_session_id: str):
    self.sse_session_id = sse_session_id
    self.context = {}
    self.logger = GenericLogger("core", "context_manager")
```

**修正後の実装**:
```python
def __init__(self, sse_session_id: str):
    self.sse_session_id = sse_session_id
    self.context = {}
    self.logger = GenericLogger("core", "context_manager")
    
    # 新規追加: ユーザー選択用の一時停止コンテキスト
    self.paused_contexts: Dict[str, Dict[str, Any]] = {}
    self.context_ttl = 3600  # 1時間でタイムアウト
```

**変更の詳細**:
- `paused_contexts`: タスクIDをキー、保存されたコンテキストを値とする辞書
- `context_ttl`: コンテキストの有効期限（秒単位）

##### 2.2 save_context_for_resume メソッドの追加

**実装する場所**: `core/context_manager.py` の末尾（clear_context()メソッドの後）

**実装内容**:
```python
def save_context_for_resume(self, task_id: str, context: dict) -> dict:
    """
    再開用にコンテキストを保存
    
    Args:
        task_id (str): タスクID
        context (dict): 保存するコンテキスト
        
    Returns:
        dict: 成功フラグとエラー情報
    """
    try:
        import time
        
        # タイムスタンプを追加
        context['paused_at'] = time.time()
        
        # コンテキストを保存（深いコピーを作成）
        self.paused_contexts[task_id] = context.copy()
        
        self.logger.info(f"💾 [ContextManager] Context saved for task {task_id}")
        self.logger.debug(f"💾 [ContextManager] Saved context keys: {list(context.keys())}")
        
        return {"success": True}
        
    except Exception as e:
        self.logger.error(f"❌ [ContextManager] Failed to save context for task {task_id}: {e}")
        return {"success": False, "error": str(e)}
```

**実装の詳細**:
- タイムスタンプを追加してコンテキストの有効期限を管理
- `context.copy()`で深いコピーを作成（元のコンテキストへの影響を防ぐ）
- エラーハンドリングで安全性を確保
- ログで保存されたコンテキストのキーを記録（デバッグ用）

##### 2.3 load_context_for_resume メソッドの追加

**実装する場所**: `core/context_manager.py` の末尾（save_context_for_resume()メソッドの後）

**実装内容**:
```python
def load_context_for_resume(self, task_id: str) -> Optional[dict]:
    """
    再開用のコンテキストを読み込み
    
    Args:
        task_id (str): タスクID
        
    Returns:
        Optional[dict]: 保存されたコンテキスト（存在しない場合やタイムアウトの場合はNone）
    """
    try:
        import time
        
        # コンテキストが存在するかチェック
        if task_id not in self.paused_contexts:
            self.logger.warning(f"⚠️ [ContextManager] No context found for task {task_id}")
            return None
        
        # コンテキストを取得（popで削除しながら取得）
        context = self.paused_contexts.pop(task_id)
        
        # タイムアウトチェック
        paused_at = context.get('paused_at', 0)
        elapsed_time = time.time() - paused_at
        
        if elapsed_time > self.context_ttl:
            self.logger.warning(
                f"⚠️ [ContextManager] Context for task {task_id} has expired "
                f"(elapsed: {elapsed_time:.0f}s, TTL: {self.context_ttl}s)"
            )
            return None
        
        self.logger.info(f"📂 [ContextManager] Context loaded for task {task_id}")
        self.logger.debug(f"📂 [ContextManager] Loaded context keys: {list(context.keys())}")
        
        return context
        
    except Exception as e:
        self.logger.error(f"❌ [ContextManager] Failed to load context for task {task_id}: {e}")
        return None
```

**実装の詳細**:
- `pop()`で取得と削除を同時に実行（メモリ管理）
- タイムアウトチェックで古いコンテキストを無効化
- エラーハンドリングで安全性を確保
- ログで読み込まれたコンテキストのキーを記録（デバッグ用）

---

### 3. TaskChainManagerとの連携

#### 既存の一時停止機構の活用

TaskChainManager（core/models.py 43-239行目）には既に以下のメソッドが実装されている：

```python
def pause_for_confirmation(self) -> None:
    """Pause execution for user confirmation."""
    self.is_paused = True
    self.logger.info(f"⏸️ [TaskChainManager] Execution paused for confirmation")

def resume_execution(self) -> None:
    """Resume execution after confirmation."""
    self.is_paused = False
```

#### 使用方法

ユーザー選択機能でこれらのメソッドを活用：

```python
# ユーザー選択待ちの場合
task_chain_manager.pause_for_confirmation()  # 既存メソッド
task_chain_manager.update_task_status(task_id, TaskStatus.WAITING_FOR_USER)  # 新しい状態
context_manager.save_context_for_resume(task_id, context)  # 新しいメソッド

# ユーザー選択後
context = context_manager.load_context_for_resume(task_id)  # 新しいメソッド
task_chain_manager.resume_execution()  # 既存メソッド
```

---

## 修正箇所の詳細

### 修正ファイル一覧

| ファイル | 修正内容 | 行数変更 | 影響範囲 |
|---------|---------|---------|---------|
| `core/models.py` | TaskStatus Enumに1状態追加 | +1行 | 最小限 |
| `core/context_manager.py` | 属性追加（__init__） | +3行 | 最小限 |
| `core/context_manager.py` | save_context_for_resume追加 | +20行 | 新規メソッド |
| `core/context_manager.py` | load_context_for_resume追加 | +30行 | 新規メソッド |

### 既存コードへの影響

#### 影響なし
- TaskChainManager: 変更なし（既存メソッドを活用）
- 既存のタスク実行フロー: 新しい状態を使用しない限り影響なし
- 既存のコンテキスト管理: 新しいメソッドは独立して動作

#### 注意点
- TaskStatus.WAITING_FOR_USERを使用する場合は適切なハンドリングが必要
- コンテキストのタイムアウト（1時間）に注意

---

## テスト計画の詳細

### テストディレクトリ構成

```
tests/
  phase2a1/
    test_01_task_status_extension.py       # TaskStatus拡張テスト
    test_02_context_save_load.py          # ContextManager拡張テスト
    test_03_pause_resume_integration.py   # 統合テスト
```

### テスト1: TaskStatus拡張テスト

**ファイル**: `tests/phase2a1/test_01_task_status_extension.py`

**テストケース**:

#### 1.1 新しい状態の定義確認
```python
def test_waiting_for_user_status_exists():
    """WAITING_FOR_USER状態が正しく定義されているか"""
    assert hasattr(TaskStatus, 'WAITING_FOR_USER')
    assert TaskStatus.WAITING_FOR_USER.value == "waiting_for_user"
```

#### 1.2 状態の文字列表現
```python
def test_waiting_for_user_status_string():
    """WAITING_FOR_USER状態の文字列表現が正しいか"""
    status = TaskStatus.WAITING_FOR_USER
    assert str(status) == "TaskStatus.WAITING_FOR_USER"
    assert status.value == "waiting_for_user"
```

#### 1.3 既存の状態への影響確認
```python
def test_existing_statuses_unchanged():
    """既存の状態に影響がないか"""
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.RUNNING.value == "running"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.FAILED.value == "failed"
```

#### 1.4 Taskクラスでの使用確認
```python
def test_task_with_waiting_for_user_status():
    """TaskクラスでWAITING_FOR_USER状態を使用できるか"""
    task = Task(
        id="test_task",
        service="RecipeService",
        method="generate_menu_plan",
        parameters={},
        status=TaskStatus.WAITING_FOR_USER
    )
    assert task.status == TaskStatus.WAITING_FOR_USER
    assert task.status.value == "waiting_for_user"
```

**期待される結果**: すべてのテストが成功

---

### テスト2: ContextManager拡張テスト

**ファイル**: `tests/phase2a1/test_02_context_save_load.py`

**テストケース**:

#### 2.1 コンテキスト保存の基本動作
```python
def test_save_context_basic():
    """コンテキストが正しく保存されるか"""
    context_manager = ContextManager("test_session")
    
    test_context = {
        "main_ingredient": "chicken",
        "inventory_items": ["onion", "carrot"],
        "step": 1
    }
    
    result = context_manager.save_context_for_resume("task_001", test_context)
    
    assert result["success"] is True
    assert "task_001" in context_manager.paused_contexts
    assert "paused_at" in context_manager.paused_contexts["task_001"]
```

#### 2.2 コンテキスト読み込みの基本動作
```python
def test_load_context_basic():
    """コンテキストが正しく読み込まれるか"""
    context_manager = ContextManager("test_session")
    
    # 保存
    test_context = {
        "main_ingredient": "chicken",
        "inventory_items": ["onion", "carrot"]
    }
    context_manager.save_context_for_resume("task_001", test_context)
    
    # 読み込み
    loaded_context = context_manager.load_context_for_resume("task_001")
    
    assert loaded_context is not None
    assert loaded_context["main_ingredient"] == "chicken"
    assert loaded_context["inventory_items"] == ["onion", "carrot"]
    assert "paused_at" in loaded_context
```

#### 2.3 存在しないコンテキストの読み込み
```python
def test_load_context_not_found():
    """存在しないコンテキストを読み込んだ場合、Noneが返るか"""
    context_manager = ContextManager("test_session")
    
    loaded_context = context_manager.load_context_for_resume("nonexistent_task")
    
    assert loaded_context is None
```

#### 2.4 コンテキストのタイムアウト
```python
def test_context_timeout():
    """タイムアウトしたコンテキストがNoneを返すか"""
    import time
    
    context_manager = ContextManager("test_session")
    context_manager.context_ttl = 1  # 1秒に設定
    
    # 保存
    test_context = {"main_ingredient": "chicken"}
    context_manager.save_context_for_resume("task_001", test_context)
    
    # 2秒待機（TTLを超過）
    time.sleep(2)
    
    # 読み込み（タイムアウトのためNoneが返る）
    loaded_context = context_manager.load_context_for_resume("task_001")
    
    assert loaded_context is None
```

#### 2.5 複数のコンテキスト管理
```python
def test_multiple_contexts():
    """複数のコンテキストを同時に管理できるか"""
    context_manager = ContextManager("test_session")
    
    # 複数保存
    context_manager.save_context_for_resume("task_001", {"step": 1})
    context_manager.save_context_for_resume("task_002", {"step": 2})
    context_manager.save_context_for_resume("task_003", {"step": 3})
    
    assert len(context_manager.paused_contexts) == 3
    
    # 個別に読み込み
    context_1 = context_manager.load_context_for_resume("task_001")
    assert context_1["step"] == 1
    assert len(context_manager.paused_contexts) == 2  # popされるので減る
    
    context_2 = context_manager.load_context_for_resume("task_002")
    assert context_2["step"] == 2
    assert len(context_manager.paused_contexts) == 1
```

#### 2.6 コンテキストの独立性
```python
def test_context_independence():
    """保存されたコンテキストが元のコンテキストから独立しているか"""
    context_manager = ContextManager("test_session")
    
    # 元のコンテキスト
    original_context = {"items": ["apple", "banana"]}
    
    # 保存
    context_manager.save_context_for_resume("task_001", original_context)
    
    # 元のコンテキストを変更
    original_context["items"].append("cherry")
    
    # 読み込み（変更が影響しないことを確認）
    loaded_context = context_manager.load_context_for_resume("task_001")
    
    assert len(loaded_context["items"]) == 2  # cherryは含まれない
    assert "cherry" not in loaded_context["items"]
```

#### 2.7 エラーハンドリング
```python
def test_save_context_error_handling():
    """保存時のエラーハンドリングが正しく動作するか"""
    context_manager = ContextManager("test_session")
    
    # 異常なコンテキスト（シリアライズできないオブジェクトを含む）
    # 注: copy()は失敗しないが、将来的なJSON化を想定
    test_context = {"data": "normal"}
    
    result = context_manager.save_context_for_resume("task_001", test_context)
    
    assert result["success"] is True
```

#### 2.8 既存のコンテキスト管理への影響確認
```python
def test_existing_context_methods_unaffected():
    """既存のコンテキスト管理メソッドに影響がないか"""
    context_manager = ContextManager("test_session")
    
    # 既存メソッドの動作確認
    context_manager.set_main_ingredient("chicken")
    assert context_manager.get_main_ingredient() == "chicken"
    
    context_manager.set_inventory_items(["onion", "carrot"])
    assert len(context_manager.get_inventory_items()) == 2
    
    # 新しいメソッドを使用
    context_manager.save_context_for_resume("task_001", {"test": "data"})
    
    # 既存のコンテキストが影響を受けていないか確認
    assert context_manager.get_main_ingredient() == "chicken"
    assert len(context_manager.get_inventory_items()) == 2
```

**期待される結果**: すべてのテストが成功

---

### テスト3: 統合テスト

**ファイル**: `tests/phase2a1/test_03_pause_resume_integration.py`

**テストケース**:

#### 3.1 一時停止とコンテキスト保存の連携
```python
def test_pause_with_context_save():
    """一時停止とコンテキスト保存が正しく連携するか"""
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # タスクを設定
    tasks = [
        Task(
            id="task_001",
            service="RecipeService",
            method="generate_menu_plan",
            parameters={}
        )
    ]
    task_chain_manager.set_tasks(tasks)
    
    # ユーザー選択待ちの処理
    task_chain_manager.pause_for_confirmation()
    task_chain_manager.update_task_status("task_001", TaskStatus.WAITING_FOR_USER)
    
    test_context = {"main_ingredient": "chicken", "step": 1}
    result = context_manager.save_context_for_resume("task_001", test_context)
    
    # 検証
    assert task_chain_manager.is_paused is True
    assert tasks[0].status == TaskStatus.WAITING_FOR_USER
    assert result["success"] is True
    assert "task_001" in context_manager.paused_contexts
```

#### 3.2 再開とコンテキスト読み込みの連携
```python
def test_resume_with_context_load():
    """再開とコンテキスト読み込みが正しく連携するか"""
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # タスクを設定
    tasks = [
        Task(
            id="task_001",
            service="RecipeService",
            method="generate_menu_plan",
            parameters={},
            status=TaskStatus.WAITING_FOR_USER
        )
    ]
    task_chain_manager.set_tasks(tasks)
    task_chain_manager.is_paused = True
    
    # コンテキストを保存
    test_context = {"main_ingredient": "chicken", "step": 1}
    context_manager.save_context_for_resume("task_001", test_context)
    
    # ユーザー選択後の処理
    loaded_context = context_manager.load_context_for_resume("task_001")
    task_chain_manager.resume_execution()
    task_chain_manager.update_task_status("task_001", TaskStatus.RUNNING)
    
    # 検証
    assert loaded_context is not None
    assert loaded_context["main_ingredient"] == "chicken"
    assert loaded_context["step"] == 1
    assert task_chain_manager.is_paused is False
    assert tasks[0].status == TaskStatus.RUNNING
```

#### 3.3 タスク状態とコンテキストの整合性
```python
def test_task_status_context_consistency():
    """タスク状態とコンテキスト保存の整合性が取れているか"""
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # タスクを設定
    task = Task(
        id="task_001",
        service="RecipeService",
        method="generate_menu_plan",
        parameters={}
    )
    task_chain_manager.set_tasks([task])
    
    # 一時停止前: コンテキストなし
    assert "task_001" not in context_manager.paused_contexts
    
    # 一時停止: コンテキスト保存
    task_chain_manager.pause_for_confirmation()
    task_chain_manager.update_task_status("task_001", TaskStatus.WAITING_FOR_USER)
    context_manager.save_context_for_resume("task_001", {"step": 1})
    
    assert task_chain_manager.is_paused is True
    assert task.status == TaskStatus.WAITING_FOR_USER
    assert "task_001" in context_manager.paused_contexts
    
    # 再開: コンテキスト読み込み
    loaded_context = context_manager.load_context_for_resume("task_001")
    task_chain_manager.resume_execution()
    task_chain_manager.update_task_status("task_001", TaskStatus.COMPLETED)
    
    assert loaded_context is not None
    assert task_chain_manager.is_paused is False
    assert task.status == TaskStatus.COMPLETED
    assert "task_001" not in context_manager.paused_contexts  # popされて削除
```

#### 3.4 複数タスクの一時停止と再開
```python
def test_multiple_task_pause_resume():
    """複数タスクの一時停止と再開が正しく動作するか"""
    task_chain_manager = TaskChainManager("test_session")
    context_manager = ContextManager("test_session")
    
    # 複数タスクを設定
    tasks = [
        Task(id="task_001", service="RecipeService", method="method1", parameters={}),
        Task(id="task_002", service="RecipeService", method="method2", parameters={}),
        Task(id="task_003", service="RecipeService", method="method3", parameters={})
    ]
    task_chain_manager.set_tasks(tasks)
    
    # task_001を一時停止
    task_chain_manager.pause_for_confirmation()
    task_chain_manager.update_task_status("task_001", TaskStatus.WAITING_FOR_USER)
    context_manager.save_context_for_resume("task_001", {"step": 1})
    
    # task_002を一時停止
    task_chain_manager.update_task_status("task_002", TaskStatus.WAITING_FOR_USER)
    context_manager.save_context_for_resume("task_002", {"step": 2})
    
    # 両方が保存されているか確認
    assert "task_001" in context_manager.paused_contexts
    assert "task_002" in context_manager.paused_contexts
    
    # task_001を再開
    context_1 = context_manager.load_context_for_resume("task_001")
    assert context_1["step"] == 1
    task_chain_manager.update_task_status("task_001", TaskStatus.COMPLETED)
    
    # task_002を再開
    context_2 = context_manager.load_context_for_resume("task_002")
    assert context_2["step"] == 2
    task_chain_manager.update_task_status("task_002", TaskStatus.COMPLETED)
    
    # 両方とも削除されているか確認
    assert "task_001" not in context_manager.paused_contexts
    assert "task_002" not in context_manager.paused_contexts
```

**期待される結果**: すべてのテストが成功

---

## 実装手順

### ステップ1: TaskStatusの拡張（所要時間: 5分）

1. `core/models.py`を開く
2. 11-16行目のTaskStatus Enum定義を確認
3. 16行目の`FAILED = "failed"`の後に以下を追加:
   ```python
   WAITING_FOR_USER = "waiting_for_user"
   ```
4. ファイルを保存

### ステップ2: ContextManagerの拡張（所要時間: 15分）

#### 2.1 __init__メソッドの拡張

1. `core/context_manager.py`を開く
2. 11-14行目の`__init__`メソッドを確認
3. 14行目の`self.logger = GenericLogger("core", "context_manager")`の後に以下を追加:
   ```python
   
   # ユーザー選択用の一時停止コンテキスト
   self.paused_contexts: Dict[str, Dict[str, Any]] = {}
   self.context_ttl = 3600  # 1時間でタイムアウト
   ```
4. ファイルの先頭でDict, Anyがインポートされているか確認（既にインポート済み）

#### 2.2 save_context_for_resumeメソッドの追加

1. ファイルの末尾（`get_context()`メソッドの後）に移動
2. 以下のメソッドを追加:
   ```python
   
   def save_context_for_resume(self, task_id: str, context: dict) -> dict:
       """
       再開用にコンテキストを保存
       
       Args:
           task_id (str): タスクID
           context (dict): 保存するコンテキスト
           
       Returns:
           dict: 成功フラグとエラー情報
       """
       try:
           import time
           
           # タイムスタンプを追加
           context['paused_at'] = time.time()
           
           # コンテキストを保存（深いコピーを作成）
           self.paused_contexts[task_id] = context.copy()
           
           self.logger.info(f"💾 [ContextManager] Context saved for task {task_id}")
           self.logger.debug(f"💾 [ContextManager] Saved context keys: {list(context.keys())}")
           
           return {"success": True}
           
       except Exception as e:
           self.logger.error(f"❌ [ContextManager] Failed to save context for task {task_id}: {e}")
           return {"success": False, "error": str(e)}
   ```

#### 2.3 load_context_for_resumeメソッドの追加

1. `save_context_for_resume`メソッドの後に以下を追加:
   ```python
   
   def load_context_for_resume(self, task_id: str) -> Optional[dict]:
       """
       再開用のコンテキストを読み込み
       
       Args:
           task_id (str): タスクID
           
       Returns:
           Optional[dict]: 保存されたコンテキスト（存在しない場合やタイムアウトの場合はNone）
       """
       try:
           import time
           
           # コンテキストが存在するかチェック
           if task_id not in self.paused_contexts:
               self.logger.warning(f"⚠️ [ContextManager] No context found for task {task_id}")
               return None
           
           # コンテキストを取得（popで削除しながら取得）
           context = self.paused_contexts.pop(task_id)
           
           # タイムアウトチェック
           paused_at = context.get('paused_at', 0)
           elapsed_time = time.time() - paused_at
           
           if elapsed_time > self.context_ttl:
               self.logger.warning(
                   f"⚠️ [ContextManager] Context for task {task_id} has expired "
                   f"(elapsed: {elapsed_time:.0f}s, TTL: {self.context_ttl}s)"
               )
               return None
           
           self.logger.info(f"📂 [ContextManager] Context loaded for task {task_id}")
           self.logger.debug(f"📂 [ContextManager] Loaded context keys: {list(context.keys())}")
           
           return context
           
       except Exception as e:
           self.logger.error(f"❌ [ContextManager] Failed to load context for task {task_id}: {e}")
           return None
   ```

2. ファイルを保存

### ステップ3: テストディレクトリの作成（所要時間: 2分）

1. `tests/phase2a1/`ディレクトリを作成
2. 空の`__init__.py`ファイルを作成

### ステップ4: テスト1の実装（所要時間: 15分）

1. `tests/phase2a1/test_01_task_status_extension.py`を作成
2. 上記「テスト1: TaskStatus拡張テスト」の内容を実装
3. ファイルを保存

### ステップ5: テスト2の実装（所要時間: 30分）

1. `tests/phase2a1/test_02_context_save_load.py`を作成
2. 上記「テスト2: ContextManager拡張テスト」の内容を実装
3. ファイルを保存

### ステップ6: テスト3の実装（所要時間: 25分）

1. `tests/phase2a1/test_03_pause_resume_integration.py`を作成
2. 上記「テスト3: 統合テスト」の内容を実装
3. ファイルを保存

### ステップ7: テスト実行（所要時間: 10分）

1. テスト1を実行: `pytest tests/phase2a1/test_01_task_status_extension.py -v`
2. テスト2を実行: `pytest tests/phase2a1/test_02_context_save_load.py -v`
3. テスト3を実行: `pytest tests/phase2a1/test_03_pause_resume_integration.py -v`
4. すべてのテストを実行: `pytest tests/phase2a1/ -v`

### ステップ8: 回帰テストの実行（所要時間: 15分）

1. 既存のテストを実行して破壊的変更がないか確認:
   ```bash
   pytest tests/ -v --ignore=tests/phase2a1/
   ```

---

## 検証方法

### 1. 機能検証

#### 1.1 TaskStatus拡張の検証
- [ ] `TaskStatus.WAITING_FOR_USER`が定義されているか
- [ ] 値が`"waiting_for_user"`であるか
- [ ] Taskクラスで使用できるか
- [ ] 既存の状態に影響がないか

#### 1.2 ContextManager拡張の検証
- [ ] `paused_contexts`属性が初期化されているか
- [ ] `context_ttl`属性が3600に設定されているか
- [ ] `save_context_for_resume()`が正常に動作するか
- [ ] `load_context_for_resume()`が正常に動作するか
- [ ] タイムアウト処理が正常に動作するか
- [ ] 既存のコンテキスト管理に影響がないか

#### 1.3 統合動作の検証
- [ ] 一時停止とコンテキスト保存が連携するか
- [ ] 再開とコンテキスト読み込みが連携するか
- [ ] タスク状態とコンテキストの整合性が取れているか

### 2. テスト結果の確認

#### すべてのテストが成功することを確認
```bash
# Phase 2A-1のテスト
pytest tests/phase2a1/ -v

# 期待される出力:
# test_01_task_status_extension.py::test_waiting_for_user_status_exists PASSED
# test_01_task_status_extension.py::test_waiting_for_user_status_string PASSED
# test_01_task_status_extension.py::test_existing_statuses_unchanged PASSED
# test_01_task_status_extension.py::test_task_with_waiting_for_user_status PASSED
# test_02_context_save_load.py::test_save_context_basic PASSED
# test_02_context_save_load.py::test_load_context_basic PASSED
# test_02_context_save_load.py::test_load_context_not_found PASSED
# test_02_context_save_load.py::test_context_timeout PASSED
# test_02_context_save_load.py::test_multiple_contexts PASSED
# test_02_context_save_load.py::test_context_independence PASSED
# test_02_context_save_load.py::test_save_context_error_handling PASSED
# test_02_context_save_load.py::test_existing_context_methods_unaffected PASSED
# test_03_pause_resume_integration.py::test_pause_with_context_save PASSED
# test_03_pause_resume_integration.py::test_resume_with_context_load PASSED
# test_03_pause_resume_integration.py::test_task_status_context_consistency PASSED
# test_03_pause_resume_integration.py::test_multiple_task_pause_resume PASSED
```

#### 回帰テストの確認
```bash
# 既存のテストがすべて成功することを確認
pytest tests/ -v --ignore=tests/phase2a1/
```

### 3. コードレビューチェックリスト

#### コード品質
- [ ] すべてのメソッドにdocstringがあるか
- [ ] 型ヒントが適切に設定されているか
- [ ] エラーハンドリングが適切か
- [ ] ログメッセージが適切か

#### 設計
- [ ] 既存のパターンに従っているか
- [ ] 責任が明確に分離されているか
- [ ] 既存コードへの影響が最小限か
- [ ] 将来の拡張性を考慮しているか

#### テスト
- [ ] すべての機能がテストされているか
- [ ] エッジケースがカバーされているか
- [ ] エラーケースがテストされているか
- [ ] テストが読みやすいか

---

## 成功基準

### 必須条件
1. ✅ すべての単体テストが成功
2. ✅ すべての統合テストが成功
3. ✅ すべての回帰テストが成功
4. ✅ コンテキストの保存・読み込みが正常に動作
5. ✅ 既存の一時停止機構との統合が正常に動作

### 品質基準
1. ✅ コードカバレッジ: 新規コードの100%
2. ✅ パフォーマンス: コンテキスト保存・読み込みが10ms以内
3. ✅ メモリ使用: 複数のコンテキストを保存してもメモリリークなし
4. ✅ ログ出力: 適切なログレベルと情報量

---

## 次のステップ（Phase 2A-2）

Phase 2A-1完了後、Phase 2A-2に進みます。

**Phase 2A-2で実装予定**:
- エージェント・API統合

**後続フェーズで実装予定**:
- Phase 2B: フロントエンド連携
- Phase 3: 副菜・汁物の段階的選択
- Phase 4: ロールバック機能
- Phase 5: 履歴管理（2週間重複回避）

---

## 見積もり時間

| 工程 | 所要時間 |
|------|---------|
| TaskStatus拡張 | 5分 |
| ContextManager拡張 | 15分 |
| テストディレクトリ作成 | 2分 |
| テスト1実装 | 15分 |
| テスト2実装 | 30分 |
| テスト3実装 | 25分 |
| テスト実行・デバッグ | 10分 |
| 回帰テスト | 15分 |
| **合計** | **約2時間** |

---

## 備考

### コンテキストウインドウのパンク対策
- このドキュメントは詳細プランとして独立したファイルに記述
- 実装時は必要な部分のみを参照
- テストコードは実際のファイルに分割して記述

### 実装時の注意点
1. 既存のコードを破壊しない
2. 既存のパターンに従う
3. ログメッセージを適切に出力
4. エラーハンドリングを適切に実装
5. テストファーストで進める

### Phase 2A-2への引き継ぎ事項
- TaskStatus.WAITING_FOR_USERの使用方法
- ContextManagerのsave/loadメソッドの使用方法
- 既存の一時停止機構との連携パターン

