#!/usr/bin/env python3
"""
ResponseProcessor - レスポンス処理

LLMServiceから分離したレスポンス処理専用クラス
JSON解析、タスク形式変換、最終回答整形を担当
"""

import json
from typing import Dict, Any, List
from config.loggers import GenericLogger


class ResponseProcessor:
    """レスポンス処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response")
    
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
    
    def format_final_response(self, results: Dict[str, Any]) -> str:
        """
        最終回答整形
        
        Args:
            results: タスク実行結果辞書 (task1, task2, task3, task4)
        
        Returns:
            整形された回答
        """
        try:
            self.logger.info(f"🔧 [ResponseProcessor] Formatting response for {len(results)} results")
            
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
            self.logger.info(f"✅ [ResponseProcessor] Response formatted successfully")
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error in format_final_response: {e}")
            return "タスクが完了しましたが、レスポンスの生成に失敗しました。"
