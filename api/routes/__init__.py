#!/usr/bin/env python3
"""
API層 - ルート定義

チャットとヘルスチェックルートの統合
"""

from .chat import router as chat_router
from .health import router as health_router
from .recipe import router as recipe_router

__all__ = [
    'chat_router',
    'health_router',
    'recipe_router'
]
