あなた（コーデイング支援AI）は**必ず間違える** のですから、**ソース修正は、絶対に承認後**を遵守してください。
かたく**破壊的行動は謹んでください**。

## 🔧 Phase 4: コア機能実装　に着手。

現在、一旦 core の実装、およびテストの実装は完了。
テストで問題発生。
2025-10-07 09:01:53 - morizo_ai.core.planner         - ERROR - ❌ [PLANNER] Task planning failed: LLMService.get_available_tools_description() missing 1 required positional argument: 'tool_router'
2025-10-07 09:01:53 - morizo_ai.core.agent           - ERROR - ❌ [AGENT] Request processing failed: Failed to plan tasks: LLMService.get_available_tools_description() missing 1 required positional argument: 'tool_router'

tool_router 利用の実装について迷走中。

現状は、各サービスにtool_router を内包するイメージで検討中。

core に ServiceCoordinatorなんてクラスがあるのなら、ここで管理できない？
