#!/usr/bin/env python3
"""
LLMService - LLM呼び出しサービス

LLM呼び出しのコントロール専用サービス
プロンプト設計・管理と動的ツール取得・プロンプト動的埋め込みを提供
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI
from config.loggers import GenericLogger, log_prompt_with_tokens

# 環境変数を読み込み
load_dotenv()


class LLMService:
    """LLM呼び出しサービス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm")
        
        # OpenAI設定を環境変数から取得
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.8"))
        
        # OpenAIクライアントを初期化
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            self.logger.info(f"✅ [LLMService] OpenAI client initialized with model: {self.openai_model}")
        else:
            self.openai_client = None
            self.logger.warning("⚠️ [LLMService] OPENAI_API_KEY not found, LLM calls will be disabled")
    
    def _build_planning_prompt(self, user_request: str) -> str:
        """
        タスク分解用のプロンプトを構築（サービスメソッド名対応版）
        
        Args:
            user_request: ユーザーリクエスト
        
        Returns:
            構築されたプロンプト
        """
        planning_prompt = f"""
ユーザー要求を分析し、適切なサービスクラスのメソッド呼び出しに分解してください。

ユーザー要求: "{user_request}"

利用可能なサービスと機能:

- **inventory_service**: 在庫管理サービス
  - `get_inventory()`: 現在の全在庫アイテムのリストを取得します。
  - `add_inventory(item_name: str, quantity: float, ...)`: 在庫に新しいアイテムを追加します。
  - `update_inventory(item_identifier: str, updates: dict, strategy: str)`: 在庫情報を更新します。strategyには 'by_id', 'by_name', 'by_name_oldest', 'by_name_latest' が指定可能です。
  - `delete_inventory(item_identifier: str, strategy: str)`: 在庫を削除します。strategyには 'by_id', 'by_name', 'by_name_oldest', 'by_name_latest' が指定可能です。

- **recipe_service**: レシピ・献立サービス
  - `generate_menu_plan(inventory_items: list, user_id: str, ...)`: 在庫リストに基づき、LLMによる独創的な献立提案を行います。過去の履歴も考慮します。
  - `search_menu_from_rag(query: str, user_id: str, ...)`: RAGを使用して過去の献立履歴から類似の献立を検索します。
  - `search_recipes_from_web(recipe_name: str, ...)`: 指定された料理名のレシピをWeb検索し、URLを含む詳細情報を返します。
  - `get_recipe_history(user_id: str, ...)`: 過去の料理履歴を取得します。

- **session_service**: セッション管理サービス（通常は直接呼び出し不要）

**最重要ルール: 献立生成の際のタスク構成**

ユーザーの要求が「献立」や「レシピ」に関するものである場合、必ず以下の4段階のタスク構成を使用してください：

1. **task1**: `inventory_service.get_inventory()` を呼び出し、現在の在庫をすべて取得する。
2. **task2**: `recipe_service.generate_menu_plan()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。
3. **task3**: `recipe_service.search_menu_from_rag()` を呼び出す。その際、ステップ1で取得した在庫情報を `inventory_items` パラメータに設定する。
4. **task4**: `recipe_service.search_recipes_from_web()` を呼び出す。その際、ステップ2とステップ3の結果を適切に処理する。

**並列実行の指示**: task2とtask3は並列で実行可能です。dependenciesにtask1のみを指定してください。

**献立データの処理ルール**:
- task2とtask3の結果は辞書形式の献立データです（main_dish, side_dish, soupフィールドを含む）
- task4では、task2とtask3の両方の結果を統合してレシピ検索を行ってください：
  - `"recipe_titles": ["task2.result.main_dish", "task2.result.side_dish", "task3.result.main_dish", "task3.result.side_dish"]`
  - または、主菜のみ: `"recipe_titles": ["task2.result.main_dish", "task3.result.main_dish"]`

**パラメータ注入のルール**:
- 先行タスクの結果を後続タスクのパラメータに注入する場合は、必ず `"先行タスク名.result"` 形式を使用してください。
- 辞書フィールド参照の場合は `"先行タスク名.result.フィールド名"` 形式を使用してください。
- 例: task1の結果をtask2で使用する場合 → `"inventory_items": "task1.result"`
- 例: task2の主菜をtask4で使用する場合 → `"recipe_title": "task2.result.main_dish"`
- この形式により、システムが自動的に先行タスクの結果を後続タスクに注入します。

**曖昧な在庫操作の指示について**:
- ユーザーが「古い方」「最新」などを明示しない限り、`update_inventory` や `delete_inventory` の `strategy` パラメータは `'by_name'` を指定してください。これにより、サービス層でユーザーへの確認プロセスが起動します。
- 例: 「牛乳を削除して」 → `delete_inventory(item_identifier='牛乳', strategy='by_name')`
- 例: 「古い牛乳を削除して」 → `delete_inventory(item_identifier='牛乳', strategy='by_name_oldest')`

**出力形式**: 必ず以下のJSON形式で回答してください（コメントは禁止）：

{{
    "tasks": [
        {{
            "id": "task1",
            "description": "タスクの自然言語での説明",
            "service": "呼び出すサービス名",
            "method": "呼び出すメソッド名",
            "parameters": {{ "key": "value" }},
            "dependencies": []
        }}
    ]
}}

**献立生成の具体例（サービスメソッド名対応）**:
{{
    "tasks": [
        {{
            "id": "task1",
            "description": "現在の全在庫アイテムのリストを取得する",
            "service": "inventory_service",
            "method": "get_inventory",
            "parameters": {{}},
            "dependencies": []
        }},
        {{
            "id": "task2",
            "description": "在庫リストに基づき、LLMによる独創的な献立を提案する",
            "service": "recipe_service",
            "method": "generate_menu_plan",
            "parameters": {{ "inventory_items": "task1.result", "user_id": "user123" }},
            "dependencies": ["task1"]
        }},
        {{
            "id": "task3",
            "description": "在庫リストに基づき、RAGを使用して過去の献立履歴から類似献立を検索する",
            "service": "recipe_service",
            "method": "search_menu_from_rag",
            "parameters": {{ "inventory_items": "task1.result", "user_id": "user123" }},
            "dependencies": ["task1"]
        }},
        {{
            "id": "task4",
            "description": "提案された献立のレシピをWeb検索して詳細情報を取得する",
            "service": "recipe_service",
            "method": "search_recipes_from_web",
            "parameters": {{ 
                "recipe_titles": ["task2.result.main_dish", "task2.result.side_dish", "task3.result.main_dish", "task3.result.side_dish"],
                "menu_categories": ["main_dish", "side_dish", "main_dish", "side_dish"],
                "menu_source": "mixed"
            }},
            "dependencies": ["task2", "task3"]
        }}
    ]
}}

**依存関係のルール**:
- 各タスクには一意のID（task1, task2, ...）を付与してください。
- `dependencies` には、実行前に完了しているべきタスクのIDをリストで指定してください。
- 依存関係がない場合は空配列 `[]` を指定してください。

**挨拶や一般的な会話の場合**:
- タスクは生成せず、空の配列 `{{"tasks": []}}` を返してください。
"""
        return planning_prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """
        OpenAI APIを呼び出してレスポンスを取得
        
        Args:
            prompt: 送信するプロンプト
        
        Returns:
            LLMからのレスポンス
        """
        try:
            if not self.openai_client:
                raise Exception("OpenAI client not initialized")
            
            self.logger.info(f"🔧 [LLMService] Calling OpenAI API with model: {self.openai_model}")
            
            # プロンプトとトークン数をログ出力（全文表示）
            log_prompt_with_tokens(prompt, max_tokens=2000, logger_name="service.llm", show_full_prompt=True)
            
            response = await self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "あなたは優秀なタスク分解アシスタントです。ユーザーの要求を適切なサービスクラスのメソッド呼び出しに分解してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.openai_temperature,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            self.logger.info(f"✅ [LLMService] OpenAI API response received: {len(content)} characters")
            
            # LLMレスポンスを改行付きでログ出力
            self.logger.info(f"📄 [LLMService] LLM Response:\n{content}")
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] OpenAI API call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        LLMレスポンスを解析してタスクリストを抽出
        
        Args:
            response: LLMからのレスポンス
        
        Returns:
            解析されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [LLMService] Parsing LLM response")
            
            # JSON部分を抽出（```json```で囲まれている場合がある）
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()
            
            # JSON解析
            result = json.loads(json_str)
            tasks = result.get("tasks", [])
            
            self.logger.info(f"✅ [LLMService] Parsed {len(tasks)} tasks from LLM response")
            return tasks
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ [LLMService] JSON parsing failed: {e}")
            self.logger.error(f"Response content: {response}")
            return []
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error parsing LLM response: {e}")
            return []
    
    def _convert_to_task_format(self, tasks: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        LLMタスクをActionPlannerが期待する形式に変換
        
        Args:
            tasks: LLMから取得したタスクリスト
            user_id: ユーザーID
        
        Returns:
            変換されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [LLMService] Converting {len(tasks)} tasks to ActionPlanner format")
            
            converted_tasks = []
            for task in tasks:
                # user_idをパラメータに追加
                parameters = task.get("parameters", {})
                if "user_id" not in parameters:
                    parameters["user_id"] = user_id
                
                converted_task = {
                    "service": task.get("service"),
                    "method": task.get("method"),
                    "parameters": parameters,
                    "dependencies": task.get("dependencies", [])
                }
                converted_tasks.append(converted_task)
            
            self.logger.info(f"✅ [LLMService] Converted {len(converted_tasks)} tasks successfully")
            return converted_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error converting tasks: {e}")
            return []
    
    async def decompose_tasks(
        self, 
        user_request: str, 
        available_tools: List[str], 
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        実際のLLM呼び出しによるタスク分解
        
        Args:
            user_request: ユーザーリクエスト
            available_tools: 利用可能なツールリスト
            user_id: ユーザーID
        
        Returns:
            分解されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [LLMService] Decomposing tasks for user: {user_id}")
            self.logger.info(f"📝 [LLMService] User request: '{user_request}'")
            
            # OpenAIクライアントが初期化されていない場合はフォールバック
            if not self.openai_client:
                self.logger.warning("⚠️ [LLMService] OpenAI client not available, using fallback")
                return self._get_fallback_tasks(user_id)
            
            # 1. プロンプト構築
            prompt = self._build_planning_prompt(user_request)
            
            # 2. OpenAI API呼び出し
            response = await self._call_openai_api(prompt)
            
            # 3. JSON解析
            tasks = self._parse_llm_response(response)
            
            # 4. タスク形式に変換
            converted_tasks = self._convert_to_task_format(tasks, user_id)
            
            # 生成されたタスクの詳細をログ出力
            self.logger.info(f"✅ [LLMService] Tasks decomposed successfully: {len(converted_tasks)} tasks")
            for i, task in enumerate(converted_tasks, 1):
                self.logger.info(f"📋 [LLMService] Task {i}:")
                self.logger.info(f"  Service: {task.get('service')}")
                self.logger.info(f"  Method: {task.get('method')}")
                self.logger.info(f"  Parameters: {task.get('parameters')}")
                self.logger.info(f"  Dependencies: {task.get('dependencies')}")
            
            return converted_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in decompose_tasks: {e}")
            # エラー時はフォールバック
            return self._get_fallback_tasks(user_id)
    
    def _get_fallback_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        フォールバック用のタスク（LLM呼び出し失敗時）
        
        Args:
            user_id: ユーザーID
        
        Returns:
            フォールバックタスクリスト
        """
        self.logger.info(f"🔄 [LLMService] Using fallback tasks for user: {user_id}")
        
        return [
            {
                "service": "InventoryService",
                "method": "get_inventory",
                "parameters": {"user_id": user_id},
                "dependencies": []
            }
        ]
    
    async def format_response(
        self, 
        results: Dict[str, Any]
    ) -> str:
        """
        最終回答整形
        
        Args:
            results: タスク実行結果辞書 (task1, task2, task3, task4)
        
        Returns:
            整形された回答
        """
        try:
            self.logger.info(f"🔧 [LLMService] Formatting response for {len(results)} results")
            
            # task4のWeb検索結果を取得
            web_recipes = []
            if "task4" in results and results["task4"].get("success"):
                web_data = results["task4"].get("result", {}).get("data", [])
                web_recipes = web_data
            
            # task2とtask3の献立を取得
            llm_menu = {}
            rag_menu = {}
            if "task2" in results and results["task2"].get("success"):
                llm_menu = results["task2"].get("result", {}).get("data", {})
            if "task3" in results and results["task3"].get("success"):
                rag_menu = results["task3"].get("result", {}).get("data", {})
            
            # レスポンスを構築
            response_parts = []
            
            # 献立提案
            if llm_menu:
                response_parts.append("🍽️ **LLM献立提案**")
                response_parts.append(f"主菜: {llm_menu.get('main_dish', 'N/A')}")
                response_parts.append(f"副菜: {llm_menu.get('side_dish', 'N/A')}")
                response_parts.append(f"汁物: {llm_menu.get('soup', 'N/A')}")
                response_parts.append("")
            
            if rag_menu:
                response_parts.append("🔍 **RAG献立提案**")
                response_parts.append(f"主菜: {rag_menu.get('main_dish', 'N/A')}")
                response_parts.append(f"副菜: {rag_menu.get('side_dish', 'N/A')}")
                response_parts.append(f"汁物: {rag_menu.get('soup', 'N/A')}")
                response_parts.append("")
            
            # Web検索結果（詳細分類対応）
            if web_recipes:
                response_parts.append("🌐 **レシピ検索結果**")
                
                # LLM献立の結果
                llm_menu = web_recipes.get("llm_menu", {})
                if any(llm_menu.values()):
                    response_parts.append("")
                    response_parts.append("🍽️ **LLM献立提案**")
                    
                    for category, data in llm_menu.items():
                        if data.get("title") and data.get("recipes"):
                            category_emoji = {"main_dish": "🥩", "side_dish": "🥬", "soup": "🍲"}.get(category, "🍽️")
                            response_parts.append(f"{category_emoji} **{category.replace('_', ' ').title()}: {data['title']}**")
                            
                            for i, recipe in enumerate(data["recipes"][:3], 1):  # 上位3件のみ
                                response_parts.append(f"{i}. {recipe.get('title', 'N/A')}")
                                response_parts.append(f"   URL: {recipe.get('url', 'N/A')}")
                                response_parts.append(f"   説明: {recipe.get('description', 'N/A')[:100]}...")
                                response_parts.append("")
                
                # RAG献立の結果
                rag_menu = web_recipes.get("rag_menu", {})
                if any(rag_menu.values()):
                    response_parts.append("")
                    response_parts.append("🔍 **RAG献立提案**")
                    
                    for category, data in rag_menu.items():
                        if data.get("title") and data.get("recipes"):
                            category_emoji = {"main_dish": "🥩", "side_dish": "🥬", "soup": "🍲"}.get(category, "🍽️")
                            response_parts.append(f"{category_emoji} **{category.replace('_', ' ').title()}: {data['title']}**")
                            
                            for i, recipe in enumerate(data["recipes"][:3], 1):  # 上位3件のみ
                                response_parts.append(f"{i}. {recipe.get('title', 'N/A')}")
                                response_parts.append(f"   URL: {recipe.get('url', 'N/A')}")
                                response_parts.append(f"   説明: {recipe.get('description', 'N/A')[:100]}...")
                                response_parts.append("")
            
            if not response_parts:
                return "タスクが完了しましたが、結果を取得できませんでした。"
            
            final_response = "\n".join(response_parts)
            self.logger.info(f"✅ [LLMService] Response formatted successfully")
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in format_response: {e}")
            return "タスクが完了しましたが、レスポンスの生成に失敗しました。"
    
    async def solve_constraints(
        self, 
        candidates: List[Dict], 
        constraints: Dict
    ) -> Dict:
        """
        制約解決（子ファイル委譲）
        
        Args:
            candidates: 候補リスト
            constraints: 制約条件
        
        Returns:
            制約解決結果
        """
        try:
            self.logger.info(f"🔧 [LLMService] Solving constraints for {len(candidates)} candidates")
            
            # TODO: 実際の制約解決ロジックを実装
            # 現在は基本的な実装
            result = {
                "selected": candidates[0] if candidates else {},
                "reason": "制約解決により選択されました"
            }
            
            self.logger.info(f"✅ [LLMService] Constraints solved successfully")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in solve_constraints: {e}")
            return {"selected": {}, "reason": "エラーが発生しました"}
    
    def get_available_tools_description(self) -> str:
        """
        利用可能なツールの説明を取得
        
        Returns:
            ツール説明の文字列
        """
        try:
            self.logger.info(f"🔧 [LLMService] Getting available tools description")
            
            # TODO: ServiceCoordinator経由で取得するように修正予定
            # 現在は基本的な実装
            description_text = "利用可能なツール:\n"
            description_text += "- inventory_list: ユーザーの全在庫アイテムを取得\n"
            description_text += "- generate_menu_plan: 在庫食材から献立構成を生成\n"
            
            self.logger.info(f"✅ [LLMService] Tools description generated successfully")
            return description_text
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in get_available_tools_description: {e}")
            return "ツール情報の取得に失敗しました。"
    
    def create_dynamic_prompt(
        self, 
        base_prompt: str, 
        tool_descriptions: str,
        user_context: Dict[str, Any]
    ) -> str:
        """
        動的プロンプト生成
        
        Args:
            base_prompt: ベースプロンプト
            tool_descriptions: ツール説明
            user_context: ユーザーコンテキスト
        
        Returns:
            動的プロンプト
        """
        try:
            self.logger.info(f"🔧 [LLMService] Creating dynamic prompt")
            
            # 動的プロンプトを生成
            dynamic_prompt = f"""
{base_prompt}

{tool_descriptions}

ユーザーコンテキスト:
- ユーザーID: {user_context.get('user_id', 'N/A')}
- セッションID: {user_context.get('session_id', 'N/A')}
- リクエスト時刻: {user_context.get('timestamp', 'N/A')}
"""
            
            self.logger.info(f"✅ [LLMService] Dynamic prompt created successfully")
            
            return dynamic_prompt
            
        except Exception as e:
            self.logger.error(f"❌ [LLMService] Error in create_dynamic_prompt: {e}")
            return base_prompt
