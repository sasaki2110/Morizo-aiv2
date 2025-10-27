# Phase 3C-1: セッション管理の拡張

## 概要

段階的選択のためのセッション情報を追加します。

## 対象範囲

- `services/session_service.py`

## 実装計画

**修正する場所**: `services/session_service.py`

**修正する内容**:

```python
class Session:
    """セッション管理クラス（拡張）"""
    
    # 既存フィールド
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    confirmation_context: Dict = {}
    
    # 新規フィールド（段階的選択用）
    current_stage: str = "main"  # "main", "sub", "soup"
    selected_main_dish: Optional[Dict] = None  # {"title": "...", "ingredients": [...]}
    selected_sub_dish: Optional[Dict] = None
    selected_soup: Optional[Dict] = None
    used_ingredients: List[str] = []  # 使用済み食材の累積
    menu_category: str = "japanese"  # "japanese", "western", "chinese"
```

**修正の理由**: 段階の状態管理が必要

**修正の影響**: 既存のセッション管理に新規フィールドを追加（後方互換）

---

## 実装手順

1. Sessionクラスに新規フィールドを追加
2. セッション取得・保存メソッドを更新
3. 既存セッションとの互換性を確保

---

## テスト

### 単体試験

#### Sessionクラスの拡張テスト
**テストファイル**: `tests/phase3c1/test_01_session_extensions.py`

**テスト項目**:
- 新規フィールドが正しく初期化されること
- 既存セッションとの互換性が保たれること
- セッション取得・保存が正常に動作すること

**テスト例**:
```python
def test_session_new_fields():
    """Sessionに新規フィールドが追加されていること"""
    session = Session(id="test", user_id="test_user")
    
    assert session.current_stage == "main"
    assert session.selected_main_dish is None
    assert session.selected_sub_dish is None
    assert session.selected_soup is None
    assert session.used_ingredients == []
    assert session.menu_category == "japanese"

def test_session_backward_compatibility():
    """既存セッションとの互換性テスト"""
    existing_session = {
        "id": "test",
        "user_id": "test_user",
        "confirmation_context": {}
    }
    session = Session(**existing_session)
    
    assert session.id == "test"
    assert session.user_id == "test_user"
    # 新規フィールドのデフォルト値
    assert session.current_stage == "main"
    assert session.menu_category == "japanese"
```

---

## 期待される効果

- 段階的選択の状態を管理できる
- 選択したレシピの履歴を保持
- 使用済み食材を追跡

