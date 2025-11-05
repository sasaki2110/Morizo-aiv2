#!/usr/bin/env python3
"""
API層 - データモデル

リクエスト・レスポンスモデルの統合
"""

from .requests import ChatRequest, ProgressUpdate, InventoryRequest, HealthRequest, RecipeAdoptionRequest, RecipeItem, MenuSaveRequest, CSVUploadError, CSVUploadResponse
from .responses import ChatResponse, HealthResponse, InventoryResponse, InventoryListResponse, InventoryItemResponse, ErrorResponse, SSEEvent, RecipeAdoptionResponse, SavedRecipe, SavedMenuRecipe, MenuSaveResponse, HistoryRecipe, HistoryEntry, MenuHistoryResponse

__all__ = [
    'ChatRequest',
    'ProgressUpdate', 
    'InventoryRequest',
    'HealthRequest',
    'RecipeAdoptionRequest',
    'RecipeItem',
    'MenuSaveRequest',
    'CSVUploadError',
    'CSVUploadResponse',
    'ChatResponse',
    'HealthResponse',
    'InventoryResponse',
    'InventoryListResponse',
    'InventoryItemResponse',
    'ErrorResponse',
    'SSEEvent',
    'RecipeAdoptionResponse',
    'SavedRecipe',
    'SavedMenuRecipe',
    'MenuSaveResponse',
    'HistoryRecipe',
    'HistoryEntry',
    'MenuHistoryResponse'
]
