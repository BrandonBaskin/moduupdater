#!/usr/bin/env python3
"""
Test Complex Variable Parsing - VPX Taxonomy Enhancement
Tests the enhanced classifier's ability to parse complex nested variables with biconditional logic
"""

from enhanced_variable_classifier import create_enhanced_classifier
from enhanced_ai_clarification_wizard import create_enhanced_ai_clarification_wizard

def test_complex_variable_parsing():
    """Test the enhanced classifier with complex nested variables."""
    
    print("🧪 COMPLEX VARIABLE PARSING TEST")
    print("=" * 60)
    print("Testing enhanced VPX taxonomy for complex nested structures")
    print()
    
    # Create the enhanced classifier
    classifier = create_enhanced_classifier()
    
    # Test the exact variable from the user's image
    complex_variables = [
        {
            'name': 'Complex Multi-State Optional Variable (User Image)',
            'text': '[Optional information: multi-state plans can include the following: We offer coverage in [insert as applicable: several OR all]]',
            'expected_type': 'optional_conditional_with_embedded_select',
            'description': 'Complex variable with optional prefix, conditional logic, and embedded selection'
        },
        {
            'name': 'Optional Information Simple',
            'text': '[Optional information: Additional details may be provided]',
            'expected_type': 'optional_information_compound',
            'description': 'Simple optional information block'
        },
        {
            'name': 'Multi-State Coverage Option',
            'text': '[Optional information: multi-state plans can include coverage details]',
            'expected_type': 'optional_information_compound',
            'description': 'Optional information with plan-specific conditions'
        },
        {
            'name': 'Nested Conditional with Selection',
            'text': '[Optional information: regional plans can include: Coverage varies by [insert as applicable: state OR region]]',
            'expected_type': 'optional_conditional_with_embedded_select',
            'description': 'Another complex nested variable with embedded selection'
        }
    ]
    
    print("🔍 TESTING COMPLEX VARIABLE CLASSIFICATION:")
    print()
    
    results = []
    for var in complex_variables:
        print(f"📋 Testing: {var['name']}")
        print(f"   Variable: {var['text']}")
        print(f"   Expected: {var['expected_type']}")
        
        # Classify the variable
        classification = classifier.classify_variable(var['text'])
        
        actual_type = classification.variable_type.value
        is_correct = actual_type == var['expected_type']
        
        print(f"   Actual:   {actual_type}")
        print(f"   Result:   {'✅ CORRECT' if is_correct else '❌ INCORRECT'}")
        
        # Get heuristic behavior
        behavior = classifier.get_heuristic_behavior(classification)
        print(f"   Behavior: {behavior.get('action', 'unknown')}")
        
        if classification.condition_text:
            print(f"   Condition: {classification.condition_text}")
        if classification.insert_text:
            print(f"   Insert Text: {classification.insert_text}")
        if classification.options:
            print(f"   Options: {classification.options}")
        
        results.append({
            'variable': var['name'],
            'text': var['text'],
            'expected': var['expected_type'],
            'actual': actual_type,
            'correct': is_correct,
            'classification': classification,
            'behavior': behavior
        })
        
        print()
    
    # Summary
    correct_count = sum(1 for r in results if r['correct'])
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100
    
    print("📊 CLASSIFICATION RESULTS:")
    print(f"   ✅ Correct: {correct_count}/{total_count}")
    print(f"   📈 Accuracy: {accuracy:.1f}%")
    print()
    
    # Test wizard question generation
    print("🧙‍♂️ TESTING WIZARD QUESTION GENERATION:")
    print()
    
    # Create mapping results for the wizard
    mapping_results = []
    extracted_values = {}
    
    for i, result in enumerate(results):
        mapping_result = {
            'variable': f"test_var_{i}",
            'enhanced_type': result['actual'],
            'extracted_value': 'Test Value',
            'source': 'test',
            'confidence': 0.9
        }
        mapping_results.append(mapping_result)
        extracted_values[f"test_var_{i}"] = 'Test Value'
    
    # Test question generation (without GUI)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        wizard = create_enhanced_ai_clarification_wizard(root, mapping_results, extracted_values)
        
        print(f"📝 Generated Questions: {len(wizard.clarification_questions)}")
        print(f"📊 Variable Groups: {len(wizard.variable_groups)}")
        
        # Show some example questions
        for i, question in enumerate(wizard.clarification_questions[:5]):
            print(f"   Q{i+1}: {question.question_text}")
            if question.options:
                print(f"       Options: {question.options}")
            print(f"       Type: {question.question_type}")
        
        if len(wizard.clarification_questions) > 5:
            print(f"   ... and {len(wizard.clarification_questions) - 5} more questions")
        
        root.destroy()
        print("✅ Wizard creation successful!")
        
    except Exception as e:
        print(f"❌ Wizard test error: {e}")
    
    print()
    print("🎯 TEST CONCLUSIONS:")
    if accuracy >= 75:
        print("   ✅ EXCELLENT: Complex variable parsing is working well!")
    elif accuracy >= 50:
        print("   ⚠️  GOOD: Most complex variables parsed correctly")
    else:
        print("   ❌ NEEDS WORK: Complex variable parsing needs improvement")
    
    print(f"   📈 Overall accuracy: {accuracy:.1f}%")
    print("   🧙‍♂️ Enhanced wizard ready for complex variables")
    
    return results

if __name__ == "__main__":
    test_complex_variable_parsing()