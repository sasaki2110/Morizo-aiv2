#!/usr/bin/env python3
"""
API層 - チャットルート

メインのチャット処理とSSE進捗表示
"""

import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from config.loggers import GenericLogger
from ..models import ChatRequest, ChatResponse, ProgressUpdate
from ..utils.sse_manager import get_sse_sender
from ..utils.auth_handler import get_auth_handler
from core.agent import TrueReactAgent

router = APIRouter()
logger = GenericLogger("api", "chat")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """AIエージェントとの対話"""
    try:
        # リクエストボディの詳細ログ
        logger.info(f"🔍 [API] Chat request received:")
        logger.info(f"  Message: {request.message[:100]}...")
        logger.info(f"  Token: {'SET' if request.token else 'NOT SET'}")
        logger.info(f"  SSE Session ID: {request.sse_session_id if request.sse_session_id else 'NOT SET'}")
        
        # 認証の確認（tokenが提供されている場合のみ）
        user_info = None
        if request.token:
            auth_handler = get_auth_handler()
            user_info = await auth_handler.verify_token(request.token)
            if not user_info:
                raise HTTPException(status_code=401, detail="認証が必要です")
        else:
            # tokenが提供されていない場合は、ミドルウェアで認証済みと仮定
            # 実際のユーザー情報はrequest.stateから取得する必要がある
            logger.info("🔍 [API] No token provided, assuming middleware authentication")
        
        # SSEセッションIDの生成（提供されていない場合）
        sse_session_id = request.sse_session_id or str(uuid.uuid4())
        
        # TrueReactAgentの初期化と実行
        agent = TrueReactAgent()
        
        # SSE進捗表示の開始
        sse_sender = get_sse_sender()
        await sse_sender.send_progress(sse_session_id, 25, "リクエストを処理中...")
        
        # リクエストの処理
        user_id = user_info["user_id"] if user_info else "anonymous"
        response_text = await agent.process_request(
            request.message, 
            user_id,
            token=request.token
        )
        
        # 進捗更新
        await sse_sender.send_progress(sse_session_id, 75, "レスポンスを生成中...")
        
        # レスポンスの生成
        response = ChatResponse(
            response=response_text,
            success=True,
            model_used="gpt-4o-mini",
            user_id=user_id
        )
        
        # 完了通知
        await sse_sender.send_complete(sse_session_id, "処理が完了しました")
        
        logger.info(f"✅ [API] Chat request completed for user: {user_info['user_id']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Chat request failed: {e}")
        
        # エラー通知（SSEセッションIDがある場合）
        if request.sse_session_id:
            sse_sender = get_sse_sender()
            await sse_sender.send_error(request.sse_session_id, str(e))
        
        raise HTTPException(status_code=500, detail="チャット処理でエラーが発生しました")


@router.get("/chat/stream/{sse_session_id}")
async def stream_progress(sse_session_id: str, request: Request):
    """Server-Sent Eventsによる進捗表示"""
    try:
        logger.info(f"🔍 [API] SSE stream requested for session: {sse_session_id}")
        
        # 認証の確認
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        auth_handler = get_auth_handler()
        token = auth_handler.extract_token_from_header(auth_header)
        if not token:
            raise HTTPException(status_code=401, detail="無効な認証トークンです")
        
        user_info = await auth_handler.verify_token(token)
        if not user_info:
            raise HTTPException(status_code=401, detail="認証に失敗しました")
        
        # SSE接続の確立
        sse_sender = get_sse_sender()
        connection_id = sse_sender.add_connection(sse_session_id)
        
        async def event_generator():
            """SSEイベントジェネレータ"""
            try:
                # 接続確認メッセージ
                yield f"data: {_create_sse_event('connected', {'message': 'SSE接続が確立されました'})}\n\n"
                
                # メッセージループ
                while True:
                    try:
                        # キューからメッセージを取得（タイムアウト付き）
                        if sse_session_id in sse_sender._connections and sse_sender._connections[sse_session_id]:
                            message = await asyncio.wait_for(
                                sse_sender._connections[sse_session_id][0].get(), 
                                timeout=1.0
                            )
                            yield message
                        else:
                            # 接続が存在しない場合は終了
                            break
                    except asyncio.TimeoutError:
                        # タイムアウト時は接続確認
                        if not sse_sender._connections.get(sse_session_id):
                            break
                        continue
                    except Exception as e:
                        logger.error(f"❌ [API] SSE message error: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"❌ [API] SSE stream error: {e}")
                yield f"data: {_create_sse_event('error', {'message': str(e)})}\n\n"
            finally:
                # 接続のクリーンアップ
                sse_sender.remove_connection(sse_session_id, connection_id)
                logger.info(f"🔌 [API] SSE connection closed for session: {sse_session_id}")
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] SSE stream failed: {e}")
        raise HTTPException(status_code=500, detail="SSEストリームでエラーが発生しました")


def _create_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """SSEイベントの作成"""
    import json
    from datetime import datetime
    
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    return json.dumps(event, ensure_ascii=False)
