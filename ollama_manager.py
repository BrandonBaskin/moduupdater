#!/usr/bin/env python3
"""
Persistent Ollama Manager
Manages Ollama in the background with automatic restart capabilities.
"""

import subprocess
import threading
import time
import requests
import os
import signal
import sys
from typing import Optional, Callable
from logging_config import logger

class OllamaManager:
    """Manages Ollama server with persistent background operation."""
    
    def __init__(self, model_name: str = "llama3:latest"):
        self.model_name = model_name
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        self.status_callback: Optional[Callable] = None
        
    def start_persistent(self, status_callback: Optional[Callable] = None) -> bool:
        """Start Ollama in persistent mode with background monitoring."""
        self.status_callback = status_callback
        
        try:
            # Check if Ollama is already running
            if self.check_ollama_running():
                logger.info("Ollama is already running")
                self.is_running = True
                self._notify_status("Ollama already running")
                return True
            
            # Start Ollama server
            logger.info("Starting Ollama server...")
            self.process = subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait a moment for it to start
            time.sleep(3)
            
            if self.check_ollama_running():
                logger.info("Ollama started successfully")
                self.is_running = True
                self._notify_status("Ollama started successfully")
                
                # Start monitoring thread
                self._start_monitor()
                return True
            else:
                logger.error("Failed to start Ollama")
                self._notify_status("Failed to start Ollama")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Ollama: {e}")
            self._notify_status(f"Error starting Ollama: {e}")
            return False
    
    def _start_monitor(self):
        """Start the background monitoring thread."""
        self.monitor_thread = threading.Thread(target=self._monitor_ollama, daemon=True)
        self.monitor_thread.start()
        logger.info("Ollama monitor thread started")
    
    def _monitor_ollama(self):
        """Monitor Ollama and restart if it goes down."""
        while not self.shutdown_event.is_set():
            try:
                if not self.check_ollama_running():
                    logger.warning("Ollama stopped running, attempting restart...")
                    self._notify_status("Ollama stopped, restarting...")
                    
                    # Kill existing process if any
                    if self.process:
                        try:
                            self.process.terminate()
                            self.process.wait(timeout=5)
                        except:
                            self.process.kill()
                    
                    # Restart Ollama
                    self.process = subprocess.Popen(
                        ['ollama', 'serve'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    time.sleep(5)  # Wait for restart
                    
                    if self.check_ollama_running():
                        logger.info("Ollama restarted successfully")
                        self._notify_status("Ollama restarted successfully")
                    else:
                        logger.error("Failed to restart Ollama")
                        self._notify_status("Failed to restart Ollama")
                
                # Check every 30 seconds
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in Ollama monitor: {e}")
                time.sleep(30)
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama is running by trying to connect to the API."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def ensure_model_available(self) -> bool:
        """Ensure the required model is available, pulling it if necessary."""
        try:
            # Check if Ollama is running
            if not self.check_ollama_running():
                logger.info("Ollama not running, attempting to start...")
                if not self.start_persistent():
                    logger.error("Failed to start Ollama")
                    return False
            
            # Check if model is available with better error handling
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=10)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [model['name'] for model in models]
                    
                    if self.model_name in model_names:
                        logger.info(f"Model {self.model_name} is already available")
                        return True
                    else:
                        logger.info(f"Model {self.model_name} not found in available models: {model_names}")
                else:
                    logger.warning(f"Ollama API returned status {response.status_code}")
            except requests.exceptions.Timeout:
                logger.error("Timeout checking Ollama models")
                return False
            except requests.exceptions.ConnectionError:
                logger.error("Could not connect to Ollama API")
                return False
            except Exception as e:
                logger.error(f"Error checking model availability: {e}")
                return False
            
            # Model not found, pull it
            logger.info(f"Model {self.model_name} not found, pulling...")
            try:
                pull_response = requests.post(
                    "http://localhost:11434/api/pull",
                    json={"name": self.model_name},
                    timeout=300  # 5 minute timeout for model pulling
                )
                
                if pull_response.status_code == 200:
                    logger.info(f"Model {self.model_name} pulled successfully")
                    return True
                else:
                    logger.error(f"Failed to pull model {self.model_name}: {pull_response.status_code}")
                    return False
            except requests.exceptions.Timeout:
                logger.error(f"Timeout pulling model {self.model_name}")
                return False
            except Exception as e:
                logger.error(f"Error pulling model {self.model_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring model availability: {e}")
            return False
    
    def _notify_status(self, message: str):
        """Notify status callback if provided."""
        if self.status_callback:
            try:
                self.status_callback(message)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def stop(self):
        """Stop Ollama and cleanup."""
        logger.info("Stopping Ollama manager...")
        self.shutdown_event.set()
        
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.is_running = False
        logger.info("Ollama manager stopped")

# Global Ollama manager instance
_ollama_manager: Optional[OllamaManager] = None

def get_ollama_manager() -> OllamaManager:
    """Get the global Ollama manager instance."""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager()
    return _ollama_manager

def start_ollama_persistent(status_callback: Optional[Callable] = None) -> bool:
    """Start Ollama in persistent mode."""
    manager = get_ollama_manager()
    return manager.start_persistent(status_callback)

def stop_ollama_persistent():
    """Stop the persistent Ollama manager."""
    global _ollama_manager
    if _ollama_manager:
        _ollama_manager.stop()
        _ollama_manager = None 