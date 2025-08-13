#!/usr/bin/env python3
"""
Test script to verify the fixes for the CMS Model Updater
"""

import sys
import os
import logging
from logging_config import logger

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_logging():
    """Test that logging works without Unicode errors."""
    try:
        logger.info("🚀 Testing Unicode logging...")
        logger.info("✅ Unicode logging works!")
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_ollama_connection():
    """Test Ollama connection and model availability."""
    try:
        from ollama_manager import get_ollama_manager
        
        manager = get_ollama_manager()
        
        # Test if Ollama is running
        if manager.check_ollama_running():
            logger.info("✅ Ollama is running")
        else:
            logger.warning("⚠️ Ollama is not running, attempting to start...")
            if manager.start_persistent():
                logger.info("✅ Ollama started successfully")
            else:
                logger.error("❌ Failed to start Ollama")
                return False
        
        # Test model availability
        if manager.ensure_model_available():
            logger.info("✅ Model is available")
            return True
        else:
            logger.error("❌ Model is not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ollama test failed: {e}")
        return False

def test_logic_mapper():
    """Test the logic mapper initialization."""
    try:
        from logic_mapper_llm import LogicMapper
        
        mapper = LogicMapper()
        logger.info("✅ Logic mapper initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Logic mapper test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🧪 Starting CMS Model Updater tests...")
    
    tests = [
        ("Logging", test_logging),
        ("Ollama Connection", test_ollama_connection),
        ("Logic Mapper", test_logic_mapper),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} test passed")
            else:
                logger.error(f"❌ {test_name} test failed")
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n📊 Test Results:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The fixes are working.")
        return 0
    else:
        logger.error("⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 