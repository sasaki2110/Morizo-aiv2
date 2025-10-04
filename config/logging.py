"""
Morizo AI v2 - Logging Configuration

This module provides centralized logging configuration for the entire application.
Implements hierarchical logging with file rotation and console output.
"""

import logging
import logging.handlers
import os
import shutil
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Centralized logging configuration for Morizo AI v2"""
    
    def __init__(self):
        self.log_file = "morizo_ai.log"
        self.backup_file = "morizo_ai.log.1"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.date_format = '%Y-%m-%d %H:%M:%S'
        
    def setup_logging(self, log_level: str = "INFO") -> logging.Logger:
        """
        Setup centralized logging configuration
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Configured root logger
        """
        # Create root logger
        root_logger = logging.getLogger('morizo_ai')
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers to avoid duplicates
        root_logger.handlers.clear()
        
        # Setup file handler with rotation
        self._setup_file_handler(root_logger)
        
        # Setup console handler for development
        self._setup_console_handler(root_logger)
        
        # Prevent propagation to avoid duplicate logs
        root_logger.propagate = False
        
        root_logger.info("🔧 [LOGGING] ロギング設定が完了しました")
        return root_logger
    
    def _setup_file_handler(self, logger: logging.Logger) -> None:
        """Setup file handler with rotation"""
        try:
            # Create backup if log file exists
            self._create_log_backup()
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            
            # Set formatter
            formatter = logging.Formatter(
                fmt=self.log_format,
                datefmt=self.date_format
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.info(f"📁 [LOGGING] ファイルハンドラー設定完了: {self.log_file}")
            
        except Exception as e:
            logger.error(f"❌ [LOGGING] ファイルハンドラー設定エラー: {e}")
    
    def _setup_console_handler(self, logger: logging.Logger) -> None:
        """Setup console handler for development"""
        try:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Set formatter
            formatter = logging.Formatter(
                fmt=self.log_format,
                datefmt=self.date_format
            )
            console_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
            logger.info("🖥️ [LOGGING] コンソールハンドラー設定完了")
            
        except Exception as e:
            logger.error(f"❌ [LOGGING] コンソールハンドラー設定エラー: {e}")
    
    def _create_log_backup(self) -> None:
        """Create backup of existing log file"""
        if os.path.exists(self.log_file):
            try:
                shutil.move(self.log_file, self.backup_file)
                print(f"📦 [LOGGING] ログファイルをバックアップ: {self.log_file} → {self.backup_file}")
            except Exception as e:
                print(f"⚠️ [LOGGING] バックアップ作成エラー: {e}")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Convenience function to setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured root logger
    """
    config = LoggingConfig()
    return config.setup_logging(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f'morizo_ai.{name}')


# Environment-based log level
def get_log_level() -> str:
    """Get log level from environment variable"""
    return os.getenv('LOG_LEVEL', 'INFO').upper()


if __name__ == "__main__":
    # Quick verification
    print("✅ ロギング設定が利用可能です")
