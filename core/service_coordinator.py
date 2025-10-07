#!/usr/bin/env python3
"""
ServiceCoordinator - サービス調整専門クラス

Core LayerとService Layerの橋渡しを担当
ToolRouterの一元管理とサービス呼び出しの調整を提供
"""

from typing import Dict, Any
from services.tool_router import ToolRouter
from config.loggers import GenericLogger


class ServiceCoordinator:
    """サービス調整クラス - ToolRouterの一元管理とサービス呼び出しの調整"""
    
    def __init__(self):
        """初期化"""
        self.tool_router = ToolRouter()
        self.logger = GenericLogger("core", "service_coordinator")
    
    async def execute_service(self, service: str, method: str, parameters: Dict[str, Any], token: str) -> Any:
        """サービスメソッドの実行"""
        try:
            # ToolRouterのroute_service_methodを使用してサービス名・メソッド名からMCPツールをルーティング
            result = await self.tool_router.route_service_method(service, method, parameters, token)
            
            # Check for ambiguity detection
            if isinstance(result, dict) and result.get("status") == "ambiguity_detected":
                from .exceptions import AmbiguityDetected
                raise AmbiguityDetected(
                    context=result.get("context", {}),
                    message=result.get("message", "Ambiguity detected")
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Service execution failed: {service}.{method} - {str(e)}")
            raise
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """利用可能なツールの説明を取得"""
        try:
            self.logger.info(f"🔧 [ServiceCoordinator] Getting tool descriptions")
            descriptions = self.tool_router.get_tool_descriptions()
            self.logger.info(f"✅ [ServiceCoordinator] Retrieved {len(descriptions)} tool descriptions")
            return descriptions
        except Exception as e:
            self.logger.error(f"❌ [ServiceCoordinator] Error getting tool descriptions: {e}")
            return {}
    
    def get_available_tools_description(self) -> str:
        """利用可能なツールの説明を文字列形式で取得"""
        try:
            self.logger.info(f"🔧 [ServiceCoordinator] Getting available tools description")
            
            tool_descriptions = self.get_tool_descriptions()
            
            description_text = "利用可能なツール:\n"
            for tool_name, description in tool_descriptions.items():
                description_text += f"- {tool_name}: {description}\n"
            
            self.logger.info(f"✅ [ServiceCoordinator] Tools description generated successfully")
            return description_text
            
        except Exception as e:
            self.logger.error(f"❌ [ServiceCoordinator] Error in get_available_tools_description: {e}")
            return "ツール情報の取得に失敗しました。"
