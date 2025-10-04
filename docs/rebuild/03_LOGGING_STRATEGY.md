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

### **2. 汎用ロガー設計**

#### **設計原則**
- **単一責任原則**: ロガーの責任はログ出力のみ
- **責任分離**: レイヤー別の整形は各レイヤーの責任
- **拡張性**: 機能追加時にロガー修正が不要
- **シンプル性**: 最小限のAPIで最大の効果

#### **汎用ロガー**
```python
class GenericLogger:
    """Simple generic logger for all application layers"""
    
    def __init__(self, layer: str, component: str = ""):
        self.layer = layer
        self.component = component
        self.logger = get_logger(f'{layer}.{component}' if component else layer)
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(message)
```

#### **使用例**
```python
# API層での使用
api_logger = GenericLogger("api")
api_logger.info("🔍 [API] GET /api/health")
api_logger.info("✅ [API] GET /api/health Status: 200 Time: 0.123s")

# サービス層での使用
service_logger = GenericLogger("service", "recipe")
service_logger.info("🚀 [SERVICE] generate_recipe started")
service_logger.info("✅ [SERVICE] generate_recipe completed")

# MCP層での使用
mcp_logger = GenericLogger("mcp", "recipe_mcp")
mcp_logger.info("🔧 [MCP] search_recipe called")
mcp_logger.info("✅ [MCP] search_recipe completed")

# コア層での使用
core_logger = GenericLogger("core", "performance")
core_logger.info("⏱️ [CORE] operation completed in 1.234s")
```

### **3. MCPプロセス別ロギング**

#### **設計原則**
- **別プロセス実行**: 各MCPは独立したプロセスで動作
- **汎用ロガー使用**: 各MCPプロセスでGenericLoggerを使用
- **出力先統一**: すべてのMCPログを`morizo_ai.log`に統一
- **プロセス識別**: プロセスIDを含めたログ出力

#### **実装例**
```python
# 各MCPプロセス内での汎用ロガー使用
from config.loggers import GenericLogger

# MCPプロセス内でのロガー設定
mcp_logger = GenericLogger("mcp", "recipe_mcp")
mcp_logger.info("🔧 [MCP] MCPプロセス開始")
mcp_logger.info(f"🆔 [MCP] プロセスID: {os.getpid()}")

# ツール呼び出しログ
mcp_logger.info("🔧 [MCP] search_recipe called")
mcp_logger.info("✅ [MCP] search_recipe completed")
```

### **4. パフォーマンスログ**

#### **デコレータによる実行時間測定**
```python
from config.loggers import log_execution_time, log_execution_time_async

# 同期関数用
@log_execution_time
def sync_function():
    # 処理内容
    pass

# 非同期関数用
@log_execution_time_async
async def async_function():
    # 処理内容
    pass
```

#### **手動でのパフォーマンスログ**
```python
from config.loggers import GenericLogger
import time

core_logger = GenericLogger("core", "performance")

# 実行時間ログ
start_time = time.time()
# 処理実行
duration = time.time() - start_time
core_logger.info(f"⏱️ [CORE] operation completed in {duration:.3f}s")

# メモリ使用量ログ
core_logger.info("💾 [CORE] Memory usage: 45.6MB")

# トークン使用量ログ
core_logger.info("🤖 [CORE] gpt-3.5-turbo tokens: 150/4096 (3.7%)")
```

## 🔤 プロンプトロギング戦略

### **プロンプトロギングの実装**

#### **汎用ロガーを使用したプロンプトログ**
```python
from config.loggers import GenericLogger

core_logger = GenericLogger("core", "llm")

# トークン数情報の記録
def log_prompt_with_tokens(prompt: str, max_tokens: int = 4000):
    """プロンプトとトークン数情報をログに記録"""
    estimated_tokens = len(prompt) // 4
    token_usage_ratio = estimated_tokens / max_tokens
    
    core_logger.info(f"🔤 [CORE] 予想トークン数: {estimated_tokens}/{max_tokens} ({token_usage_ratio:.1%})")
    
    # トークン数超過警告
    if token_usage_ratio > 0.8:
        core_logger.warning(f"⚠️ [CORE] トークン数が80%を超過: {token_usage_ratio:.1%}")
    elif token_usage_ratio > 1.0:
        core_logger.error(f"❌ [CORE] トークン数が上限を超過: {token_usage_ratio:.1%}")
    
    # プロンプト内容（5行で省略）
    prompt_lines = prompt.split('\n')
    if len(prompt_lines) > 5:
        displayed_prompt = '\n'.join(prompt_lines[:5]) + f"\n... (省略: 残り{len(prompt_lines)-5}行)"
    else:
        displayed_prompt = prompt
    
    core_logger.debug(f"🔤 [CORE] プロンプト内容:\n{displayed_prompt}")
```

#### **使用例**
```python
# LLMリクエストのプロンプトログ
prompt = "あなたは料理の専門家です。以下の在庫食材から献立を提案してください。"
log_prompt_with_tokens(prompt, 4096)
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

### **Phase 1: 基本ロギング** ✅
1. **ログ設定**: 基本的なログ設定
2. **ファイル出力**: ログファイルへの出力
3. **コンソール出力**: 開発時のコンソール出力

### **Phase 2: 汎用ロガー** ✅
1. **GenericLogger**: シンプルな汎用ロガーの実装
2. **レイヤー別使用**: API層・サービス層・MCP層・コア層での使用
3. **責任分離**: ログ整形は各レイヤーの責任

### **Phase 3: 高度な機能** ✅
1. **パフォーマンスログ**: デコレータによる実行時間測定
2. **プロンプトログ**: トークン数監視とプロンプト内容記録
3. **MCPプロセス対応**: 独立プロセスでのログ出力

## 📊 成功基準

### **機能面**
- [x] 基本的なログ出力が動作
- [x] 階層別ログが動作
- [x] ログローテーションが動作
- [x] パフォーマンスログが動作
- [x] エラーログが動作

### **技術面**
- [x] ログレベルが適切に設定
- [x] ログフォーマットが統一
- [x] ログファイルが適切に管理
- [x] メモリ使用量が最適化
- [x] パフォーマンスが良好

### **品質面**
- [x] デバッグの容易性
- [x] 監視の実現
- [x] 運用支援
- [x] セキュリティ監査
- [x] 障害調査

## 🎉 実装完了

**完了日**: 2025年1月29日  
**実装ファイル**: 
- `config/logging.py` (148行) - 基本ロギング設定
- `config/loggers.py` (91行) - 汎用ロガー
- `tests/03_1_test_logging.py` (97行) - テストスクリプト

**テスト結果**: ✅ 全てのテストが正常に動作

### **最終的な設計**
- **単一責任原則**: ロガーの責任はログ出力のみ
- **責任分離**: レイヤー別の整形は各レイヤーの責任
- **拡張性**: 機能追加時にロガー修正が不要
- **シンプル性**: 最小限のAPIで最大の効果

### **使用例**
```python
# 各レイヤーで直接GenericLoggerを使用
api_logger = GenericLogger("api")
service_logger = GenericLogger("service", "recipe")
mcp_logger = GenericLogger("mcp", "recipe_mcp")
core_logger = GenericLogger("core", "performance")

# 各レイヤーが自分でメッセージを整形
api_logger.info("🔍 [API] GET /api/health")
service_logger.info("🚀 [SERVICE] generate_recipe started")
mcp_logger.info("🔧 [MCP] search_recipe called")
core_logger.info("⏱️ [CORE] operation completed in 1.234s")
```

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
