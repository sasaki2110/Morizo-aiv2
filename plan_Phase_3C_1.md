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

## 期待される効果

- 段階的選択の状態を管理できる
- 選択したレシピの履歴を保持
- 使用済み食材を追跡

