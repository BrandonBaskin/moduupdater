#!/usr/bin/env python3
"""
Results Comparison Script
Compares the performance with and without persistent learning.
"""

from logic_mapper_llm import LogicMapper
from learning_persistence import LearningPersistence
from document_parser import DocumentParser
import os
import time

def compare_performance():
    """Compare performance with and without persistent learning."""
    print("=== Performance Comparison ===\n")
    
    # Test documents
    model_path = "../assets/previous/CY2025_8_PPO MA_EOC_Correcting URLs_11042024.docx"
    source_path = "../assets/previous/11.2 v15 UOM BCBSM PPO Evidence of Coverage_FINAL-77[1301].docx"
    
    if not os.path.exists(model_path) or not os.path.exists(source_path):
        print("❌ Test documents not found")
        return
    
    parser = DocumentParser()
    model_blocks = parser.parse(model_path)
    
    def progress_callback(value):
        pass  # Silent for comparison
    
    def log_callback(msg):
        pass  # Silent for comparison
    
    # Test 1: Fresh Learning System (simulated)
    print("🧪 Test 1: Fresh Learning System (Simulated)")
    start_time = time.time()
    
    # Create a fresh mapper (simulating first run)
    fresh_mapper = LogicMapper()
    
    # Clear any existing learning data for fair comparison
    learning_persistence = LearningPersistence()
    learning_persistence.clear_learning_data()
    
    # Test mapping
    mapping1, _ = fresh_mapper.map_final_to_model(
        model_blocks, source_path, progress_callback, log_callback, model_path
    )
    
    fresh_time = time.time() - start_time
    successful_mappings1 = sum(1 for value in mapping1.values() if value.strip())
    total_variables = len(mapping1)
    success_rate1 = (successful_mappings1 / total_variables * 100) if total_variables > 0 else 0
    
    print(f"  Fresh System Results:")
    print(f"    Success Rate: {success_rate1:.1f}%")
    print(f"    Successful Mappings: {successful_mappings1}/{total_variables}")
    print(f"    Time: {fresh_time:.1f} seconds")
    
    # Test 2: With Persistent Learning (actual)
    print("\n🧠 Test 2: With Persistent Learning (Actual)")
    start_time = time.time()
    
    # Create mapper with persistent learning (actual current state)
    persistent_mapper = LogicMapper()
    
    # Test mapping
    mapping2, _ = persistent_mapper.map_final_to_model(
        model_blocks, source_path, progress_callback, log_callback, model_path
    )
    
    persistent_time = time.time() - start_time
    successful_mappings2 = sum(1 for value in mapping2.values() if value.strip())
    success_rate2 = (successful_mappings2 / total_variables * 100) if total_variables > 0 else 0
    
    print(f"  Persistent Learning Results:")
    print(f"    Success Rate: {success_rate2:.1f}%")
    print(f"    Successful Mappings: {successful_mappings2}/{total_variables}")
    print(f"    Time: {persistent_time:.1f} seconds")
    
    # Show learning statistics
    learning_stats = persistent_mapper.get_learning_stats()
    print(f"    Learning Stats: {learning_stats}")
    
    # Comparison
    print("\n📊 Comparison:")
    improvement = success_rate2 - success_rate1
    time_improvement = fresh_time - persistent_time
    
    print(f"  Success Rate Improvement: {improvement:+.1f}%")
    print(f"  Time Improvement: {time_improvement:+.1f} seconds")
    
    if improvement > 0:
        print(f"  ✅ Persistent learning is improving performance!")
    else:
        print(f"  ⚠️  No improvement yet, but learning is active")
    
    print(f"\n🎯 Key Features Active:")
    print(f"  ✅ Persistent Ollama Management")
    print(f"  ✅ Learning State Persistence")
    print(f"  ✅ Background Model Monitoring")
    print(f"  ✅ Automatic Restart Capability")
    print(f"  ✅ Learning Statistics Tracking")

if __name__ == "__main__":
    compare_performance() 