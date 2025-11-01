# Phase 2.5: プロンプト肥大化問題の解決（統合ドキュメント）

> ⚠️ **このファイルは分割されました**
> 
> 詳細は以下の3つのファイルを参照してください：
> - [Phase 2.5-1: 概要](./plan_Phase_2.5_1_overview.md)
> - [Phase 2.5-2: テスト計画](./plan_Phase_2.5_2_testing.md)
> - [Phase 2.5-3: 実装計画](./plan_Phase_2.5_3_implementation.md)
> 
> このファイルは後方互換性のために残されています。

---

## 問題の背景

### 異常な状況
- プロンプトが270行以上に肥大化
- 主菜提案だけで複雑なルール（在庫操作、献立生成、主菜提案、追加提案、曖昧性解消等）が詰め込まれている
- 副菜・汁物のルールを追加すると、LLMが混乱して正しくタスク生成できない
- プロンプトのトークン数が増大し、コストとレスポンス時間が悪化

### 根本原因
1. **単一のプロンプトに全てのシナリオを詰め込んでいる**
2. **条件分岐が複雑すぎる**（9つのパターンが混在）
3. **プロンプトが静的**（リクエストの種類に応じた動的なプロンプト生成が必要）

---

## 解決策

### 方式B: パターンマッチング分岐（推奨）

**仕組み**:
1. **事前判定**: キーワードベースでパターンを判定
2. **動的プロンプト構築**: 該当パターンのプロンプトのみ構築
3. **LLM呼び出し**: 小さいプロンプトでタスクJSON生成

**メリット**:
- ✓ プロンプトがシンプル（各パターン50-80行程度）
- ✓ LLMが混乱しない（1パターンのみ提示）
- ✓ トークン消費が削減
- ✓ レスポンス時間が改善
- ✓ 保守性が高い（パターン別に管理）
- ✓ テストが容易（パターン別にテスト可能）

---

## 現在のプロンプトのパターン分類

### パターン1: 在庫操作
**キーワード**: 「追加」「削除」「更新」「変えて」「確認」  
**タスク構成**: 単一タスク
- `inventory_service.add_inventory()`
- `inventory_service.update_inventory()`
- `inventory_service.delete_inventory()`
- `inventory_service.get_inventory()`

**必要な情報**:
- 操作種別: add / update / delete / get
- アイテム名: 「牛乳」「ピーマン」等
- 数量: 5本、3個等
- strategy: by_name / by_name_all / by_name_oldest / by_name_latest
- その他属性: 保存場所、単位等

**曖昧性**: 複数の同名アイテム存在 → エージェント実行時に検出（既存機能）

---

### パターン2: 献立生成（従来の一括提案）
**キーワード**: 「献立」「メニュー」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `recipe_service.generate_menu_plan()`
3. `recipe_service.search_menu_from_rag()`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）

**曖昧性**: ほぼなし

---

### パターン3: 主菜提案（初回）
**キーワード**: 「主菜」「メイン」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `history_service.history_get_recent_titles(category="main")`
3. `recipe_service.generate_proposals(category="main")`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- category: "main"
- main_ingredient: 主要食材（オプション）

**曖昧性**: main_ingredient未指定 → 確認質問「食材を指定しますか？」（Phase 1B実装済み）

---

### パターン4: 主菜追加提案
**キーワード**: 「もう5件」「他の提案」「もっと」+ 「主菜」+ sse_session_id存在  
**タスク構成**: 4段階（在庫取得なし）
1. `history_service.history_get_recent_titles(category="main")`
2. `session_service.session_get_proposed_titles(category="main")`
3. `recipe_service.generate_proposals(category="main")` ← セッションから取得
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- sse_session_id（必須）
- category: "main"
- セッションコンテキスト: inventory_items, main_ingredient, menu_type

**曖昧性**: sse_session_id不在 → 初回提案に切り替え

---

### パターン5: 曖昧性解消後の再開（Phase 1E実装済み）
**条件**: セッションに確認待ち状態が存在  
**処理**: 元のリクエスト + ユーザー回答を統合 → パターン1-9に再分類

**必要な情報**:
- 元のリクエスト（セッションから取得）
- ユーザー回答

---

### パターン6: 副菜提案（Phase 3で追加予定）
**キーワード**: 「副菜」「サブ」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `history_service.history_get_recent_titles(category="sub")`
3. `recipe_service.generate_proposals(category="sub", used_ingredients=セッションから取得)`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- category: "sub"
- used_ingredients: 主菜で使った食材（**セッションから取得**）

