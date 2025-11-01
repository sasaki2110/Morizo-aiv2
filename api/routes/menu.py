#!/usr/bin/env python3
"""
API層 - 献立ルート

献立保存のエンドポイント
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from config.loggers import GenericLogger
from ..models import MenuSaveRequest, MenuSaveResponse, SavedMenuRecipe, MenuHistoryResponse, HistoryRecipe, HistoryEntry
from mcp_servers.recipe_history_crud import RecipeHistoryCRUD
from mcp_servers.utils import get_authenticated_client
from services.session.service import session_service

router = APIRouter()
logger = GenericLogger("api", "menu")


@router.post("/menu/save", response_model=MenuSaveResponse)
async def save_menu(request: MenuSaveRequest, http_request: Request):
    """献立をDBに保存するエンドポイント"""
    try:
        logger.info(f"🔍 [API] Menu save request received: sse_session_id={request.sse_session_id}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 2. 選択済みレシピを取得（フロントエンドから直接送信された場合は優先）
        if request.recipes:
            # フロントエンドから直接送信されたレシピ情報を使用
            selected_recipes = request.recipes
            logger.info(f"🔍 [API] Using recipes from request: main={selected_recipes.get('main') is not None}, sub={selected_recipes.get('sub') is not None}, soup={selected_recipes.get('soup') is not None}")
        elif request.sse_session_id:
            # セッションIDから選択済みレシピを取得（後方互換性）
            selected_recipes = await session_service.get_selected_recipes(request.sse_session_id)
            logger.info(f"🔍 [API] Using recipes from session: main={selected_recipes.get('main') is not None}, sub={selected_recipes.get('sub') is not None}, soup={selected_recipes.get('soup') is not None}")
        else:
            # どちらも指定されていない場合はエラー
            logger.warning(f"⚠️ [API] Neither recipes nor sse_session_id provided")
            return MenuSaveResponse(
                success=False,
                message="レシピ情報またはセッションIDが必要です",
                saved_recipes=[],
                total_saved=0
            )
        
        # 選択済みレシピがない、またはすべてNoneの場合
        if not selected_recipes or all(recipe is None for recipe in selected_recipes.values()):
            logger.warning(f"⚠️ [API] No selected recipes found")
            return MenuSaveResponse(
                success=False,
                message="保存するレシピがありません",
                saved_recipes=[],
                total_saved=0
            )
        
        # 選択済みレシピのログ出力
        logger.info(f"🔍 [API] Selected recipes to save:")
        for category in ["main", "sub", "soup"]:
            recipe = selected_recipes.get(category)
            if recipe:
                logger.info(f"  {category}: {recipe.get('title', 'N/A')} (source: {recipe.get('source', 'N/A')})")
            else:
                logger.info(f"  {category}: None")
        
        # 3. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 4. 各レシピをDBに保存
        crud = RecipeHistoryCRUD()
        saved_recipes = []
        failed_count = 0
        
        category_prefix_map = {
            "main": "主菜: ",
            "sub": "副菜: ",
            "soup": "汁物: "
        }
        
        source_mapping = {
            "llm": "web",
            "rag": "rag",
            "web": "web"
        }
        
        for category in ["main", "sub", "soup"]:
            recipe = selected_recipes.get(category)
            if not recipe:
                continue  # 未選択のレシピはスキップ
            
            try:
                # タイトルにプレフィックスを追加
                original_title = recipe.get("title", "")
                prefixed_title = f"{category_prefix_map[category]}{original_title}"
                
                # source のマッピング
                recipe_source = recipe.get("source", "web")
                db_source = source_mapping.get(recipe_source, "web")
                
                # URLの取得
                url = recipe.get("url")
                
                logger.info(f"🔍 [API] Saving {category}: title='{prefixed_title}', source={recipe_source}→{db_source}")
                
                # DBに保存
                result = await crud.add_history(
                    client=client,
                    user_id=user_id,
                    title=prefixed_title,
                    source=db_source,
                    url=url
                )
                
                if result.get("success"):
                    history_id = result.get("data", {}).get("id")
                    logger.info(f"✅ [API] {category} saved successfully: history_id={history_id}")
                    saved_recipes.append(SavedMenuRecipe(
                        category=category,
                        title=prefixed_title,
                        history_id=history_id
                    ))
                else:
                    failed_count += 1
                    error_msg = result.get("error", "不明なエラー")
                    logger.error(f"❌ [API] Failed to save {category}: {error_msg}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ [API] Error saving {category}: {e}")
        
        # 5. レスポンスの生成
        total_saved = len(saved_recipes)
        if total_saved == 0:
            message = "レシピの保存に失敗しました"
            success = False
        elif failed_count > 0:
            message = f"{total_saved}つのレシピが保存されました（{failed_count}つ失敗）"
            success = True
        else:
            message = f"{total_saved}つのレシピが履歴に保存されました"
            success = True
        
        logger.info(f"🔍 [API] Final result: {total_saved} recipes saved, {failed_count} failed")
        
        return MenuSaveResponse(
            success=success,
            message=message,
            saved_recipes=saved_recipes,
            total_saved=total_saved
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in save_menu: {e}")
        raise HTTPException(status_code=500, detail="献立保存処理でエラーが発生しました")


@router.get("/menu/history", response_model=MenuHistoryResponse)
async def get_menu_history(
    days: int = 14,
    category: Optional[str] = None,
    http_request: Request = None
):
    """献立履歴を取得するエンドポイント"""
    try:
        logger.info(f"🔍 [API] Menu history request received: days={days}, category={category}")
        
        # 1. 認証処理
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        user_info = getattr(http_request.state, 'user_info', None)
        if not user_info:
            logger.error("❌ [API] User info not found in request state")
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        user_id = user_info['user_id']
        logger.info(f"🔍 [API] User ID: {user_id}")
        
        # 2. 認証済みSupabaseクライアントの作成
        try:
            client = get_authenticated_client(user_id, token)
            logger.info(f"✅ [API] Authenticated client created for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ [API] Failed to create authenticated client: {e}")
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # 3. 履歴を取得
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # recipe_historysテーブルから取得
        result = client.table("recipe_historys")\
            .select("*")\
            .eq("user_id", user_id)\
            .gte("cooked_at", cutoff_date.isoformat())\
            .order("cooked_at", desc=True)\
            .execute()
        
        logger.info(f"🔍 [API] Retrieved {len(result.data)} recipe histories from database")
        
        # 4. 日付ごとにグループ化
        history_by_date = {}
        category_prefix_map = {
            "main": "主菜: ",
            "sub": "副菜: ",
            "soup": "汁物: "
        }
        
        for item in result.data:
            # cooked_atから日付を取得
            cooked_at_str = item.get("cooked_at")
            if not cooked_at_str:
                logger.warning(f"⚠️ [API] Missing cooked_at for history_id={item.get('id')}")
                continue
            
            try:
                # ISO形式の日時文字列をパース
                if "Z" in cooked_at_str:
                    cooked_at = datetime.fromisoformat(cooked_at_str.replace("Z", "+00:00"))
                else:
                    cooked_at = datetime.fromisoformat(cooked_at_str)
                
                # タイムゾーン情報を削除して日付のみ取得
                if cooked_at.tzinfo:
                    cooked_at = cooked_at.replace(tzinfo=None)
                
                date_key = cooked_at.date().isoformat()
            except Exception as e:
                logger.error(f"❌ [API] Failed to parse cooked_at: {cooked_at_str}, error: {e}")
                continue
            
            if date_key not in history_by_date:
                history_by_date[date_key] = []
            
            # カテゴリを判定（タイトルのプレフィックスから）
            title = item.get("title", "")
            recipe_category = None
            for cat, prefix in category_prefix_map.items():
                if title.startswith(prefix):
                    recipe_category = cat
                    break
            
            # カテゴリフィルター適用
            if category and recipe_category != category:
                continue
            
            history_by_date[date_key].append(HistoryRecipe(
                category=recipe_category,
                title=title,
                source=item.get("source", "web"),
                url=item.get("url"),
                history_id=item.get("id")
            ))
        
        # 5. 日付順にソート（最新順）
        sorted_history = sorted(
            [HistoryEntry(date=date, recipes=recipes) for date, recipes in history_by_date.items()],
            key=lambda x: x.date,
            reverse=True
        )
        
        logger.info(f"✅ [API] Returning {len(sorted_history)} date entries with total {sum(len(entry.recipes) for entry in sorted_history)} recipes")
        
        # 6. レスポンスを生成
        return MenuHistoryResponse(
            success=True,
            data=sorted_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Unexpected error in get_menu_history: {e}")
        raise HTTPException(status_code=500, detail="履歴取得処理でエラーが発生しました")

