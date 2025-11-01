# Phase 1A: 基本機能実装

## 概要

主菜5件提案機能の基本部分を実装します。LLM推論で2件、RAG検索で3件の計5件を生成し、統合・表示する機能を構築します。

## 対象範囲

- LLM推論で主菜2件生成（主要食材考慮、重複回避）
- RAG検索で主菜3件検索（主要食材考慮、重複回避）
- MCP統合レイヤー（LLM + RAG統合）
- レスポンスフォーマッター（5件表示）
- レスポンス処理統合
- **履歴取得機能（重複回避用）**

## 実装計画

### 1. LLM推論の拡張（主菜2件生成）

**修正ファイル**: `mcp_servers/recipe_llm.py`

**変更内容**:
- `generate_menu_titles()`メソッドを拡張し、主菜のみ複数件生成する新メソッド`generate_main_dish_candidates()`を追加
- プロンプトを修正し、主菜タイトルを2件生成するよう指示
- **主要食材を考慮した提案**
- **各提案に使用食材リストを含める**
- **重複回避機能（excluded_recipesパラメータを活用）**

**実装例**:
```python
async def generate_main_dish_candidates(
    self, 
    inventory_items: List[str], 
    menu_type: str,
    main_ingredient: str = None,  # 主要食材
    excluded_recipes: List[str] = None,
    count: int = 2
) -> Dict[str, Any]:
    """主菜候補を複数件生成（主要食材考慮）"""
    
    main_ingredient_text = ""
    if main_ingredient:
        main_ingredient_text = f"\n重要: {main_ingredient}を必ず使用してください。"
    
    # 除外レシピの追加
    excluded_text = ""
    if excluded_recipes:
        excluded_text = f"\n除外レシピ（提案しないでください）: {', '.join(excluded_recipes)}"
    
    prompt = f"""
在庫食材: {', '.join(inventory_items)}
献立タイプ: {menu_type}{main_ingredient_text}{excluded_text}

以下の条件で主菜のタイトルを{count}件生成してください:
1. 在庫食材のみを使用
2. 独創的で新しいレシピタイトル
3. 除外レシピは絶対に使用しない
4. 各提案に使用食材リストを含める

以下のJSON形式で回答してください:
{{
    "candidates": [
        {{"title": "主菜タイトル1", "ingredients": ["食材1", "食材2"]}},
        {{"title": "主菜タイトル2", "ingredients": ["食材1", "食材3"]}}
    ]
}}
"""
    
    try:
        self.logger.info(f"🤖 [LLM] Generating {count} main dish candidates with main ingredient: {main_ingredient}")
        
        # プロンプトロギング
        log_prompt_with_tokens(prompt, max_tokens=1000, logger_name="mcp.recipe_llm")
        
        # LLM呼び出し
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=1000
        )
        
        # レスポンスを解析
        candidates = self._parse_main_dish_response(response.choices[0].message.content)
        
        self.logger.info(f"✅ [LLM] Generated {len(candidates)} main dish candidates")
        return {"success": True, "data": {"candidates": candidates}}
        
    except Exception as e:
        self.logger.error(f"❌ [LLM] Failed to generate main dish candidates: {e}")
        return {"success": False, "error": str(e)}

def _parse_main_dish_response(self, response_content: str) -> List[Dict[str, Any]]:
    """LLMレスポンスを解析して主菜候補を抽出"""
    try:
        import json
        import re
        
        # JSON部分を抽出
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data.get("candidates", [])
        
        return []
    except Exception as e:
        self.logger.error(f"❌ [LLM] Failed to parse main dish response: {e}")
        return []
```

### 2. RAG検索の拡張（主菜3件検索）

**修正ファイル**: `mcp_servers/recipe_rag/client.py`

**変更内容**:
- `search_recipes_by_category()`メソッドで主菜カテゴリのlimitパラメータを3件に設定
- 主菜のみ検索する新メソッド`search_main_dish_candidates()`を追加
- **主要食材を考慮した検索**
- **各提案に使用食材リストを含める**
- **重複回避機能（excluded_recipesパラメータを活用）**

