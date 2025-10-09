#!/usr/bin/env python3
"""
ResponseProcessor - レスポンス処理

LLMServiceから分離したレスポンス処理専用クラス
JSON解析、タスク形式変換、最終回答整形を担当
"""

import json
from typing import Dict, Any, List, Optional
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
    
    def format_final_response(self, results: Dict[str, Any]) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        最終回答整形（サービス・メソッドベース）
        
        Args:
            results: タスク実行結果辞書
        
        Returns:
            (整形された回答, JSON形式のレシピデータ)
        """
        try:
            
            # レスポンスを構築
            response_parts = []
            menu_data = None  # JSON形式のレシピデータ
            
            # サービス・メソッドベースの処理
            for task_id, task_result in results.items():
                
                # 各フィールドの値を安全に取得
                try:
                    success_value = task_result.get("success")
                    service_value = task_result.get("service", "")
                    method_value = task_result.get("method", "")
                    
                    
                    if not success_value:
                        continue
                        
                except Exception as e:
                    self.logger.error(f"❌ [ResponseProcessor] Error processing task {task_id}: {e}")
                    continue
                
                service = service_value
                method = method_value
                
                # 安全なデータ取得
                try:
                    result_value = task_result.get("result", {})
                    
                    if isinstance(result_value, dict):
                        data = result_value.get("data", [])
                    else:
                        # resultが辞書でない場合は空リスト
                        data = []
                        self.logger.warning(f"⚠️ [ResponseProcessor] Task {task_id} result is not a dict: {type(result_value)}")
                        
                except Exception as e:
                    self.logger.error(f"❌ [ResponseProcessor] Error accessing result field for task {task_id}: {e}")
                    data = []
                
                # サービス・メソッドの組み合わせで処理を決定
                try:
                    # 安全な文字列変換
                    service_str = str(service) if service is not None else ""
                    method_str = str(method) if method is not None else ""
                    service_method = f"{service_str}.{method_str}"
                    
                    
                except Exception as e:
                    self.logger.error(f"❌ [ResponseProcessor] Error creating service_method for task {task_id}: {e}")
                    service_method = "unknown.unknown"
                
                if service_method == "inventory_service.get_inventory":
                    try:
                        response_parts.extend(self._format_inventory_list(data))
                    except Exception as e:
                        self.logger.error(f"❌ [ResponseProcessor] Error formatting inventory list for task {task_id}: {e}")
                        response_parts.append(f"在庫データの処理中にエラーが発生しました: {str(e)}")
                elif service_method == "recipe_service.generate_menu_plan":
                    try:
                        response_parts.extend(self._format_menu_plan(data, "LLM献立提案"))
                    except Exception as e:
                        self.logger.error(f"❌ [ResponseProcessor] Error formatting menu plan for task {task_id}: {e}")
                        response_parts.append(f"献立データの処理中にエラーが発生しました: {str(e)}")
                elif service_method == "recipe_service.search_menu_from_rag":
                    try:
                        response_parts.extend(self._format_menu_plan(data, "RAG献立提案"))
                    except Exception as e:
                        self.logger.error(f"❌ [ResponseProcessor] Error formatting RAG menu for task {task_id}: {e}")
                        response_parts.append(f"RAG献立データの処理中にエラーが発生しました: {str(e)}")
                elif service_method == "recipe_service.search_recipes_from_web":
                    try:
                        response_parts.extend(self._format_web_recipes(data))
                        # JSON形式のレシピデータも生成
                        menu_data = self._generate_menu_data_json(data)
                    except Exception as e:
                        self.logger.error(f"❌ [ResponseProcessor] Error formatting web recipes for task {task_id}: {e}")
                        response_parts.append(f"レシピ検索データの処理中にエラーが発生しました: {str(e)}")
                else:
                    # 未知のサービス・メソッドの場合は汎用処理
                    try:
                        response_parts.extend(self._format_generic_result(service_method, data))
                    except Exception as e:
                        self.logger.error(f"❌ [ResponseProcessor] Error formatting generic result for task {task_id}: {e}")
                        response_parts.append(f"汎用データの処理中にエラーが発生しました: {str(e)}")
            
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
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error in format_final_response: {e}")
            return "タスクが完了しましたが、レスポンスの生成に失敗しました。", None
    
    def _format_inventory_list(self, inventory_data: List[Dict]) -> List[str]:
        """在庫一覧のフォーマット"""
        if not inventory_data:
            return []
        
        response_parts = []
        response_parts.append("📋 **現在の在庫一覧**")
        response_parts.append(f"総アイテム数: {len(inventory_data)}個")
        response_parts.append("")
        
        # アイテムをカテゴリ別に整理
        categories = {}
        for item in inventory_data:
            storage = item.get('storage_location', 'その他')
            if storage not in categories:
                categories[storage] = []
            categories[storage].append(item)
        
        # カテゴリ別に表示
        for storage, items in categories.items():
            storage_emoji = {"冷蔵庫": "🧊", "冷凍": "❄️", "常温": "🌡️"}.get(storage, "📦")
            response_parts.append(f"{storage_emoji} **{storage}**")
            response_parts.append("")  # セクションタイトル後の空行
            for item in items:
                expiry_info = f" (期限: {item['expiry_date']})" if item.get('expiry_date') else ""
                response_parts.append(f"  • {item['item_name']}: {item['quantity']} {item['unit']}{expiry_info}")
            response_parts.append("")  # セクション終了後の空行
        
        return response_parts
    
    def _format_menu_plan(self, menu_data: Dict, title: str) -> List[str]:
        """献立提案のフォーマット"""
        if not menu_data:
            return []
        
        response_parts = []
        response_parts.append(f"🍽️ **{title}**")
        response_parts.append("")  # タイトル後の空行
        response_parts.append(f"主菜: {menu_data.get('main_dish', 'N/A')}")
        response_parts.append(f"副菜: {menu_data.get('side_dish', 'N/A')}")
        response_parts.append(f"汁物: {menu_data.get('soup', 'N/A')}")
        response_parts.append("")  # セクション終了後の空行
        
        return response_parts
    
    def _format_web_recipes(self, web_data: Any) -> List[str]:
        """Web検索結果のフォーマット"""
        response_parts = []
        response_parts.append("🌐 **レシピ検索結果**")
        response_parts.append("")  # タイトル後の空行
        
        try:
            # web_dataが辞書の場合、適切な部分を抽出
            if isinstance(web_data, dict):
                recipes = []
                # llm_menu と rag_menu からレシピを抽出
                for menu_type in ['llm_menu', 'rag_menu']:
                    if menu_type in web_data:
                        menu = web_data[menu_type]
                        for dish_type in ['main_dish', 'side_dish', 'soup']:
                            if dish_type in menu and 'recipes' in menu[dish_type]:
                                recipes.extend(menu[dish_type]['recipes'])
                
                # 上位5件のみ表示
                for i, recipe in enumerate(recipes[:5], 1):
                    title = str(recipe.get('title', 'N/A'))
                    url = str(recipe.get('url', 'N/A'))
                    description = str(recipe.get('description', 'N/A'))
                    
                    response_parts.append(f"{i}. {title}")
                    response_parts.append(f"   URL: {url}")
                    response_parts.append(f"   説明: {description[:100]}...")
                    response_parts.append("")  # 各レシピ項目後の空行
            else:
                response_parts.append("レシピデータの形式が正しくありません。")
                
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error in _format_web_recipes: {e}")
            response_parts.append("レシピデータの処理中にエラーが発生しました。")
        
        return response_parts
    
    def _format_generic_result(self, service_method: str, data: Any) -> List[str]:
        """汎用結果のフォーマット"""
        response_parts = []
        response_parts.append(f"📊 **{service_method}の結果**")
        response_parts.append("")  # タイトル後の空行
        
        if isinstance(data, list):
            response_parts.append(f"取得件数: {len(data)}件")
            for i, item in enumerate(data[:3], 1):  # 上位3件のみ
                if isinstance(item, dict):
                    response_parts.append(f"{i}. {item}")
                else:
                    response_parts.append(f"{i}. {str(item)[:100]}...")
        elif isinstance(data, dict):
            response_parts.append(f"データ: {str(data)[:200]}...")
        else:
            response_parts.append(f"結果: {str(data)[:200]}...")
        
        response_parts.append("")  # セクション終了後の空行
        return response_parts
    
    def _generate_menu_data_json(self, web_data: Any) -> Optional[Dict[str, Any]]:
        """
        レシピデータをJSON形式に変換
        
        Args:
            web_data: Web検索結果データ
        
        Returns:
            仕様書に準拠したJSON形式のレシピデータ
        """
        try:
            # Web検索結果の詳細ログを追加
            self.logger.info(f"🔍 [ResponseProcessor] Web data type: {type(web_data)}")
            self.logger.info(f"📊 [ResponseProcessor] Web data content: {json.dumps(web_data, ensure_ascii=False, indent=2)}")
            
            if not isinstance(web_data, dict):
                self.logger.warning("⚠️ [ResponseProcessor] web_data is not a dict, skipping JSON generation")
                return None
            
            # 仕様書の構造に合わせてデータを構築
            menu_data = {
                "innovative": {
                    "title": "📝 斬新な提案",
                    "recipes": {
                        "main": [],
                        "side": [],
                        "soup": []
                    }
                },
                "traditional": {
                    "title": "📚 伝統的な提案",
                    "recipes": {
                        "main": [],
                        "side": [],
                        "soup": []
                    }
                }
            }
            
            # llm_menu と rag_menu からレシピを抽出
            for menu_type in ['llm_menu', 'rag_menu']:
                if menu_type not in web_data:
                    continue
                    
                menu = web_data[menu_type]
                
                # カテゴリ別に処理
                for dish_type in ['main_dish', 'side_dish', 'soup']:
                    if dish_type not in menu or 'recipes' not in menu[dish_type]:
                        continue
                        
                    recipes = menu[dish_type]['recipes']
                    if not recipes:
                        continue
                    
                    # カテゴリマッピング
                    category_map = {
                        'main_dish': 'main',
                        'side_dish': 'side',
                        'soup': 'soup'
                    }
                    category = category_map.get(dish_type, 'main')
                    
                    # 絵文字マッピング
                    emoji_map = {
                        'main': '🍖',
                        'side': '🥗',
                        'soup': '🍵'
                    }
                    emoji = emoji_map.get(category, '🍽️')
                    
                    # レシピを変換（カテゴリ統合処理）
                    category_urls = []  # カテゴリ全体のURLリスト
                    
                    for recipe in recipes[:2]:  # 最大2件まで
                        urls = self._extract_recipe_urls(recipe)
                        category_urls.extend(urls)  # 全URLを統合
                    
                    # カテゴリにURLがある場合は1つのレシピオブジェクトとして追加
                    if category_urls:
                        # カテゴリ名に基づいたタイトルを生成
                        category_titles = {
                            'main': '主菜のレシピ',
                            'side': '副菜のレシピ', 
                            'soup': '汁物のレシピ'
                        }
                        combined_title = category_titles.get(category, f'{category}のレシピ')
                        
                        combined_recipe = {
                            "title": combined_title,
                            "emoji": emoji,
                            "category": category,
                            "urls": category_urls
                        }
                        
                        # innovative または traditional に分類
                        target_section = self._classify_recipe(combined_recipe, menu_type)
                        menu_data[target_section]["recipes"][category].append(combined_recipe)
            
            # 空のセクションをチェック
            has_data = False
            for section in ['innovative', 'traditional']:
                for category in ['main', 'side', 'soup']:
                    if menu_data[section]["recipes"][category]:
                        has_data = True
                        break
            
            if not has_data:
                self.logger.warning("⚠️ [ResponseProcessor] No recipe data found for JSON generation")
                return None
            
            # 生成されたmenu_dataの全文ログを追加
            self.logger.info(f"📋 [ResponseProcessor] Generated menu_data: {json.dumps(menu_data, ensure_ascii=False, indent=2)}")
            self.logger.info(f"✅ [ResponseProcessor] Menu data JSON generated successfully")
            return menu_data
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error generating menu data JSON: {e}")
            return None
    
    def _extract_recipe_urls(self, recipe: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        レシピからURL情報を抽出
        
        Args:
            recipe: レシピデータ
        
        Returns:
            URL情報のリスト
        """
        urls = []
        
        try:
            # レシピのURL情報を抽出（実際の構造に応じて調整が必要）
            if 'url' in recipe:
                url = str(recipe['url'])
                title = str(recipe.get('title', 'レシピ詳細'))
                domain = self._extract_domain(url)
                
                urls.append({
                    "title": title,
                    "url": url,
                    "domain": domain
                })
            
            # 複数URLがある場合の処理（必要に応じて拡張）
            
        except Exception as e:
            self.logger.error(f"❌ [ResponseProcessor] Error extracting recipe URLs: {e}")
        
        return urls
    
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
            return "unknown"
    
    def _classify_recipe(self, recipe: Dict[str, Any], menu_type: str) -> str:
        """
        レシピをinnovativeまたはtraditionalに分類
        
        Args:
            recipe: レシピデータ
            menu_type: メニュータイプ（llm_menu または rag_menu）
        
        Returns:
            'innovative' または 'traditional'
        """
        # 簡易的な分類ロジック
        # llm_menu = innovative, rag_menu = traditional
        if menu_type == 'llm_menu':
            return 'innovative'
        else:
            return 'traditional'
