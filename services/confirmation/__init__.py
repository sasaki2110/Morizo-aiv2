#!/usr/bin/env python3
"""
Confirmation Service パッケージ

曖昧性検出と確認プロセスのビジネスロジックを提供
"""

from .models import AmbiguityInfo, AmbiguityResult, ConfirmationResult

# ConfirmationServiceは後で追加予定
# from .confirmation_service import ConfirmationService

__all__ = [
    "AmbiguityInfo",
    "AmbiguityResult", 
    "ConfirmationResult",
    # "ConfirmationService",  # 後で追加
]
