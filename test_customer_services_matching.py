#!/usr/bin/env python3
"""
Test Customer Services Number Matching Issue
Test the specific case where "Customer Services number" should match "phone number" patterns
"""

from enhanced_variable_classifier import create_enhanced_classifier

def test_customer_services_matching():
    """Test Customer Services number classification and suggestion matching."""
    
    print("🔍 TESTING CUSTOMER SERVICES NUMBER MATCHING")
    print("=" * 60)
    print("Testing the mismatch between 'Customer Services number' and 'phone number'")
    print()
    
    # Test the specific variable from the user's image
    test_variable = "insert Customer Services number"
    
    print(f"🧪 Testing variable: [{test_variable}]")
    
    # Create classifier
    classifier = create_enhanced_classifier()
    
    # Test classification
    print("\n1. VARIABLE CLASSIFICATION:")
    classification = classifier.classify_variable(test_variable)
    
    print(f"   Variable Type: {classification.variable_type.value}")
    print(f"   Confidence: {classification.confidence_score}")
    
    # Check if it's classified correctly for phone numbers
    expected_types = ["insert_numeric_inline", "phone_number", "contact_info"]
    if any(expected in classification.variable_type.value for expected in expected_types):
        print("   ✅ Correctly classified for phone number context")
    else:
        print("   ❌ NOT classified as phone number type")
        print(f"   Expected one of: {expected_types}")
    
    # Test fuzzy matching scenarios
    print("\n2. FUZZY MATCHING TEST:")
    
    test_scenarios = [
        ("insert Customer Services number", "insert phone number"),
        ("insert Customer Service number", "insert phone number"), 
        ("insert customer services number", "insert phone number"),
        ("insert customer service number", "insert phone number"),
        ("Customer Services number", "phone number"),
        ("Customer Service number", "phone number")
    ]
    
    for source, target in test_scenarios:
        # Simple similarity test
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, source.lower(), target.lower()).ratio()
        
        print(f"   '{source}' → '{target}': {similarity:.2%}")
        
        if similarity > 0.6:
            print("     ✅ Should match with fuzzy logic")
        else:
            print("     ❌ Too different for basic fuzzy matching")
    
    print("\n3. ENHANCED MATCHING SUGGESTIONS:")
    print("   💡 Need semantic matching for:")
    print("      • Customer Service(s) → phone/contact")
    print("      • number → phone number") 
    print("      • Service context → contact information")
    
    return classification

if __name__ == "__main__":
    result = test_customer_services_matching()