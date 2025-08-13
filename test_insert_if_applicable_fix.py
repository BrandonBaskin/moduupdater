#!/usr/bin/env python3
"""
Test Insert If Applicable Parsing Fix
Test the specific variable from the user's image to ensure correct parsing
"""

from enhanced_variable_classifier import create_enhanced_classifier

def test_insert_if_applicable_parsing():
    """Test the specific variable that wasn't parsing correctly."""
    
    print("🔧 INSERT IF APPLICABLE PARSING FIX TEST")
    print("=" * 55)
    
    # Create classifier
    classifier = create_enhanced_classifier()
    
    # Test the exact variable from user's image
    test_variable = "[insert if applicable: or territory]"
    
    print(f"🧪 Testing variable: {test_variable}")
    print()
    
    # Classify the variable
    classification = classifier.classify_variable(test_variable)
    
    print("📊 CLASSIFICATION RESULTS:")
    print(f"   Variable Type: {classification.variable_type.value}")
    print(f"   Confidence: {classification.confidence_score}")
    print(f"   Expected Type: if_applicable")
    print()
    
    # Check if content was extracted
    print("🎯 CONTENT EXTRACTION:")
    print(f"   Insert Text: '{classification.insert_text}'")
    print(f"   Expected Content: 'or territory'")
    print()
    
    # Check classification correctness
    is_correct_type = classification.variable_type.value == "if_applicable"
    is_content_extracted = classification.insert_text and "territory" in classification.insert_text
    
    print("✅ VALIDATION:")
    print(f"   Type Correct: {'✅ YES' if is_correct_type else '❌ NO'}")
    print(f"   Content Extracted: {'✅ YES' if is_content_extracted else '❌ NO'}")
    print()
    
    # Test with similar patterns
    similar_variables = [
        "[Insert if applicable: URLs, notices]",
        "[insert if applicable: also]", 
        "[insert if applicable: and suppliers]"
    ]
    
    print("🔄 TESTING SIMILAR PATTERNS:")
    for var in similar_variables:
        result = classifier.classify_variable(var)
        print(f"   {var}")
        print(f"      Type: {result.variable_type.value}")
        print(f"      Content: '{result.insert_text}'")
        print()
    
    # Overall result
    if is_correct_type and is_content_extracted:
        print("🎉 SUCCESS: Insert if applicable parsing is now working correctly!")
        print("✅ The variable will now be properly classified and content extracted")
    else:
        print("❌ ISSUE: Parsing still needs refinement")
        if not is_correct_type:
            print(f"   - Expected type 'if_applicable', got '{classification.variable_type.value}'")
        if not is_content_extracted:
            print(f"   - Expected content 'or territory', got '{classification.insert_text}'")

if __name__ == "__main__":
    test_insert_if_applicable_parsing()