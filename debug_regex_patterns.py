#!/usr/bin/env python3
"""
Debug Regex Patterns for Complex Variables
Test the regex patterns directly to fix pattern matching issues
"""

import re

def test_regex_patterns():
    """Test regex patterns for complex variables."""
    
    print("🔍 REGEX PATTERN TESTING")
    print("=" * 50)
    
    # Test variables
    test_variable = "[Optional information: multi-state plans can include the following: We offer coverage in [insert as applicable: several OR all]]"
    simpler_variable = "[Optional information: Additional details may be provided]"
    
    # Current patterns from the enhanced classifier
    patterns = {
        "optional_conditional_with_embedded_select": r"^\[Optional\s+information:\s*([^:\[]+):\s*([^\[]+)\[insert\s+as\s+applicable:\s*([^\]]+)\]([^\]]*)\]$",
        "optional_information_compound": r"^\[Optional\s+information:\s*([^:\]]+)(?::\s*([^\]]+))?\]$",
        "existing_select_one_with_embedded": r"^\[([^]]+)\[insert\s+as\s+applicable:\s*([^\]]+)\]([^]]*)\]$"
    }
    
    print(f"🧪 Testing variable: {test_variable}")
    print()
    
    for pattern_name, pattern in patterns.items():
        print(f"📋 Pattern: {pattern_name}")
        print(f"   Regex: {pattern}")
        
        try:
            match = re.match(pattern, test_variable)
            if match:
                print(f"   ✅ MATCHES!")
                print(f"   Groups: {match.groups()}")
            else:
                print(f"   ❌ No match")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print(f"🧪 Testing simpler variable: {simpler_variable}")
    print()
    
    for pattern_name, pattern in patterns.items():
        print(f"📋 Pattern: {pattern_name}")
        
        try:
            match = re.match(pattern, simpler_variable)
            if match:
                print(f"   ✅ MATCHES!")
                print(f"   Groups: {match.groups()}")
            else:
                print(f"   ❌ No match")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test improved patterns
    print("🔧 TESTING IMPROVED PATTERNS:")
    print()
    
    improved_patterns = {
        "optional_conditional_with_embedded_select_v2": r"^\[Optional\s+information:\s*([^:]+):\s*([^:]+)\[insert\s+as\s+applicable:\s*([^\]]+)\]([^\]]*)\]$",
        "optional_information_compound_v2": r"^\[Optional\s+information:\s*([^\]]+)\]$"
    }
    
    print(f"🧪 Testing with improved patterns: {test_variable}")
    print()
    
    for pattern_name, pattern in improved_patterns.items():
        print(f"📋 Pattern: {pattern_name}")
        print(f"   Regex: {pattern}")
        
        try:
            match = re.match(pattern, test_variable)
            if match:
                print(f"   ✅ MATCHES!")
                print(f"   Groups: {match.groups()}")
            else:
                print(f"   ❌ No match")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Test step by step breakdown
    print("🔍 STEP-BY-STEP PATTERN BREAKDOWN:")
    print()
    
    # Break down the complex variable
    print(f"Variable: {test_variable}")
    print("Structure breakdown:")
    print("  [Optional information: CONDITION: TEXT [insert as applicable: OPTIONS] SUFFIX]")
    print()
    
    # Test progressive patterns
    progressive_patterns = [
        (r"^\[Optional\s+information:", "Optional information prefix"),
        (r"^\[Optional\s+information:\s*([^:]+):", "Condition capture"),
        (r"^\[Optional\s+information:\s*([^:]+):\s*([^:\[]+)", "Text before insert"),
        (r"\[insert\s+as\s+applicable:\s*([^\]]+)\]", "Insert as applicable part"),
        (r"^\[Optional\s+information:\s*([^:]+):\s*([^:\[]+)\[insert\s+as\s+applicable:\s*([^\]]+)\]([^\]]*)\]$", "Full pattern"),
    ]
    
    for pattern, description in progressive_patterns:
        print(f"Testing: {description}")
        print(f"Pattern: {pattern}")
        
        if pattern.startswith("^") and pattern.endswith("$"):
            match = re.match(pattern, test_variable)
        else:
            match = re.search(pattern, test_variable)
        
        if match:
            print(f"✅ Match: {match.groups() if match.groups() else 'Found'}")
        else:
            print("❌ No match")
        print()

if __name__ == "__main__":
    test_regex_patterns()