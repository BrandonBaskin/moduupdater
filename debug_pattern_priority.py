#!/usr/bin/env python3
"""
Debug Pattern Priority and Matching Logic
Focus on fixing the simple vs complex optional information classification
"""

import re
from enhanced_variable_classifier import create_enhanced_classifier

def debug_pattern_priority():
    """Debug why simple optional variables are being misclassified."""
    
    print("🔍 PATTERN PRIORITY DEBUG")
    print("=" * 50)
    
    # Test variables - focus on the problem cases
    test_cases = [
        {
            'name': 'Simple Optional (should be optional_information_compound)',
            'text': '[Optional information: Additional details may be provided]',
            'has_embedded_insert': False
        },
        {
            'name': 'Complex Optional (should be optional_conditional_with_embedded_select)',
            'text': '[Optional information: multi-state plans can include the following: We offer coverage in [insert as applicable: several OR all]]',
            'has_embedded_insert': True
        }
    ]
    
    # Test patterns directly
    patterns = {
        'complex': r"^\[Optional\s+information:\s*([^:\[]+):\s*([^\[]+)\[insert\s+as\s+applicable:\s*([^\]]+)\]([^\]]*)\]$",
        'simple': r"^\[Optional\s+information:\s*([^:\]]+)(?::\s*([^\]]+))?\]$"
    }
    
    print("🧪 DIRECT PATTERN TESTING:")
    print()
    
    for case in test_cases:
        text = case['text']
        print(f"📋 Testing: {case['name']}")
        print(f"   Text: {text}")
        print(f"   Has embedded insert: {case['has_embedded_insert']}")
        print(f"   Actual check: {'[insert as applicable:' in text.lower()}")
        print()
        
        for pattern_name, pattern in patterns.items():
            match = re.match(pattern, text, re.IGNORECASE | re.DOTALL)
            print(f"   Pattern '{pattern_name}': {'✅ MATCHES' if match else '❌ No match'}")
            if match:
                print(f"      Groups: {match.groups()}")
        print()
    
    print("🔧 TESTING CLASSIFIER LOGIC:")
    print()
    
    # Test with the actual classifier
    classifier = create_enhanced_classifier()
    
    for case in test_cases:
        text = case['text']
        print(f"📋 Classifying: {case['name']}")
        print(f"   Text: {text}")
        
        # Test step by step
        normalized_text = text.strip()
        
        # Test if it matches our patterns
        complex_pattern = patterns['complex']
        simple_pattern = patterns['simple']
        
        complex_match = re.match(complex_pattern, text, re.IGNORECASE | re.DOTALL)
        simple_match = re.match(simple_pattern, text, re.IGNORECASE | re.DOTALL)
        
        print(f"   Complex pattern match: {'✅' if complex_match else '❌'}")
        print(f"   Simple pattern match: {'✅' if simple_match else '❌'}")
        print(f"   Has '[insert as applicable:': {'✅' if '[insert as applicable:' in text.lower() else '❌'}")
        
        # Test classification
        classification = classifier.classify_variable(text)
        print(f"   Actual classification: {classification.variable_type.value}")
        print()
    
    print("🎯 ANALYSIS:")
    print("If both patterns match for simple variables, the issue is pattern specificity.")
    print("The complex pattern should NOT match simple variables.")

if __name__ == "__main__":
    debug_pattern_priority()