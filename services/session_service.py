#!/usr/bin/env python3
"""
SessionService - 後方互換性のためのリダイレクトファイル

このファイルは後方互換性のために残されています。
新しいコードでは `from services.session import SessionService, Session` を使用してください。
"""

# 新しいパッケージからインポート（後方互換性のため）
from .session import SessionService, Session, session_service

__all__ = ['SessionService', 'Session', 'session_service']
