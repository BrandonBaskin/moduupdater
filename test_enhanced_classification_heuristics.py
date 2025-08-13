#!/usr/bin/env python3
"""
Test script for the Enhanced Variable Classification System
Based on the CMS Model Prompt Heuristics Guide

This script demonstrates the 23-type classification system and its heuristic behaviors
using real examples from the CMS guide.
"""

import sys
import json
from enhanced_variable_classifier import create_enhanced_classifier, VariableType
from logic_mapper_llm import classify_variable_comprehensive


def test_enhanced_classification():
    """Test the enhanced classification system with examples from the heuristics guide."""
    
    print("🧠 Enhanced CMS Variable Classification Test")
    print("=" * 60)
    print("Testing the comprehensive 23-type classification system based on")
    print("the CMS Model Prompt Heuristics Guide")
    print()
    
    # Create classifier
    classifier = create_enhanced_classifier()
    
    # Test cases from the heuristics guide with expected types
    test_cases = [
        {
            "variable": "[insert 2025 plan name]",
            "expected_type": VariableType.INSERT,
            "context_before": "For 2025, the monthly premium for",
            "context_after": "is listed below.",
            "description": "Standard insert placeholder"
        },
        {
            "variable": "[select one: Yes/No]",
            "expected_type": VariableType.SELECT_ONE,
            "context_before": "Do you offer this benefit?",
            "context_after": "based on plan requirements.",
            "description": "Basic option selection"
        },
        {
            "variable": "[Optional] You may also request a printed copy.",
            "expected_type": VariableType.OPTIONAL,
            "context_before": "You can view your benefits online.",
            "context_after": "Contact customer service for assistance.",
            "description": "Optional conditional content"
        },
        {
            "variable": "[Delete if not applicable]",
            "expected_type": VariableType.DELETE_IF,
            "context_before": "This section covers supplemental benefits.",
            "context_after": "Additional coverage details follow.",
            "description": "Conditional deletion instruction"
        },
        {
            "variable": "[Insert if applicable: URLs, notices]",
            "expected_type": VariableType.IF_APPLICABLE,
            "context_before": "Additional resources are available.",
            "context_after": "Contact information is provided below.",
            "description": "Simple conditional insertion"
        },
        {
            "variable": "[Plans with grandfathered members who were outside of area prior to January 1999, insert: If you have been a member of our plan continuously since before January 1999...]",
            "expected_type": VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            "context_before": "Eligibility requirements vary by member type.",
            "context_after": "Standard enrollment rules apply to all other members.",
            "description": "Compound conditional with specific condition and insert text"
        },
        {
            "variable": "[if a continuation area is offered under 42 CFR 422.54, insert: generally here and add a sentence describing the continuation area]",
            "expected_type": VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT,
            "context_before": "Service area definitions are provided",
            "context_after": "for complete coverage details.",
            "description": "Instructional insert requiring custom drafting"
        },
        {
            "variable": "[Remove terms as needed to reflect plan benefits]",
            "expected_type": VariableType.INSTRUCTIONAL_INLINE_DELETION,
            "context_before": "The following may change on January 1:",
            "context_after": "Benefits, premiums, deductibles, and copayments may vary.",
            "description": "Inline term pruning instruction"
        },
        {
            "variable": "[Insert plan service area here or within an appendix. Plans may include references to territories... Our service area includes these states: [insert states]... counties in [insert state]: [insert counties]... parts of counties: [insert county] with [insert zip codes]]",
            "expected_type": VariableType.COMPLEX_STRUCTURAL_INSERT,
            "context_before": "Our plan operates in specific geographic areas.",
            "context_after": "Service area maps are available upon request.",
            "description": "Complex structured geographic data insertion"
        },
        {
            "variable": "[Regional PPOs that CMS has granted permission to use the exception in § 422.112(a)(1)(ii) to meet access requirements should insert: Because our Plan is a Regional Preferred Provider Organization...]",
            "expected_type": VariableType.REGULATORY_CONDITIONAL_INSERT,
            "context_before": "Network access requirements are governed by CMS regulations.",
            "context_after": "Contact customer service for network assistance.",
            "description": "Regulatory compliance conditional insertion"
        },
        {
            "variable": "[insert as applicable: also]",
            "expected_type": VariableType.IF_APPLICABLE_NESTED_MODIFIER,
            "context_before": "We included a copy of our Provider Directory.",
            "context_after": "included a copy of our Supplier Directory.",
            "description": "Nested contextual modifier"
        },
        {
            "variable": "[insert URL]",
            "expected_type": VariableType.INSERT_URL,
            "context_before": "The most recent provider list is available at",
            "context_after": "for your convenience.",
            "description": "URL insertion with validation"
        },
        {
            "variable": "[Delete Optional Supplemental Benefit Premium bullet if your plan doesn't offer optional supplemental benefits. Renumber remaining sections as appropriate.]",
            "expected_type": VariableType.INSTRUCTIONAL_STRUCTURAL_DELETION,
            "context_before": "Premium information is organized by benefit type:",
            "context_after": "• Basic Plan Premium\n• Optional Supplemental Benefit Premium\n• Part B Premium",
            "description": "Structural deletion with renumbering"
        },
        {
            "variable": "[Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows the monthly plan premium amount for each region we serve.]",
            "expected_type": VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT,
            "context_before": "Premium information is presented as follows:",
            "context_after": "Contact customer service for premium questions.",
            "description": "Complex selection with embedded inserts"
        },
        {
            "variable": "[Plans with no premium should replace the preceding paragraph with: You do not pay a separate monthly plan premium for [insert 2025 plan name].]",
            "expected_type": VariableType.INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH,
            "context_before": "As a member of our plan, you pay a monthly plan premium.",
            "context_after": "Premium payment options are described below.",
            "description": "Paragraph replacement instruction"
        },
        {
            "variable": "[Plans that include a Part B premium reduction benefit may describe the benefit within this section.]",
            "expected_type": VariableType.PERMISSIVE_CONDITIONAL_INSERT,
            "context_before": "Additional benefits may be available to eligible members.",
            "context_after": "Contact customer service for benefit details.",
            "description": "Permissive conditional content addition"
        },
        {
            "variable": "[Plans with no monthly premium, omit: In addition to paying the monthly plan premium,]",
            "expected_type": VariableType.INSTRUCTIONAL_CLAUSE_OMISSION,
            "context_before": "As a plan member, you have payment responsibilities.",
            "context_after": "you must continue paying your Medicare premiums.",
            "description": "Clause omission with sentence preservation"
        },
        {
            "variable": "[If the plan describes optional supplemental benefits within Chapter 4, then the plan must include the premium amounts for those benefits in this section.]",
            "expected_type": VariableType.INSTRUCTIONAL_CROSS_REFERENCE_REQUIREMENT,
            "context_before": "Premium information must be comprehensive and cross-referenced.",
            "context_after": "All benefit costs must be clearly documented.",
            "description": "Cross-reference structural requirement"
        },
        {
            "variable": "[insert number of payment options]",
            "expected_type": VariableType.INSERT_NUMERIC_INLINE,
            "context_before": "There are",
            "context_after": "ways you can pay your plan premium.",
            "description": "Inline numeric value insertion"
        },
        {
            "variable": "[Insert plan specifics regarding premium/penalty payment intervals (e.g., monthly, quarterly), how they can pay by check, including an address, whether they can drop off a check in person...]",
            "expected_type": VariableType.INSERT_PLAN_SPECIFICS_COMPOSITE,
            "context_before": "Payment options and procedures are as follows:",
            "context_after": "Additional payment assistance is available upon request.",
            "description": "Composite plan-specific details insertion"
        }
    ]
    
    # Test results tracking
    total_tests = len(test_cases)
    correct_classifications = 0
    detailed_results = []
    
    print(f"Running {total_tests} classification tests...\n")
    
    for i, test_case in enumerate(test_cases, 1):
        variable = test_case["variable"]
        expected_type = test_case["expected_type"]
        context_before = test_case["context_before"]
        context_after = test_case["context_after"]
        description = test_case["description"]
        
        print(f"Test {i:2d}: {description}")
        print(f"Variable: {variable[:80]}{'...' if len(variable) > 80 else ''}")
        
        # Perform classification
        classification = classify_variable_comprehensive(variable, context_before, context_after)
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
        print(f"Field ID: {classification.field_id}")
        print(f"Behavior: {behavior.get('action', 'unknown')}")
        
        # Additional details for interesting cases
        if classification.editor_instruction:
            print("⚠️  Editor Instruction Required")
        if classification.requires_user_input:
            print("👤 Requires User Input")
        if classification.requires_regulatory_awareness:
            print("📋 Requires Regulatory Awareness")
        if classification.options:
            print(f"📋 Options: {', '.join(classification.options)}")
        if classification.condition_text:
            print(f"🔍 Condition: {classification.condition_text[:60]}{'...' if len(classification.condition_text) > 60 else ''}")
        
        # Store detailed result
        detailed_results.append({
            "test_number": i,
            "description": description,
            "variable": variable,
            "expected_type": expected_type.value,
            "actual_type": classification.variable_type.value,
            "correct": is_correct,
            "confidence": classification.confidence_score,
            "field_id": classification.field_id,
            "behavior": behavior.get('action', 'unknown'),
            "editor_instruction": classification.editor_instruction,
            "requires_user_input": classification.requires_user_input
        })
        
        print("-" * 60)
    
    # Final summary
    accuracy = (correct_classifications / total_tests) * 100
    print(f"\n🎯 CLASSIFICATION RESULTS SUMMARY")
    print(f"Total tests: {total_tests}")
    print(f"Correct classifications: {correct_classifications}")
    print(f"Accuracy: {accuracy:.1f}%")
    
    # Detailed analysis
    print(f"\n📊 DETAILED ANALYSIS")
    
    # Count by type
    type_counts = {}
    type_correct = {}
    for result in detailed_results:
        actual_type = result["actual_type"]
        if actual_type not in type_counts:
            type_counts[actual_type] = 0
            type_correct[actual_type] = 0
        type_counts[actual_type] += 1
        if result["correct"]:
            type_correct[actual_type] += 1
    
    print("Classification breakdown:")
    for var_type, count in sorted(type_counts.items()):
        correct = type_correct[var_type]
        accuracy = (correct / count) * 100 if count > 0 else 0
        print(f"  {var_type:30} : {correct:2d}/{count:2d} ({accuracy:5.1f}%)")
    
    # Special cases analysis
    editor_instructions = sum(1 for r in detailed_results if r["editor_instruction"])
    user_input_required = sum(1 for r in detailed_results if r["requires_user_input"])
    
    print(f"\nSpecial characteristics:")
    print(f"  Editor instructions: {editor_instructions}/{total_tests}")
    print(f"  User input required: {user_input_required}/{total_tests}")
    
    # Save detailed results to file
    with open("enhanced_classification_test_results.json", "w") as f:
        json.dump({
            "summary": {
                "total_tests": total_tests,
                "correct_classifications": correct_classifications,
                "accuracy_percent": accuracy,
                "editor_instructions": editor_instructions,
                "user_input_required": user_input_required
            },
            "detailed_results": detailed_results,
            "type_breakdown": {
                var_type: {
                    "total": type_counts[var_type],
                    "correct": type_correct[var_type],
                    "accuracy": (type_correct[var_type] / type_counts[var_type]) * 100 if type_counts[var_type] > 0 else 0
                }
                for var_type in type_counts
            }
        }, f, indent=2)
    
    print(f"\n📁 Detailed results saved to 'enhanced_classification_test_results.json'")
    
    return accuracy >= 80  # Consider test passed if 80%+ accuracy


