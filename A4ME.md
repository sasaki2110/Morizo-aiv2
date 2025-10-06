あなた（コーデイング支援AI）は**必ず間違える** のですから、**ソース修正は、絶対に承認後**を遵守してください。
かたく**破壊的行動は謹んでください**。

LLM献立推論 での食材重複抑止　⇒　完了
RAG献立検索 での食材重複抑止　⇒　完了

 そして、またmcp_servers/recipe_rag.pyが肥大化したので
 ダイエットが必要。

 ### **💡 ダイエット案**

#### **案1: 機能別ファイル分割**
```
mcp_servers/recipe_rag/
├── __init__.py (10行)
├── client.py (50行) - RecipeRAGClient基本機能
├── search.py (80行) - 検索機能
├── menu_format.py (80行) - 献立変換機能
└── llm_solver.py (80行) - LLM制約解決機能
```

#### **案2: ヘルパー関数の外部化**
```
mcp_servers/recipe_rag.py (100行) - メイン機能のみ
utils/recipe_helpers.py (200行) - ヘルパー関数群
```

#### **案3: 段階的分割**
1. **Phase 1**: LLM関連機能を `recipe_llm_solver.py` に分離
2. **Phase 2**: 検索機能を `recipe_search.py` に分離
3. **Phase 3**: 献立変換を `menu_formatter.py` に分離
