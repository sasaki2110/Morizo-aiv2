#!/usr/bin/env python3
"""
ResponseProcessor - レスポンス処理

LLMServiceから分離したレスポンス処理専用クラス
JSON解析、タスク形式変換、最終回答整形を担当
"""

import json
from typing import Dict, Any, List, Optional
from config.loggers import GenericLogger
from .utils import ResponseProcessorUtils
from .response_formatters import ResponseFormatters
from .menu_data_generator import MenuDataGenerator


class ResponseProcessor:
    """レスポンス処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response")
        self.utils = ResponseProcessorUtils()
        self.formatters = ResponseFormatters()
        self.menu_generator = MenuDataGenerator()
    
    def parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        LLMレスポンスを解析してタスクリストを抽出
        
        Args:
            response: LLMからのレスポンス
        
        Returns:
            解析されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [ResponseProcessor] Parsing LLM response")
            
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
            
            self.logger.info(f"✅ [ResponseProcessor] Parsed {len(tasks)} tasks from LLM response")
            return tasks
            
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ [ResponseProcessor] JSON parsing failed: {e}")
            self.logger.error(f"Response content: {response}")
            return []
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error parsing LLM response: {e}")
            return []
    
    def convert_to_task_format(self, tasks: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        LLMタスクをActionPlannerが期待する形式に変換
        
        Args:
            tasks: LLMから取得したタスクリスト
            user_id: ユーザーID
        
        Returns:
            変換されたタスクリスト
        """
        try:
            self.logger.info(f"🔧 [ResponseProcessor] Converting {len(tasks)} tasks to ActionPlanner format")
            
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
            
            self.logger.info(f"✅ [ResponseProcessor] Converted {len(converted_tasks)} tasks successfully")
            return converted_tasks
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error converting tasks: {e}")
            return []
    
    async def format_final_response(self, results: Dict[str, Any], sse_session_id: str = None) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        最終回答整形（サービス・メソッドベース）
        
        Args:
            results: タスク実行結果辞書
            sse_session_id: SSEセッションID
        
        Returns:
            (整形された回答, JSON形式のレシピデータ)
        """
        try:
            # 献立提案シナリオかどうかを判定
            is_menu_scenario = self.utils.is_menu_scenario(results)
            
            # レスポンス構築
            response_parts, menu_data = await self._build_response_parts(results, is_menu_scenario, sse_session_id)
            
            # 空レスポンスの処理
            return self._handle_empty_response(response_parts, menu_data)
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error in format_final_response: {e}")
            return "タスクが完了しましたが、レスポンスの生成に失敗しました。", None
    
    async def _build_response_parts(self, results: Dict[str, Any], is_menu_scenario: bool, sse_session_id: str = None) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """
        レスポンスパーツを構築
        
        Args:
            results: タスク実行結果辞書
            is_menu_scenario: 献立提案シナリオかどうか
        
        Returns:
            (レスポンスパーツリスト, JSON形式のレシピデータ)
        """
        response_parts = []
        menu_data = None
        
        # サービス・メソッドベースの処理
        for task_id, task_result in results.items():
            try:
                # タスクの成功チェック
                if not task_result.get("success"):
                    continue
                
                # サービス・メソッド情報の取得
                service = task_result.get("service", "")
                method = task_result.get("method", "")
                service_method = f"{service}.{method}"
                
                # データの取得
                self.logger.info(f"🔍 [DEBUG] task_result: {task_result}")
                self.logger.info(f"🔍 [DEBUG] task_result type: {type(task_result)}")
                self.logger.info(f"🔍 [DEBUG] task_result keys: {list(task_result.keys()) if isinstance(task_result, dict) else 'Not a dict'}")
                result_value = task_result.get("result", {})
                self.logger.info(f"🔍 [DEBUG] result_value: {result_value}")
                data = result_value if isinstance(result_value, dict) else {}
                self.logger.info(f"🔍 [DEBUG] data: {data}")
                
                # サービス・メソッド別の処理
                parts, menu = await self._process_service_method(service_method, data, is_menu_scenario, task_id, results, sse_session_id)
                response_parts.extend(parts)
                
                # メニューデータの更新（最初に見つかったものを使用）
                if menu and not menu_data:
                    menu_data = menu
                    
            except Exception as e:
                self.logger.error(f"❌ [ResponseProcessor] Error processing task {task_id}: {e}")
                continue
        
        return response_parts, menu_data
    
    async def _process_service_method(self, service_method: str, data: Any, is_menu_scenario: bool, task_id: str, results: Dict[str, Any] = None, sse_session_id: str = None) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """
        サービス・メソッド別の処理
        
        Args:
            service_method: サービス・メソッド名
            data: 処理データ
            is_menu_scenario: 献立提案シナリオかどうか
            task_id: タスクID
            results: 全タスクの実行結果
        
        Returns:
            (レスポンスパーツリスト, JSON形式のレシピデータ)
        """
        response_parts = []
        menu_data = None
        
        try:
            if service_method == "inventory_service.get_inventory":
                response_parts.extend(self.formatters.format_inventory_list(data, is_menu_scenario))
                
                # Phase 1F: 在庫情報をセッションに保存（追加提案時の再利用用）
                if data.get("success") and sse_session_id:
                    from services.session_service import session_service
                    inventory_items = data.get("data", [])
                    item_names = [item.get("item_name") for item in inventory_items if item.get("item_name")]
                    
                    await session_service.set_session_context(sse_session_id, "inventory_items", item_names)
                    self.logger.info(f"💾 [RESPONSE] Saved {len(item_names)} inventory items to session")
                
            elif service_method == "inventory_service.add_inventory":
                # デバッグログ: サービスメソッドとデータを確認
                self.logger.info(f"🔍 [DEBUG] Processing inventory_service.add_inventory")
                self.logger.info(f"🔍 [DEBUG] service_method: {service_method}")
                self.logger.info(f"🔍 [DEBUG] data: {data}")
                self.logger.info(f"🔍 [DEBUG] data type: {type(data)}")
                response_parts.extend(self.formatters.format_inventory_add(data))
                
            elif service_method == "inventory_service.update_inventory":
                response_parts.extend(self.formatters.format_inventory_update(data))
                
            elif service_method == "inventory_service.delete_inventory":
                response_parts.extend(self.formatters.format_inventory_delete(data))
                
            elif service_method == "recipe_service.generate_menu_plan":
                # LLM献立提案は表示しない（Web検索結果のみ表示）
                pass
                
            elif service_method == "recipe_service.search_menu_from_rag":
                # RAG献立提案は表示しない（Web検索結果のみ表示）
                pass
                
            elif service_method == "recipe_service.search_recipes_from_web":
                # task4完了時にtask3とtask4の結果を統合して選択UIを表示
                self.logger.info(f"🔍 [ResponseProcessor] Task4 completed, integrating with task3 results")
                
                # resultsからtask3の結果を直接取得
                task3_result = None
                if results:
                    for task_key, task_data in results.items():
                        if task_key == "task3" and task_data.get("success"):
                            task3_result = task_data.get("result", {})
                            break
                
                if task3_result and task3_result.get("success") and task3_result.get("data", {}).get("candidates"):
                    candidates = task3_result["data"]["candidates"]
                    
                    # task4のWeb検索結果を統合
                    candidates_with_urls = self._integrate_web_search_results(candidates, task_id, data)
                    
                    # Phase 1F: 提案済みタイトルをセッションに保存
                    if sse_session_id:
                        from services.session_service import session_service
                        titles = [c.get("title") for c in candidates_with_urls if c.get("title")]
                        
                        await session_service.add_proposed_recipes(sse_session_id, "main", titles)
                        self.logger.info(f"💾 [RESPONSE] Saved {len(titles)} proposed titles to session")
                    
                    # Phase 3C-3: 候補情報をセッションに保存（詳細情報）
                    if sse_session_id:
                        from services.session_service import session_service
                        session = await session_service.get_session(sse_session_id, user_id=None)
                        if session:
                            current_stage = session.get_current_stage()
                            category = current_stage  # "main", "sub", "soup"
                            await session_service.set_candidates(sse_session_id, category, candidates_with_urls)
                            self.logger.info(f"💾 [RESPONSE] Saved {len(candidates_with_urls)} {category} candidates to session")
                    
                    # Phase 3D: セッションから段階情報を取得
                    stage_info = {}
                    if sse_session_id:
                        from services.session_service import session_service
                        session = await session_service.get_session(sse_session_id, user_id=None)
                        if session:
                            current_stage = session.get_current_stage()
                            self.logger.info(f"🔍 [ResponseProcessor] Phase 3D: current_stage={current_stage}")
                            stage_info["current_stage"] = current_stage
                            
                            # 使い残し食材を計算（在庫食材 - 使用済み食材）
                            used_ingredients = session.get_used_ingredients()
                            inventory_items = session.context.get("inventory_items", [])
                            
                            # 使い残し食材 = 在庫食材から使用済み食材を除外
                            # 表記ゆれ（「レンコン」と「れんこん」など）に対応するため、正規化して比較
                            # Sessionクラスの正規化メソッドを使用
                            used_ingredients_normalized = {
                                session._normalize_ingredient_name(item) for item in used_ingredients
                            }
                            
                            remaining_ingredients = []
                            remaining_normalized = set()  # 重複除去用
                            
                            for item in inventory_items:
                                item_normalized = session._normalize_ingredient_name(item)
                                if item_normalized not in used_ingredients_normalized:
                                    # 重複除去：正規化後の名前で既に追加済みかチェック
                                    if item_normalized not in remaining_normalized:
                                        remaining_ingredients.append(item)  # 元の在庫名を保持
                                        remaining_normalized.add(item_normalized)
                            
                            self.logger.info(f"🔍 [ResponseProcessor] Phase 3D: used_ingredients={used_ingredients}")
                            self.logger.info(f"🔍 [ResponseProcessor] Phase 3D: inventory_items={inventory_items}")
                            self.logger.info(f"🔍 [ResponseProcessor] Phase 3D: remaining_ingredients={remaining_ingredients}")
                            
                            if remaining_ingredients:
                                stage_info["used_ingredients"] = remaining_ingredients  # 使い残し食材を返す（フィールド名は変更しない）
                            
                            # メニューカテゴリを取得
                            menu_category = session.get_menu_category()
                            self.logger.info(f"🔍 [ResponseProcessor] Phase 3D: menu_category={menu_category}")
                            if menu_category:
                                stage_info["menu_category"] = menu_category
                        
                        self.logger.info(f"🔍 [ResponseProcessor] Phase 3D: stage_info={stage_info}")
                    
                    # 選択UI用のデータを返す
                    return [], {
                        "requires_selection": True,
                        "candidates": candidates_with_urls,
                        "task_id": task_id,
                        "message": "以下の5件から選択してください:",
                        **stage_info  # Phase 3D: 段階情報を統合
                    }
                else:
                    # task3の結果が取得できない場合は通常のWeb検索結果を表示
                    response_parts.extend(self.formatters.format_web_recipes(data))
                    menu_data = self.menu_generator.generate_menu_data_json(data)
                
            elif service_method == "recipe_service.generate_proposals":
                # task3完了時は進捗のみ（選択UIは表示しない）
                # task4完了後に統合処理を行う
                self.logger.info(f"🔍 [ResponseProcessor] Task3 completed, waiting for task4 integration")
                
                # Phase 1F: 提案済みタイトルをセッションに保存
                if data.get("success") and sse_session_id:
                    from services.session_service import session_service
                    candidates = data.get("data", {}).get("candidates", [])
                    titles = [c.get("title") for c in candidates if c.get("title")]
                    
                    await session_service.add_proposed_recipes(sse_session_id, "main", titles)
                    self.logger.info(f"💾 [RESPONSE] Saved {len(titles)} proposed titles to session")
                
                # 何も返さない（進捗状態のみ）
                pass
                
            else:
                # 未知のサービス・メソッドの場合は汎用処理
                response_parts.extend(self.formatters.format_generic_result(service_method, data))
                
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error formatting {service_method} for task {task_id}: {e}")
            response_parts.append(f"データの処理中にエラーが発生しました: {str(e)}")
        
        return response_parts, menu_data
    
    def _integrate_web_search_results(self, candidates: List[Dict[str, Any]], task_id: str, task4_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Web検索結果を主菜提案結果に統合
        
        Args:
            candidates: 主菜提案の候補リスト
            task_id: タスクID
            task4_data: task4の実行結果データ
        
        Returns:
            URL情報が統合された候補リスト
        """
        try:
            # task4の結果からWeb検索結果を取得
            web_search_results = []
            if task4_data and task4_data.get("success") and task4_data.get("data"):
                web_data = task4_data["data"]
                # Web検索結果からレシピリストを抽出
                if "rag_menu" in web_data and "main_dish" in web_data["rag_menu"]:
                    recipes = web_data["rag_menu"]["main_dish"].get("recipes", [])
                    web_search_results = recipes
            
            if not web_search_results:
                self.logger.info(f"🔍 [ResponseProcessor] No web search results found for task {task_id}")
                return candidates
            
            # 候補とWeb検索結果を統合
            integrated_candidates = []
            for i, candidate in enumerate(candidates):
                integrated_candidate = candidate.copy()
                
                # 対応するWeb検索結果を取得
                if i < len(web_search_results):
                    web_result = web_search_results[i]
                    if web_result.get("url"):
                        # URL情報を統合
                        integrated_candidate["urls"] = [{
                            "title": web_result.get("title", ""),
                            "url": web_result.get("url", ""),
                            "domain": self._extract_domain(web_result.get("url", ""))
                        }]
                        self.logger.info(f"🔗 [ResponseProcessor] Integrated URLs for candidate {i}: {integrated_candidate.get('urls', [])}")
                    else:
                        self.logger.warning(f"⚠️ [ResponseProcessor] Web search result has no URL for candidate {i}")
                else:
                    self.logger.warning(f"⚠️ [ResponseProcessor] No web search result for candidate {i}")
                
                integrated_candidates.append(integrated_candidate)
            
            self.logger.info(f"✅ [ResponseProcessor] Successfully integrated web search results for {len(integrated_candidates)} candidates")
            return integrated_candidates
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error integrating web search results: {e}")
            return candidates
    
    def _get_task3_result_from_history(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスク実行履歴からtask3の結果を取得
        
        Args:
            task_id: タスクID
        
        Returns:
            task3の結果
        """
        try:
            # タスク実行履歴からtask3の結果を取得
            # 実際の実装では、タスク実行履歴サービスを使用
            self.logger.info(f"🔍 [ResponseProcessor] Getting task3 result for task {task_id}")
            
            # TODO: 実際のタスク実行履歴サービスから取得
            # task_history = self.task_history_service.get_task_results(task_id)
            # task3_result = task_history.get("task3", {}).get("result", {})
            
            # 簡易実装としてNoneを返す（実際の実装では正しい結果を返す）
            return None
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error getting task3 result: {e}")
            return None

    def _get_web_search_results_from_task_history(self, task_id: str) -> List[Dict[str, Any]]:
        """
        タスク実行履歴からWeb検索結果を取得
        
        Args:
            task_id: タスクID
        
        Returns:
            Web検索結果のリスト
        """
        try:
            # タスク実行履歴からtask4の結果を取得
            # 実際の実装では、タスク実行履歴サービスを使用
            # ここでは簡易実装として空のリストを返す
            self.logger.info(f"🔍 [ResponseProcessor] Getting web search results for task {task_id}")
            
            # TODO: 実際のタスク実行履歴サービスから取得
            # task_history = self.task_history_service.get_task_results(task_id)
            # web_search_results = task_history.get("task4", {}).get("result", [])
            
            return []
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error getting web search results: {e}")
            return []
    
    def _extract_urls_from_web_result(self, web_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Web検索結果からURL情報を抽出
        
        Args:
            web_data: Web検索結果データ
        
        Returns:
            URL情報のリスト
        """
        try:
            urls = []
            
            # Web検索結果の構造に応じてURL情報を抽出
            if isinstance(web_data, dict):
                # レシピリストからURL情報を抽出
                recipes = web_data.get("recipes", [])
                for recipe in recipes:
                    if isinstance(recipe, dict) and "url" in recipe:
                        url_info = {
                            "title": recipe.get("title", ""),
                            "url": recipe.get("url", ""),
                            "domain": self._extract_domain(recipe.get("url", ""))
                        }
                        urls.append(url_info)
            
            self.logger.info(f"🔗 [ResponseProcessor] Extracted {len(urls)} URLs from web result")
            return urls
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error extracting URLs: {e}")
            return []
    
    def _extract_domain(self, url: str) -> str:
        """
        URLからドメイン名を抽出
        
        Args:
            url: URL文字列
        
        Returns:
            ドメイン名
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""
    
    def _handle_empty_response(self, response_parts: List[str], menu_data: Optional[Dict[str, Any]]) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        空レスポンスの処理
        
        Args:
            response_parts: レスポンスパーツリスト
            menu_data: JSON形式のレシピデータ
        
        Returns:
            (最終レスポンス, JSON形式のレシピデータ)
        """
        # レスポンスが空の場合は適切な挨拶メッセージを返す
        if not response_parts:
            return "こんにちは！何かお手伝いできることはありますか？", None
        
        final_response = "\n".join(response_parts)
        self.logger.info(f"🔧 [ResponseProcessor] Final response: {final_response}")
        self.logger.info(f"✅ [ResponseProcessor] Response formatted successfully")
        
        # JSON形式のレシピデータがある場合は、レスポンスに含める
        if menu_data:
            self.logger.info(f"📊 [ResponseProcessor] Menu data JSON generated: {len(str(menu_data))} characters")
            self.logger.info(f"🔍 [ResponseProcessor] Menu data preview: {str(menu_data)[:200]}...")
        else:
            self.logger.info(f"⚠️ [ResponseProcessor] No menu data generated")
        
        return final_response, menu_data
