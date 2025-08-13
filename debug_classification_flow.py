#!/usr/bin/env python3
"""
Debug Classification Flow
Step through the exact classification logic to find where the wrong result comes from
"""

from enhanced_variable_classifier import create_enhanced_classifier, VariableType

def debug_classification_flow():
    """Debug the complete classification flow step by step."""
    
    print("🔍 DEBUGGING CLASSIFICATION FLOW")
    print("=" * 50)
    
    test_variable = "insert Customer Services number"
    
    print(f"🧪 Testing: '{test_variable}'")
    print()
    
    # Create classifier
    classifier = create_enhanced_classifier()
    
    # Test the classification methods directly
    print("📋 TESTING CLASSIFICATION METHODS:")
    
    # 1. Test pattern match classification 
    print("1. Pattern Match Classification:")
    try:
        pattern_result = classifier._pattern_match_classification(test_variable)
        if pattern_result:
            print(f"   ✅ Pattern match: {pattern_result.variable_type.value} (confidence: {pattern_result.confidence_score})")
        else:
            print("   ❌ No pattern match")
    except Exception as e:
        print(f"   ❌ Error in pattern matching: {e}")
    
    # 2. Test enhanced keyword match
    print("\n2. Enhanced Keyword Matching:")
    for var_type in [VariableType.INSERT_NUMERIC_INLINE, VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT]:
        try:
            keywords = []
            if var_type in classifier.pattern_matchers:
                for matcher in classifier.pattern_matchers[var_type]:
                    keywords.extend(matcher.get("keywords", []))
            
            match_result = classifier._enhanced_keyword_match(test_variable.lower(), keywords, var_type)
            print(f"   {var_type.value}: {match_result} (keywords: {keywords[:3]}...)")
        except Exception as e:
            print(f"   {var_type.value}: Error - {e}")
    
    # 3. Test the complete classification
    print("\n3. Complete Classification:")
    try:
        final_result = classifier.classify_variable(test_variable)
        print(f"   Final result: {final_result.variable_type.value}")
        print(f"   Confidence: {final_result.confidence_score}")
        print(f"   Method used: {getattr(final_result, 'classification_method', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Error in complete classification: {e}")
    
    # 4. Check if there's a high-priority pattern that's matching incorrectly
    print("\n4. Priority Order Check:")
    
    priority_order = [
        VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT,
        VariableType.OPTIONAL_INFORMATION_COMPOUND,
        VariableType.INSERT_NUMERIC_INLINE,
        VariableType.INSERT_URL,
        VariableType.SELECT_ONE,
        VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
        VariableType.IF_APPLICABLE,
        VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT,
        VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT
    ]
    
    for var_type in priority_order[:9]:  # Check first 9 types
        if var_type in classifier.pattern_matchers:
            for i, matcher in enumerate(classifier.pattern_matchers[var_type]):
                pattern = matcher.get("pattern", "")
                keywords = matcher.get("keywords", [])
                
                # Test pattern match
                import re
                try:
                    match = re.match(pattern, f"[{test_variable}]", re.IGNORECASE | re.DOTALL)
                    if match:
                        print(f"   🚨 {var_type.value} Pattern {i+1} MATCHES: {pattern[:50]}...")
                        print(f"      This explains the wrong classification!")
                        return
                except:
                    pass
    
    print("   ❌ No higher-priority pattern found that matches")

if __name__ == "__main__":
    debug_classification_flow()