#!/usr/bin/env python3
"""
MenuFormatter - メニュー選択フォーマット処理

メニュー選択関連のレスポンスフォーマット処理を担当
"""

from typing import Dict, List
from .base import BaseFormatter


class MenuFormatter(BaseFormatter):
    """メニュー選択フォーマット処理クラス"""
    
    def __init__(self):
        """初期化"""
        super().__init__("service", "llm.response.formatters.menu")
    
    def format_selection_request(self, candidates: list, task_id: str) -> dict:
        """選択要求レスポンスのフォーマット"""
        formatted = "以下の5件から選択してください:\n\n"
        
        for i, candidate in enumerate(candidates, 1):
            formatted += f"{i}. {candidate.get('title', '不明なレシピ')}\n"
            
            # 食材リスト
            ingredients = candidate.get('ingredients', [])
            if ingredients:
                formatted += f"   食材: {', '.join(ingredients)}\n"
            
            # 調理時間
            cooking_time = candidate.get('cooking_time')
            if cooking_time:
                formatted += f"   調理時間: {cooking_time}\n"
            
            # カテゴリ
            category = candidate.get('category')
            if category:
                formatted += f"   カテゴリ: {category}\n"
            
            formatted += "\n"
        
        formatted += "番号を選択してください（1-5）:"
        
        return {
            "message": formatted,
            "requires_selection": True,
            "candidates": candidates,
            "task_id": task_id
        }
    
    def format_selection_result(self, selection: int, task_id: str) -> dict:
        """選択結果レスポンスのフォーマット"""
        return {
            "message": f"選択肢 {selection} を受け付けました。",
            "success": True,
            "task_id": task_id,
            "selection": selection
        }

