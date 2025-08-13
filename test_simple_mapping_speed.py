#!/usr/bin/env python3
"""
Quick test of simple mapping engine speed and accuracy
"""

import time
from simple_mapping_engine import create_simple_mapping_engine
from logging_config import logger

def test_simple_mapping_speed():
    """Test simple mapping for speed and basic functionality."""
    
    print("🚀 SIMPLE MAPPING SPEED TEST")
    print("=" * 50)
    
    # Create simple engine
    simple_engine = create_simple_mapping_engine()
    
    # Sample variables for testing
    test_variables = [
        {
            'name': 'insert URL',
            'text': '[insert URL]',
            'context_before': 'provider directory available at',
            'context_after': 'for more information'
        },
        {
            'name': 'insert 2025 plan name', 
            'text': '[insert 2025 plan name]',
            'context_before': 'Welcome to',
            'context_after': 'for the year 2025'
        },
        {
            'name': 'insert phone number',
            'text': '[insert phone number]', 
            'context_before': 'Call us at',
            'context_after': 'for assistance'
        },
        {
            'name': 'insert day of the month',
            'text': '[insert day of the month]',
            'context_before': 'bills are due on the',
            'context_after': 'of each month'
        },
        {
            'name': 'plans with a premium insert: premium',
            'text': '[plans with a premium insert: premium]',
            'context_before': 'For plans that have costs',
            'context_after': 'will be charged monthly'
        }
    ]
    
    # Sample source paragraphs
    source_paragraphs = [
        "Visit our website at https://www.bcbsm.com/providersmedicare for provider information.",
        "This Evidence of Coverage is for Medicare Plus Blue Group PPO for 2025.",
        "Call Member Services at 1-800-662-2667 for questions.",
        "Premium bills are typically due on the 15th of each month.",
        "Plans with monthly premiums will have premium costs listed separately."
    ]
    
    print(f"📊 Testing {len(test_variables)} variables with simple extraction...")
    print("🎯 Expected: Fast processing (< 1 second per variable)")
    print()
    
    # Time the extraction
    start_time = time.time()
    results = []
    
    for var in test_variables:
        var_start = time.time()
        
        extracted_value, confidence, reasoning, metadata = simple_engine.extract_variable_simple(
            var['name'], var['text'], var['context_before'], var['context_after'], source_paragraphs
        )
        
        var_time = time.time() - var_start
        
        result = {
            'variable': var['name'],
            'extracted_value': extracted_value,
            'confidence': confidence,
            'time_ms': var_time * 1000,
            'enhanced_type': metadata['enhanced_type'],
            'requires_ai_review': metadata['requires_ai_review']
        }
        results.append(result)
        
        print(f"  ⚡ {var['name'][:30]:<30} → {extracted_value[:20]:<20} ({confidence:.2f}, {var_time*1000:.0f}ms)")
    
    total_time = time.time() - start_time
    avg_time = total_time / len(test_variables)
    
    print()
    print("📊 SIMPLE MAPPING RESULTS:")
    print(f"   🔧 Total variables: {len(test_variables)}")
    print(f"   ⚡ Total time: {total_time:.2f} seconds")
    print(f"   🚀 Average per variable: {avg_time*1000:.0f}ms")
    print(f"   🧙‍♂️ All require AI wizard review: {all(r['requires_ai_review'] for r in results)}")
    print()
    
    print("🎯 SPEED COMPARISON:")
    old_ai_time = len(test_variables) * 6  # Estimated 6 seconds per AI call
    print(f"   ❌ Old enhanced mapping (with AI): ~{old_ai_time} seconds")
    print(f"   ✅ New simple mapping (no AI): {total_time:.2f} seconds")
    print(f"   🚀 Speed improvement: {old_ai_time/total_time:.1f}x faster!")
    print()
    
    print("✨ EFFICIENCY BENEFITS:")
    print("   ⚡ NO AI calls during initial mapping")
    print("   🛡️ NO timeout protection needed")
    print("   🧵 NO threading issues")
    print("   🧙‍♂️ ALL intelligence moved to AI Clarification Wizard")
    print()
    
    return results

if __name__ == "__main__":
    test_simple_mapping_speed()