#!/usr/bin/env python3
"""
GenericFormatter - 汎用フォーマット処理

汎用のレスポンスフォーマット処理を担当
"""

from typing import Dict, Any, List
from .base import BaseFormatter


class GenericFormatter(BaseFormatter):
    """汎用フォーマット処理クラス"""
    
    def __init__(self):
        """初期化"""
        super().__init__("service", "llm.response.formatters.generic")
    
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