**実装例**:
```python
async def search_main_dish_candidates(
    self,
    ingredients: List[str],
    menu_type: str,
    main_ingredient: str = None,  # 主要食材
    excluded_recipes: List[str] = None,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """主菜候補を検索（主要食材考慮）"""
    try:
        logger.info(f"🔍 [RAG] Searching {limit} main dish candidates")
        logger.info(f"🔍 [RAG] Main ingredient: {main_ingredient}, Excluded: {len(excluded_recipes or [])} recipes")
        
        search_engine = self._get_search_engines()["main"]
        
        # 主要食材がある場合は検索クエリに追加
        search_query = ingredients.copy()
        if main_ingredient:
            search_query.insert(0, main_ingredient)  # 主要食材を優先
        
        # RAG検索（除外レシピを渡す）
        results = await search_engine.search_similar_recipes(
            search_query, menu_type, excluded_recipes, limit
        )
        
        # 各結果に使用食材リストを含める
        for result in results:
            if "ingredients" not in result:
                result["ingredients"] = result.get("ingredients_list", [])
        
        logger.info(f"✅ [RAG] Found {len(results)} main dish candidates")
        return results
        
    except Exception as e:
        logger.error(f"❌ [RAG] Failed to search main dish candidates: {e}")
        return []
```

### 3. MCP統合レイヤーの追加

**新規ファイル**: `mcp_servers/recipe_mcp.py`に新メソッド追加

**変更内容**:
- LLMとRAGの結果を統合する新ツール`generate_main_dish_proposals()`を追加
- LLM 2件 + RAG 3件を統合して5件の主菜候補リストを返す
- **主要食材パラメータを追加**
- **重複回避機能（excluded_recipesパラメータをLLMとRAGに渡す）**

**実装例**:
```python
@mcp.tool()
async def generate_main_dish_proposals(
    inventory_items: List[str],
    user_id: str,
    menu_type: str = "",
    main_ingredient: str = None,  # 主要食材
    excluded_recipes: List[str] = None,
    token: str = None
) -> Dict[str, Any]:
    """主菜5件提案（LLM 2件 + RAG 3件、主要食材考慮、重複回避）"""
    logger.info(f"🔧 [RECIPE] Starting generate_main_dish_proposals")
    logger.info(f"  User: {user_id}, Main ingredient: {main_ingredient}")
    logger.info(f"  Excluded recipes: {len(excluded_recipes or [])} recipes")
    
    try:
        # 認証済みクライアントを取得
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [RECIPE] Authenticated client created for user: {user_id}")
        
        # LLMで2件生成（除外レシピを渡す）
        llm_result = await llm_client.generate_main_dish_candidates(
            inventory_items, menu_type, main_ingredient, excluded_recipes, count=2
        )
        
        # RAGで3件検索（除外レシピを渡す）
        rag_result = await rag_client.search_main_dish_candidates(
            inventory_items, menu_type, main_ingredient, excluded_recipes, limit=3
        )
        
        # 統合
        candidates = []
        if llm_result.get("success"):
            candidates.extend(llm_result["data"]["candidates"])
        if rag_result:
            candidates.extend([{"title": r["title"], "ingredients": r.get("ingredients", [])} for r in rag_result])
        
        logger.info(f"✅ [RECIPE] generate_main_dish_proposals completed: {len(candidates)} candidates")
        
        return {
            "success": True,
            "data": {
                "candidates": candidates,
                "total": len(candidates),
                "main_ingredient": main_ingredient,
                "excluded_count": len(excluded_recipes or []),
                "llm_count": len(llm_result.get("data", {}).get("candidates", [])),
                "rag_count": len(rag_result)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [RECIPE] Error in generate_main_dish_proposals: {e}")
        return {"success": False, "error": str(e)}
```

### 4. レスポンスフォーマッターの拡張

**修正ファイル**: `services/llm/response_formatters.py`

**変更内容**:
- 主菜5件候補を表示する新メソッド`format_main_dish_proposals()`を追加
- LLM提案とRAG提案を区別して表示
- **主要食材の表示**

