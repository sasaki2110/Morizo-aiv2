#!/usr/bin/env python3
"""
WebSearchResultIntegrator - Web検索結果統合

Web検索結果と候補リストを統合する処理を担当
"""

from typing import Dict, Any, List, Optional
from config.loggers import GenericLogger


class WebSearchResultIntegrator:
    """Web検索結果統合ハンドラー"""
    
    def __init__(self):
        """初期化"""
        self.logger = GenericLogger("service", "llm.response.web_integrator")
    
    def integrate(self, candidates: List[Dict[str, Any]], task_id: str, task4_data: Optional[Dict[str, Any]] = None, utils = None) -> List[Dict[str, Any]]:
        """
        Web検索結果を主菜提案結果に統合
        
        Args:
            candidates: 主菜提案の候補リスト
            task_id: タスクID
            task4_data: task4の実行結果データ
            utils: ResponseProcessorUtilsインスタンス
        
        Returns:
            URL情報が統合された候補リスト
        """
        try:
            # task4の結果からWeb検索結果を取得
            web_search_results = []
            if task4_data and task4_data.get("success") and task4_data.get("data"):
                web_data = task4_data["data"]
                # Web検索結果からレシピリストを抽出
                if "rag_menu" in web_data and "main_dish" in web_data["rag_menu"]:
                    recipes = web_data["rag_menu"]["main_dish"].get("recipes", [])
                    web_search_results = recipes
            
            if not web_search_results:
                self.logger.info(f"🔍 [WebSearchResultIntegrator] No web search results found for task {task_id}")
                return candidates
            
            # 候補とWeb検索結果を統合
            integrated_candidates = []
            for i, candidate in enumerate(candidates):
                integrated_candidate = candidate.copy()
                
                # 対応するWeb検索結果を取得
                if i < len(web_search_results):
                    web_result = web_search_results[i]
                    if web_result.get("url"):
                        # URL情報を統合
                        domain = utils.extract_domain(web_result.get("url", "")) if utils else ""
                        integrated_candidate["urls"] = [{
                            "title": web_result.get("title", ""),
                            "url": web_result.get("url", ""),
                            "domain": domain
                        }]
                        self.logger.info(f"🔗 [WebSearchResultIntegrator] Integrated URLs for candidate {i}: {integrated_candidate.get('urls', [])}")
                    else:
                        self.logger.warning(f"⚠️ [WebSearchResultIntegrator] Web search result has no URL for candidate {i}")
                else:
                    self.logger.warning(f"⚠️ [WebSearchResultIntegrator] No web search result for candidate {i}")
                
                integrated_candidates.append(integrated_candidate)
            
            self.logger.info(f"✅ [WebSearchResultIntegrator] Successfully integrated web search results for {len(integrated_candidates)} candidates")
            return integrated_candidates
            
        except Exception as e:
            self.logger.error(f"❌ [WebSearchResultIntegrator] Error integrating web search results: {e}")
            return candidates

