#!/usr/bin/env python3
"""
Debug Pattern Matching Order
Debug why IF_APPLICABLE_INSTRUCTIONAL_INSERT is matching instead of IF_APPLICABLE
"""

import re
from enhanced_variable_classifier import create_enhanced_classifier, VariableType

def debug_pattern_matching():
    """Debug the specific pattern matching issue."""
    
    print("🔍 PATTERN MATCHING DEBUG")
    print("=" * 50)
    
    test_variable = "[insert if applicable: or territory]"
    print(f"🧪 Testing: {test_variable}")
    print()
    
    # Test patterns directly
    patterns_to_test = [
        (VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT, r"^\[if\s+([^,]+),\s*insert:\s*([^]]+)\]$"),
        (VariableType.IF_APPLICABLE, r"^\[insert\s+if\s+applicable:\s*([^]]+)\]$"),
        (VariableType.IF_APPLICABLE, r"^\[Insert\s+if\s+applicable:\s*([^]]+)\]$"),
        (VariableType.IF_APPLICABLE, r"^\[[^]]*if\s+applicable[^]]*\]$"),
    ]
    
    print("📋 DIRECT PATTERN TESTING:")
    for var_type, pattern in patterns_to_test:
        print(f"   {var_type.value}:")
        print(f"      Pattern: {pattern}")
        
        match = re.match(pattern, test_variable, re.IGNORECASE | re.DOTALL)
        if match:
            print(f"      ✅ MATCHES! Groups: {match.groups()}")
        else:
            print(f"      ❌ No match")
        print()
    
    # Test with classifier
    print("🧠 CLASSIFIER TESTING:")
    classifier = create_enhanced_classifier()
    
    # Get all IF_APPLICABLE patterns from classifier
    if_applicable_patterns = classifier.pattern_matchers.get(VariableType.IF_APPLICABLE, [])
    if_instructional_patterns = classifier.pattern_matchers.get(VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT, [])
    
    print("📌 IF_APPLICABLE patterns:")
    for i, pattern_info in enumerate(if_applicable_patterns):
        pattern = pattern_info["pattern"]
        print(f"   {i+1}. {pattern}")
        match = re.match(pattern, test_variable, re.IGNORECASE | re.DOTALL)
        print(f"      Match: {'✅ YES' if match else '❌ NO'}")
        if match and match.groups():
            print(f"      Groups: {match.groups()}")
    
    print()
    print("📌 IF_APPLICABLE_INSTRUCTIONAL_INSERT patterns:")
    for i, pattern_info in enumerate(if_instructional_patterns):
        pattern = pattern_info["pattern"]
        print(f"   {i+1}. {pattern}")
        match = re.match(pattern, test_variable, re.IGNORECASE | re.DOTALL)
        print(f"      Match: {'✅ YES' if match else '❌ NO'}")
        if match and match.groups():
            print(f"      Groups: {match.groups()}")
    
    print()
    
    # Full classification
    result = classifier.classify_variable(test_variable)
    print("🎯 FINAL CLASSIFICATION:")
    print(f"   Type: {result.variable_type.value}")
    print(f"   Insert Text: '{result.insert_text}'")
    print(f"   Confidence: {result.confidence_score}")

if __name__ == "__main__":
    debug_pattern_matching()