あなた（コーデイング支援AI）は**必ず間違える** のですから、**ソース修正は、絶対に承認後**を遵守してください。
かたく**破壊的行動は謹んでください**。

## 🔧 Phase 4: コア機能実装　に着手。

現在、一旦 core の実装、およびテストの実装は完了。

大まかな方針は整理して、04_1_test_core.py で
- LLMによるタスクプラン生成
- task1の在庫一覧取得（inventory_list） ⇒ 結果をtask2 のパラメータに注入
- task2のLLM献立推論（generate_menu_plan_with_history） ⇒ 献立提案
まで一連の流れが完成。

後は、最終的な目的であるタスク構成

1. task1 在庫一覧取得（inventory_list） ⇒ 結果をtask2、task3 のパラメータに注入
2. task2 LLM献立推論（generate_menu_plan_with_history） ⇒ 結果をtask4 のパラメータに注入
3. task3 RAG献立検索（search_menu_from_rag_with_history） ⇒ 結果をtask4 のパラメータに注入
4. task4 レシピ検索（search_recipe_from_web）　⇒ 最終的な献立＋レシピURLを、ユーザーへレスポンス
注：task2 と task3 は並列動作

への対応中。

1. ～ 4. の疎通確認まで完了。
後は、task4 へのデータ注入が正常終了。

基本的な動作確認は完了。

最後、若干レスポンスに不満あり。
（LLM献立提案のレシピURLが表示されていない）
（RAG献立提案のレシピURLは表示されている。）

その後、肥大化したソースのダイエット
services/llm_service.py　等

そして、task2 と task3 の並列動作を確認。

そして、**TODOが残っていないか確認。**