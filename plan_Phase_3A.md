# Phase 3A: バックエンド汎用メソッドの実装

## 概要

`category`パラメータ（"main"/"sub"/"soup"）を受け取る汎用メソッドを追加します。
既存のメソッドは後方互換性のため残します。

## 対象範囲

- LLM層: `mcp_servers/recipe_llm.py`
- RAG層: `mcp_servers/recipe_rag/client.py`
- MCP層: `mcp_servers/recipe_mcp.py`

## 実装計画

### 1. LLM層の汎用メソッド追加

**修正する場所**: `mcp_servers/recipe_llm.py`

**修正する内容**:
```python
async def generate_candidates(
    self, 
    inventory_items: List[str], 
    menu_type: str,
    category: str,  # "main", "sub", "soup"
    main_ingredient: str = None,
    used_ingredients: List[str] = None,  # 副菜・汁物用（主菜で使った食材）
    excluded_recipes: List[str] = None,
    count: int = 2
) -> Dict[str, Any]:
    """
    汎用候補生成メソッド（主菜・副菜・汁物対応）
    
    Args:
        category: "main", "sub", "soup"
        used_ingredients: すでに使った食材（副菜・汁物で主菜で使った食材を除外）
        inventory_items: 在庫食材リスト
        menu_type: 献立タイプ
        main_ingredient: 主要食材（主菜の場合のみ）
        excluded_recipes: 除外レシピ
        count: 生成件数
    """
```

**プロンプトのカテゴリ別切り替え**:
- category="main" → "主菜" + main_ingredientの指定
- category="sub" → "副菜" + 主菜で使っていない食材を使用
- category="soup" → "汁物（味噌汁orスープ）" + 使っていない食材を使用

**修正の理由**: 副菜・汁物を生成するための汎用メソッドが必要

**修正の影響**: 既存の`generate_main_dish_candidates()`はそのまま動作（後方互換性）

---

### 2. RAG層の汎用メソッド追加

**修正する場所**: `mcp_servers/recipe_rag/client.py`

**修正する内容**:
```python
async def search_candidates(
    self,
    ingredients: List[str],
    menu_type: str,
    category: str,  # "main", "sub", "soup"
    main_ingredient: str = None,
    used_ingredients: List[str] = None,
    excluded_recipes: List[str] = None,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """
    汎用候補検索メソッド（主菜・副菜・汁物対応）
    
    categoryに応じて適切なベクトルストアを選択：
    - "main" → main ベクトルストア
    - "sub" → sub ベクトルストア
    - "soup" → soup ベクトルストア
    """
    search_engine = self._get_search_engines()[category]
    # ... 検索処理
```

**修正の理由**: 副菜・汁物のRAG検索に対応

**修正の影響**: 既存の`search_main_dish_candidates()`はそのまま動作

---

### 3. MCP層の汎用メソッド追加

**修正する場所**: `mcp_servers/recipe_mcp.py`

**修正する内容**:
```python
@mcp.tool()
async def generate_proposals(
    inventory_items: List[str],
    user_id: str,
    category: str = "main",  # "main", "sub", "soup"
    menu_type: str = "",
    main_ingredient: str = None,
    used_ingredients: List[str] = None,
    excluded_recipes: List[str] = None,
    menu_category: str = "japanese",  # "japanese", "western", "chinese"
    token: str = None
) -> Dict[str, Any]:
    """
    汎用提案メソッド（主菜・副菜・汁物対応）
    
    Args:
        category: "main", "sub", "soup"
        used_ingredients: すでに使った食材（副菜・汁物で使用）
        menu_category: 献立カテゴリ（汁物の判断に使用）
    """
    # LLMとRAGを並列実行
    llm_result = await llm_client.generate_candidates(
        inventory_items, menu_type, category, 
        main_ingredient, used_ingredients, excluded_recipes, count=2
    )
    rag_result = await rag_client.search_candidates(
        inventory_items, menu_type, category,
        main_ingredient, used_ingredients, excluded_recipes, limit=3
    )
    
    # 統合
    candidates = []
    if llm_result.get("success"):
        candidates.extend(llm_result["data"]["candidates"])
    if rag_result:
        candidates.extend([{"title": r["title"], "ingredients": r.get("ingredients", [])} for r in rag_result])
    
    return {
        "success": True,
        "data": {
            "candidates": candidates,
            "category": category,
            "total": len(candidates)
        }
    }
```

**修正の理由**: 副菜・汁物提案の統合メソッド

**修正の影響**: 既存の`generate_main_dish_proposals()`はそのまま動作

---

## 期待される効果

- 主菜・副菜・汁物を同じメソッドで処理できる
- コードの重複を削減
- メンテナンス性が向上

