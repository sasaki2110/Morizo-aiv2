# 食材削除機能 実装プラン（概要）

## 概要

採用したレシピで利用した食材をリストし、選択された食材を削除（あるいは数量をマイナスし更新）する機能を実装します。

## 実装方針

### デグレード防止の原則

1. **後方互換性の維持**: 既存の機能に影響を与えない
2. **段階的実装**: 小さな単位で実装し、各段階で動作確認
3. **オプショナルな拡張**: 食材情報がない場合でも既存機能は動作する
4. **デフォルト値の設定**: 新規カラムはデフォルト値を持つ

## 実装フェーズ概要

### Phase 1: 食材情報の保持と保存（バックエンド）
- **Phase 1A**: 段階提案での食材保持と保存
- **Phase 1B**: 献立提案での食材保持と保存
- **Phase 1C**: 提案レスポンスに食材情報を含める

### Phase 2: 食材削除API（バックエンド）
- **Phase 2A**: 1日分のレシピから利用食材を集約するAPI
- **Phase 2B**: 在庫更新API（既存APIを使用）

### Phase 3: レシピ履歴のingredients_deletedフラグ更新

### Phase 4: フロントエンド実装

## 実装セッション分割

このプランは以下の5つのセッションに分割して実装します：

1. **セッション1**: Phase 1A（段階提案での食材保持と保存）
   - 詳細: [INVENTORY_DELETE_SESSION1.md](./INVENTORY_DELETE_SESSION1.md)

2. **セッション2**: Phase 1B + Phase 1C（献立提案と提案レスポンス）
   - 詳細: [INVENTORY_DELETE_SESSION2.md](./INVENTORY_DELETE_SESSION2.md)

3. **セッション3**: Phase 2A（食材集約API）
   - 詳細: [INVENTORY_DELETE_SESSION3.md](./INVENTORY_DELETE_SESSION3.md)

4. **セッション4**: Phase 2B + Phase 3（在庫更新とフラグ更新）
   - 詳細: [INVENTORY_DELETE_SESSION4.md](./INVENTORY_DELETE_SESSION4.md)

5. **セッション5**: Phase 4（フロントエンド実装）
   - 詳細: [INVENTORY_DELETE_SESSION5.md](./INVENTORY_DELETE_SESSION5.md)

## 実装順序と依存関係

```
Phase 1A (段階提案での食材保持と保存)
  ↓
Phase 1B (献立提案での食材保持と保存)
  ↓
Phase 1C (提案レスポンスに食材情報を含める)
  ↓
Phase 2A (1日分のレシピから利用食材を集約するAPI)
  ↓
Phase 2B (在庫更新API)
  ↓
Phase 3 (レシピ履歴のingredients_deletedフラグ更新)
  ↓
Phase 4 (フロントエンド実装)
```

## データモデル

### リクエスト/レスポンスモデル

**新規追加が必要なモデル**:

```python
# api/models/requests.py
class IngredientDeleteRequest(BaseModel):
    """食材削除リクエスト"""
    date: str = Field(..., description="日付（YYYY-MM-DD形式）")
    ingredients: List[IngredientDeleteItem] = Field(..., description="削除対象食材リスト")

class IngredientDeleteItem(BaseModel):
    """削除対象食材アイテム"""
    item_name: str = Field(..., description="食材名")
    quantity: float = Field(0, description="更新後の数量（0で削除）")
    inventory_id: Optional[str] = Field(None, description="在庫ID（指定がある場合）")
```

```python
# api/models/responses.py
class IngredientDeleteCandidate(BaseModel):
    """削除候補食材"""
    inventory_id: str = Field(..., description="在庫ID")
    item_name: str = Field(..., description="食材名")
    current_quantity: float = Field(..., description="現在の数量")
    unit: str = Field(..., description="単位")

class IngredientDeleteCandidatesResponse(BaseModel):
    """削除候補食材レスポンス"""
    success: bool
    date: str
    candidates: List[IngredientDeleteCandidate]

class IngredientDeleteResponse(BaseModel):
    """食材削除レスポンス"""
    success: bool
    deleted_count: int
    updated_count: int
    failed_items: List[str]
```

## 注意事項

1. **食材名のマッチング**
   - 表記ゆれ（「レンコン」と「れんこん」など）に対応
   - 既存の`IngredientMapperComponent`を活用

2. **複数在庫の処理**
   - 初期実装では「すべて更新」とする
   - 将来的には「最新のみ」「最古のみ」などの選択肢を追加可能

3. **パフォーマンス**
   - 1日分のレシピから食材を集約する処理は軽量
   - 在庫一覧取得は既存APIを使用

4. **エラーハンドリング**
   - 在庫に存在しない食材はエラーではなく警告として扱う
   - 一部の食材削除に失敗しても、成功した分は反映

## 実装後の確認事項

1. **既存機能の動作確認**
   - レシピ履歴の保存・取得
   - 在庫管理機能
   - 段階提案・献立提案

2. **新機能の動作確認**
   - 食材情報の保存
   - 食材削除機能
   - 削除済み表示

3. **パフォーマンス確認**
   - 食材集約APIのレスポンス時間
   - 食材削除APIのレスポンス時間
