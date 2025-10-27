# Phase 2.5-2: テスト計画（回帰テスト基盤の確立）

## 目次

- [概要](#概要)
- [Phase 2.5F: バックエンド回帰テスト（HTTP リクエストベース）](#phase-25f-バックエンド回帰テストhttp-リクエストベース)
- [Phase 2.5G: フロントエンド確認リクエスト集の整備](#phase-25g-フロントエンド確認リクエスト集の整備)
- [関連ドキュメント](#関連ドキュメント)

---

## 概要

Phase 2.5 は**システムの根幹にかかわる**ため、破壊的活動の早期発見と早期解決のために回帰テストが不可欠です。

2種類の回帰テストが必要です：

1. **バックエンド確認**: サーバー起動状態（`python main.py`）で、HTTPリクエストを自動で投げるテスト
2. **フロント連動確認**: フロントエンド（/app/Morizo-web）の目視確認用テストシナリオ

---

## Phase 2.5F: バックエンド回帰テスト（HTTP リクエストベース）

**テストファイル**: `tests/phase2_5/test_backend_regression.py`

**目的**: 破壊的活動の早期発見のため、各パターンの HTTP リクエストを自動テスト

### テストパターン洗い出し

| # | パターン | リクエスト例 | 期待されるタスク | 曖昧性ケース |
|---|---------|-----------|--------------|------------|
| 1-1 | 在庫追加 | `POST /api/inventory {"message": "牛乳を2本追加して"}` | `inventory_service.add_inventory()` のみ | なし |
| 1-2 | 在庫削除（曖昧性あり） | `POST /api/inventory {"message": "牛乳を削除して"}` | 曖昧性検出 → 確認質問 | 複数の牛乳存在 |
| 1-3 | 在庫更新（全件） | `POST /api/inventory {"message": "牛乳を全部1本に変えて"}` | `update_inventory(strategy='by_name_all')` | なし |
| 2-1 | 献立生成 | `POST /api/recipes {"message": "献立を教えて"}` | 4段階タスク（menu） | なし |
| 3-1 | 主菜提案（食材指定） | `POST /api/recipes {"message": "レンコンの主菜を5件提案して"}` | 4段階タスク（main）、main_ingredient="レンコン" | なし |
| 3-2 | 主菜提案（食材未指定） | `POST /api/recipes {"message": "主菜を5件提案して"}` | 曖昧性検出 → 確認質問 | main_ingredient未指定 |
| 3-3 | 主菜提案（曖昧性解消） | `POST /api/recipes {"message": "主菜を5件提案して", "context": {"confirmation": "レンコンを指定する"}}` | 4段階タスク（main）、main_ingredient="レンコン" | - |
| 4-1 | 主菜追加提案 | `POST /api/recipes {"message": "もう5件主菜を提案して", "sse_session_id": "xxx"}` | 4段階タスク（main_additional）、在庫取得なし | なし |
| 4-2 | 主菜追加提案（セッションなし） | `POST /api/recipes {"message": "もう5件主菜を提案して"}` | 初回提案に切り替え | sse_session_id不在 |
| 6-1 | 副菜提案（セッションあり） | `POST /api/recipes {"message": "副菜を5件提案して", "session": {"used_ingredients": ["レンコン", "肉"]}}` | 4段階タスク（sub）、used_ingredients付与 | なし |
| 6-2 | 副菜提案（セッションなし） | `POST /api/recipes {"message": "副菜を5件提案して"}` | 曖昧性検出 → 確認質問 | used_ingredients不在 |
| 7-1 | 汁物提案（和食） | `POST /api/recipes {"message": "味噌汁を5件提案して", "session": {"used_ingredients": [...], "menu_category": "japanese"}}` | 4段階タスク（soup）、和食判定 | なし |
| 7-2 | 汁物提案（洋食） | `POST /api/recipes {"message": "スープを5件提案して", "session": {"used_ingredients": [...], "menu_category": "western"}}` | 4段階タスク（soup）、洋食判定 | なし |
| 8-1 | 副菜追加提案 | `POST /api/recipes {"message": "もう5件副菜を提案して", "sse_session_id": "xxx"}` | 4段階タスク（sub_additional） | なし |
| 9-1 | 汁物追加提案 | `POST /api/recipes {"message": "もう5件味噌汁を提案して", "sse_session_id": "xxx"}` | 4段階タスク（soup_additional） | なし |

### 実装イメージ

```python
import pytest
import requests

BASE_URL = "http://localhost:8000"

class TestBackendRegression:
    """バックエンド回帰テスト"""
    
    @pytest.mark.parametrize("test_case", [
        {
            "name": "在庫追加",
            "endpoint": "/api/inventory",
            "method": "POST",
            "data": {"message": "牛乳を2本追加して"},
            "expected_tasks": ["add_inventory"],
            "expected_ambiguity": None
        },
        {
            "name": "主菜提案（食材指定）",
            "endpoint": "/api/recipes",
            "method": "POST",
            "data": {"message": "レンコンの主菜を5件提案して"},
            "expected_tasks": ["get_inventory", "history_get_recent_titles", "generate_proposals", "search_recipes_from_web"],
            "expected_ambiguity": None
        },
        # ... 他のテストケース
    ])
    async def test_backend_pattern(self, test_case):
        """パターン別バックエンドテスト"""
        response = requests.post(
            f"{BASE_URL}{test_case['endpoint']}",
            json=test_case['data']
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # タスクチェーン検証
        if "tasks" in result:
            task_names = [task["method"] for task in result["tasks"]]
            assert set(test_case['expected_tasks']) == set(task_names)
        
        # 曖昧性検証
        if "ambiguity" in result:
            assert result["ambiguity"]["type"] == test_case['expected_ambiguity']
```

**修正の理由**: 破壊的活動の早期発見のため、Phase 2.5 の実装前後の回帰テストが必要

**修正の影響**: 新しいテストファイルを追加

---

## Phase 2.5G: フロントエンド確認リクエスト集の整備

**ファイル**: `tests/phase2_5/frontend_manual_tests.md`

**目的**: フロントエンド（/app/Morizo-web）の目視確認用テストシナリオを整備

### 手動テストシナリオ洗い出し

```markdown
# Phase 2.5 フロントエンド手動テストシナリオ

## パターン1: 在庫操作

### 1-1. 在庫追加
1. チャットで「牛乳を2本追加して」と入力
2. 送信
3. **確認**: 在庫に牛乳が2本追加される

### 1-2. 在庫削除（曖昧性）
1. 在庫に牛乳を複数登録
2. チャットで「牛乳を削除して」と入力
3. 送信
4. **確認**: 確認質問が表示される
5. 選択肢から一つ選ぶ
6. **確認**: 正しく削除される

## パターン2: 献立生成

### 2-1. 献立生成
1. 在庫に食材を登録
2. チャットで「献立を教えて」と入力
3. 送信
4. **確認**: main/sub/soup が表示される

## パターン3: 主菜提案（初回）

### 3-1. 主菜提案（食材指定）
1. 在庫にレンコンを登録
2. チャットで「レンコンの主菜を5件提案して」と入力
3. 送信
4. **確認**: レンコンの主菜が5件提案される

### 3-2. 主菜提案（食材未指定）
1. チャットで「主菜を5件提案して」と入力
2. 送信
3. **確認**: 確認質問が表示される
4. 「在庫から提案する」を選択
5. **確認**: 在庫から主菜が5件提案される

### 3-3. 主菜提案（曖昧性解消）
1. 「主菜を5件提案して」と入力
2. 確認質問で「レンコンを指定する」を選択
3. **確認**: レンコンの主菜が提案される

### 3-4. 主菜追加提案
1. 3-1を実行して主菜を提案
2. チャットで「もう5件主菜を提案して」と入力
3. 送信
4. **確認**: 別の5件が提案される

## パターン6: 副菜提案

### 6-1. 副菜提案（主菜選択後）
1. 主菜を選択
2. 自動的に副菜が提案される
3. **確認**: 主菜で使った食材が副菜に含まれない

### 6-2. 副菜提案（主菜未選択）
1. チャットで「副菜を5件提案して」と入力
2. 送信
3. **確認**: 確認質問が表示される

## パターン7: 汁物提案

### 7-1. 汁物提案（和食）
1. 主菜（和食）、副菜を選択
2. 自動的に味噌汁が提案される
3. **確認**: 和風の汁物が提案される

### 7-2. 汁物提案（洋食）
1. 主菜（洋食）、副菜を選択
2. 自動的にスープが提案される
3. **確認**: 洋風のスープが提案される

## パターン8-9: 追加提案
※ パターン3-4と同じ要領でテスト

---
```

**修正の理由**: フロントエンド（/app/Morizo-web）の目視確認用テストシナリオを整備

**修正の影響**: 新しいマニュアルテストファイルを追加

---

## 関連ドキュメント

- [Phase 2.5-1: 概要](./plan_Phase_2.5_1_overview.md)
- [Phase 2.5-3: 実装計画](./plan_Phase_2.5_3_implementation.md)

