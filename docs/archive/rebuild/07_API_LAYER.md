# Morizo AI v2 - API層設計

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: API層のアーキテクチャ設計と実装方針

## 🧠 設計思想

### **API層の役割**
- **HTTP通信の処理**: クライアントとのHTTP通信を処理
- **リクエスト・レスポンスの変換**: データ形式の変換
- **認証・認可**: APIレベルの認証・認可
- **エラーハンドリング**: HTTPエラーの処理

### **責任分離の徹底**
- **FastAPIアプリケーション**: メインアプリケーション
- **ルート定義**: エンドポイントの定義
- **ミドルウェア**: 認証・CORS・ログなどの共通処理
- **データモデル**: リクエスト・レスポンスの型定義

## 🏗️ API層アーキテクチャ

### **全体構成**
```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                             │
├─────────────────┬─────────────────┬─────────────────────────┤
│   FastAPI App   │   Route Defs    │      Middleware         │
│                 │                 │                         │
│ • アプリ起動    │ • エンドポイント│ • 認証・認可            │
│ • 設定管理      │ • ハンドラー    │ • CORS設定              │
│ • 依存性注入    │ • バリデーション│ • ログ出力              │
│ • エラーハンドリング│ • レスポンス生成│ • リクエスト処理      │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### **データフロー**
```
Client (HTTP Request)
    ↓
API Layer (FastAPI)
    ↓
Core Layer (TrueReactAgent)
    ↓ (Service.Method Call)
Service Layer (各サービス -> MCPClient)
    ↓ (Tool Name Call)
MCP Layer (各MCPツール)
    ↓ (DB Access, API Call)
External Systems (DB, 外部API)
    ↓
(各層を逆順に経由してレスポンス)
    ↓
Client (HTTP Response)
```

## 🔧 APIコンポーネント

### **1. FastAPIアプリケーション**

#### **役割**
- メインアプリケーションの起動・設定
- 依存性注入の設定
- ミドルウェアの設定

#### **実装方針**
```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時の処理
    logger.info("🚀 [API] Morizo AI v2 starting...")
    
    # サービスの初期化
    app.state.recipe_service = RecipeService()
    app.state.inventory_service = InventoryService()
    app.state.session_service = SessionService()
    
    yield
    
    # アプリケーション終了時の処理
    logger.info("🛑 [API] Morizo AI v2 shutting down...")