**曖昧性**: used_ingredients不在（主菜未選択） → 確認質問「まず主菜を選びますか？」

---

### パターン7: 汁物提案（Phase 3で追加予定）
**キーワード**: 「汁物」「味噌汁」「スープ」  
**タスク構成**: 4段階
1. `inventory_service.get_inventory()`
2. `history_service.history_get_recent_titles(category="soup")`
3. `recipe_service.generate_proposals(category="soup", used_ingredients=セッションから取得, menu_category=セッションから判定)`
4. `recipe_service.search_recipes_from_web()`

**必要な情報**:
- user_id（必須）
- category: "soup"
- used_ingredients: 主菜・副菜で使った食材（**セッションから取得**）
- menu_category: "japanese" / "western" / "chinese"（**セッションから判定**）

**曖昧性**: used_ingredients不在（主菜・副菜未選択） → デフォルトで和食（味噌汁）提案 or 確認質問

---

### パターン8: 副菜追加提案（Phase 3で追加予定）
**キーワード**: 「もう5件」+ 「副菜」+ sse_session_id存在  
**タスク構成**: パターン4と同様（category="sub"）

**必要な情報**:
- user_id（必須）
- sse_session_id（必須）
- category: "sub"
- セッションコンテキスト: inventory_items, used_ingredients, menu_type

---

### パターン9: 汁物追加提案（Phase 3で追加予定）
**キーワード**: 「もう5件」+ 「汁物」+ sse_session_id存在  
**タスク構成**: パターン4と同様（category="soup"）

**必要な情報**:
- user_id（必須）
- sse_session_id（必須）
- category: "soup"
- セッションコンテキスト: inventory_items, used_ingredients, menu_category, menu_type

---

## パターン別の必要情報まとめ

| パターン | 必要な情報 | 抽出方法 | セッション依存 |
|---------|----------|---------|--------------|
| 1. 在庫操作 | item_name, quantity, strategy, updates | 正規表現 | なし |
| 2. 献立生成 | user_id | 固定 | なし |
| 3. 主菜提案（初回） | user_id, category="main", main_ingredient(opt) | キーワード+正規表現 | なし |
| 4. 主菜追加提案 | user_id, sse_session_id, category="main" | キーワード | **セッション必須** |
| 5. 曖昧性再開 | 元のリクエスト, ユーザー回答 | セッション | **セッション必須** |
| 6. 副菜提案 | user_id, category="sub", used_ingredients | キーワード | **セッション必須** |
| 7. 汁物提案 | user_id, category="soup", used_ingredients, menu_category | キーワード | **セッション必須** |
| 8. 副菜追加提案 | user_id, sse_session_id, category="sub" | キーワード | **セッション必須** |
| 9. 汁物追加提案 | user_id, sse_session_id, category="soup" | キーワード | **セッション必須** |

---

## 曖昧性検出のケースまとめ

| パターン | 曖昧性のケース | 検出タイミング | 確認質問 |
|---------|-------------|-------------|---------|
| 1. 在庫操作 | 複数の同名アイテム存在 | **エージェント実行時** | 「どの牛乳を削除しますか？」 |
| 3. 主菜提案 | main_ingredient未指定 | **プランナー実行前** | 「食材を指定しますか？」 |
| 4. 主菜追加提案 | sse_session_id不在 | **プランナー実行前** | N/A（初回提案に切り替え） |
| 6. 副菜提案 | used_ingredients不在（主菜未選択） | **プランナー実行前** | 「まず主菜を選びますか？」 |
| 7. 汁物提案 | used_ingredients不在（主菜・副菜未選択） | **プランナー実行前** | 「まず主菜・副菜を選びますか？」or デフォルト和食 |

**曖昧性検出の2つのタイミング**:
1. **プランナー実行前**（事前検出）: リクエスト分析時に検出
2. **エージェント実行時**（実行時検出）: タスク実行中に検出（既存）

---

## 実装計画

Phase 2.5 を以下のサブフェーズに分割：

### Phase 2.5A: RequestAnalyzer の実装

**修正する場所**: `services/llm/request_analyzer.py`（新規作成）

