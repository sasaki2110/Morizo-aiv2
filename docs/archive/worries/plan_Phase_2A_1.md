# Phase 2A-1: 基本実装（改訂版）

## 概要

ユーザー選択機能のバックエンド基盤の基礎部分を実装します。既存の確認プロセスの仕組みを活用し、ContextManagerにコンテキスト保存機能を追加します。単体テストで各機能を個別に検証します。

## Phase 2A-1の位置づけ

このフェーズでは「**ユーザー選択の基盤**」のみを実装します。

**実装範囲:**
- ✅ ユーザー選択待ちの状態管理
- ✅ コンテキスト保存・読み込み機能
- ✅ 既存の一時停止機構との統合

**実装しない機能:**
- 🔜 **Phase 2A-2**: エージェント・API統合
- 🔜 **Phase 2B**: フロントエンド連携
- 🔜 **Phase 3**: 副菜・汁物の段階的選択
- 🔜 **Phase 4**: ロールバック機能
- 🔜 **Phase 5**: 履歴管理（2週間重複回避）

## 対象範囲

- TaskStatusの拡張（WAITING_FOR_USER状態の追加）
- ContextManagerの拡張（コンテキスト保存・読み込み機能）
- 既存の一時停止機構の活用（TaskChainManagerの変更なし）
- 単体テスト（各機能を個別に検証）

## 実装計画

### 1. TaskStatusの拡張

**修正する場所**: `core/models.py` (10-15行目)

**修正する内容**:
```python
class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_USER = "waiting_for_user"  # 新規追加
```

**修正の理由**: ユーザー選択待ちの状態を明示的に管理するため

**修正の影響**: 既存のタスク状態管理に影響なし（新しい状態を追加するのみ）

**前回プランとの違い**: `PAUSED`は不要（既存の`is_paused`フラグで対応）

---

### 2. TaskChainManagerの扱い

**修正する場所**: なし

**理由**: 既存の`pause_for_confirmation()`と`resume_execution()`を活用するため、新しいメソッドは不要

**使用方法**:
```python
# ユーザー選択待ちの場合
task_chain_manager.pause_for_confirmation()  # 既存メソッドを活用
task_chain_manager.update_task_status(task_id, TaskStatus.WAITING_FOR_USER)

# ユーザー選択後
task_chain_manager.resume_execution()  # 既存メソッドを活用
```

**前回プランとの違い**: 
- `pause_task_for_user_selection()`メソッドは追加しない
- `resume_task_after_selection()`メソッドは追加しない
- `paused_contexts`属性は追加しない（ContextManagerが責任を持つ）

---

### 3. ContextManagerの拡張

**修正する場所**: `core/context_manager.py`

**修正する内容**:

#### 3.1 一時停止コンテキスト管理用の属性追加
```python
class ContextManager:
    """コンテキスト管理クラス"""
    
    def __init__(self, sse_session_id: str):
        self.sse_session_id = sse_session_id
        self.context = {}
        self.logger = GenericLogger("core", "context_manager")
        
        # 新規追加: ユーザー選択用の一時停止コンテキスト
        self.paused_contexts: Dict[str, Dict[str, Any]] = {}
        self.context_ttl = 3600  # 1時間でタイムアウト
```

#### 3.2 コンテキスト保存機能
```python
def save_context_for_resume(self, task_id: str, context: dict) -> dict:
    """再開用にコンテキストを保存"""
    try:
        import time
        
        # タイムスタンプを追加
        context['paused_at'] = time.time()
        
        # コンテキストを保存
        self.paused_contexts[task_id] = context.copy()
        
        self.logger.info(f"💾 [ContextManager] Context saved for task {task_id}")
        return {"success": True}
        
    except Exception as e:
        self.logger.error(f"❌ [ContextManager] Failed to save context for task {task_id}: {e}")
        return {"success": False, "error": str(e)}
```