app = FastAPI(
    title="Morizo AI v2",
    description="Smart Pantry MVPのAIエージェント",
    version="2.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### **依存性注入**
```python
def get_recipe_service() -> RecipeService:
    """レシピサービスの取得"""
    return app.state.recipe_service

def get_inventory_service() -> InventoryService:
    """在庫サービスの取得"""
    return app.state.inventory_service

def get_session_service() -> SessionService:
    """セッションサービスの取得"""
    return app.state.session_service
```

### **2. ルート定義**

#### **役割**
- エンドポイントの定義
- リクエスト・レスポンスの処理
- バリデーション

#### **主要エンドポイント**
```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from models.requests import ChatRequest
from models.responses import ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    recipe_service: RecipeService = Depends(get_recipe_service),
    inventory_service: InventoryService = Depends(get_inventory_service),
    session_service: SessionService = Depends(get_session_service)
):
    """AIエージェントとの対話"""
    try:
        # 1. 認証の確認
        user_info = await session_service.verify_token(request.token)
        if not user_info:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # 2. セッションの取得・作成
        session = await session_service.get_or_create_session(
            user_info["user_id"], 
            request.token
        )
        
        # 3. リクエストの処理
        response = await process_chat_request(
            request, 
            session, 
            recipe_service, 
            inventory_service
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/stream/{sse_session_id}")
async def stream_progress(
    sse_session_id: str,
    token: str = Depends(get_bearer_token)
):
    """Server-Sent Eventsによる進捗表示"""
    try:
        # 1. 認証の確認
        user_info = await session_service.verify_token(token)
        if not user_info:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # 2. SSE接続の確立
        async def event_generator():
            # SSESenderを取得し、このクライアント用のキューを登録
            sse_sender = get_sse_sender(sse_session_id)
            queue = asyncio.Queue()
            connection_id = sse_sender.add_connection(queue)
            
            try:
                while True:
                    # キューからメッセージを取得してクライアントに送信
                    message = await queue.get()
                    yield f"data: {message}\n\n"
                    if '"type": "complete"' in message or '"type": "error"' in message:
                        break
            finally:
                # 接続が切れたらキューを削除
                sse_sender.remove_connection(connection_id)

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
        
    except Exception as e:
        logger.error(f"SSE stream failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

#### SSE実装の仕組み
1.  **SSESenderの役割**: `SSESender` クラスは、特定の `sse_session_id` に関連付けられたすべてのクライアント接続（キュー）を管理するシングルトンです。
2.  **接続とキュー**: クライアントが `/chat/stream/{sse_session_id}` に接続すると、`SSESender` はそのクライアント専用の `asyncio.Queue` を作成し、管理下の接続リストに追加します。
3.  **進捗イベントの発行**: コア層（`TaskChainManager`など）は、タスクの進捗があるたびに、`sse_session_id` を使って `SSESender` のインスタンスを取得し、`send_progress()` などのメソッドを呼び出します。
4.  **メッセージの配信**: `SSESender` は、受け取った進捗情報を、管理しているすべてのキュー（＝接続中の全クライアント）に投入します。
5.  **ストリーミング**: `/chat/stream` エンドポイントの `event_generator` は、自身のキューからメッセージを非同期に取得し、それをクライアントに `data: ...` の形式で送信し続けます。処理完了またはエラーのメッセージを受け取るとストリームを終了します。

@router.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": "Morizo AI v2",
        "version": "2.0.0"
    }
```

#### **リクエスト処理**
```python
async def process_chat_request(
    request: ChatRequest,
    session: Session,
    recipe_service: RecipeService,
    inventory_service: InventoryService
) -> ChatResponse:
    """チャットリクエストの処理"""
    
    # 1. TrueReactAgentの初期化
    agent = TrueReactAgent(
        recipe_service=recipe_service,
        inventory_service=inventory_service
    )
    
    # 2. リクエストの処理
    response_text = await agent.process_request(
        request.message, 
        session.user_id
    )
    
    # 3. レスポンスの生成
    return ChatResponse(
        response=response_text,
        success=True,
        model_used="gpt-4o-mini",
        user_id=session.user_id
    )
```

### **3. ミドルウェア**

#### **役割**
- 認証・認可の処理
- CORS設定
- ログ出力
- リクエスト処理

#### **認証ミドルウェア**
```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 認証が必要なエンドポイントのチェック
        if self._requires_auth(request.url.path):
            # トークンの取得
            token = self._extract_token(request)
            if not token:
                raise HTTPException(status_code=401, detail="Token required")
            
            # トークンの検証
            user_info = await self._verify_token(token)
            if not user_info:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # リクエストにユーザー情報を追加
            request.state.user_info = user_info
        
        response = await call_next(request)
        return response
    
    def _requires_auth(self, path: str) -> bool:
        """認証が必要なパスかどうかを判定"""
        public_paths = ["/health", "/docs", "/openapi.json"]
        return path not in public_paths
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """リクエストからトークンを抽出"""
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]
        return None
    
    async def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """トークンを検証"""
        # トークン検証の実装
        pass
```

#### **ログミドルウェア**
```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # リクエストログ
        logger.info(f"🔍 [API] {request.method} {request.url}")
        
        response = await call_next(request)
        
        # レスポンスログ
        process_time = time.time() - start_time
        logger.info(
            f"✅ [API] {request.method} {request.url} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.3f}s"
        )
        
        return response
```

### **4. データモデル**

#### **役割**
- リクエスト・レスポンスの型定義
- バリデーション
- シリアライゼーション

#### **リクエストモデル**
```python
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """チャットリクエスト"""
    message: str = Field(..., description="ユーザーメッセージ")
    token: str = Field(..., description="認証トークン")
    sse_session_id: Optional[str] = Field(None, description="SSEセッションID")

class ProgressUpdate(BaseModel):
    """進捗更新"""
    type: str = Field(..., description="更新タイプ")
    progress: int = Field(..., description="進捗率（0-100）")
    message: str = Field(..., description="進捗メッセージ")
    timestamp: str = Field(..., description="タイムスタンプ")

class InventoryRequest(BaseModel):
    """在庫リクエスト"""
    item_name: str = Field(..., description="アイテム名")
    quantity: float = Field(..., description="数量")
    unit: str = Field(..., description="単位")
    storage_location: Optional[str] = Field(None, description="保管場所")
    expiry_date: Optional[str] = Field(None, description="消費期限")
```

#### **レスポンスモデル**
```python
class ChatResponse(BaseModel):
    """チャットレスポンス"""
    response: str = Field(..., description="AIからの応答")
    success: bool = Field(..., description="処理成功フラグ")
    model_used: str = Field(..., description="使用されたモデル")
    user_id: str = Field(..., description="ユーザーID")

class InventoryResponse(BaseModel):
    """在庫レスポンス"""
    id: str = Field(..., description="アイテムID")
    item_name: str = Field(..., description="アイテム名")
    quantity: float = Field(..., description="数量")
    unit: str = Field(..., description="単位")
    storage_location: Optional[str] = Field(None, description="保管場所")
    expiry_date: Optional[str] = Field(None, description="消費期限")
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")
```

## 🔄 エラーハンドリング

### **HTTPエラーの処理**
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPエラーの処理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般的なエラーの処理"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )
```

### **バリデーションエラーの処理**
```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーの処理"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.now().isoformat()
        }
    )
```

## 🚀 実装戦略

### **Phase 1: 基本API**
1. **FastAPIアプリケーション**: 基本的なアプリケーション
2. **ルート定義**: 基本的なエンドポイント
3. **データモデル**: 基本的なリクエスト・レスポンス

### **Phase 2: 高度な機能**
1. **認証・認可**: トークンベース認証
2. **ミドルウェア**: 認証・CORS・ログ
3. **エラーハンドリング**: 包括的なエラー処理

### **Phase 3: 最適化**
1. **パフォーマンス最適化**: レスポンス時間の短縮
2. **セキュリティ強化**: セキュリティヘッダー・レート制限
3. **監視・ログ**: 詳細な監視・ログ出力

## 📊 成功基準

### **機能面**
- [ ] FastAPIアプリケーションの動作確認
- [ ] ルート定義の動作確認
- [ ] ミドルウェアの動作確認
- [ ] データモデルの動作確認
- [ ] エラーハンドリングの動作確認

### **技術面**
- [ ] 全ファイルが100行以下
- [ ] 認証・認可の実装
- [ ] バリデーションの実装
- [ ] 保守性の確認

---

**このドキュメントは、Morizo AI v2のAPI層設計を定義します。**
**すべてのAPIは、この設計に基づいて実装されます。**
