あなた（コーデイング支援AI）は**必ず間違える** のですから、**ソース修正は、絶対に承認後**を遵守してください。
かたく**破壊的行動は謹んでください**。

## 🔧 Phase 4: コア機能実装　に着手。

現在、一旦 core の実装、およびテストの実装は完了。

最終的な目的であるタスク構成

1. task1 在庫一覧取得（inventory_list） ⇒ 結果をtask2、task3 のパラメータに注入
2. task2 LLM献立推論（generate_menu_plan_with_history） ⇒ 結果をtask4 のパラメータに注入
3. task3 RAG献立検索（search_menu_from_rag_with_history） ⇒ 結果をtask4 のパラメータに注入
4. task4 レシピ検索（search_recipe_from_web）　⇒ 最終的な献立＋レシピURLを、ユーザーへレスポンス
注：task2 と task3 は並列動作

への実装およびテスト完全完了！

これ以降は安定稼働した後に実施。

その後、肥大化したソースのダイエット
services/llm_service.py　
services/recipe_service.py 等

そして、task2 と task3 の並列動作を確認。

そして、**TODOが残っていないか確認。**