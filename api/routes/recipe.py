#!/usr/bin/env python3
"""
API層 - レシピルート

レシピ採用通知と履歴管理のエンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List
from config.loggers import GenericLogger
from ..models import RecipeAdoptionRequest, RecipeAdoptionResponse, SavedRecipe
from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
from mcp_servers.utils import get_authenticated_client

router = APIRouter()
logger = GenericLogger("api", "recipe")


@router.post("/recipe/adopt", response_model=RecipeAdoptionResponse)
async def adopt_recipe(request: RecipeAdoptionRequest, http_request: Request):
    """レシピ採用通知エンドポイント（複数対応）"""
    try:
        logger.info(f"🔍 [API] Recipe adoption request received:")
        logger.info(f"  Number of recipes: {len(request.recipes)}")
        
        for i, recipe in enumerate(request.recipes):
            logger.info(f"  Recipe {i+1}: {recipe.title} ({recipe.category}, {recipe.menu_source})")
        
        # 1. 認証トークンの取得（ヘッダーまたはリクエストボディ）
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        # リクエストボディのトークンを優先
        if request.token:
            token = request.token
            
        logger.info(f"🔍 [API] Token: {'SET' if token else 'NOT SET'}")
        
        # 2. ユーザー情報の取得（ミドルウェアから）
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
            
        user_id = user_info['user_id']
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 3. menu_source → source のマッピング変換
        db_source_mapping = {
            "llm_menu": "web",   # LLM推論で生成したメニューはWeb検索でレシピ取得
            "rag_menu": "rag",   # RAG検索で生成したメニュー
            "manual": "manual"   # 将来の手動検索用
        }
        
        # 4. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"🔍 [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 5. 各レシピを順次保存
        crud = RecipeHistoryCRUD()
        saved_recipes = []
        failed_recipes = []
        
        for i, recipe in enumerate(request.recipes):
            try:
                logger.info(f"🔍 [API] Processing recipe {i+1}/{len(request.recipes)}: {recipe.title}")
                
                # menu_source → source のマッピング
                db_source = db_source_mapping.get(recipe.menu_source)
                if not db_source:
                    logger.error(f"❌ [API] Invalid menu_source for recipe {i+1}: {recipe.menu_source}")
                    failed_recipes.append(f"Recipe {i+1}: Invalid menu_source '{recipe.menu_source}'")
                    continue
                
                logger.info(f"🔍 [API] Mapped source for recipe {i+1}: {recipe.menu_source} → {db_source}")
                
                # RecipeHistoryCRUD.add_history()を呼び出し
                result = await crud.add_history(
                    client=client,
                    user_id=user_id,
                    title=recipe.title,
                    source=db_source,
                    url=recipe.url
                )
                
                if result.get("success"):
                    history_id = result.get("data", {}).get("id")
                    logger.info(f"✅ [API] Recipe {i+1} saved successfully: {history_id}")
                    
                    saved_recipes.append(SavedRecipe(
                        title=recipe.title,
                        category=recipe.category,
                        history_id=history_id
                    ))
                else:
                    error_msg = result.get("error", "不明なエラー")
                    logger.error(f"❌ [API] Failed to save recipe {i+1}: {error_msg}")
                    failed_recipes.append(f"Recipe {i+1}: {error_msg}")
                    
            except Exception as e:
                logger.error(f"❌ [API] Error processing recipe {i+1}: {e}")
                failed_recipes.append(f"Recipe {i+1}: {str(e)}")
        
        # 6. レスポンスの生成
        total_recipes = len(request.recipes)
        saved_count = len(saved_recipes)
        failed_count = len(failed_recipes)
        
        if saved_count == total_recipes:
            # すべて成功
            message = f"{saved_count}つのレシピが履歴に保存されました"
            success = True
        elif saved_count > 0:
            # 一部成功
            message = f"{saved_count}つのレシピが保存されました（{failed_count}つ失敗）"
            success = True
        else:
            # すべて失敗
            message = f"すべてのレシピの保存に失敗しました"
            success = False
        
        logger.info(f"🔍 [API] Final result: {saved_count}/{total_recipes} recipes saved")
        
        return RecipeAdoptionResponse(
            success=success,
            message=message,
            saved_recipes=saved_recipes,
            total_saved=saved_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in adopt_recipe: {e}")
        raise HTTPException(status_code=500, detail="レシピ採用処理でエラーが発生しました")
