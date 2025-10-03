# Morizo AI v2 - ロギング戦略

## 📋 概要

**作成日**: 2025年1月29日  
**バージョン**: 1.0  
**目的**: ロギング戦略と実装方針の明確化

## 🎯 ロギングの目的

### **主要目的**
1. **デバッグ支援**: 問題の特定と解決
2. **監視**: システムの動作状況の把握
3. **パフォーマンス分析**: 処理時間の測定
4. **セキュリティ監査**: アクセスログの記録
5. **運用支援**: 障害時の原因調査

### **ログレベル戦略**
- **ERROR**: システムエラー、例外発生
- **WARNING**: 注意が必要な状況
- **INFO**: 重要な処理の開始・完了
- **DEBUG**: 詳細なデバッグ情報（開発時のみ）

## 🏗️ ロギングアーキテクチャ

### **階層別ロギング**
```
┌─────────────────────────────────────────────────────────────┐
│                    Logging Architecture                     │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Application   │    Service      │        MCP              │
│     Layer       │     Layer       │       Layer             │
│                 │                 │                         │
│ • リクエスト    │ • ビジネス      │ • ツール呼び出し        │
│ • レスポンス    │ • データ変換    │ • 外部API呼び出し       │
│ • エラーハンドリング│ • バリデーション│ • データベース操作    │
│ • 認証・認可    │ • エラー処理    │ • 認証処理              │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### **ログ出力先**
- **ファイル**: `morizo_ai.log` (永続化)
- **コンソール**: 開発時のリアルタイム確認
- **バックアップ**: ローテーションによる古いログの保存

## 🔧 ロギング実装

### **1. ログ設定**

#### **基本設定**
```python
import logging
from config.logging_config import setup_logging

# ログ設定の初期化
logger = setup_logging()

# ログレベルの設定
logger.setLevel(logging.INFO)
```

#### **ログフォーマット**
```python
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

#### **ログファイル管理**
```python
def setup_log_rotation() -> str:
    """ログローテーション設定"""
    log_file = 'morizo_ai.log'
    backup_file = 'morizo_ai.log.1'
    
    # 既存のログファイルがある場合はバックアップを作成
    if os.path.exists(log_file):
        shutil.move(log_file, backup_file)
        logger.info(f"📦 ログファイルをバックアップ: {log_file} → {backup_file}")
    
    return log_file
```

### **2. 階層別ログ出力**

#### **API層ログ**
```python
class APILogger:
    def __init__(self):
        self.logger = logging.getLogger('morizo_ai.api')
    
    def log_request(self, method: str, url: str, user_id: str = None):
        """リクエストログ"""
        self.logger.info(f"🔍 [API] {method} {url} User: {user_id}")
    
    def log_response(self, method: str, url: str, status_code: int, duration: float):
        """レスポンスログ"""
        self.logger.info(
            f"✅ [API] {method} {url} Status: {status_code} Time: {duration:.3f}s"
        )
    
    def log_error(self, method: str, url: str, error: Exception):
        """エラーログ"""
        self.logger.error(f"❌ [API] {method} {url} Error: {error}")
```

#### **サービス層ログ**
```python
class ServiceLogger:
    def __init__(self, service_name: str):
        self.logger = logging.getLogger(f'morizo_ai.service.{service_name}')
    
    def log_operation_start(self, operation: str, parameters: dict):
        """操作開始ログ"""
        self.logger.info(f"🚀 [SERVICE] {operation} started with {parameters}")
    
    def log_operation_end(self, operation: str, result: any):
        """操作終了ログ"""
        self.logger.info(f"✅ [SERVICE] {operation} completed: {result}")
    
    def log_operation_error(self, operation: str, error: Exception):
        """操作エラーログ"""
        self.logger.error(f"❌ [SERVICE] {operation} failed: {error}")
```

#### **MCP層ログ**
```python
class MCPLogger:
    def __init__(self, mcp_name: str):
        self.logger = logging.getLogger(f'morizo_ai.mcp.{mcp_name}')
    
    def log_tool_call(self, tool_name: str, parameters: dict):
        """ツール呼び出しログ"""
        self.logger.info(f"🔧 [MCP] {tool_name} called with {parameters}")
    
    def log_tool_result(self, tool_name: str, result: any):
        """ツール結果ログ"""
        self.logger.info(f"✅ [MCP] {tool_name} completed: {result}")
    
    def log_tool_error(self, tool_name: str, error: Exception):
        """ツールエラーログ"""
        self.logger.error(f"❌ [MCP] {tool_name} failed: {error}")
```

### **MCPプロセス別ロギング**

#### **設計原則**
- **別プロセス実行**: 各MCPは独立したプロセスで動作
- **個別logger生成**: 各MCPプロセスで個別にloggerを生成
- **出力先統一**: すべてのMCPログを`morizo_ai.log`に統一
- **プロセス識別**: プロセスIDを含めたログ出力