**修正する内容**:
```python
class RequestAnalyzer:
    """リクエスト分析（パターンマッチング方式）"""
    
    def analyze(self, request: str, user_id: str, sse_session_id: str, session_context: dict) -> dict:
        """
        リクエストを分析して必要な情報を抽出
        
        Returns:
            {
                "pattern": "inventory" | "menu" | "main" | "main_additional" | "sub" | "soup" | ...,
                "params": {
                    "category": "main" | "sub" | "soup",
                    "main_ingredient": str | None,
                    "used_ingredients": list | None,
                    "menu_category": str | None,
                    ...
                },
                "ambiguities": [
                    {
                        "type": "missing_main_ingredient" | "missing_session" | ...,
                        "question": "確認質問",
                        "options": ["選択肢1", "選択肢2"]
                    }
                ]
            }
        """
        # 1. パターン判定（キーワードベース）
        pattern = self._detect_pattern(request, sse_session_id)
        
        # 2. パラメータ抽出
        params = self._extract_params(request, pattern, session_context)
        
        # 3. 曖昧性チェック
        ambiguities = self._check_ambiguities(pattern, params, session_context)
        
        return {
            "pattern": pattern,
            "params": params,
            "ambiguities": ambiguities
        }
    
    def _detect_pattern(self, request: str, sse_session_id: str) -> str:
        """
        パターン判定（優先順位順にチェック）
        """
        # 優先度1: 追加提案
        if self._is_additional_proposal(request, sse_session_id):
            if "主菜" in request or "メイン" in request:
                return "main_additional"
            if "副菜" in request or "サブ" in request:
                return "sub_additional"
            if "汁物" in request or "スープ" in request or "味噌汁" in request:
                return "soup_additional"
        
        # 優先度2: カテゴリ提案
        if "主菜" in request or "メイン" in request:
            return "main"
        if "副菜" in request or "サブ" in request:
            return "sub"
        if "汁物" in request or "スープ" in request or "味噌汁" in request:
            return "soup"
        
        # 優先度3: 在庫操作
        if self._is_inventory_operation(request):
            return "inventory"
        
        # 優先度4: 献立生成
        if "献立" in request or "メニュー" in request:
            return "menu"
        
        # 優先度5: その他
        return "other"
    
    def _is_additional_proposal(self, request: str, sse_session_id: str) -> bool:
        """追加提案の判定"""
        if not sse_session_id:
            return False
        
        additional_keywords = ["もう", "他の", "もっと", "追加"]
        return any(keyword in request for keyword in additional_keywords)
    
    def _is_inventory_operation(self, request: str) -> bool:
        """在庫操作の判定"""
        inventory_keywords = ["追加", "削除", "更新", "変えて", "確認", "在庫"]
        return any(keyword in request for keyword in inventory_keywords)
    
    def _extract_params(self, request: str, pattern: str, session_context: dict) -> dict:
        """パラメータ抽出"""
        params = {}
        
        if pattern in ["main", "sub", "soup"]:
            # カテゴリ
            params["category"] = pattern
            
            # 主要食材抽出（簡易版）
            params["main_ingredient"] = self._extract_ingredient(request)
            
            # セッションから used_ingredients を取得
            if pattern in ["sub", "soup"]:
                params["used_ingredients"] = session_context.get("used_ingredients", [])
            
            # 汁物の menu_category 判定
            if pattern == "soup":
                params["menu_category"] = session_context.get("menu_category", "japanese")
        
        elif pattern in ["main_additional", "sub_additional", "soup_additional"]:
            # カテゴリ
            category_map = {
                "main_additional": "main",
                "sub_additional": "sub",
                "soup_additional": "soup"
            }
            params["category"] = category_map[pattern]
        
        return params
    
    def _extract_ingredient(self, request: str) -> str | None:
        """主要食材の抽出（簡易版）"""
        # 「レンコンの主菜」「鶏肉を使った副菜」等のパターン
        import re
        
        # パターン1: 「○○の主菜」「○○で主菜」
        match = re.search(r'([ぁ-ん一-龥ァ-ヴー]+)(の|で|を使った)(主菜|副菜|汁物|メイン|サブ)', request)
        if match:
            return match.group(1)
        
        # パターン2: 「○○主菜」（スペースなし）
        match = re.search(r'([ぁ-ん一-龥ァ-ヴー]{2,})(主菜|副菜|汁物|メイン|サブ)', request)
        if match:
            return match.group(1)
        
        return None
    
    def _check_ambiguities(self, pattern: str, params: dict, session_context: dict) -> list:
        """曖昧性チェック"""
        ambiguities = []
        
        # 主菜提案で main_ingredient 未指定
        if pattern == "main" and not params.get("main_ingredient"):
            ambiguities.append({
                "type": "missing_main_ingredient",
                "question": "何か食材を指定しますか？それとも在庫から提案しますか？",
                "options": ["食材を指定する", "在庫から提案する"]
            })
        
        # 副菜提案で used_ingredients 不在
        if pattern == "sub" and not params.get("used_ingredients"):
            ambiguities.append({
                "type": "missing_used_ingredients",
                "question": "まず主菜を選択しますか？それとも副菜のみ提案しますか？",
                "options": ["主菜から選ぶ", "副菜のみ提案"]
            })
        
        # 汁物提案で used_ingredients 不在
        if pattern == "soup" and not params.get("used_ingredients"):
            # デフォルトで和食（味噌汁）を提案する場合は曖昧性なし
            # 確認したい場合は以下を有効化
            # ambiguities.append({
            #     "type": "missing_used_ingredients",
            #     "question": "まず主菜・副菜を選択しますか？それとも汁物のみ提案しますか？",
            #     "options": ["主菜・副菜から選ぶ", "汁物のみ提案"]
            # })
            pass
        
        return ambiguities
```

