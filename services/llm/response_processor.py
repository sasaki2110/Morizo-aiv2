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
    
    def format_final_response(self, results: Dict[str, Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        最終回答整形（サービス・メソッドベース）
        
        Args:
            results: タスク実行結果辞書
        
        Returns:
            (整形された回答, JSON形式のレシピデータ)
        """
        try:
            # 献立提案シナリオかどうかを判定
            is_menu_scenario = self.utils.is_menu_scenario(results)
            
            # レスポンス構築
            response_parts, menu_data = self._build_response_parts(results, is_menu_scenario)
            
            # 空レスポンスの処理
            return self._handle_empty_response(response_parts, menu_data)
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error in format_final_response: {e}")
            return "タスクが完了しましたが、レスポンスの生成に失敗しました。", None
    
    def _build_response_parts(self, results: Dict[str, Any], is_menu_scenario: bool) -> tuple[List[str], Optional[Dict[str, Any]]]:
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
                parts, menu = self._process_service_method(service_method, data, is_menu_scenario, task_id)
                response_parts.extend(parts)
                
                # メニューデータの更新（最初に見つかったものを使用）
                if menu and not menu_data:
                    menu_data = menu
                    
            except Exception as e:
                self.logger.error(f"❌ [ResponseProcessor] Error processing task {task_id}: {e}")
                continue
        
        return response_parts, menu_data
    
    def _process_service_method(self, service_method: str, data: Any, is_menu_scenario: bool, task_id: str) -> tuple[List[str], Optional[Dict[str, Any]]]:
        """
        サービス・メソッド別の処理
        
        Args:
            service_method: サービス・メソッド名
            data: 処理データ
            is_menu_scenario: 献立提案シナリオかどうか
            task_id: タスクID
        
        Returns:
            (レスポンスパーツリスト, JSON形式のレシピデータ)
        """
        response_parts = []
        menu_data = None
        
        try:
            if service_method == "inventory_service.get_inventory":
                response_parts.extend(self.formatters.format_inventory_list(data, is_menu_scenario))
                
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
                response_parts.extend(self.formatters.format_web_recipes(data))
                # JSON形式のレシピデータも生成
                menu_data = self.menu_generator.generate_menu_data_json(data)
                
            else:
                # 未知のサービス・メソッドの場合は汎用処理
                response_parts.extend(self.formatters.format_generic_result(service_method, data))
                
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error formatting {service_method} for task {task_id}: {e}")
            response_parts.append(f"データの処理中にエラーが発生しました: {str(e)}")
        
        return response_parts, menu_data
    
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
