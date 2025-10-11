#!/usr/bin/env python3
"""
ResponseFormatters - レスポンスフォーマット処理

レスポンスの整形とフォーマット処理を担当
"""

from typing import Dict, Any, List
from config.loggers import GenericLogger
from .utils import STORAGE_EMOJI_MAP


class ResponseFormatters:
    """レスポンスフォーマット処理クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.formatters")
    
    def format_inventory_list(self, data: Dict, is_menu_scenario: bool = False) -> List[str]:
        """在庫一覧のフォーマット"""
        response_parts = []
        
        # 修正: success判定を追加
        if isinstance(data, dict) and data.get("success"):
            # 成功時: dataから在庫データを取得
            inventory_data = data.get("data", [])
            
            if not inventory_data:
                return []
            
            # 献立提案シナリオの場合は表示しない
            if is_menu_scenario:
                return []
            
            # 通常の在庫表示（詳細）
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
                storage_emoji = STORAGE_EMOJI_MAP.get(storage, "📦")
                response_parts.append(f"{storage_emoji} **{storage}**")
                response_parts.append("")  # セクションタイトル後の空行
                for item in items:
                    expiry_info = f" (期限: {item['expiry_date']})" if item.get('expiry_date') else ""
                    response_parts.append(f"  • {item['item_name']}: {item['quantity']} {item['unit']}{expiry_info}")
                response_parts.append("")  # セクション終了後の空行
            
            return response_parts
        else:
            # エラー時の表示
            error_msg = data.get("error", "不明なエラー") if isinstance(data, dict) else "不明なエラー"
            response_parts.append("❌ **在庫一覧の取得に失敗しました**")
            response_parts.append("")
            response_parts.append(f"エラー: {error_msg}")
            response_parts.append("")
            response_parts.append("もう一度お試しください。")
            
            return response_parts
    
    def format_web_recipes(self, web_data: Any) -> List[str]:
        """Web検索結果のフォーマット（簡素化版）"""
        response_parts = []
        
        try:
            # 修正: success判定を追加
            if isinstance(web_data, dict) and web_data.get("success"):
                # 成功時: dataからllm_menuとrag_menuを取得
                data = web_data.get("data", {})
                
                # 斬新な提案（LLM）
                if 'llm_menu' in data:
                    response_parts.extend(self.format_llm_menu(data['llm_menu']))
                
                # 伝統的な提案（RAG）
                if 'rag_menu' in data:
                    response_parts.extend(self.format_rag_menu(data['rag_menu']))
            else:
                # エラー時またはデータ形式エラー
                response_parts.append("レシピデータの形式が正しくありません。")
                
        except Exception as e:
            self.logger.error(f"❌ [ResponseFormatters] Error in format_web_recipes: {e}")
            response_parts.append("レシピデータの処理中にエラーが発生しました。")
        
        return response_parts
    
    def format_llm_menu(self, llm_menu: Dict[str, Any]) -> List[str]:
        """LLMメニューのフォーマット"""
        response_parts = []
        response_parts.append("🍽️ 斬新な提案")
        response_parts.append("")
        
        # 主菜
        if 'main_dish' in llm_menu and llm_menu['main_dish']:
            dish_text = self.format_dish_item(llm_menu['main_dish'], "主菜")
            response_parts.append(dish_text)
        
        # 副菜
        if 'side_dish' in llm_menu and llm_menu['side_dish']:
            dish_text = self.format_dish_item(llm_menu['side_dish'], "副菜")
            response_parts.append(dish_text)
        
        # 汁物
        if 'soup' in llm_menu and llm_menu['soup']:
            dish_text = self.format_dish_item(llm_menu['soup'], "汁物")
            response_parts.append(dish_text)
        else:
            response_parts.append("汁物:")
        
        response_parts.append("")
        return response_parts
    
    def format_rag_menu(self, rag_menu: Dict[str, Any]) -> List[str]:
        """RAGメニューのフォーマット"""
        response_parts = []
        response_parts.append("🍽️ 伝統的な提案")
        response_parts.append("")
        
        # 主菜
        if 'main_dish' in rag_menu and rag_menu['main_dish']:
            dish_text = self.format_dish_item(rag_menu['main_dish'], "主菜")
            response_parts.append(dish_text)
        
        # 副菜
        if 'side_dish' in rag_menu and rag_menu['side_dish']:
            dish_text = self.format_dish_item(rag_menu['side_dish'], "副菜")
            response_parts.append(dish_text)
        
        # 汁物
        if 'soup' in rag_menu and rag_menu['soup']:
            dish_text = self.format_dish_item(rag_menu['soup'], "汁物")
            response_parts.append(dish_text)
        else:
            response_parts.append("汁物:")
        
        response_parts.append("")
        return response_parts
    
    def format_dish_item(self, dish_data: Any, dish_type: str) -> str:
        """料理項目のフォーマット（共通処理）"""
        if isinstance(dish_data, str):
            return f"{dish_type}: {dish_data}"
        elif isinstance(dish_data, dict) and 'title' in dish_data:
            return f"{dish_type}: {dish_data['title']}"
        else:
            return f"{dish_type}:"
    
    def format_generic_result(self, service_method: str, data: Any) -> List[str]:
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
    
    def format_inventory_add(self, data: Dict) -> List[str]:
        """在庫追加のフォーマット"""
        response_parts = []
        
        # デバッグログ: 受信データの構造を確認
        self.logger.info(f"🔍 [DEBUG] format_inventory_add received data: {data}")
        self.logger.info(f"🔍 [DEBUG] data type: {type(data)}")
        self.logger.info(f"🔍 [DEBUG] data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # 修正: success判定を追加
        if isinstance(data, dict) and data.get("success"):
            # 成功時の表示
            self.logger.info(f"🔍 [DEBUG] Success branch executed")
            item_data = data.get("data", {})
            self.logger.info(f"🔍 [DEBUG] item_data: {item_data}")
            item_name = item_data.get("item_name", "アイテム")
            quantity = item_data.get("quantity", 0)
            unit = item_data.get("unit", "個")
            storage = item_data.get("storage_location", "冷蔵庫")
            
            response_parts.append("✅ **在庫を追加しました**")
            response_parts.append("")
            response_parts.append(f"📦 **{item_name}**: {quantity}{unit}")
            response_parts.append(f"📍 **保管場所**: {storage}")
            
            if item_data.get("expiry_date"):
                response_parts.append(f"📅 **賞味期限**: {item_data['expiry_date']}")
            
            response_parts.append("")
            response_parts.append("在庫に正常に追加されました。")
        else:
            # エラー時の表示
            self.logger.info(f"🔍 [DEBUG] Error branch executed")
            error_msg = data.get("error", "不明なエラー") if isinstance(data, dict) else "不明なエラー"
            self.logger.info(f"🔍 [DEBUG] error_msg: {error_msg}")
            response_parts.append("❌ **在庫の追加に失敗しました**")
            response_parts.append("")
            response_parts.append(f"エラー: {error_msg}")
            response_parts.append("")
            response_parts.append("もう一度お試しください。")
        
        return response_parts
    
    def format_inventory_update(self, data: Dict) -> List[str]:
        """在庫更新のフォーマット"""
        response_parts = []
        
        # 修正: success判定を追加
        if isinstance(data, dict) and data.get("success"):
            # 成功時の表示
            item_data = data.get("data", {})
            
            # 複数件の更新結果に対応
            if isinstance(item_data, list):
                # 複数件の場合
                response_parts.append("✅ **在庫を更新しました**")
                response_parts.append("")
                response_parts.append(f"📦 **更新件数**: {len(item_data)}件")
                response_parts.append("")
                
                # 各アイテムの情報を表示
                for i, item in enumerate(item_data, 1):
                    if isinstance(item, dict):
                        item_name = item.get("item_name", "アイテム")
                        quantity = item.get("quantity", 0)
                        unit = item.get("unit", "個")
                        response_parts.append(f"{i}. **{item_name}**: {quantity}{unit}")
                
                response_parts.append("")
                response_parts.append("在庫情報が正常に更新されました。")
            else:
                # 単一アイテムの場合（既存の処理）
                item_name = item_data.get("item_name", "アイテム")
                quantity = item_data.get("quantity", 0)
                unit = item_data.get("unit", "個")
                
                response_parts.append("✅ **在庫を更新しました**")
                response_parts.append("")
                response_parts.append(f"📦 **{item_name}**: {quantity}{unit}")
                response_parts.append("")
                response_parts.append("在庫情報が正常に更新されました。")
        else:
            # エラー時の表示
            error_msg = data.get("error", "不明なエラー") if isinstance(data, dict) else "不明なエラー"
            
            # AMBIGUITY_DETECTEDエラーの特別処理
            if error_msg == "AMBIGUITY_DETECTED":
                message = data.get("message", "在庫が複数あるため更新できません。")
                items = data.get("items", [])
                count = data.get("count", 0)
                
                response_parts.append("⚠️ **在庫の更新について**")
                response_parts.append("")
                response_parts.append(message)
                response_parts.append("")
                
                if items:
                    response_parts.append("**現在の在庫:**")
                    for i, item in enumerate(items, 1):
                        quantity = item.get("quantity", 0)
                        unit = item.get("unit", "個")
                        storage_location = item.get("storage_location", "")
                        expiry_date = item.get("expiry_date", "")
                        created_at = item.get("created_at", "")
                        
                        # 日付のフォーマット
                        if created_at:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                created_str = dt.strftime("%m/%d")
                            except:
                                created_str = created_at[:10] if len(created_at) >= 10 else created_at
                        else:
                            created_str = "不明"
                        
                        response_parts.append(f"{i}. {quantity}{unit} - {storage_location} (作成: {created_str})")
                        if expiry_date:
                            response_parts.append(f"   賞味期限: {expiry_date}")
                
                response_parts.append("")
                response_parts.append("**選択肢:**")
                response_parts.append("- 「最新の○○を変えて」")
                response_parts.append("- 「一番古い○○を変えて」")
                response_parts.append("- 「全部の○○を変えて」")
            else:
                # 通常のエラー処理
                response_parts.append("❌ **在庫の更新に失敗しました**")
                response_parts.append("")
                response_parts.append(f"エラー: {error_msg}")
                response_parts.append("")
                response_parts.append("もう一度お試しください。")
        
        return response_parts
    
    def format_inventory_delete(self, data: Dict) -> List[str]:
        """在庫削除のフォーマット"""
        response_parts = []
        
        # 修正: success判定を追加
        if isinstance(data, dict) and data.get("success"):
            # 成功時の表示
            item_data = data.get("data", {})
            item_name = item_data.get("item_name", "アイテム")
            
            response_parts.append("✅ **在庫を削除しました**")
            response_parts.append("")
            response_parts.append(f"🗑️ **{item_name}** を在庫から削除しました。")
            response_parts.append("")
            response_parts.append("在庫から正常に削除されました。")
        else:
            # エラー時の表示
            error_msg = data.get("error", "不明なエラー") if isinstance(data, dict) else "不明なエラー"
            response_parts.append("❌ **在庫の削除に失敗しました**")
            response_parts.append("")
            response_parts.append(f"エラー: {error_msg}")
            response_parts.append("")
            response_parts.append("もう一度お試しください。")
        
        return response_parts