#### 3.3 コンテキスト読み込み機能
```python
def load_context_for_resume(self, task_id: str) -> Optional[dict]:
    """再開用のコンテキストを読み込み"""
    try:
        import time
        
        if task_id not in self.paused_contexts:
            self.logger.warning(f"⚠️ [ContextManager] No context found for task {task_id}")
            return None
        
        context = self.paused_contexts.pop(task_id)
        
        # タイムアウトチェック
        if time.time() - context.get('paused_at', 0) > self.context_ttl:
            self.logger.warning(f"⚠️ [ContextManager] Context for task {task_id} has expired")
            return None
        
        self.logger.info(f"📂 [ContextManager] Context loaded for task {task_id}")
        return context
        
    except Exception as e:
        self.logger.error(f"❌ [ContextManager] Failed to load context for task {task_id}: {e}")
        return None
```

**修正の理由**: 一時停止中のコンテキストを管理する責任をContextManagerに集約するため

**修正の影響**: 既存のコンテキスト管理機能に影響なし

**前回プランとの違い**: コンテキスト保存の責任がContextManagerに一元化（TaskChainManagerとの重複なし）

---

## テスト計画

### 1. TaskStatus拡張テスト

**テストファイル**: `tests/phase2a1/test_01_task_status_extension.py`

**テストケース**:
- 新しい状態（`WAITING_FOR_USER`）が正しく定義されているか
- 状態の文字列表現が正しいか
- 既存の状態に影響がないか

### 2. ContextManager拡張テスト

**テストファイル**: `tests/phase2a1/test_02_context_save_load.py`

**テストケース**:
- `save_context_for_resume()`: コンテキストが正しく保存されるか
- `load_context_for_resume()`: コンテキストが正しく読み込まれるか
- タイムアウト処理が正しく動作するか
- エラーハンドリングが正しく動作するか
- 既存のコンテキスト管理機能に影響がないか

### 3. 統合テスト

**テストファイル**: `tests/phase2a1/test_03_pause_resume_integration.py`

**テストケース**:
- 既存の`pause_for_confirmation()`とContextManagerの連携が正しく動作するか
- 既存の`resume_execution()`とContextManagerの連携が正しく動作するか
- タスク状態とコンテキスト保存の整合性が取れているか

---

## 実装順序

1. TaskStatusの拡張（Enum定義に1行追加）
2. ContextManagerの拡張（保存・読み込みメソッド追加）
3. 単体テスト実装（3ファイル）
4. テスト実行・検証

---

## 期待される効果

- ユーザー選択機能の基盤が完成
- 既存の確認プロセスとの一貫性を保持
- Phase 2A-2での統合実装の準備が整う
- コンテキスト管理の責任が明確化

---

## 制約事項

- エージェントやAPI層の修正は含まない（Phase 2A-2で実施）
- 既存の確認プロセスとの統合は行わない（Phase 2A-2で実施）
- フロントエンドの修正は含まない（Phase 2Bで実施）
- Phase 1の機能を破壊しない

---

## 成功基準

- すべての単体テストが成功
- 既存のテストが引き続き成功（回帰テストOK）
- コンテキストの保存・読み込みが正常に動作
- 既存の一時停止機構との統合が正常に動作

---

## 前回プランからの主要な変更点

### **1. TaskChainManagerの変更を削除**
- `pause_task_for_user_selection()`メソッドは追加しない
- `resume_task_after_selection()`メソッドは追加しない
- `paused_contexts`属性は追加しない
- 既存の`pause_for_confirmation()`と`resume_execution()`を活用

### **2. TaskStatusの簡素化**
- `PAUSED`状態は追加しない（既存の`is_paused`フラグで対応）
- `WAITING_FOR_USER`のみ追加

### **3. 責任の明確化**
- コンテキスト保存: ContextManagerに一元化
- 一時停止フラグ: TaskChainManagerの既存機能を活用
- 重複設計を排除

### **4. 既存パターンの踏襲**
- 確認プロセスと同じ仕組みを活用
- シンプルで一貫性のある設計
- 既存コードとの整合性が高い

---

## 次のステップ

Phase 2A-1完了後、Phase 2A-2（統合実装）に進みます。Phase 2A-2では、TrueReactAgentとAPI層を拡張し、エンドツーエンドでユーザー選択機能が動作するようにします。