#### **実装例**
```python
import logging
import os

# 各MCPプロセス内でのlogger設定
def setup_mcp_logger(mcp_name: str):
    """MCPプロセス用のlogger設定"""
    logger = logging.getLogger(f'morizo_ai.mcp.{mcp_name}')
    logger.setLevel(logging.INFO)
    
    # 既存のハンドラーをクリア（重複回避）
    logger.handlers.clear()
    
    # ファイルハンドラー（統一出力先）
    file_handler = logging.FileHandler('morizo_ai.log', encoding='utf-8', mode='a')
    file_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # プロセスIDの記録
    logger.debug(f"🔧 [{mcp_name}] シンプルログ設定完了")
    logger.debug(f"🔧 [{mcp_name}] プロセスID: {os.getpid()}")
    
    return logger

# 使用例
logger = setup_mcp_logger('recipe_mcp')
logger.info("レシピ検索を開始します")
```

#### **実際の実装例（recipe_mcp_server_stdio.pyより）**
```python
# ログ設定
log_file = 'morizo_ai.log'
logger = logging.getLogger('morizo_ai.recipe_mcp')
logger.setLevel(logging.INFO)

# 既存のハンドラーをクリア（重複回避）
logger.handlers.clear()

# ファイルハンドラー
file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# ログテスト
logger.debug("🔧 [recipe_mcp] シンプルログ設定完了")
logger.debug(f"🔧 [recipe_mcp] プロセスID: {os.getpid()}")
```

### **3. パフォーマンスログ**

#### **処理時間測定**
```python
import time
from functools import wraps

def log_execution_time(func):
    """実行時間をログに記録するデコレータ"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"⏱️ [PERF] {func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"⏱️ [PERF] {func.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper
```

#### **メモリ使用量ログ**
```python
import psutil
import os

def log_memory_usage(operation: str):
    """メモリ使用量をログに記録"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    logger.info(f"💾 [MEMORY] {operation} - Memory usage: {memory_mb:.1f}MB")
```

## 🔤 プロンプトロギング戦略

### **プロンプトロギングのルール**

#### **1. トークン数情報の記録**
```python
def log_prompt_with_tokens(prompt: str, max_tokens: int = 4000):
    """プロンプトとトークン数情報をログに記録"""
    # 簡易的なトークン数計算（1トークン ≈ 4文字）
    estimated_tokens = len(prompt) // 4
    token_usage_ratio = estimated_tokens / max_tokens
    
    logger.info(f"🔤 [PROMPT] 予想トークン数: {estimated_tokens}/{max_tokens} ({token_usage_ratio:.1%})")
    
    # トークン数超過警告
    if token_usage_ratio > 0.8:
        logger.warning(f"⚠️ [PROMPT] トークン数が80%を超過: {token_usage_ratio:.1%}")
    elif token_usage_ratio > 1.0:
        logger.error(f"❌ [PROMPT] トークン数が上限を超過: {token_usage_ratio:.1%}")
    
    # プロンプト内容（5行で省略）
    prompt_lines = prompt.split('\n')
    if len(prompt_lines) > 5:
        displayed_prompt = '\n'.join(prompt_lines[:5]) + f"\n... (省略: 残り{len(prompt_lines)-5}行)"
    else:
        displayed_prompt = prompt
    
    logger.debug(f"🔤 [PROMPT] 内容:\n{displayed_prompt}")
```

#### **2. プロンプトロギングの実装例**
```python
import tiktoken

def log_llm_request(prompt: str, model: str = "gpt-3.5-turbo"):
    """LLMリクエストのプロンプトをログに記録"""
    try:
        # 正確なトークン数計算
        encoding = tiktoken.encoding_for_model(model)
        token_count = len(encoding.encode(prompt))
        
        # モデル別の最大トークン数
        max_tokens_map = {
            "gpt-3.5-turbo": 4096,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000
        }
        max_tokens = max_tokens_map.get(model, 4000)
        
        # トークン使用率
        usage_ratio = token_count / max_tokens
        
        # ログ出力
        logger.info(f"🤖 [LLM] {model} - トークン数: {token_count}/{max_tokens} ({usage_ratio:.1%})")
        
        # 警告レベル判定
        if usage_ratio > 1.0:
            logger.error(f"❌ [LLM] トークン数超過: {usage_ratio:.1%}")
        elif usage_ratio > 0.8:
            logger.warning(f"⚠️ [LLM] トークン数警告: {usage_ratio:.1%}")
        
        # プロンプト内容（5行で省略）
        prompt_lines = prompt.split('\n')
        if len(prompt_lines) > 5:
            short_prompt = '\n'.join(prompt_lines[:5]) + f"\n... (省略: 残り{len(prompt_lines)-5}行)"
        else:
            short_prompt = prompt
            
        logger.debug(f"🤖 [LLM] プロンプト:\n{short_prompt}")
        
    except Exception as e:
        logger.error(f"❌ [LLM] トークン数計算エラー: {e}")
        # フォールバック: 簡易計算
        estimated_tokens = len(prompt) // 4
        logger.info(f"🤖 [LLM] 簡易トークン数: {estimated_tokens}")
```