**修正の理由**: プロンプトの肥大化を防ぐため、事前にパターン判定を行う

**修正の影響**: LLMService に RequestAnalyzer を統合する必要がある

---

### Phase 2.5B: PromptManager のリファクタリング（モジュール化）

**修正する場所**: `services/llm/prompt_manager/`（新規ディレクトリ作成）

**修正する内容**:

#### ディレクトリ構造

```
services/llm/prompt_manager/
├── __init__.py              # PromptManager クラスのエクスポート
├── base.py                   # PromptManager（基本クラス）
├── patterns/
│   ├── __init__.py
│   ├── inventory.py         # 在庫操作プロンプト（50-80行程度）
│   ├── menu.py              # 献立生成プロンプト（50-80行程度）
│   ├── main_proposal.py     # 主菜提案プロンプト（50-80行程度）
│   ├── sub_proposal.py     # 副菜提案プロンプト（50-80行程度）
│   ├── soup_proposal.py    # 汁物提案プロンプト（50-80行程度）
│   └── additional_proposal.py  # 追加提案プロンプト（50-80行程度）
└── utils.py                 # 共通ユーティリティ（ベースプロンプト等）
```

**メリット**:
- ✓ ファイルが小さくなる（50-80行程度）
- ✓ 可読性が向上
- ✓ 保守性が向上（差分が小さくなる）
- ✓ テストが容易（パターン別にテスト可能）
- ✓ コーディング支援ツールのコンテキストウインドウ圧迫が緩和

#### base.py

```python
"""PromptManager 基本クラス"""
from typing import Dict, Any
from .patterns.inventory import build_inventory_prompt
from .patterns.menu import build_menu_prompt
from .patterns.main_proposal import build_main_proposal_prompt
from .patterns.sub_proposal import build_sub_proposal_prompt
from .patterns.soup_proposal import build_soup_proposal_prompt
from .patterns.additional_proposal import build_additional_proposal_prompt

class PromptManager:
    """プロンプト管理クラス（統合版）"""
    
    def build_prompt(self, analysis_result: Dict[str, Any], user_id: str, sse_session_id: str = None) -> str:
        """
        分析結果に基づいてプロンプトを動的に構築
        """
        pattern = analysis_result["pattern"]
        params = analysis_result["params"]
        
        # パターン別にプロンプト構築
        pattern_map = {
            "inventory": lambda **kwargs: build_inventory_prompt(user_id, **kwargs),
            "menu": lambda **kwargs: build_menu_prompt(user_id, **kwargs),
            "main": lambda **kwargs: build_main_proposal_prompt(user_id, **kwargs),
            "main_additional": lambda **kwargs: build_additional_proposal_prompt(user_id, sse_session_id, "main", **kwargs),
            "sub": lambda **kwargs: build_sub_proposal_prompt(user_id, **kwargs),
            "soup": lambda **kwargs: build_soup_proposal_prompt(user_id, **kwargs),
            "sub_additional": lambda **kwargs: build_additional_proposal_prompt(user_id, sse_session_id, "sub", **kwargs),
            "soup_additional": lambda **kwargs: build_additional_proposal_prompt(user_id, sse_session_id, "soup", **kwargs),
        }
        
        builder = pattern_map.get(pattern)
        if builder:
            return builder(**params)
        return self._build_default_prompt()
    
    def _build_default_prompt(self) -> str:
        """デフォルトプロンプト（挨拶等）"""
        return """
ユーザー要求をタスクに分解してください。

挨拶や一般的な会話の場合、タスクは生成せず、空の配列を返してください。
"""
```

