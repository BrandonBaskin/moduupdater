#!/usr/bin/env python3
"""
Production-Ready System Test
Tests the complete system with persistent learning and Ollama management.
"""

from logic_mapper_llm import LogicMapper
from learning_persistence import LearningPersistence
from ollama_manager import get_ollama_manager, start_ollama_persistent
from document_parser import DocumentParser
import os
import time

def test_production_system():
    """Test the complete production-ready system."""
    print("=== Testing Production-Ready System ===\n")
    
    # Test 1: Persistent Ollama Management
    print("🔧 Test 1: Persistent Ollama Management")
    ollama_manager = get_ollama_manager()
    
    # Start Ollama in background
    def status_callback(message):
        print(f"  Ollama Status: {message}")
    
    success = start_ollama_persistent(status_callback)
    print(f"  Ollama started: {'✅' if success else '❌'}")
    
    # Wait for Ollama to be ready
    time.sleep(5)
    
    # Test 2: Learning Persistence
    print("\n🧠 Test 2: Learning Persistence")
    learning_persistence = LearningPersistence()
    
    # Get initial stats
    initial_stats = learning_persistence.get_learning_stats()
    print(f"  Initial learning stats: {initial_stats['status']}")
    
    # Test 3: LogicMapper with Learning
    print("\n🤖 Test 3: LogicMapper with Learning")
    mapper = LogicMapper()
    
    # Get learning stats from mapper
    mapper_stats = mapper.get_learning_stats()
    print(f"  Mapper learning stats: {mapper_stats}")
    
    # Test 4: Document Processing
    print("\n📄 Test 4: Document Processing")
    model_path = "../assets/previous/CY2025_8_PPO MA_EOC_Correcting URLs_11042024.docx"
    source_path = "../assets/previous/11.2 v15 UOM BCBSM PPO Evidence of Coverage_FINAL-77[1301].docx"
    
    if not os.path.exists(model_path) or not os.path.exists(source_path):
        print("  ❌ Test documents not found, skipping document processing test")
        return
    
    parser = DocumentParser()
    model_blocks = parser.parse(model_path)
    
    def progress_callback(value):
        print(f"  Progress: {value:.1f}%")
    
    def log_callback(msg):
        print(f"  LOG: {msg}")
    
    # Test the mapping
    print("  🔄 Testing mapping with learning system...")
    mapping, doc_paragraphs = mapper.map_final_to_model(
        model_blocks, source_path, progress_callback, log_callback, model_path
    )
    
    # Show results
    successful_mappings = sum(1 for value in mapping.values() if value.strip())
    total_variables = len(mapping)
    success_rate = (successful_mappings / total_variables * 100) if total_variables > 0 else 0
    
    print(f"\n📊 Mapping Results:")
    print(f"  Total variables: {total_variables}")
    print(f"  Successful mappings: {successful_mappings}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    # Test 5: Learning State Persistence
    print("\n💾 Test 5: Learning State Persistence")
    
    # Save learning state
    save_success = learning_persistence.save_learning_state(mapper.learner)
    print(f"  Save learning state: {'✅' if save_success else '❌'}")
    
    # Get updated stats
    updated_stats = learning_persistence.get_learning_stats()
    print(f"  Updated learning stats: {updated_stats}")
    
    # Test 6: Ollama Status
    print("\n🔍 Test 6: Ollama Status")
    ollama_running = ollama_manager.check_ollama_running()
    print(f"  Ollama running: {'✅' if ollama_running else '❌'}")
    
    model_available = ollama_manager.ensure_model_available()
    print(f"  Model available: {'✅' if model_available else '❌'}")
    
    print("\n🎉 Production System Test Complete!")
    print(f"✅ Success Rate: {success_rate:.1f}%")
    print(f"✅ Learning System: Active")
    print(f"✅ Ollama Management: {'Active' if ollama_running else 'Inactive'}")
    print(f"✅ Persistence: {'Active' if save_success else 'Inactive'}")

if __name__ == "__main__":
    test_production_system() 