#### **3. プロンプトロギングの使用例**
```python
# 使用例
prompt = """
あなたは料理の専門家です。
以下の在庫食材から献立を提案してください。

在庫食材:
- 鶏もも肉 300g
- 玉ねぎ 2個
- にんじん 1本
- じゃがいも 3個
- 米 2kg

献立の条件:
1. 主菜・副菜・汁物の3品構成
2. 在庫食材のみを使用
3. 食材の重複を避ける
4. 実用的で美味しいレシピ

JSON形式で回答してください。
"""

# プロンプトログ出力
log_llm_request(prompt, "gpt-3.5-turbo")
```

### **プロンプトロギングの出力例**
```
2025-01-29 10:30:15 - morizo_ai.recipe_mcp - INFO - 🤖 [LLM] gpt-3.5-turbo - 総トークン数: 245/4096 (6.0%)
2025-01-29 10:30:15 - morizo_ai.recipe_mcp - DEBUG - 🤖 [LLM] プロンプト:
あなたは料理の専門家です。
以下の在庫食材から献立を提案してください。

在庫食材:
- 鶏もも肉 300g
... (省略: 残り8行)
```

## 📊 ログレベル戦略

### **本番環境**
- **ERROR**: システムエラー、例外発生
- **WARNING**: 注意が必要な状況
- **INFO**: 重要な処理の開始・完了

### **開発環境**
- **ERROR**: システムエラー、例外発生
- **WARNING**: 注意が必要な状況
- **INFO**: 重要な処理の開始・完了
- **DEBUG**: 詳細なデバッグ情報

### **ログレベル設定**
```python
# 本番環境
if os.getenv('ENVIRONMENT') == 'production':
    logging.getLogger('morizo_ai').setLevel(logging.INFO)
else:
    # 開発環境
    logging.getLogger('morizo_ai').setLevel(logging.DEBUG)
```

## 🔍 ログ分析と監視

### **重要なログパターン**
1. **エラーパターン**: `ERROR`レベルのログ
2. **パフォーマンスパターン**: 処理時間が長いログ
3. **セキュリティパターン**: 認証失敗、不正アクセス
4. **ビジネスパターン**: 重要な操作の完了

### **ログ監視**
```python
def monitor_logs():
    """ログの監視とアラート"""
    # エラーログの監視
    error_count = count_error_logs()
    if error_count > 10:
        send_alert("High error rate detected")
    
    # パフォーマンスの監視
    slow_operations = find_slow_operations()
    if slow_operations:
        send_alert("Slow operations detected")
```

## 🚀 実装戦略

### **Phase 1: 基本ロギング**
1. **ログ設定**: 基本的なログ設定
2. **ファイル出力**: ログファイルへの出力
3. **コンソール出力**: 開発時のコンソール出力

### **Phase 2: 階層別ロギング**
1. **API層ログ**: リクエスト・レスポンスログ
2. **サービス層ログ**: ビジネスロジックログ
3. **MCP層ログ**: ツール呼び出しログ

### **Phase 3: 高度な機能**
1. **パフォーマンスログ**: 処理時間の測定
2. **メモリログ**: メモリ使用量の記録
3. **ログ分析**: ログパターンの分析

## 📊 成功基準

### **機能面**
- [ ] 基本的なログ出力が動作
- [ ] 階層別ログが動作
- [ ] ログローテーションが動作
- [ ] パフォーマンスログが動作
- [ ] エラーログが動作

### **技術面**
- [ ] ログレベルが適切に設定
- [ ] ログフォーマットが統一
- [ ] ログファイルが適切に管理
- [ ] メモリ使用量が最適化
- [ ] パフォーマンスが良好

### **品質面**
- [ ] デバッグの容易性
- [ ] 監視の実現
- [ ] 運用支援
- [ ] セキュリティ監査
- [ ] 障害調査

## 🔧 設定例

### **環境変数**
```bash
# ログレベル設定
LOG_LEVEL=INFO

# ログファイル設定
LOG_FILE=morizo_ai.log
LOG_MAX_SIZE=10MB
LOG_BACKUP_COUNT=5

# 環境設定
ENVIRONMENT=development
```

### **設定ファイル**
```python
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'morizo_ai.log',
            'level': 'INFO',
            'formatter': 'standard',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'morizo_ai': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

**このドキュメントは、Morizo AI v2のロギング戦略を定義します。**
**すべてのログ出力は、この戦略に基づいて実装されます。**