#### patterns/main_proposal.py

```python
"""主菜提案プロンプトビルダー"""
from .utils import build_base_prompt

def build_main_proposal_prompt(user_id: str, main_ingredient: str | None, **kwargs) -> str:
    """主菜提案用のプロンプトを構築"""
    main_ingredient_info = f"\n主要食材: {main_ingredient}" if main_ingredient else "\n主要食材: 指定なし（在庫から提案）"
    
    return f"""
{build_base_prompt()}

ユーザー要求: 主菜を5件提案してください。
{main_ingredient_info}

**主菜提案の4段階タスク構成**:

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `history_service.history_get_recent_titles(user_id, "main", 14)` を呼び出し、14日間の主菜履歴を取得する。
   - user_id: "{user_id}"

c. **task3**: `recipe_service.generate_proposals(category="main")` を呼び出す。その際:
   - `inventory_items`: "task1.result"
   - `excluded_recipes`: "task2.result.data"
   - `category`: "main"
   - `main_ingredient`: {"\"" + main_ingredient + "\"" if main_ingredient else "null"}
   - `user_id`: "{user_id}"

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際:
   - `recipe_titles`: "task3.result.data.candidates"

**依存関係**: task1 → task2, task3 → task4

**並列実行**: task2 と task3 は並列で実行可能です（dependencies に task1 のみ指定）。
"""
```

#### __init__.py

```python
"""PromptManager モジュール"""
from .base import PromptManager

__all__ = ['PromptManager']
```

**修正の理由**: プロンプトをパターン別に分割し、動的に構築することで肥大化を防ぐ

**修正の影響**: 
- `services/llm/prompt_manager.py` → `services/llm/prompt_manager/` ディレクトリに分割
- 各パターンのプロンプトが50-80行程度にシンプル化される
- 既存のインポートは `from services.llm.prompt_manager import PromptManager` のまま動作（後方互換性）

---

#### 実装の詳細（Phase 2.5B の残りの部分）

**修正する内容**（実装詳細の部分は以前と同じ内容なので省略）:

