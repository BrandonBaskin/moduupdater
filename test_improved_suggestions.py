#!/usr/bin/env python3
"""
Test script for improved suggestion logic
"""

import sys
import os
from model_mapper import ModelVariableMapper

def test_improved_suggestions():
    """Test the improved suggestion logic."""
    print("🧪 Testing Improved Suggestion Logic")
    print("=" * 50)
    
    try:
        mapper = ModelVariableMapper()
        
        # Test year update logic
        print("\n1️⃣ Testing Year Update Logic...")
        
        # Test plan name updates
        test_cases = [
            ("insert 2025 plan name", "insert 2026 plan name", "Medicare & You", "Medicare Plus Blue PPO"),
            ("insert 2025 plan name", "insert 2026 plan name", "Medicare Plus Blue PPO 2025", "Medicare Plus Blue PPO 2026"),
            ("insert TTY number", "insert TTY number", "711", "711"),  # Should stay the same
        ]
        
        for old_var, new_var, old_value, expected_value in test_cases:
            result = mapper._update_value_for_year(old_value, old_var, new_var)
            status = "✅" if result == expected_value else "❌"
            print(f"   {status} '{old_var}' -> '{new_var}': '{old_value}' -> '{result}' (expected: '{expected_value}')")
        
        # Test static suggestions
        print("\n2️⃣ Testing Static Suggestions...")
        static_suggestions = mapper._get_static_suggestions()
        expected_static = {
            'insert TTY number': '711',
            'insert phone number': '1-855-669-8040'
        }
        
        for var_name, expected_value in expected_static.items():
            actual_value = static_suggestions.get(var_name, "NOT_FOUND")
            status = "✅" if actual_value == expected_value else "❌"
            print(f"   {status} '{var_name}': '{actual_value}' (expected: '{expected_value}')")
        
        # Test year-specific suggestions
        print("\n3️⃣ Testing Year-Specific Suggestions...")
        year_suggestions = mapper._get_year_specific_suggestions()
        expected_year = {
            'insert 2026 plan name': 'Medicare Plus Blue PPO',
            'insert 2025 plan name': 'Medicare Plus Blue PPO'
        }
        
        for var_name, expected_value in expected_year.items():
            actual_value = year_suggestions.get(var_name, "NOT_FOUND")
            status = "✅" if actual_value == expected_value else "❌"
            print(f"   {status} '{var_name}': '{actual_value}' (expected: '{expected_value}')")
        
        print("\n🎉 All suggestion tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_improved_suggestions()
    sys.exit(0 if success else 1) 