#!/usr/bin/env python3
"""
Base Formatter - フォーマッター基底クラス

全フォーマッターの共通機能を提供
"""

from config.loggers import GenericLogger


class BaseFormatter:
    """フォーマッター基底クラス"""
    
    def __init__(self, logger_name: str = "service", logger_category: str = "llm.response.formatters"):
        """初期化"""
        self.logger = GenericLogger(logger_name, logger_category)