```python
# 以前と同じ実装
class PromptManager:
    """プロンプト管理（モジュール化版）"""
    
    def build_prompt(self, analysis_result: dict, user_id: str, sse_session_id: str = None) -> str:
        """
        分析結果に基づいてプロンプトを動的に構築
        """
        pattern = analysis_result["pattern"]
        params = analysis_result["params"]
        
        # パターン別にプロンプト構築
        if pattern == "inventory":
            return self._build_inventory_prompt(user_id)
        elif pattern == "menu":
            return self._build_menu_prompt(user_id)
        elif pattern == "main":
            return self._build_main_proposal_prompt(user_id, params)
        elif pattern == "main_additional":
            return self._build_additional_proposal_prompt(user_id, sse_session_id, "main")
        elif pattern == "sub":
            return self._build_sub_proposal_prompt(user_id, params)
        elif pattern == "soup":
            return self._build_soup_proposal_prompt(user_id, params)
        elif pattern == "sub_additional":
            return self._build_additional_proposal_prompt(user_id, sse_session_id, "sub")
        elif pattern == "soup_additional":
            return self._build_additional_proposal_prompt(user_id, sse_session_id, "soup")
        else:
            return self._build_default_prompt()
    
    def _build_base_prompt(self) -> str:
        """共通ベースプロンプト"""
        return """
ユーザー要求を分析し、適切なサービスクラスのメソッド呼び出しに分解してください。

利用可能なサービス:

- **inventory_service**: 在庫管理サービス
  - `get_inventory()`: 現在の全在庫アイテムのリストを取得します。
  - `add_inventory(item_name: str, quantity: float, ...)`: 在庫に新しいアイテムを追加します。
  - `update_inventory(item_identifier: str, updates: dict, strategy: str)`: 在庫情報を更新します。
  - `delete_inventory(item_identifier: str, strategy: str)`: 在庫を削除します。

- **recipe_service**: レシピ・献立サービス
  - `generate_proposals(category: str, ...)`: 主菜・副菜・汁物5件を提案します。
  - `generate_menu_plan(inventory_items: list, user_id: str, ...)`: 献立提案を行います。
  - `search_menu_from_rag(query: str, user_id: str, ...)`: RAGを使用して過去の献立履歴から検索します。
  - `search_recipes_from_web(recipe_name: str, ...)`: レシピをWeb検索します。

- **history_service**: レシピ履歴サービス
  - `history_get_recent_titles(user_id: str, category: str, days: int, ...)`: 指定期間内のレシピタイトルを取得。

- **session_service**: セッション管理サービス
  - `session_get_proposed_titles(sse_session_id: str, category: str, ...)`: セッション内で提案済みのレシピタイトルを取得。

**出力形式**: 必ず以下のJSON形式で回答してください（コメントは禁止）：

{
    "tasks": [
        {
            "id": "task1",
            "description": "タスクの自然言語での説明",
            "service": "呼び出すサービス名",
            "method": "呼び出すメソッド名",
            "parameters": { "key": "value" },
            "dependencies": []
        }
    ]
}
"""
    
    def _build_main_proposal_prompt(self, user_id: str, params: dict) -> str:
        """主菜提案用のプロンプト（シンプル版）"""
        main_ingredient = params.get("main_ingredient")
        main_ingredient_info = f"\n主要食材: {main_ingredient}" if main_ingredient else "\n主要食材: 指定なし（在庫から提案）"
        
        return f"""
{self._build_base_prompt()}

ユーザー要求: 主菜を5件提案してください。
{main_ingredient_info}

**主菜提案の4段階タスク構成**:

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `history_service.history_get_recent_titles(user_id, "main", 14)` を呼び出し、14日間の主菜履歴を取得する。
   - user_id: "{user_id}"

c. **task3**: `recipe_service.generate_proposals(category="main")` を呼び出す。その際:
   - `inventory_items`: "task1.result"
   - `excluded_recipes`: "task2.result.data"
   - `category`: "main"
   - `main_ingredient`: {"\"" + main_ingredient + "\"" if main_ingredient else "null"}
   - `user_id`: "{user_id}"

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際:
   - `recipe_titles`: "task3.result.data.candidates"

**依存関係**: task1 → task2, task3 → task4

**並列実行**: task2 と task3 は並列で実行可能です（dependencies に task1 のみ指定）。
"""
    
    def _build_sub_proposal_prompt(self, user_id: str, params: dict) -> str:
        """副菜提案用のプロンプト"""
        used_ingredients = params.get("used_ingredients", [])
        used_ingredients_info = f"\n主菜で使った食材: {', '.join(used_ingredients)}" if used_ingredients else "\n主菜で使った食材: なし"
        
        return f"""
{self._build_base_prompt()}

ユーザー要求: 副菜を5件提案してください。
{used_ingredients_info}

**副菜提案の4段階タスク構成**:

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `history_service.history_get_recent_titles(user_id, "sub", 14)` を呼び出し、14日間の副菜履歴を取得する。
   - user_id: "{user_id}"

c. **task3**: `recipe_service.generate_proposals(category="sub")` を呼び出す。その際:
   - `inventory_items`: "task1.result"
   - `excluded_recipes`: "task2.result.data"
   - `category`: "sub"
   - `used_ingredients`: {used_ingredients}
   - `user_id`: "{user_id}"

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際:
   - `recipe_titles`: "task3.result.data.candidates"

**依存関係**: task1 → task2, task3 → task4
"""
    
    def _build_soup_proposal_prompt(self, user_id: str, params: dict) -> str:
        """汁物提案用のプロンプト"""
        used_ingredients = params.get("used_ingredients", [])
        menu_category = params.get("menu_category", "japanese")
        
        used_ingredients_info = f"\n主菜・副菜で使った食材: {', '.join(used_ingredients)}" if used_ingredients else "\n主菜・副菜で使った食材: なし"
        
        return f"""
{self._build_base_prompt()}

ユーザー要求: 汁物を5件提案してください。
{used_ingredients_info}
献立カテゴリ: {menu_category}

**汁物提案の4段階タスク構成**:

a. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。

b. **task2**: `history_service.history_get_recent_titles(user_id, "soup", 14)` を呼び出し、14日間の汁物履歴を取得する。
   - user_id: "{user_id}"

c. **task3**: `recipe_service.generate_proposals(category="soup")` を呼び出す。その際:
   - `inventory_items`: "task1.result"
   - `excluded_recipes`: "task2.result.data"
   - `category`: "soup"
   - `used_ingredients`: {used_ingredients}
   - `menu_category`: "{menu_category}"
   - `user_id`: "{user_id}"

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際:
   - `recipe_titles`: "task3.result.data.candidates"

**依存関係**: task1 → task2, task3 → task4
"""
    
    def _build_additional_proposal_prompt(self, user_id: str, sse_session_id: str, category: str) -> str:
        """追加提案用のプロンプト（主菜・副菜・汁物共通）"""
        category_name = {"main": "主菜", "sub": "副菜", "soup": "汁物"}[category]
        
        return f"""
{self._build_base_prompt()}

ユーザー要求: {category_name}をもう5件提案してください。

現在のSSEセッションID: {sse_session_id}

**{category_name}追加提案の4段階タスク構成**:

a. **task1**: `history_service.history_get_recent_titles(user_id, "{category}", 14)` を呼び出し、14日間の{category_name}履歴を取得する。
   - user_id: "{user_id}"

b. **task2**: `session_service.session_get_proposed_titles(sse_session_id, "{category}")` を呼び出し、セッション内で提案済みのタイトルを取得する。
   - sse_session_id: "{sse_session_id}"

c. **task3**: `recipe_service.generate_proposals(category="{category}")` を呼び出す。その際:
   - `inventory_items`: "session.context.inventory_items"
   - `excluded_recipes`: "task1.result.data + task2.result.data"
   - `category`: "{category}"
   - `main_ingredient`: "session.context.main_ingredient"
   - `menu_type`: "session.context.menu_type"
   - `user_id`: "{user_id}"

d. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際:
   - `recipe_titles`: "task3.result.data.candidates"

**重要**: 
- 追加提案の場合、在庫取得タスクは生成しないでください。セッション内に保存された在庫情報を再利用してください。
- inventory_items は "session.context.inventory_items" と指定してください。

**依存関係**: task1, task2 → task3 → task4
"""
    
    # 他のパターン用のメソッドも同様に実装
    # _build_inventory_prompt(), _build_menu_prompt(), etc.
```

