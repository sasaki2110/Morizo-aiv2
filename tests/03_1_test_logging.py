"""
Morizo AI v2 - Logging Tests

Test script for logging configuration and hierarchical loggers.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging import setup_logging
from config.loggers import GenericLogger


def test_basic_logging():
    """Test basic logging configuration"""
    print("🧪 Testing basic logging configuration...")
    
    # Setup logging
    logger = setup_logging()
    
    # Test different log levels
    logger.debug("🔍 [TEST] Debug message")
    logger.info("ℹ️ [TEST] Info message")
    logger.warning("⚠️ [TEST] Warning message")
    logger.error("❌ [TEST] Error message")
    
    print("✅ Basic logging test completed")


def test_hierarchical_loggers():
    """Test hierarchical loggers"""
    print("🧪 Testing hierarchical loggers...")
    
    # Test API logger
    api_logger = GenericLogger("api")
    api_logger.info("🔍 [API] GET /api/health")
    api_logger.info("✅ [API] GET /api/health Status: 200 Time: 0.123s")
    api_logger.info("🔐 [API] Authentication successful for user: user123")
    
    # Test Service logger
    service_logger = GenericLogger("service", "recipe")
    service_logger.info("🚀 [SERVICE] generate_recipe started with {'ingredients': ['chicken', 'rice']}")
    service_logger.info("✅ [SERVICE] generate_recipe completed")
    service_logger.info("🔍 [SERVICE] Data validation: ✅ Valid")
    
    # Test MCP logger
    mcp_logger = GenericLogger("mcp", "recipe_mcp")
    mcp_logger.info("🔧 [MCP] search_recipe called with {'query': 'chicken rice'}")
    mcp_logger.info("✅ [MCP] search_recipe completed")
    mcp_logger.info("🌐 [MCP] External API call: cookpad")
    mcp_logger.info("🗄️ [MCP] Database SELECT on recipes: 5 records")
    
    # Test Core logger (performance functions)
    core_logger = GenericLogger("core", "performance")
    core_logger.info("⏱️ [CORE] test_operation completed in 1.234s")
    core_logger.info("💾 [CORE] test_operation - Memory usage: 45.6MB")
    core_logger.info("🤖 [CORE] gpt-3.5-turbo tokens: 150/4096 (3.7%)")
    
    print("✅ Hierarchical loggers test completed")


def test_log_file_creation():
    """Test log file creation and rotation"""
    print("🧪 Testing log file creation...")
    
    # Check if log files exist
    log_files = ["morizo_ai.log", "morizo_ai.log.1"]
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"✅ Log file exists: {log_file}")
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 {log_file} contains {len(content)} characters")
        else:
            print(f"❌ Log file not found: {log_file}")
    
    print("✅ Log file creation test completed")


if __name__ == "__main__":
    print("🚀 Starting Morizo AI v2 Logging Tests")
    print("=" * 50)
    
    try:
        test_basic_logging()
        print()
        test_hierarchical_loggers()
        print()
        test_log_file_creation()
        
        print("=" * 50)
        print("🎉 All logging tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)
