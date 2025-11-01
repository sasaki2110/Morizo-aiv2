#!/usr/bin/env python3
"""
API層 - FastAPIアプリケーション

メインアプリケーションの起動と設定
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from datetime import datetime
from dotenv import load_dotenv
from config.loggers import GenericLogger
from config.logging import setup_logging
from api.middleware import AuthenticationMiddleware, LoggingMiddleware
from api.routes import chat_router, health_router, recipe_router, menu_router
from api.models import ErrorResponse

# 環境変数の読み込み
load_dotenv()

# ログ設定の初期化とローテーション
setup_logging(log_level="INFO", initialize=True)

# ロガーの初期化
logger = GenericLogger("api", "main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger.info("🚀 [API] Morizo AI v2 starting...")
    
    try:
        # サービスの初期化
        logger.info("🔧 [API] Initializing services...")
        
        # Core層の初期化確認
        from core.agent import TrueReactAgent
        agent = TrueReactAgent()
        logger.info("✅ [API] Core layer initialized")
        
        # Service層の初期化確認
        from services.tool_router import ToolRouter
        tool_router = ToolRouter()
        logger.info("✅ [API] Service layer initialized")
        
        # MCP層の初期化確認
        from mcp_servers.client import MCPClient
        mcp_client = MCPClient()
        logger.info("✅ [API] MCP layer initialized")
        
        logger.info("🎉 [API] All services initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ [API] Service initialization failed: {e}")
        raise
    
    yield
    
    # 終了時の処理
    logger.info("🛑 [API] Morizo AI v2 shutting down...")


# FastAPIアプリケーションの作成
app = FastAPI(
    title="Morizo AI v2",
    description="Smart Pantry MVPのAIエージェント",
    version="2.0.0"
    # lifespan=lifespan  # 一時的に無効化
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# カスタムミドルウェアの追加
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthenticationMiddleware)

# ルートの登録
app.include_router(chat_router, prefix="", tags=["chat"])
app.include_router(health_router, prefix="", tags=["health"])
app.include_router(recipe_router, prefix="/api", tags=["recipe"])
app.include_router(menu_router, prefix="/api", tags=["menu"])


# エラーハンドラー
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーの処理"""
    logger.error(f"❌ [API] Validation error: {exc.errors()}")
    logger.error(f"❌ [API] Request body: {await request.body()}")
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail=f"バリデーションエラー: {exc.errors()}",
            status_code=422,
            timestamp=datetime.now().isoformat(),
            error_type="validation_error"
        ).dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTPエラーの処理"""
    logger.error(f"❌ [API] HTTP error: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            status_code=exc.status_code,
            timestamp=datetime.now().isoformat(),
            error_type="http_error"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """一般的なエラーの処理"""
    logger.error(f"❌ [API] Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="内部サーバーエラーが発生しました",
            status_code=500,
            timestamp=datetime.now().isoformat(),
            error_type="internal_error"
        ).dict()
    )


# ルートエンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Morizo AI v2 API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


# アプリケーションの起動確認
if __name__ == "__main__":
    import uvicorn
    import os
    
    # 環境変数から設定を取得
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 [API] Starting Morizo AI v2 on {host}:{port} (reload={reload})...")
    uvicorn.run(app, host=host, port=port, reload=reload)
