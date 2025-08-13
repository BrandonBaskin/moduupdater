#!/usr/bin/env python3
"""
CMS Model Updater - Main Entry Point
Launches the application with persistent learning and Ollama management.
"""

import sys
import os
import logging
from logging_config import logger

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the CMS Model Updater application."""
    try:
        logger.info("🚀 Starting CMS Model Updater with Learning System...")
        
        # Import here to ensure all dependencies are available
        from dashboard import DashboardUI
        from ollama_manager import start_ollama_persistent
        from learning_persistence import LearningPersistence
        
        # Initialize persistent Ollama management
        def ollama_status_callback(message):
            logger.info(f"Ollama Status: {message}")
        
        logger.info("🔧 Starting persistent Ollama management...")
        ollama_success = start_ollama_persistent(ollama_status_callback)
        
        if ollama_success:
            logger.info("✅ Ollama management started successfully")
        else:
            logger.warning("⚠️ Ollama management failed to start, but continuing...")
        
        # Initialize learning persistence
        learning_persistence = LearningPersistence()
        logger.info("🧠 Learning persistence system initialized")
        
        # Initialize the application
        logger.info("🎯 Launching CMS Model Updater GUI...")
        app = DashboardUI()
        
        # Start the GUI
        logger.info("🎉 CMS Model Updater is ready!")
        app.mainloop()
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        print(f"❌ Import error: {e}")
        print("Please ensure all required packages are installed.")
        return 1
    except Exception as e:
        logger.error(f"❌ Application failed to start: {e}")
        print(f"❌ Application failed to start: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
