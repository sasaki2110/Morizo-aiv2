# SessionService分割アプローチ案

## 現状分析

### ファイル構成（614行）
- **基本CRUD操作** (約200行): create, get, update, delete, cleanup
- **ヘルパーメソッド** (約60行): _call_session_method, _call_session_void_method
- **確認状態管理** (約110行): save/get/clear_confirmation_state
- **提案レシピ管理** (約40行): add/get_proposed_recipes
- **候補情報管理** (約40行): set/get_candidates
- **セッションコンテキスト** (約40行): set/get_session_context
- **段階管理** (約80行): get_current_stage, set/get_selected_recipe, get_used_ingredients, get_menu_category

### 使用状況
- シングルトンパターンで実装されている
- 約20ファイルから`session_service`が使用されている
- 後方互換性のため`services/session_service.py`からリダイレクト

---

## アプローチ1: Mixinパターン（推奨度：⭐⭐⭐）

### 概要
機能ごとにMixinクラスを作成し、SessionServiceに合成する。

### 構造
```
services/session/
├── __init__.py
├── service.py (メイン - シングルトン管理のみ)
├── mixins/
│   ├── __init__.py
│   ├── crud_mixin.py (基本CRUD操作)
│   ├── confirmation_mixin.py (確認状態管理)
│   ├── proposal_mixin.py (提案レシピ管理)
│   ├── candidate_mixin.py (候補情報管理)
│   ├── context_mixin.py (セッションコンテキスト)
│   └── stage_mixin.py (段階管理)
└── helpers.py (ヘルパーメソッド)
```

### メリット
- ✅ 機能が明確に分離される
- ✅ 後方互換性を維持しやすい（同じインターフェース）
- ✅ テストが書きやすい（各Mixinを独立してテスト可能）
- ✅ 既存コードの変更が最小限

### デメリット
- ⚠️ クラス継承の複雑さが増す
- ⚠️ メソッド解決順序（MRO）の理解が必要

### 実装イメージ
```python
# services/session/mixins/crud_mixin.py
class SessionCRUDMixin:
    """基本CRUD操作"""
    async def create_session(self, ...): ...
    async def get_session(self, ...): ...
    # ...

# services/session/service.py
class SessionService(
    SessionCRUDMixin,
    ConfirmationMixin,
    ProposalMixin,
    CandidateMixin,
    ContextMixin,
    StageMixin
):
    """セッション管理サービス（シングルトン）"""
    _instance = None
    # ...
```

---

## アプローチ2: コンポジションパターン（推奨度：⭐⭐⭐⭐）

### 概要
各機能を独立したクラスに分離し、SessionServiceがそれらを組み合わせて使用する。

### 構造
```
services/session/
├── __init__.py
├── service.py (メイン - コンポジション管理)
├── crud_manager.py (基本CRUD操作)
├── confirmation_manager.py (確認状態管理)
├── proposal_manager.py (提案レシピ管理)
├── candidate_manager.py (候補情報管理)
├── context_manager.py (セッションコンテキスト)
├── stage_manager.py (段階管理)
└── helpers.py (ヘルパーメソッド)
```

### メリット
- ✅ 各クラスが独立しており、理解しやすい
- ✅ 依存関係が明確
- ✅ 将来的に一部を置き換えやすい
- ✅ テストが容易（各マネージャーを独立してテスト）

### デメリット
- ⚠️ 各マネージャーがSessionへのアクセス方法を統一する必要がある
- ⚠️ メソッド呼び出しが1層深くなる（`service.crud.create_session`）

### 実装イメージ
```python
# services/session/crud_manager.py
class SessionCRUDManager:
    def __init__(self, session_service):
        self.session_service = session_service
    
    async def create_session(self, user_id, session_id=None):
        # self.session_service.user_sessions を使用
        # ...

# services/session/service.py
class SessionService:
    def __init__(self):
        self.crud = SessionCRUDManager(self)
        self.confirmation = ConfirmationManager(self)
        self.proposal = ProposalManager(self)
        # ...
    
    # 後方互換性のためのラッパー
    async def create_session(self, *args, **kwargs):
        return await self.crud.create_session(*args, **kwargs)
```

---

## アプローチ3: モジュール分割（機能別ファイル分割）（推奨度：⭐⭐）

### 概要
機能ごとに完全に別ファイルに分割し、SessionServiceは薄いラッパーとして機能。

### 構造
```
services/session/
├── __init__.py
├── service.py (薄いラッパー - 50行程度)
├── crud.py (基本CRUD操作)
├── confirmation.py (確認状態管理)
├── proposal.py (提案レシピ管理)
├── candidate.py (候補情報管理)
├── context.py (セッションコンテキスト)
├── stage.py (段階管理)
└── helpers.py (ヘルパーメソッド)
```

