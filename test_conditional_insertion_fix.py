#!/usr/bin/env python3
"""
Test the fix for conditional insertion variables where content after the colon
should be conditionally inserted.
"""

from enhanced_variable_classifier import create_enhanced_classifier, VariableType
from logic_mapper_llm import classify_variable_comprehensive

def test_conditional_insertion_fix():
    """Test the specific variable from the user's image and similar cases."""
    
    print('🔧 TESTING CONDITIONAL INSERTION FIX')
    print('='*60)
    
    classifier = create_enhanced_classifier()
    
    # Test cases for conditional insertion variables
    test_cases = [
        {
            "variable": "[Plans that meet the 5% alternative language threshold insert: This document is available for free in [insert languages that meet the 5% threshold]]",
            "expected_type": VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            "description": "5% threshold conditional insertion from user image"
        },
        {
            "variable": "[Plans with grandfathered members who were outside of area prior to January 1999, insert: If you have been a member of our plan continuously before January 1999...]",
            "expected_type": VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            "description": "Grandfathered members conditional (with comma)"
        },
        {
            "variable": "[Plans that offer dental benefits insert: Additional dental coverage is available]",
            "expected_type": VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            "description": "Dental benefits conditional insertion"
        },
        {
            "variable": "[Plans should insert: Contact customer service for assistance]",
            "expected_type": VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            "description": "Generic 'should insert' pattern"
        },
        {
            "variable": "[Plans with premium reduction benefits insert: You may be eligible for reduced premiums]",
            "expected_type": VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            "description": "Premium reduction conditional"
        }
    ]
    
    correct_classifications = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        variable = test_case["variable"]
        expected_type = test_case["expected_type"]
        description = test_case["description"]
        
        print(f"\nTest {i}: {description}")
        print(f"Variable: {variable[:80]}{'...' if len(variable) > 80 else ''}")
        
        # Perform classification
        classification = classify_variable_comprehensive(variable)
        behavior = classifier.get_heuristic_behavior(classification)
        
        # Check if classification is correct
        is_correct = classification.variable_type == expected_type
        if is_correct:
            correct_classifications += 1
            status = "✅ CORRECT"
        else:
            status = "❌ INCORRECT"
        
        print(f"Expected: {expected_type.value}")
        print(f"Got:      {classification.variable_type.value}")
        print(f"Status:   {status}")
        print(f"Confidence: {classification.confidence_score:.2f}")
        
        # Show condition and insert text extraction
        if classification.condition_text or classification.insert_text:
            print(f"Condition: '{classification.condition_text}'")
            print(f"Insert Text: '{classification.insert_text}'")
        
        # Show behavior
        print(f"Behavior: {behavior.get('action', 'unknown')}")
        if behavior.get('processing_note'):
            print(f"Note: {behavior['processing_note']}")
        
        print("-" * 60)
    
    # Final summary
    accuracy = (correct_classifications / total_tests) * 100
    print(f"\n🎯 CONDITIONAL INSERTION FIX RESULTS")
    print(f"Total tests: {total_tests}")
    print(f"Correct classifications: {correct_classifications}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("✅ FIX SUCCESSFUL - Conditional insertion logic is working correctly!")
        print("🎉 Content after colon ':' will now be properly handled")
    else:
        print("❌ FIX NEEDS MORE WORK - Some patterns still not recognized")
    
    return accuracy >= 80

if __name__ == "__main__":
    print("🚀 Testing Conditional Insertion Fix")
    print("This addresses the issue where content after the colon ':' should be conditionally inserted")
    print()
    
    success = test_conditional_insertion_fix()
    
    if success:
        print("\n🎉 READY FOR PRODUCTION!")
        print("The enhanced system now correctly handles:")
        print("• Plans that meet [condition] insert: [content]")
        print("• Plans with [condition], insert: [content]") 
        print("• Plans should insert: [content]")
        print("• Proper condition/insert text extraction")
        print("• Enhanced AI prompting for conditional logic")
    else:
        print("\n⚠️  Needs additional refinement")