**実装例**:
```python
def format_main_dish_proposals(self, data: Dict[str, Any]) -> List[str]:
    """主菜5件提案のフォーマット（主要食材考慮）"""
    response_parts = []
    
    try:
        if data.get("success"):
            candidates = data.get("data", {}).get("candidates", [])
            main_ingredient = data.get("data", {}).get("main_ingredient")
            llm_count = data.get("data", {}).get("llm_count", 0)
            rag_count = data.get("data", {}).get("rag_count", 0)
            
            # 主要食材の表示
            if main_ingredient:
                response_parts.append(f"🍽️ **主菜の提案（5件）- {main_ingredient}使用**")
            else:
                response_parts.append("🍽️ **主菜の提案（5件）**")
            response_parts.append("")
            
            # LLM提案（最初の2件）
            if llm_count > 0:
                response_parts.append("💡 **斬新な提案（LLM推論）**")
                for i, candidate in enumerate(candidates[:llm_count], 1):
                    title = candidate.get("title", "")
                    ingredients = ", ".join(candidate.get("ingredients", []))
                    response_parts.append(f"{i}. {title}")
                    response_parts.append(f"   使用食材: {ingredients}")
                    response_parts.append("")
            
            # RAG提案（残りの3件）
            if rag_count > 0:
                response_parts.append("📚 **伝統的な提案（RAG検索）**")
                start_idx = llm_count
                for i, candidate in enumerate(candidates[start_idx:], start_idx + 1):
                    title = candidate.get("title", "")
                    ingredients = ", ".join(candidate.get("ingredients", []))
                    response_parts.append(f"{i}. {title}")
                    response_parts.append(f"   使用食材: {ingredients}")
                    response_parts.append("")
        else:
            # エラー時の表示
            error_msg = data.get("error", "不明なエラー")
            response_parts.append("❌ **主菜提案の取得に失敗しました**")
            response_parts.append("")
            response_parts.append(f"エラー: {error_msg}")
            response_parts.append("")
            response_parts.append("もう一度お試しください。")
            
    except Exception as e:
        self.logger.error(f"❌ [ResponseFormatters] Error in format_main_dish_proposals: {e}")
        response_parts.append("主菜提案の処理中にエラーが発生しました。")
    
    return response_parts
```

### 5. 履歴取得機能の追加（重複回避用）

**修正ファイル**: `mcp_servers/recipe_history_crud.py`

**変更内容**:
- `get_recent_recipe_titles()` メソッドを追加
- カテゴリ（main/sub/soup）と期間（日数）を指定してレシピタイトルリストを取得

**実装例**:
```python
async def get_recent_recipe_titles(
    self,
    client: Client,
    user_id: str,
    category: str,  # "main", "sub", "soup"
    days: int = 14  # デフォルト14日間
) -> Dict[str, Any]:
    """指定期間内のレシピタイトルを取得（重複回避用）
    
    Args:
        client: Supabaseクライアント
        user_id: ユーザーID
        category: カテゴリ（"main", "sub", "soup"）
        days: 重複回避期間（日数）
    
    Returns:
        Dict[str, Any]: {"success": bool, "data": List[str]} レシピタイトルのリスト
    """
    try:
        self.logger.info(f"📋 [CRUD] Getting recent {category} recipes for user: {user_id} (last {days} days)")
        
        # カテゴリのマッピング（将来の拡張用）
        # 現状はtitleのみで判定するため、全レシピを取得
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 指定期間内のレシピを取得
        result = client.table("recipe_historys")\
            .select("title")\
            .eq("user_id", user_id)\
            .gte("cooked_at", cutoff_date.isoformat())\
            .execute()
        
        # タイトルのリストを作成
        titles = [item["title"] for item in result.data]
        
        self.logger.info(f"✅ [CRUD] Retrieved {len(titles)} recent {category} recipe titles")
        return {"success": True, "data": titles}
        
    except Exception as e:
        self.logger.error(f"❌ [CRUD] Failed to get recent recipe titles: {e}")
        return {"success": False, "error": str(e), "data": []}
```

### 6. 履歴取得MCPツールの追加

**修正ファイル**: `mcp_servers/recipe_history_mcp.py`