### メリット
- ✅ ファイルが小さく、各ファイルの責任が明確
- ✅ インポートが明確

### デメリット
- ⚠️ 各モジュール間でSessionストレージ（user_sessions）を共有する方法が必要
- ⚠️ グローバル状態管理が複雑になる可能性
- ⚠️ 後方互換性のためラッパーが必要（結局service.pyが大きくなる可能性）

### 実装イメージ
```python
# services/session/crud.py
_session_storage = {}  # グローバル状態

async def create_session(user_id, session_id=None):
    # _session_storageを使用
    # ...

# services/session/service.py
from . import crud, confirmation, proposal, ...

class SessionService:
    async def create_session(self, *args, **kwargs):
        return await crud.create_session(*args, **kwargs)
```

---

## アプローチ4: 現状維持 + 内部整理（推奨度：⭐⭐⭐⭐⭐）

### 概要
ファイル分割は行わず、内部でメソッドをグループ化し、コメントで明確化。将来的な分割を容易にする。

### 実装
- メソッドを機能グループごとに整理（物理的な順序変更）
- 各グループに明確なコメントセクションを追加
- プライベートヘルパーを明確にマーク
- 将来的な分割に向けた準備（メソッドの依存関係を明確化）

### メリット
- ✅ リスクが最小
- ✅ 既存コードへの影響がゼロ
- ✅ 理解しやすくなる（コメントで明確化）
- ✅ 将来的に分割する際の準備になる

### デメリット
- ⚠️ ファイルサイズは変わらない
- ⚠️ 物理的な分割は行わない

---

## アプローチ5: Facadeパターン（推奨度：⭐⭐⭐）

### 概要
SessionServiceをFacadeとして残し、実際の実装を内部クラスまたはサブモジュールに分割。

### 構造
```
services/session/
├── __init__.py
├── service.py (Facade - 薄いラッパー)
├── impl/
│   ├── __init__.py
│   ├── base.py (基本実装 - user_sessions管理)
│   ├── crud.py (CRUD操作)
│   ├── confirmation.py (確認状態管理)
│   └── ...
```

### メリット
- ✅ 外部インターフェースを変更しない
- ✅ 内部実装を自由に分割できる
- ✅ 段階的にリファクタリング可能

### デメリット
- ⚠️ 内部実装へのアクセス方法を設計する必要がある

---

## 推奨アプローチ比較

| アプローチ | 難易度 | リスク | 効果 | 後方互換性 | 推奨度 |
|-----------|--------|--------|------|------------|--------|
| 1. Mixin | 中 | 低 | 高 | ✅ | ⭐⭐⭐ |
| 2. コンポジション | 中 | 中 | 高 | ✅ | ⭐⭐⭐⭐ |
| 3. モジュール分割 | 高 | 高 | 中 | ⚠️ | ⭐⭐ |
| 4. 現状維持+整理 | 低 | 最低 | 中 | ✅ | ⭐⭐⭐⭐⭐ |
| 5. Facade | 中 | 低 | 高 | ✅ | ⭐⭐⭐ |

---

## 具体的な推奨：アプローチ2（コンポジション）+ 段階的移行

### Phase 1: 内部リファクタリング（現状維持）
- メソッドを機能グループごとに整理
- コメントセクションを追加
- プライベートヘルパーを明確化

### Phase 2: マネージャークラスの作成（並行運用）
- 各機能を独立したマネージャークラスに抽出
- SessionServiceでコンポジションとして使用開始
- 既存のメソッドはラッパーとして維持（後方互換性）

### Phase 3: 段階的移行
- 新しいコードからは`session_service.crud.create_session()`形式を使用
- 既存コードは`session_service.create_session()`のまま（ラッパー経由）
- すべての移行が完了したら、ラッパーを削除可能

### 利点
- リスクが分散される
- 後方互換性を維持しながら改善できる
- 段階的に移行できる

---

## 注意事項

1. **シングルトンパターン**: どのアプローチでもシングルトンは維持する必要がある
2. **user_sessionsの管理**: 全機能で共有するストレージの設計が重要
3. **既存コードへの影響**: 約20ファイルで使用されているため、後方互換性が必須
4. **テスト**: リファクタリング前後でテストカバレッジを確認

---

## 結論

**まずはアプローチ4（現状維持+内部整理）から始めることを推奨**

理由：
- リスクが最小
- 即座に理解しやすくなる
- 将来的な分割の準備になる
- 既存コードへの影響がゼロ

その後、必要に応じてアプローチ2（コンポジション）へ段階的に移行するのが現実的です。

