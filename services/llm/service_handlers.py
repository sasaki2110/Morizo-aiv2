#!/usr/bin/env python3
"""
ServiceHandlers - サービス別レスポンス処理ハンドラー

在庫サービス、レシピサービス、汎用サービスのレスポンス処理を担当
"""

from typing import Dict, Any, List, Optional
from config.loggers import GenericLogger


class InventoryServiceHandler:
    """在庫サービス処理ハンドラー"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.inventory_handler")
    
    async def handle(self, service_method: str, data: Any, is_menu_scenario: bool, sse_session_id: Optional[str] = None, formatters = None, session_service = None) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """
        在庫サービス関連の処理
        
        Args:
            service_method: サービス・メソッド名
            data: 処理データ
            is_menu_scenario: 献立提案シナリオかどうか
            sse_session_id: SSEセッションID
            formatters: ResponseFormattersインスタンス
            session_service: セッションサービスインスタンス
        
        Returns:
            (レスポンスパーツリスト, JSON形式のレシピデータ)
        """
        response_parts = []
        
        try:
            if service_method == "inventory_service.get_inventory":
                response_parts.extend(formatters.format_inventory_list(data, is_menu_scenario))
                
                # Phase 1F: 在庫情報をセッションに保存（追加提案時の再利用用）
                if data.get("success") and sse_session_id and session_service:
                    inventory_items = data.get("data", [])
                    item_names = [item.get("item_name") for item in inventory_items if item.get("item_name")]
                    
                    await session_service.set_session_context(sse_session_id, "inventory_items", item_names)
                    self.logger.info(f"💾 [InventoryServiceHandler] Saved {len(item_names)} inventory items to session")
                
            elif service_method == "inventory_service.add_inventory":
                response_parts.extend(formatters.format_inventory_add(data))
                
            elif service_method == "inventory_service.update_inventory":
                response_parts.extend(formatters.format_inventory_update(data))
                
            elif service_method == "inventory_service.delete_inventory":
                response_parts.extend(formatters.format_inventory_delete(data))
        
        except Exception as e:
            self.logger.error(f"❌ [InventoryServiceHandler] Error handling inventory service {service_method}: {e}")
            response_parts.append(f"データの処理中にエラーが発生しました: {str(e)}")
        
        return response_parts, None


class RecipeServiceHandler:
    """レシピサービス処理ハンドラー"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.recipe_handler")
    
    async def handle(self, service_method: str, data: Any, is_menu_scenario: bool, task_id: str, results: Optional[Dict[str, Any]] = None, sse_session_id: Optional[str] = None, formatters = None, menu_generator = None, session_service = None, stage_info_handler = None, web_integrator = None, utils = None) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """
        レシピサービス関連の処理
        
        Args:
            service_method: サービス・メソッド名
            data: 処理データ
            is_menu_scenario: 献立提案シナリオかどうか
            task_id: タスクID
            results: 全タスクの実行結果
            sse_session_id: SSEセッションID
            formatters: ResponseFormattersインスタンス
            menu_generator: MenuDataGeneratorインスタンス
            session_service: セッションサービスインスタンス
            stage_info_handler: SessionInfoHandlerインスタンス
            web_integrator: WebSearchResultIntegratorインスタンス
            utils: ResponseProcessorUtilsインスタンス
        
        Returns:
            (レスポンスパーツリスト, JSON形式のレシピデータ)
        """
        response_parts = []
        menu_data = None
        
        try:
            if service_method == "recipe_service.generate_menu_plan":
                # LLM献立提案を表示（斬新な提案）
                try:
                    llm_menu = data.get("data", data)
                    if isinstance(llm_menu, dict):
                        response_parts.extend(formatters.format_llm_menu(llm_menu))
                except Exception as e:
                    self.logger.error(f"❌ [RecipeServiceHandler] Failed to format LLM menu: {e}")
                
            elif service_method == "recipe_service.search_menu_from_rag":
                # RAG献立提案を表示（伝統的な提案）
                try:
                    rag_menu = data.get("data", data)
                    if isinstance(rag_menu, dict):
                        response_parts.extend(formatters.format_rag_menu(rag_menu))
                except Exception as e:
                    self.logger.error(f"❌ [RecipeServiceHandler] Failed to format RAG menu: {e}")
                
            elif service_method == "recipe_service.search_recipes_from_web":
                # task4完了時にtask3とtask4の結果を統合して選択UIを表示
                self.logger.info(f"🔍 [RecipeServiceHandler] Task4 completed, integrating with task3 results")
                
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
                    candidates_with_urls = web_integrator.integrate(candidates, task_id, data, utils)
                    
                    # Phase 1F: 提案済みタイトルをセッションに保存
                    if sse_session_id and session_service:
                        titles = [c.get("title") for c in candidates_with_urls if c.get("title")]
                        
                        await session_service.add_proposed_recipes(sse_session_id, "main", titles)
                        self.logger.info(f"💾 [RecipeServiceHandler] Saved {len(titles)} proposed titles to session")
                    
                    # Phase 3C-3: 候補情報をセッションに保存（詳細情報）
                    if sse_session_id and session_service:
                        session = await session_service.get_session(sse_session_id, user_id=None)
                        if session:
                            current_stage = session.get_current_stage()
                            category = current_stage  # "main", "sub", "soup"
                            await session_service.set_candidates(sse_session_id, category, candidates_with_urls)
                            self.logger.info(f"💾 [RecipeServiceHandler] Saved {len(candidates_with_urls)} {category} candidates to session")
                    
                    # Phase 3D: セッションから段階情報を取得
                    stage_info = await stage_info_handler.get_stage_info(sse_session_id, session_service)
                    
                    # 選択UI用のデータを返す
                    return [], {
                        "requires_selection": True,
                        "candidates": candidates_with_urls,
                        "task_id": task_id,
                        "message": "以下の5件から選択してください:",
                        **stage_info  # Phase 3D: 段階情報を統合
                    }
                else:
                    # task3の結果が取得できない場合
                    # 献立提案ではtask3（候補生成）が無い構成もあるため、エラーにしない
                    if is_menu_scenario:
                        self.logger.info(f"ℹ️ [RecipeServiceHandler] Task3 result not found (menu scenario). Generating menu JSON only to avoid duplicate text.")
                        if results:
                            self.logger.debug(f"🔍 [RecipeServiceHandler] Available task keys in results: {list(results.keys())}")
                        # 献立提案ではテキスト重複を避けるため、Web整形テキストは追加しない
                        # （generate_menu_plan/search_menu_from_rag で既に表示済み）
                        menu_data = menu_generator.generate_menu_data_json(data)
                    else:
                        # デバッグ: results辞書の内容を確認
                        self.logger.error(f"❌ [RecipeServiceHandler] Task3 result not found")
                        self.logger.error(f"🔍 [RecipeServiceHandler] Available task keys in results: {list(results.keys()) if results else 'results is None or empty'}")
                        if results:
                            for task_key, task_data in results.items():
                                self.logger.info(f"🔍 [RecipeServiceHandler] Task key: {task_key}, success: {task_data.get('success')}, has result: {'result' in task_data}")
                                if task_key == "task3":
                                    task_data_result = task_data.get("result", {})
                                    self.logger.info(f"🔍 [RecipeServiceHandler] Task3 result structure: success={task_data_result.get('success')}, has_data={'data' in task_data_result}, data_keys={list(task_data_result.get('data', {}).keys()) if isinstance(task_data_result.get('data'), dict) else 'data is not dict'}")
                        # 副菜・汁物提案では致命的
                        self.logger.error(f"❌ [RecipeServiceHandler] FATAL: Task3 result not found for category proposal")
                        response_parts.append("レシピ提案の結果を取得できませんでした。")
                
            elif service_method == "recipe_service.generate_proposals":
                # task3完了時は進捗のみ（選択UIは表示しない）
                # task4完了後に統合処理を行う
                self.logger.info(f"🔍 [RecipeServiceHandler] Task3 completed, waiting for task4 integration")
                
                # Phase 1F: 提案済みタイトルをセッションに保存
                if data.get("success") and sse_session_id and session_service:
                    data_obj = data.get("data", {})
                    candidates = data_obj.get("candidates", [])
                    titles = [c.get("title") for c in candidates if c.get("title")]
                    
                    # カテゴリを取得（main/sub/soup）。デフォルトは"main"
                    category = data_obj.get("category", "main")
                    
                    await session_service.add_proposed_recipes(sse_session_id, category, titles)
                    self.logger.info(f"💾 [RecipeServiceHandler] Saved {len(titles)} proposed titles to session (category: {category})")
                
                # 何も返さない（進捗状態のみ）
                pass
        
        except Exception as e:
            self.logger.error(f"❌ [RecipeServiceHandler] Error handling recipe service {service_method} for task {task_id}: {e}")
            response_parts.append(f"データの処理中にエラーが発生しました: {str(e)}")
        
        return response_parts, menu_data


class GenericServiceHandler:
    """汎用サービス処理ハンドラー"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.generic_handler")
    
    def handle(self, service_method: str, data: Any, formatters = None) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """
        汎用サービス処理
        
        Args:
            service_method: サービス・メソッド名
            data: 処理データ
            formatters: ResponseFormattersインスタンス
        
        Returns:
            (レスポンスパーツリスト, JSON形式のレシピデータ)
        """
        response_parts = formatters.format_generic_result(service_method, data)
        return response_parts, None