**修正の理由**: プロンプトをパターン別に分割し、動的に構築することで肥大化を防ぐ

**修正の影響**: 各パターンのプロンプトが50-80行程度にシンプル化される

---

### Phase 2.5C: LLMService への統合

**修正する場所**: `services/llm_service.py`

**修正する内容**:
```python
from services.llm.request_analyzer import RequestAnalyzer

class LLMService:
    def __init__(self):
        self.prompt_manager = PromptManager()
        self.response_processor = ResponseProcessor()
        self.llm_client = LLMClient()
        self.request_analyzer = RequestAnalyzer()  # 追加
    
    async def plan_tasks(self, user_request: str, user_id: str, sse_session_id: str = None, session_context: dict = None) -> List[Dict[str, Any]]:
        """
        ユーザーリクエストをタスクに分解
        """
        try:
            # Phase 2.5A: リクエスト分析
            analysis_result = self.request_analyzer.analyze(
                request=user_request,
                user_id=user_id,
                sse_session_id=sse_session_id,
                session_context=session_context or {}
            )
            
            # 曖昧性がある場合、確認質問を返す
            if analysis_result["ambiguities"]:
                # 確認質問を生成して返す（Phase 1Bと同じ仕組み）
                return self._generate_confirmation_tasks(analysis_result["ambiguities"])
            
            # Phase 2.5B: 動的プロンプト構築
            prompt = self.prompt_manager.build_prompt(
                analysis_result=analysis_result,
                user_id=user_id,
                sse_session_id=sse_session_id
            )
            
            # LLM呼び出し
            response = await self.llm_client.call_openai_api(prompt)
            
            # レスポンス処理
            tasks = self.response_processor.parse_response(response)
            
            return tasks
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in plan_tasks: {e}")
            raise
    
    def _generate_confirmation_tasks(self, ambiguities: list) -> List[Dict[str, Any]]:
        """曖昧性確認タスクを生成"""
        # Phase 1Bと同じ仕組みを使用
        # ...
```

**修正の理由**: RequestAnalyzer と PromptManager を統合してプランニングを実行

**修正の影響**: LLMService のプランニングロジックが変更される

---

### Phase 2.5D: セッション管理の拡張

