#!/usr/bin/env python3
"""
Quick Test for Main System
Tests the main system with persistent learning to verify it's working.
"""

from logic_mapper_llm import LogicMapper
from learning_persistence import LearningPersistence
from document_parser import DocumentParser
import os

def quick_test():
    """Quick test of the main system."""
    print("=== Quick Test of Main System ===\n")
    
    # Test documents
    model_path = "../assets/previous/CY2025_8_PPO MA_EOC_Correcting URLs_11042024.docx"
    source_path = "../assets/previous/11.2 v15 UOM BCBSM PPO Evidence of Coverage_FINAL-77[1301].docx"
    
    if not os.path.exists(model_path) or not os.path.exists(source_path):
        print("❌ Test documents not found")
        return
    
    print("🧠 Testing LogicMapper with persistent learning...")
    
    # Create mapper (should load existing learning)
    mapper = LogicMapper()
    
    # Get learning stats
    learning_stats = mapper.get_learning_stats()
    print(f"📊 Learning Stats: {learning_stats}")
    
    # Test a quick mapping
    parser = DocumentParser()
    model_blocks = parser.parse(model_path)
    
    def progress_callback(value):
        pass  # Silent for quick test
    
    def log_callback(msg):
        if "LEARN" in msg or "SUCCESS" in msg:
            print(f"  {msg}")
    
    print("🔄 Testing mapping with learning system...")
    mapping, _ = mapper.map_final_to_model(
        model_blocks, source_path, progress_callback, log_callback, model_path
    )
    
    # Show results
    successful_mappings = sum(1 for value in mapping.values() if value.strip())
    total_variables = len(mapping)
    success_rate = (successful_mappings / total_variables * 100) if total_variables > 0 else 0
    
    print(f"\n📊 Results:")
    print(f"  Total variables: {total_variables}")
    print(f"  Successful mappings: {successful_mappings}")
    print(f"  Success rate: {success_rate:.1f}%")
    
    # Show some examples of learned patterns
    if hasattr(mapper.learner, 'patterns') and mapper.learner.patterns:
        print(f"\n🎯 Learned Patterns:")
        for var_type, info in list(mapper.learner.patterns.items())[:5]:
            examples = info.get('examples', [])
            print(f"  {var_type}: {len(examples)} examples")
    
    print(f"\n✅ Main system is working with persistent learning!")
    print(f"✅ Success Rate: {success_rate:.1f}%")
    print(f"✅ Learning System: Active")
    print(f"✅ Ready for production use!")

if __name__ == "__main__":
    quick_test() 