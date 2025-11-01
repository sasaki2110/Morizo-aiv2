# Phase 5.1: 候補情報へのsourceフィールド追加

## 概要

Phase 5A実装前に、セッションに保存される候補情報に`source`フィールドを追加します。
これにより、Phase 5Aで実装する`/api/menu/save`エンドポイントが、選択済みレシピの出典（LLM/RAG/Web）を正しく判定してDBの`source`カラムに保存できるようになります。

## 背景

### 問題点

Phase 5Aの実装計画では、以下のように`source`マッピングを想定しています：

```python
source_mapping = {
    "llm": "web",
    "rag": "rag",
    "web": "web"
}
```

しかし、実際のコードを調査した結果、**候補情報（candidates）に`source`フィールドが含まれていない**ことが判明しました。

1. `generate_proposals`でLLM候補とRAG候補を生成する際、`source`フィールドを付与していない
2. `web_integrator.integrate`でURL情報を統合する際、`source`フィールドを保持していない
3. セッションに保存される候補情報（`get_selected_recipes()`で取得される情報）に`source`が含まれていない

そのため、Phase 5Aで実装予定の以下のコードが機能しません：

```python
recipe_source = recipe.get("source", "web")  # sourceが存在しないため常に"web"になる
db_source = source_mapping.get(recipe_source, "web")
```

### 影響範囲

- **Phase 5A**: `/api/menu/save`エンドポイントで`source`が正しく設定されない
- **データ品質**: すべてのレシピが`source="web"`で保存され、実際の出典（LLM/RAG）が失われる
- **将来の分析**: 出典別の統計や分析が不可能になる

## 実装計画

### 修正箇所1: `generate_proposals`関数

**修正する場所**: `/app/Morizo-aiv2/mcp_servers/recipe_mcp.py`

**関数名**: `generate_proposals`（行409-413あたり）

**修正内容**:
- LLM候補に`"source": "llm"`を追加
- RAG候補に`"source": "rag"`を追加

**修正前**:
```python
# 統合
candidates = []
if llm_result.get("success"):
    candidates.extend(llm_result["data"]["candidates"])
if rag_result:
    candidates.extend([{"title": r["title"], "ingredients": r.get("ingredients", [])} for r in rag_result])
```

**修正後**:
```python
# 統合（sourceフィールドを追加）
candidates = []
if llm_result.get("success"):
    llm_candidates = llm_result["data"]["candidates"]
    # LLM候補にsourceフィールドを追加
    for candidate in llm_candidates:
        if "source" not in candidate:
            candidate["source"] = "llm"
    candidates.extend(llm_candidates)
if rag_result:
    # RAG候補にsourceフィールドを追加
    rag_candidates = [{"title": r["title"], "ingredients": r.get("ingredients", []), "source": "rag"} for r in rag_result]
    candidates.extend(rag_candidates)
```

**修正の理由**:
- LLMで生成された候補とRAGで検索された候補を区別するため
- Phase 5Aの`source_mapping`で正しくマッピングできるようにするため

**修正の影響**:
- 既存のコードへの影響は最小限（新規フィールド追加のみ）
- フロントエンドへの影響なし（未使用フィールドの追加）
- 後方互換性あり（`source`が存在しない場合のデフォルト処理も残す）

### 修正箇所2: `web_integrator.integrate`メソッド

**修正する場所**: `/app/Morizo-aiv2/services/llm/web_search_integrator.py`

**関数名**: `integrate`（行48-68あたり）

**修正内容**:
- 候補情報に既存の`source`フィールドがある場合は保持
- URL情報を統合する際に`source`フィールドを保持する

**修正前**:
```python
# 候補とWeb検索結果を統合
integrated_candidates = []
for i, candidate in enumerate(candidates):
    integrated_candidate = candidate.copy()
    
    # 対応するWeb検索結果を取得
    if i < len(web_search_results):
        web_result = web_search_results[i]
        if web_result.get("url"):
            # URL情報を統合
            domain = utils.extract_domain(web_result.get("url", "")) if utils else ""
            integrated_candidate["urls"] = [{
                "title": web_result.get("title", ""),
                "url": web_result.get("url", ""),
                "domain": domain
            }]
```

**修正後**:
```python
# 候補とWeb検索結果を統合（sourceフィールドを保持）
integrated_candidates = []
for i, candidate in enumerate(candidates):
    integrated_candidate = candidate.copy()
    
    # sourceフィールドが存在しない場合はデフォルト値"web"を設定
    if "source" not in integrated_candidate:
        integrated_candidate["source"] = "web"
    
    # 対応するWeb検索結果を取得
    if i < len(web_search_results):
        web_result = web_search_results[i]
        if web_result.get("url"):
            # URL情報を統合（sourceは既存の値を保持）
            domain = utils.extract_domain(web_result.get("url", "")) if utils else ""
            integrated_candidate["urls"] = [{
                "title": web_result.get("title", ""),
                "url": web_result.get("url", ""),
                "domain": domain
            }]
            # URLが存在する場合でも、元のsource（llm/rag）を保持
            # Web検索はレシピ詳細取得のための補助情報であり、出典は変えない
```

**修正の理由**:
- Web検索結果を統合しても、元の出典（LLM/RAG）を保持するため
- Phase 5Aの`source_mapping`で正しくマッピングできるようにするため

**修正の影響**:
- 既存のコードへの影響は最小限（新規フィールド追加のみ）
- フロントエンドへの影響なし（未使用フィールドの追加）
- 後方互換性あり（`source`が存在しない場合のデフォルト処理を追加）

## テスト項目

### 単体テスト

1. **`generate_proposals`のsourceフィールド確認**
   - LLM候補に`source: "llm"`が設定されていること
   - RAG候補に`source: "rag"`が設定されていること
   - 候補数が正しいこと（LLM: 2件、RAG: 3件）

2. **`web_integrator.integrate`のsource保持確認**
   - LLM候補（`source: "llm"`）のsourceが保持されること
   - RAG候補（`source: "rag"`）のsourceが保持されること
   - sourceが存在しない候補にデフォルト値`"web"`が設定されること
   - URL情報が正しく統合されること

### 統合テスト

1. **セッション保存・取得のフロー確認**
   - `set_candidates`で候補を保存
   - `get_selected_recipes`で選択済みレシピを取得
   - 取得したレシピに`source`フィールドが含まれていることを確認

2. **Phase 5Aとの連携確認**
   - `/api/menu/save`エンドポイントで`source`が正しく取得できること
   - `source_mapping`で正しくマッピングされること（`"llm"`→`"web"`, `"rag"`→`"rag"`）
   - DBの`source`カラムに正しい値が保存されること

## 実装順序

1. **Phase 5.1** → 候補情報へのsourceフィールド追加（本プラン）
2. **Phase 5A** → バックエンド実装（DB保存機能）

## 期待される効果

- Phase 5Aで実装する`/api/menu/save`エンドポイントが正しく動作する
- 選択済みレシピの出典（LLM/RAG）が正しくDBに保存される
- 将来の出典別統計や分析が可能になる
- データ品質が向上する

## 制約事項

- Phase 5.1が完成してからPhase 5Aを開始
- 既存のPhase 1-3の機能を破壊しない
- フロントエンドへの影響なし（未使用フィールドの追加のみ）

## 次のフェーズ

- **Phase 5A**: バックエンド実装（DB保存機能）([plan_Phase_5A.md](./plan_Phase_5A.md))

