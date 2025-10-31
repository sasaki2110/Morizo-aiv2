# Phase 5C-2: 重複警告計算機能

## 概要

過去に保存した献立履歴に対して、重複警告を計算する機能を実装します。主菜・副菜は14日前、汁物は昨日の重複をチェックします。

## 背景

### worries.mdの要件

- **主菜・副菜**: 2週間程度重複を避けたい
- **汁物**: 昨日と同じでなければ、ある程度重複しても良い

### 重複警告の計算ロジック

- **主菜・副菜**: 過去14日間で同じタイトルが使用されていた場合、「X日前に使用」と表示
- **汁物**: 昨日同じタイトルが使用されていた場合、「昨日使用」と表示

## 実装方針

重複警告はバックエンドで計算し、APIレスポンスに含める方式を採用します。

**理由**:
- 計算ロジックをバックエンドに集約できる
- フロントエンドの処理がシンプルになる
- 将来的に重複判定ロジックを変更する場合、バックエンドのみ修正すれば良い

## 対象範囲

- `/app/Morizo-aiv2/api/routes/menu.py` (Phase 5C-1の拡張)

## 実装計画

### 1. 重複警告計算関数の実装

**修正する場所**: `/app/Morizo-aiv2/api/routes/menu.py`

**実装内容**:

```python
def calculate_duplicate_warnings(
    history_entries: List[Dict[str, Any]],
    current_date: datetime
) -> Dict[str, Dict[str, str]]:
    """重複警告を計算
    
    Args:
        history_entries: 履歴エントリのリスト（全期間）
        current_date: 現在の日付
    
    Returns:
        Dict[date, Dict[title, warning_message]]: 重複警告の辞書
    """
    warnings = {}
    
    # 主菜・副菜用: 過去14日間の重複をチェック
    cutoff_date_main_sub = current_date - timedelta(days=14)
    
    # 汁物用: 昨日の重複をチェック
    yesterday = (current_date - timedelta(days=1)).date()
    
    # 各日付の履歴を処理
    for entry in history_entries:
        date = entry["date"]
        date_obj = datetime.fromisoformat(date).date()
        
        if date not in warnings:
            warnings[date] = {}
        
        for recipe in entry["recipes"]:
            category = recipe.get("category")
            title = recipe["title"]
            
            if not category:
                continue
            
            # 主菜・副菜の場合: 14日前の重複をチェック
            if category in ["main", "sub"]:
                # 同じタイトルが過去14日間に存在するかチェック
                for other_entry in history_entries:
                    other_date = datetime.fromisoformat(other_entry["date"]).date()
                    
                    # 同じ日付はスキップ
                    if other_date == date_obj:
                        continue
                    
                    # 14日以内で、かつその日より前の日付
                    if cutoff_date_main_sub.date() <= other_date < date_obj:
                        for other_recipe in other_entry["recipes"]:
                            if (other_recipe.get("category") == category and 
                                other_recipe["title"] == title):
                                days_ago = (date_obj - other_date).days
                                warnings[date][title] = f"{days_ago}日前に使用"
                                break
                        
                        if title in warnings[date]:
                            break
            
            # 汁物の場合: 昨日の重複をチェック
            elif category == "soup":
                # 昨日同じタイトルが使用されていたかチェック
                for other_entry in history_entries:
                    other_date = datetime.fromisoformat(other_entry["date"]).date()
                    
                    if other_date == yesterday:
                        for other_recipe in other_entry["recipes"]:
                            if (other_recipe.get("category") == "soup" and 
                                other_recipe["title"] == title):
                                warnings[date][title] = "昨日使用"
                                break
                        
                        if title in warnings[date]:
                            break
    
    return warnings
```

### 2. APIエンドポイントへの統合

**修正する場所**: `/app/Morizo-aiv2/api/routes/menu.py`

**修正内容**:

`get_menu_history`エンドポイントで、重複警告を計算してレスポンスに含める：

```python
@router.get("/menu/history", response_model=MenuHistoryResponse)
async def get_menu_history(
    days: int = 14,
    category: Optional[str] = None,
    http_request: Request = None
):
    """献立履歴を取得するエンドポイント"""
    try:
        # ... 既存の処理（履歴取得、日付別グループ化） ...
        
        # 重複警告を計算
        current_date = datetime.now()
        duplicate_warnings = calculate_duplicate_warnings(
            sorted_history, current_date
        )
        
        # 重複警告を各レシピに追加
        for entry in sorted_history:
            date = entry["date"]
            if date in duplicate_warnings:
                for recipe in entry["recipes"]:
                    title = recipe["title"]
                    if title in duplicate_warnings[date]:
                        recipe["duplicate_warning"] = duplicate_warnings[date][title]
        
        return MenuHistoryResponse(
            success=True,
            data=sorted_history
        )
    except Exception as e:
        # エラーハンドリング
        ...
```

### 3. レスポンスモデルの拡張

**修正する場所**: `/app/Morizo-aiv2/api/models.py`

**修正内容**:

```python
class HistoryRecipe(BaseModel):
    """履歴レシピ情報"""
    category: Optional[str]
    title: str
    source: str
    url: Optional[str]
    history_id: str
    duplicate_warning: Optional[str] = None  # 新規追加
```

## 実装のポイント

### 1. パフォーマンス

- 重複チェックはO(n²)の計算量になる可能性がある
- 履歴が多い場合は最適化を検討（インデックス、キャッシュ等）

### 2. 日付の比較

- 日付の比較が正確に行われること
- タイムゾーンを考慮すること

### 3. 重複判定のロジック

- **主菜・副菜**: 14日前から現在までの範囲でチェック
- **汁物**: 昨日のみチェック
- 同じ日付内のレシピは重複として扱わない

## テスト項目

### 単体テスト

1. **重複警告計算関数**
   - 主菜・副菜の14日前重複チェック
   - 汁物の昨日重複チェック
   - 重複がない場合の処理
   - 複数の重複がある場合の処理

2. **APIエンドポイント**
   - 重複警告がレスポンスに含まれること
   - 警告がない場合も正しく動作すること

### 統合テスト

1. **Phase 5C-1との統合**
   - 履歴取得と重複警告計算が正しく動作すること
   - レスポンス形式が正しいこと

## 期待される効果

- 重複警告が自動的に計算される
- フロントエンドで警告を表示できる
- ユーザーが重複を視覚的に確認できる

## 次のフェーズ

- **Phase 5C-3**: フロントエンドUI実装

