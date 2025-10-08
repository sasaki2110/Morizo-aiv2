#!/usr/bin/env python3
"""
API層 - ヘルスチェックルート

サービス状態の確認とヘルスチェック
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Dict, Any
from config.loggers import GenericLogger
from ..models.requests import HealthRequest
from ..models.responses import HealthResponse

router = APIRouter()
logger = GenericLogger("api", "health")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """基本的なヘルスチェック"""
    try:
        logger.info("🔍 [API] Health check requested")
        
        response = HealthResponse(
            status="healthy",
            service="Morizo AI v2",
            version="2.0.0",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info("✅ [API] Health check completed")
        return response
        
    except Exception as e:
        logger.error(f"❌ [API] Health check failed: {e}")
        raise HTTPException(status_code=500, detail="ヘルスチェックに失敗しました")


@router.post("/health", response_model=HealthResponse)
async def detailed_health_check(request: HealthRequest):
    """詳細なヘルスチェック"""
    try:
        logger.info("🔍 [API] Detailed health check requested")
        
        # 基本的なヘルス情報
        health_info = {
            "status": "healthy",
            "service": "Morizo AI v2",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # サービス状態の確認が要求された場合
        if request.check_services:
            services_status = await _check_services_status()
            health_info["services"] = services_status
        
        response = HealthResponse(**health_info)
        
        logger.info("✅ [API] Detailed health check completed")
        return response
        
    except Exception as e:
        logger.error(f"❌ [API] Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="詳細ヘルスチェックに失敗しました")


async def _check_services_status() -> Dict[str, Any]:
    """各サービスの状態を確認"""
    try:
        services_status = {}
        
        # Core層の状態確認
        try:
            from core.agent import TrueReactAgent
            agent = TrueReactAgent()
            services_status["core"] = {"status": "healthy", "message": "Core layer is operational"}
        except Exception as e:
            services_status["core"] = {"status": "unhealthy", "message": str(e)}
        
        # Service層の状態確認
        try:
            from services.tool_router import ToolRouter
            tool_router = ToolRouter()
            services_status["services"] = {"status": "healthy", "message": "Service layer is operational"}
        except Exception as e:
            services_status["services"] = {"status": "unhealthy", "message": str(e)}
        
        # MCP層の状態確認
        try:
            from mcp_servers.client import MCPClient
            mcp_client = MCPClient()
            services_status["mcp"] = {"status": "healthy", "message": "MCP layer is operational"}
        except Exception as e:
            services_status["mcp"] = {"status": "unhealthy", "message": str(e)}
        
        return services_status
        
    except Exception as e:
        logger.error(f"❌ [API] Service status check failed: {e}")
        return {"error": str(e)}
