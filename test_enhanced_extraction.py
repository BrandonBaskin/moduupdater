#!/usr/bin/env python3
"""
Test script for enhanced context-based extraction system.
Tests the specific examples provided by the user.
"""

import json
from logic_mapper_llm import extract_variable_with_contextual_clues, map_final_to_model
from document_parser import DocumentParser
from learning_persistence import LearningPersistence

def test_context_extraction():
    """Test the enhanced context-based extraction with user examples."""
    print("🧪 Testing Enhanced Context-Based Extraction")
    print("=" * 60)
    
    # Test cases based on user examples
    test_cases = [
        {
            'variable_name': 'insert 2025 plan name',
            'model_sentence': 'This plan, [insert 2025 plan name], is offered by [insert MAO name]',
            'source_sentence': 'This plan, Medicare Plus Blue Group PPO, is offered by Blue Cross Blue Shield of Michigan',
            'expected': 'Medicare Plus Blue Group PPO'
        },
        {
            'variable_name': 'insert MAO name', 
            'model_sentence': 'This plan, [insert 2025 plan name], is offered by [insert MAO name]',
            'source_sentence': 'This plan, Medicare Plus Blue Group PPO, is offered by Blue Cross Blue Shield of Michigan',
            'expected': 'Blue Cross Blue Shield of Michigan'
        },
        {
            'variable_name': 'remove terms as needed to reflect plan benefits',
            'model_sentence': '[remove terms as needed to reflect plan benefits] may apply',
            'source_sentence': 'Benefits, premiums, and/or copayments/coinsurance may apply',
            'expected': 'Benefits, premiums, and/or copayments/coinsurance'
        },
        {
            'variable_name': 'insert TTY number',
            'model_sentence': 'Call [insert phone number] or TTY [insert TTY number] for help',
            'source_sentence': 'Call 1-855-669-8040 or TTY 711 for help',
            'expected': '711'
        }
    ]
    
    # Initialize learning system
    learner = LearningPersistence()
    
    print(f"📚 Loaded {len(learner._load_learned_patterns())} learned pattern types")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['variable_name']}")
        print(f"  Model: {test_case['model_sentence']}")
        print(f"  Source: {test_case['source_sentence']}")
        print(f"  Expected: {test_case['expected']}")
        
        # Get learned patterns for this variable
        learned_patterns = learner.get_learned_patterns_for_variable(test_case['variable_name'])
        
        # Perform extraction
        extracted_value, reasoning, confidence = extract_variable_with_contextual_clues(
            test_case['variable_name'],
            test_case['model_sentence'],
            test_case['source_sentence'],
            learned_patterns
        )
        
        print(f"  Result: '{extracted_value}' (confidence: {confidence:.2f})")
        print(f"  Reasoning: {reasoning}")
        
        # Check if result matches expectation
        success = extracted_value.lower().strip() in test_case['expected'].lower() or \
                 test_case['expected'].lower() in extracted_value.lower().strip()
        
        print(f"  Status: {'✅ PASS' if success else '❌ FAIL'}")
        print()
        
        # Save the extraction experience for learning
        context_parts = test_case['model_sentence'].split(f"[{test_case['variable_name']}]")
        before_context = context_parts[0].strip() if len(context_parts) > 0 else ""
        after_context = context_parts[1].strip() if len(context_parts) > 1 else ""
        
        learner.save_extraction_experience(
            variable_name=test_case['variable_name'],
            context_before=before_context,
            context_after=after_context,
            extracted_value=extracted_value,
            confidence=confidence,
            reasoning=reasoning,
            extraction_method="test_enhanced"
        )

def test_document_parsing():
    """Test that document parsing creates individual variable blocks."""
    print("🧪 Testing Individual Variable Block Creation")
    print("=" * 60)
    
    # Create a test paragraph with multiple variables
    test_text = "This plan, [insert 2026 plan name], is offered by [insert MAO name] in [insert states]."
    
    parser = DocumentParser()
    
    # Test the enhanced parsing
    blocks = parser._parse_nested_brackets(test_text, para_idx=0)
    
    print(f"📄 Test text: {test_text}")
    print(f"🔢 Number of blocks created: {len(blocks)}")
    print()
    
    for i, block in enumerate(blocks, 1):
        print(f"Block {i}:")
        print(f"  Variable: {block.get('inner_text', 'N/A')}")
        print(f"  Type: {block.get('type', 'unknown')}")
        print(f"  Before context: '{block.get('before_context', '')}'")
        print(f"  After context: '{block.get('after_context', '')}'")
        print(f"  Full context: '{block.get('text', '')[:100]}...'")
        print()
    
    # Verify each variable gets its own block
    expected_variables = ['insert 2026 plan name', 'insert MAO name', 'insert states']
    found_variables = [block.get('inner_text') for block in blocks]
    
    print(f"Expected variables: {expected_variables}")
    print(f"Found variables: {found_variables}")
    
    success = all(var in found_variables for var in expected_variables)
    print(f"Status: {'✅ PASS - Each variable has its own block' if success else '❌ FAIL - Variables not properly isolated'}")

def test_learning_system():
    """Test the learning system's pattern recognition."""
    print("🧪 Testing Learning System Pattern Recognition")
    print("=" * 60)
    
    learner = LearningPersistence()
    
    # Test pattern suggestions
    test_contexts = [
        {
            'variable_name': 'insert 2026 plan name',
            'before_context': 'This plan,',
            'after_context': ', is offered by'
        },
        {
            'variable_name': 'insert MAO name',
            'before_context': 'is offered by',
            'after_context': 'throughout this document'
        }
    ]
    
    for test in test_contexts:
        suggestions = learner.get_smart_suggestions(
            test['variable_name'],
            test['before_context'],
            test['after_context']
        )
        
        print(f"Variable: {test['variable_name']}")
        print(f"Context: '{test['before_context']}' ... '{test['after_context']}'")
        print(f"Smart suggestions: {len(suggestions)}")
        
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"  {i}. '{suggestion['value']}' (confidence: {suggestion['confidence']:.2f})")
            print(f"     Reasoning: {suggestion['reasoning']}")
        
        print()

if __name__ == "__main__":
    print("🚀 Enhanced CMS Extraction System Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_context_extraction()
        print()
        test_document_parsing()
        print()
        test_learning_system()
        
        print("🎉 All tests completed!")
        
    except Exception as e:
        import traceback
        print(f"❌ Test failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}") 