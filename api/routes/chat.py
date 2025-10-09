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
from core.agent import TrueReactAgent

router = APIRouter()
logger = GenericLogger("api", "chat")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """AIエージェントとの対話"""
    try:
        # リクエストボディの詳細ログ
        logger.info(f"🔍 [API] Chat request received:")
        logger.info(f"  Message: {request.message[:100]}...")
        logger.info(f"  Token: {'SET' if request.token else 'NOT SET'}")
        logger.info(f"  SSE Session ID: {request.sse_session_id if request.sse_session_id else 'NOT SET'}")
        
        # ミドルウェアで認証済みのユーザー情報を取得
        user_info = getattr(http_request.state, 'user_info', None)
        user_id = user_info['user_id'] if user_info else "anonymous"
        
        # Authorizationヘッダーからトークンを取得
        authorization = http_request.headers.get("Authorization")
        token = authorization[7:] if authorization and authorization.startswith("Bearer ") else ""
        
        logger.info(f"🔍 [API] User info from middleware: {user_id}")
        logger.info(f"🔍 [API] Token from Authorization header: {'SET' if token else 'NOT SET'}")
        
        # SSEセッションIDの生成（提供されていない場合）
        sse_session_id = request.sse_session_id or str(uuid.uuid4())
        
        # TrueReactAgentの初期化と実行
        agent = TrueReactAgent()
        
        # リクエストの処理（TaskChainManagerが進捗送信を担当）
        response_text = await agent.process_request(
            request.message, 
            user_id,
            token=token,
            sse_session_id=sse_session_id
        )
        
        # レスポンスの生成
        response = ChatResponse(
            response=response_text,
            success=True,
            model_used="gpt-4o-mini",
            user_id=user_id
        )
        
        # 完了通知はTaskChainManagerで送信されるため、ここでは送信しない
        # await sse_sender.send_complete(sse_session_id, response_text)
        
        logger.info(f"✅ [API] Chat request completed for user: {user_id}")
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
        
        # ミドルウェアで認証済みのユーザー情報を取得
        user_info = getattr(request.state, 'user_info', None)
        if not user_info:
            raise HTTPException(status_code=401, detail="認証が必要です")
        
        logger.info(f"🔍 [API] SSE stream authenticated for user: {user_info['user_id']}")
        
        # SSE接続の確立
        sse_sender = get_sse_sender()
        connection_id = sse_sender.add_connection(sse_session_id)
        
        async def event_generator():
            """SSEイベントジェネレータ"""
            try:
                # 接続確認メッセージ
                yield f"data: {_create_sse_event('connected', {'message': 'SSE接続が確立されました'})}\n\n"
                
                # メッセージループ
                heartbeat_counter = 0
                while True:
                    try:
                        # キューからメッセージを取得（タイムアウト付き）
                        if sse_session_id in sse_sender._connections and sse_sender._connections[sse_session_id]:
                            message = await asyncio.wait_for(
                                sse_sender._connections[sse_session_id][0].get(), 
                                timeout=30.0  # 30秒に延長
                            )
                            yield message
                            
                            # 完了メッセージの場合は接続を終了
                            try:
                                import json
                                message_data = json.loads(message.split('data: ')[1].strip())
                                if message_data.get('type') == 'complete':
                                    logger.info(f"🔚 [API] Processing complete, closing SSE connection for session: {sse_session_id}")
                                    yield f"data: {_create_sse_event('close', {'message': 'Connection will close after completion'})}\n\n"
                                    break
                            except (json.JSONDecodeError, IndexError):
                                # JSON解析エラーは無視
                                pass
                        else:
                            # 接続が存在しない場合は終了
                            logger.warning(f"⚠️ [API] SSE session {sse_session_id} not found, closing connection")
                            break
                    except asyncio.TimeoutError:
                        # タイムアウト時はハートビートを送信
                        heartbeat_counter += 1
                        logger.info(f"💓 [API] Sending heartbeat #{heartbeat_counter} to session: {sse_session_id}")
                        yield f"data: {_create_sse_event('heartbeat', {'message': 'ping', 'counter': heartbeat_counter})}\n\n"
                        
                        # 接続状態を確認
                        if not sse_sender._connections.get(sse_session_id):
                            logger.warning(f"⚠️ [API] SSE session {sse_session_id} disconnected, closing connection")
                            break
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