**修正する場所**: `models/session.py`

**修正する内容**:
```python
from sqlalchemy import Column, String, JSON, DateTime, Enum
from datetime import datetime
import enum

class SessionStage(enum.Enum):
    """セッション段階"""
    INITIAL = "initial"           # 初期状態
    MAIN_SELECTED = "main_selected"     # 主菜選択済み
    SUB_SELECTED = "sub_selected"      # 副菜選択済み
    SOUP_SELECTED = "soup_selected"     # 汁物選択済み
    COMPLETED = "completed"         # 完了

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    
    # Phase 2.5D: 段階管理
    stage = Column(Enum(SessionStage), default=SessionStage.INITIAL)
    
    # Phase 2.5D: 選択履歴
    selected_recipes = Column(JSON, default=dict)  # {"main": {...}, "sub": {...}, "soup": {...}}
    
    # Phase 2.5D: 使用食材
    used_ingredients = Column(JSON, default=list)  # ["レンコン", "牛豚合挽肉", ...]
    
    # Phase 2.5D: 献立カテゴリ
    menu_category = Column(String, default="japanese")  # "japanese" / "western" / "chinese"
    
    # 既存フィールド
    context = Column(JSON, default=dict)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**修正の理由**: 副菜・汁物提案に必要な情報をセッションに保存

**修正の影響**: データベースマイグレーションが必要

---

### Phase 2.5E: 統合テスト

**テストファイル**: `tests/phase2_5/test_integration.py`

**テスト項目**:
1. パターン判定の正確性テスト
2. パラメータ抽出の正確性テスト
3. 曖昧性検出の正確性テスト
4. プロンプト構築の正確性テスト
5. エンドツーエンドテスト（リクエスト→タスク生成）
6. セッション管理テスト

---

### Phase 2.5F: バックエンド回帰テスト（HTTP リクエストベース）

**テストファイル**: `tests/phase2_5/test_backend_regression.py`

**目的**: 破壊的活動の早期発見のため、各パターンの HTTP リクエストを自動テスト

**テストパターン洗い出し**:

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

**実装イメージ**:

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

### Phase 2.5G: フロントエンド確認リクエスト集の整備

**ファイル**: `tests/phase2_5/frontend_manual_tests.md`

**目的**: フロントエンド（/app/Morizo-web）の目視確認用テストシナリオを整備

**手動テストシナリオ洗い出し**:

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

## 期待される効果

- ✅ プロンプトがシンプル化（各パターン50-80行程度）
- ✅ LLMが混乱しない（1パターンのみ提示）
- ✅ トークン消費が削減
- ✅ レスポンス時間が改善
- ✅ 保守性が高い（パターン別に管理）
- ✅ テストが容易（パターン別にテスト可能）
- ✅ Phase 3B（副菜・汁物提案）の実装基盤が完成

---

## 実装順序

1. **Phase 2.5A** → RequestAnalyzer の実装
2. **Phase 2.5B** → PromptManager のリファクタリング
3. **Phase 2.5C** → LLMService への統合
4. **Phase 2.5D** → セッション管理の拡張
5. **Phase 2.5E** → 統合テスト
6. **Phase 2.5F** → バックエンド回帰テスト
7. **Phase 2.5G** → フロントエンド手動テストシナリオ

---

## 制約事項

- Phase 2.5A が完了してから Phase 2.5B を開始
- Phase 2.5B が完了してから Phase 2.5C を開始
- Phase 2.5C が完了してから Phase 2.5D を開始
- Phase 2.5D が完了してから Phase 2.5E を開始
- 既存の Phase 1-2 の機能を破壊しない
- 既存のテストが全て成功することを確認

---

## 代替案: ハイブリッド方式（参考）

### 方式C: 軽量LLM判定 + 動的プロンプト

**仕組み**:
1. **事前判定（軽量LLM）**: パターンとパラメータを抽出
2. **動的プロンプト構築**: 該当パターンのプロンプトのみ構築
3. **LLM呼び出し**: 小さいプロンプトでタスクJSON生成

**メリット**:
- ✓ 方式Bのメリット全て
- ✓ 柔軟な判断が可能（LLM判定）

**デメリット**:
- ✗ 2回のLLM呼び出し（コスト・時間）
- ✗ 事前判定用のプロンプト設計が必要

**採用判断**: まずは方式B（パターンマッチング）で実装し、問題が出たら方式Cに移行することを推奨します。

