あなた（コーデイング支援AI）は**必ず間違える** のですから、**ソース修正は、絶対に承認後**を遵守してください。
かたく**破壊的行動は謹んでください**。

## 🔧 Phase 3: サービス層実装　に着手。

とりあえず、TOOL_ROUTER の実装と、inventory_listでの、簡易試験tests/05_1_test_service_first.py　はOK。

後は、残り各サービスの簡単なテスト

- recipe_service.py　⇒　06_6_test_mcp_integration.py相当をサービス経由でテスト
命名は、05_2_test_service_integration.py を実装。
⇒　とりあえず、テスト完了


以降は良くわからんから、とりあえず動作確認のテストを作ってもらうか。
- llm_service.py
- confirmation_service.py
- session_service.py