**変更内容**:
- `history_get_recent_titles()` ツールを追加
- カテゴリと期間を指定して重複回避対象のタイトルリストを取得

**実装例**:
```python
@mcp.tool()
async def history_get_recent_titles(
    user_id: str,
    category: str,  # "main", "sub", "soup"
    days: int = 14,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    指定期間内のレシピタイトルを取得（重複回避用）
    
    Args:
        user_id: ユーザーID
        category: カテゴリ（"main", "sub", "soup"）
        days: 重複回避期間（日数）
        token: 認証トークン
    
    Returns:
        Dict[str, Any]: レシピタイトルのリスト
    """
    logger.info(f"🔧 [RECIPE_HISTORY] Starting history_get_recent_titles for user: {user_id}, category: {category}, days: {days}")
    
    try:
        client = get_authenticated_client(user_id, token)
        logger.info(f"🔐 [RECIPE_HISTORY] Authenticated client created for user: {user_id}")
        
        result = await crud.get_recent_recipe_titles(client, user_id, category, days)
        logger.info(f"✅ [RECIPE_HISTORY] history_get_recent_titles completed successfully")
        logger.debug(f"📊 [RECIPE_HISTORY] Recent titles result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [RECIPE_HISTORY] Error in history_get_recent_titles: {e}")
        return {"success": False, "error": str(e), "data": []}
```

### 7. レスポンス処理の統合

**修正ファイル**: `services/llm/response_processor.py`

**変更内容**:
- `_process_service_method()`に新サービスメソッド`recipe_service.generate_main_dish_proposals`の処理を追加

**実装箇所**: 210-227行目のservice_method判定に追加
```python
elif service_method == "recipe_service.generate_main_dish_proposals":
    response_parts.extend(self.formatters.format_main_dish_proposals(data))
```

## テスト計画

### 単体テスト
1. `generate_main_dish_candidates()`が2件の主菜を生成することを確認
2. `search_main_dish_candidates()`が3件の主菜を検索することを確認
3. `generate_main_dish_proposals()`が5件統合することを確認
4. **主要食材指定時の動作を確認**
5. **`get_recent_recipe_titles()`が履歴タイトルを正しく取得することを確認**
6. **`history_get_recent_titles()`がMCPツールとして正しく動作することを確認**

### 統合テスト
1. LLM 2件 + RAG 3件が正しく統合されることを確認
2. レスポンスが適切にフォーマットされることを確認
3. **主要食材が正しく表示されることを確認**
4. **重複回避機能が正しく動作することを確認（除外レシピが提案されない）**

## 制約事項
- プランナーの修正は含まない（Phase 1Bで対応）
- 曖昧性検出は含まない（Phase 1Bで対応）
- 動的タスク構築は含まない（Phase 1Bで対応）

## 期待される効果
- 主菜5件提案の基本機能が完成
- LLMの独創性とRAGの伝統的レシピのバランスが取れる
- **主要食材を考慮した提案でユーザーの意図に沿った提案**
- **重複回避機能により、ユーザーが同じレシピを短期間に繰り返し見ることを防止**
- Phase 1B以降の基盤となる

### To-dos

- [ ] LLM推論で主菜2件を生成する generate_main_dish_candidates() メソッドを recipe_llm.py に追加（主要食材考慮、重複回避）
- [ ] RAG検索で主菜3件を検索する search_main_dish_candidates() メソッドを recipe_rag/client.py に追加（主要食材考慮、重複回避）
- [ ] LLMとRAGを統合する generate_main_dish_proposals() ツールを recipe_mcp.py に追加（主要食材パラメータ、重複回避）
- [ ] 主菜5件候補を表示する format_main_dish_proposals() メソッドを response_formatters.py に追加（主要食材表示）
- [ ] 履歴取得メソッド get_recent_recipe_titles() を recipe_history_crud.py に追加（重複回避用）
- [ ] 履歴取得ツール history_get_recent_titles() を recipe_history_mcp.py に追加（重複回避用）
- [ ] レスポンス処理に新サービスメソッドの処理を追加（response_processor.py）
- [ ] Phase 1Aの統合テスト: LLM + RAG統合とレスポンス表示の確認、重複回避機能の確認
