#!/usr/bin/env python3
"""
Debug Customer Services Pattern Matching
Test the exact pattern matching for Customer Services number
"""

import re
from enhanced_variable_classifier import create_enhanced_classifier, VariableType

def debug_customer_services_pattern():
    """Debug the exact pattern matching for Customer Services number."""
    
    print("🔍 DEBUGGING CUSTOMER SERVICES PATTERN MATCHING")
    print("=" * 60)
    
    test_variable = "insert Customer Services number"
    full_variable = f"[{test_variable}]"
    
    print(f"🧪 Testing: '{full_variable}'")
    print()
    
    # Test the patterns directly
    patterns_to_test = [
        ("Generic insert numeric", r"^\[insert\s+number\s+of\s+([^]]+)\]$"),
        ("Phone number", r"^\[insert\s+phone\s+number\]$"),
        ("TTY number", r"^\[insert\s+TTY\s+number\]$"), 
        ("Customer Services (exact)", r"^\[insert\s+Customer\s+Services?\s+number\]$"),
        ("Flexible phone/service", r"^\[insert\s+([^]]*(?:phone|service|contact|number)[^]]*)\]$"),
        ("SELECT_ONE_WITH_EMBEDDED_INSERT", r"^\[Select\s+one\s+of\s+the\s+following:.*\[insert\s+([^]]+)\].*OR.*\]$")
    ]
    
    print("📋 PATTERN TESTING:")
    for name, pattern in patterns_to_test:
        try:
            match = re.match(pattern, full_variable, re.IGNORECASE)
            if match:
                print(f"   ✅ '{name}': MATCHES")
                if match.groups():
                    print(f"      Groups: {match.groups()}")
            else:
                print(f"   ❌ '{name}': NO MATCH")
        except Exception as e:
            print(f"   ❌ '{name}': ERROR - {e}")
    
    print(f"\n🧩 KEYWORD TESTING:")
    keywords_to_test = [
        "insert Customer Service number",
        "insert Customer Services number", 
        "customer service",
        "customer services",
        "phone",
        "service", 
        "contact",
        "number"
    ]
    
    for keyword in keywords_to_test:
        if keyword.lower() in test_variable.lower():
            print(f"   ✅ '{keyword}': FOUND")
        else:
            print(f"   ❌ '{keyword}': NOT FOUND")
    
    print(f"\n🔬 CLASSIFIER STEP-BY-STEP:")
    classifier = create_enhanced_classifier()
    
    # Get the pattern matchers for INSERT_NUMERIC_INLINE
    pattern_matchers = classifier.pattern_matchers.get(VariableType.INSERT_NUMERIC_INLINE, [])
    
    print(f"   INSERT_NUMERIC_INLINE has {len(pattern_matchers)} patterns:")
    for i, matcher in enumerate(pattern_matchers):
        pattern = matcher.get("pattern", "")
        keywords = matcher.get("keywords", [])
        
        print(f"   Pattern {i+1}: {pattern}")
        print(f"   Keywords: {keywords}")
        
        # Test this specific pattern
        try:
            match = re.match(pattern, full_variable, re.IGNORECASE)
            if match:
                print(f"      ✅ MATCHES!")
                if match.groups():
                    print(f"      Groups: {match.groups()}")
            else:
                print(f"      ❌ No match")
        except Exception as e:
            print(f"      ❌ Error: {e}")
        print()

if __name__ == "__main__":
    debug_customer_services_pattern()