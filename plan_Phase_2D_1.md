# Phase 2D-1: バックエンド実装 + 試験

## 概要

主菜提案機能を3タスク構成から4タスク構成に拡張するバックエンド実装と単体テストを行います。

## 実装内容

1. **プランナーの更新（3→4タスク構成）**
2. **Web検索機能の拡張**
3. **バックエンド単体テスト**

## Phase 2D-1-1: プランナーの更新

### **修正する場所**
- **ファイル**: `services/llm/prompt_manager.py`
- **対象**: `build_planning_prompt()` メソッド

### **修正する内容**
1. **主菜提案のタスク構成を3→4に変更**
2. **Web検索タスクの追加**
3. **パラメータ注入ルールの更新**

### **具体的な変更**
```python
# 現在の3タスク構成
3. **主菜提案の場合**: ユーザーの要求が「主菜」「メイン」「主菜を提案して」等の主菜提案に関する場合、以下の3段階のタスク構成を使用してください：

   a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。
   b. **task2**: `history_service.history_get_recent_titles(user_id, "main", 14)` を呼び出し、14日間の主菜履歴を取得する。
   c. **task3**: `recipe_service.generate_main_dish_proposals()` を呼び出す。

# 新しい4タスク構成
3. **主菜提案の場合**: ユーザーの要求が「主菜」「メイン」「主菜を提案して」等の主菜提案に関する場合、以下の4段階のタスク構成を使用してください：

   a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。
   b. **task2**: `history_service.history_get_recent_titles(user_id, "main", 14)` を呼び出し、14日間の主菜履歴を取得する。
   c. **task3**: `recipe_service.generate_main_dish_proposals()` を呼び出す。
   d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際、ステップ3で取得したレシピタイトルを `recipe_titles` パラメータに設定する。
```

### **パラメータ注入ルールの追加**
```python
**主菜提案のパラメータ注入ルール**:
- task1の結果をtask3で使用する場合 → `"inventory_items": "task1.result"`
- task2の結果をtask3で使用する場合 → `"excluded_recipes": "task2.result.data"`
- task3の結果をtask4で使用する場合 → `"recipe_titles": "task3.result.candidates"`
- 主要食材がある場合 → `"main_ingredient": "抽出された食材名"`
- 主要食材がない場合 → `"main_ingredient": null`
```

## Phase 2D-1-2: Web検索機能の拡張

### **修正する場所**
- **ファイル**: `mcp_servers/recipe_mcp.py`
- **対象**: `search_recipe_from_web()` 関数

### **修正する内容**
1. **主菜提案結果の解析機能追加**
2. **レシピタイトル抽出機能の実装**
3. **画像URL取得機能の追加**

### **具体的な実装**
```python
def extract_recipe_titles_from_proposals(proposals_result: Dict[str, Any]) -> List[str]:
    """主菜提案結果からレシピタイトルを抽出"""
    titles = []
    
    if proposals_result.get("success") and "candidates" in proposals_result:
        candidates = proposals_result["candidates"]
        for candidate in candidates:
            if "title" in candidate:
                titles.append(candidate["title"])
    
    return titles

async def search_recipe_from_web(
    recipe_titles: List[str], 
    num_results: int = 5, 
    user_id: str = "", 
    token: str = None,
    menu_categories: List[str] = None,
    menu_source: str = "mixed"
) -> Dict[str, Any]:
    """
    Web検索によるレシピ検索（主菜提案対応）
    
    Args:
        recipe_titles: 検索するレシピタイトルのリスト
        num_results: 各料理名あたりの取得結果数
        user_id: ユーザーID
        token: 認証トークン
        menu_categories: 料理名の分類リスト
        menu_source: 検索元（llm, rag, mixed）
    
    Returns:
        Dict[str, Any]: 検索結果のレシピリスト（画像URL含む）
    """
    # 既存の実装を拡張
    # 画像URL取得機能を追加
    # 主菜提案結果の解析機能を追加
```

## Phase 2D-1-3: バックエンド単体テスト

### **テスト計画**
1. **プランナーテスト**: 3→4タスク構成の生成確認
2. **パラメータ注入テスト**: タスク間のデータ注入確認
3. **Web検索テスト**: レシピタイトル抽出とWeb検索の動作確認
4. **API統合テスト**: バックエンドAPIの動作確認
5. **エラーハンドリングテスト**: 異常系の処理確認

### **テスト項目詳細**

#### **1. プランナーテスト**
- **テスト内容**: 主菜提案要求で4タスク構成が生成されることを確認
- **テストケース**:
  - 「レンコンを使った主菜を教えて」→ 4タスク構成生成
  - 「主菜を5件提案して」→ 4タスク構成生成
  - 「メインを提案して」→ 4タスク構成生成
- **期待結果**: task4にWeb検索タスクが含まれる

#### **2. パラメータ注入テスト**
- **テスト内容**: タスク間のデータ注入が正しく行われることを確認
- **テストケース**:
  - task1 → task3: inventory_itemsの注入
  - task2 → task3: excluded_recipesの注入
  - task3 → task4: recipe_titlesの注入
- **期待結果**: 各タスクで正しいパラメータが設定される

#### **3. Web検索テスト**
- **テスト内容**: レシピタイトル抽出とWeb検索の動作確認
- **テストケース**:
  - 主菜提案結果からレシピタイトル抽出
  - Web検索の実行
  - 画像URL取得
- **期待結果**: レシピタイトルが正しく抽出され、Web検索が実行される

#### **4. API統合テスト**
- **テスト内容**: バックエンドAPIの動作確認
- **テストケース**:
  - 4タスク構成の実行
  - 各タスクの完了確認
  - 最終結果の取得
- **期待結果**: 4タスクが順次実行され、最終結果が取得される

#### **5. エラーハンドリングテスト**
- **テスト内容**: 異常系の処理確認
- **テストケース**:
  - Web検索APIの失敗
  - レシピタイトル抽出の失敗
  - ネットワークエラー
- **期待結果**: 適切なエラーメッセージが返される

## 実装順序

1. **Phase 2D-1-1** → プランナーの更新
2. **Phase 2D-1-2** → Web検索機能の拡張
3. **Phase 2D-1-3** → バックエンド単体テスト

## 期待される効果

### **技術的改善**
- **4タスク構成**: より詳細なレシピ情報を提供
- **Web検索統合**: 既存のWeb検索機能を主菜提案に適用
- **パラメータ注入**: タスク間のデータ連携の強化

### **品質向上**
- **単体テスト**: バックエンド機能の品質保証
- **エラーハンドリング**: 異常系の適切な処理
- **API統合**: 既存システムとの整合性確保

## 制約事項

- **既存機能の維持**: Phase 1-2の機能を破壊しない
- **パフォーマンス**: Web検索の追加による処理時間の増加を考慮
- **エラーハンドリング**: Web検索失敗時の適切な処理
- **API制限**: Web検索APIの利用制限を考慮

## 次のフェーズ

- **Phase 2D-2**: フロントエンド実装
- **Phase 2D-3**: 結合試験

この実装により、バックエンド側で4タスク構成とWeb検索機能が完成し、フロントエンド実装の基盤が整います。