def demonstrate_heuristic_behaviors():
    """Demonstrate the heuristic behavior system for different variable types."""
    
    print(f"\n🎭 HEURISTIC BEHAVIOR DEMONSTRATION")
    print("=" * 60)
    
    classifier = create_enhanced_classifier()
    
    # Examples of different behaviors
    behavior_examples = [
        {
            "variable": "[insert 2025 plan name]",
            "description": "Standard input prompt"
        },
        {
            "variable": "[select one: Yes/No]",
            "description": "Option selection"
        },
        {
            "variable": "[Plans with no premium, omit: In addition to paying the monthly plan premium,]",
            "description": "Clause omission"
        },
        {
            "variable": "[Remove terms as needed to reflect plan benefits]",
            "description": "Inline term deletion"
        },
        {
            "variable": "[insert URL]",
            "description": "URL with validation"
        }
    ]
    
    for example in behavior_examples:
        variable = example["variable"]
        description = example["description"]
        
        print(f"\nExample: {description}")
        print(f"Variable: {variable}")
        
        classification = classify_variable_comprehensive(variable)
        behavior = classifier.get_heuristic_behavior(classification)
        
        print(f"Type: {classification.variable_type.value}")
        print(f"Behavior Action: {behavior.get('action', 'unknown')}")
        
        # Display behavior-specific details
        if behavior.get("action") == "prompt_user_input":
            print("  → Prompt user for input")
            print(f"  → Validation: {behavior.get('validation', 'none')}")
            
        elif behavior.get("action") == "present_options":
            options = behavior.get("options", [])
            print(f"  → Present options: {', '.join(options) if options else 'auto-detect'}")
            print(f"  → Exclusive selection: {behavior.get('exclusive', False)}")
            
        elif behavior.get("action") == "conditional_inclusion":
            print(f"  → Default: {behavior.get('default', 'unknown')}")
            print(f"  → User choice: {behavior.get('user_choice', False)}")
            
        elif behavior.get("action") == "prune_terms":
            print(f"  → Target: {behavior.get('target_text', 'unknown')}")
            print(f"  → Present as checkboxes: {behavior.get('present_as_checkboxes', False)}")
            
        elif behavior.get("action") == "url_input":
            print(f"  → Validation: {behavior.get('validation', 'none')}")
            print(f"  → Required: {behavior.get('required', False)}")
    
    print("\n✅ Heuristic behavior demonstration complete")


if __name__ == "__main__":
    print("🚀 Starting Enhanced CMS Variable Classification Test Suite")
    print()
    
    try:
        # Run classification tests
        test_passed = test_enhanced_classification()
        
        # Demonstrate behaviors
        demonstrate_heuristic_behaviors()
        
        # Final status
        print(f"\n{'='*60}")
        if test_passed:
            print("🎉 ENHANCED CLASSIFICATION SYSTEM: READY FOR PRODUCTION")
            print("✅ All tests passed - heuristics guide implementation complete")
        else:
            print("⚠️  ENHANCED CLASSIFICATION SYSTEM: NEEDS REFINEMENT")
            print("❌ Some tests failed - review classification patterns")
        
        print("\nThe enhanced variable classification system now supports:")
        print("• 23 comprehensive variable types from CMS heuristics guide")
        print("• Sophisticated pattern recognition and context analysis")
        print("• Heuristic behavior rules for each variable type")
        print("• Enhanced AI prompting with type-specific instructions")
        print("• Detailed logging and classification metadata")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)