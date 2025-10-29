#!/usr/bin/env python3
"""
RequestAnalyzer - リクエスト分析

プロンプト肥大化問題を解決するため、リクエストを事前分析する。
パターンマッチング方式でリクエストを判定し、必要な情報を抽出する。
"""

from typing import Dict, Any, List, Optional
import re
from config.loggers import GenericLogger


class RequestAnalyzer:
    """リクエスト分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.request_analyzer")
    
    def analyze(
        self, 
        request: str, 
        user_id: str, 
        sse_session_id: str = None, 
        session_context: dict = None
    ) -> Dict[str, Any]:
        """
        リクエストを分析してパターンとパラメータを抽出
        
        Args:
            request: ユーザーリクエスト
            user_id: ユーザーID
            sse_session_id: SSEセッションID
            session_context: セッションコンテキスト
        
        Returns:
            {
                "pattern": str,  # パターン種別
                "params": dict,  # 抽出されたパラメータ
                "ambiguities": list  # 曖昧性リスト
            }
        """
        try:
            self.logger.info(f"🔍 [RequestAnalyzer] Analyzing request: '{request}'")
            
            # セッションコンテキストのデフォルト値
            if session_context is None:
                session_context = {}
            
            # 1. パターン判定
            pattern = self._detect_pattern(request, sse_session_id, session_context)
            
            # 2. パラメータ抽出
            params = self._extract_params(request, pattern, user_id, session_context)
            
            # 3. 曖昧性チェック
            ambiguities = self._check_ambiguities(pattern, params, sse_session_id, session_context)
            
            result = {
                "pattern": pattern,
                "params": params,
                "ambiguities": ambiguities
            }
            
            self.logger.info(f"✅ [RequestAnalyzer] Analysis result: pattern={pattern}, ambiguities={len(ambiguities)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ [RequestAnalyzer] Error in analyze: {e}")
            raise
    
    def _detect_pattern(
        self, 
        request: str, 
        sse_session_id: str, 
        session_context: dict
    ) -> str:
        """
        パターン判定（優先順位順にチェック）
        
        Returns:
            pattern: パターン種別
        """
        # 優先度1: 曖昧性解消後の再開
        if self._is_ambiguity_resume(session_context):
            return "ambiguity_resume"
        
        # 優先度2: 追加提案
        if self._is_additional_proposal(request, sse_session_id):
            if "主菜" in request or "メイン" in request or "main" in request.lower():
                return "main_additional"
            elif "副菜" in request or "サブ" in request or "sub" in request.lower():
                return "sub_additional"
            elif "汁物" in request or "スープ" in request or "味噌汁" in request or "soup" in request.lower():
                return "soup_additional"
        
        # 優先度3: カテゴリ提案（初回）
        if "主菜" in request or "メイン" in request or "main" in request.lower():
            return "main"
        elif "副菜" in request or "サブ" in request or "sub" in request.lower():
            return "sub"
        elif "汁物" in request or "スープ" in request or "味噌汁" in request or "soup" in request.lower():
            return "soup"
        
        # 優先度4: 在庫操作
        if self._is_inventory_operation(request):
            return "inventory"
        
        # 優先度5: 献立生成
        if "献立" in request or "メニュー" in request or "menu" in request.lower():
            return "menu"
        
        # 優先度6: その他
        return "other"
    
    def _is_ambiguity_resume(self, session_context: dict) -> bool:
        """曖昧性解消後の再開判定"""
        # TODO: セッションに確認待ち状態が存在する場合にTrueを返す
        return session_context.get("waiting_confirmation", False)
    
    def _is_additional_proposal(self, request: str, sse_session_id: str) -> bool:
        """追加提案の判定"""
        if not sse_session_id:
            return False
        
        additional_keywords = ["もう", "他の", "もっと", "追加", "あと", "さらに"]
        return any(keyword in request for keyword in additional_keywords)
    
    def _is_inventory_operation(self, request: str) -> bool:
        """在庫操作の判定"""
        inventory_keywords = ["追加", "削除", "更新", "変えて", "変更", "確認", "在庫"]
        return any(keyword in request for keyword in inventory_keywords)
    
    def _extract_params(
        self, 
        request: str, 
        pattern: str, 
        user_id: str, 
        session_context: dict
    ) -> Dict[str, Any]:
        """パラメータ抽出"""
        params = {
            "user_id": user_id,
            "user_request": request  # user_request を params に追加
        }
        
        # カテゴリ提案の場合
        if pattern in ["main", "sub", "soup", "main_additional", "sub_additional", "soup_additional"]:
            # カテゴリ設定
            category_map = {
                "main": "main",
                "sub": "sub",
                "soup": "soup",
                "main_additional": "main",
                "sub_additional": "sub",
                "soup_additional": "soup"
            }
            params["category"] = category_map[pattern]
            
            # 主要食材抽出
            if pattern in ["main", "main_additional"]:
                params["main_ingredient"] = self._extract_ingredient(request)
            else:
                params["main_ingredient"] = None
            
            # 使用済み食材（セッションから取得）
            if pattern in ["sub", "soup", "sub_additional", "soup_additional"]:
                params["used_ingredients"] = session_context.get("used_ingredients", [])
            else:
                params["used_ingredients"] = None
            
            # 汁物の献立カテゴリ判定
            if pattern in ["soup", "soup_additional"]:
                params["menu_category"] = session_context.get("menu_category", "japanese")
            else:
                params["menu_category"] = None
        
        return params
    
    def _extract_ingredient(self, request: str) -> Optional[str]:
        """主要食材の抽出（簡易版）"""
        # パターン1: 「○○の主菜」「○○で主菜」「○○を使った主菜」
        match = re.search(r'([ぁ-ん一-龥ァ-ヴー]+?)(の|で|を使った)(主菜|副菜|汁物|メイン|サブ|スープ)', request)
        if match:
            return match.group(1)
        
        # パターン2: 「○○主菜」（スペースなし）
        match = re.search(r'([ぁ-ん一-龥ァ-ヴー]{2,})(主菜|副菜|汁物|メイン|サブ|スープ)', request)
        if match:
            return match.group(1)
        
        # パターン3: 「○○を主菜に」「○○でメインを」
        match = re.search(r'([ぁ-ん一-龥ァ-ヴー]+?)(を|で)(主菜|メイン)', request)
        if match:
            return match.group(1)
        
        # パターン4: 「○○で味噌汁を作りたい」「○○でスープを」
        match = re.search(r'([ぁ-ん一-龥ァ-ヴー]+?)(で)(味噌汁|スープ)', request)
        if match:
            return match.group(1)
        
        return None
    
    def _check_ambiguities(
        self, 
        pattern: str, 
        params: dict, 
        sse_session_id: str, 
        session_context: dict
    ) -> List[Dict[str, Any]]:
        """曖昧性チェック"""
        ambiguities = []
        
        # 主菜提案で main_ingredient 未指定
        if pattern == "main" and not params.get("main_ingredient"):
            ambiguities.append({
                "type": "missing_main_ingredient",
                "question": "何か食材を指定しますか？それとも在庫から提案しますか？",
                "options": ["食材を指定する", "在庫から提案する"]
            })
        
        # 追加提案で sse_session_id 不在
        if pattern in ["main_additional", "sub_additional", "soup_additional"] and not sse_session_id:
            # 曖昧性ではなく、初回提案に切り替え
            # ここでは特に処理しない（呼び出し側で対応）
            pass
        
        # 副菜提案で used_ingredients 不在
        if pattern == "sub" and not params.get("used_ingredients"):
            ambiguities.append({
                "type": "missing_used_ingredients",
                "question": "まず主菜を選択しますか？それとも副菜のみ提案しますか？",
                "options": ["主菜から選ぶ", "副菜のみ提案"]
            })
        
        # 汁物提案で used_ingredients 不在
        if pattern == "soup" and not params.get("used_ingredients"):
            # デフォルトで和食（味噌汁）を提案
            # 曖昧性を設けない
            pass
        
        return ambiguities

