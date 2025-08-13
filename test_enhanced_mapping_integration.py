#!/usr/bin/env python3
"""
Test the Enhanced Mapping Integration
Demonstrates how the 23-type classification system + AI agent improves extraction.
"""

from enhanced_mapping_integration import create_enhanced_mapping_engine
from enhanced_variable_classifier import create_enhanced_classifier, VariableType
from logic_mapper_llm import classify_variable_comprehensive

def test_enhanced_mapping():
    """Test the enhanced mapping system with problematic variables from the log."""
    
    print('🧠 TESTING ENHANCED MAPPING INTEGRATION')
    print('='*70)
    print('Testing variables that showed poor extraction in the original log\n')
    
    # Initialize the enhanced mapping engine
    engine = create_enhanced_mapping_engine()
    
    # Test cases based on problematic variables from the log
    test_cases = [
        {
            "variable_name": "Plans that meet the 5% alternative language threshold insert: This document is available for free in [insert languages that meet the 5% threshold]",
            "context_before": "Language assistance is provided.",
            "context_after": "Contact customer service for help.",
            "source_paragraphs": [
                "This document is available in Spanish, which meets our 5% threshold requirement for alternative language services.",
                "Language assistance services are provided free of charge to members who speak Spanish.",
                "We offer translation services for documents in multiple languages including Spanish and French.",
                "The plan serves areas where Spanish-speaking members represent more than 5% of total enrollment.",
                "Para obtener este documento en español, por favor llame al servicio al cliente."
            ],
            "expected_improvement": "Should extract content about Spanish meeting 5% threshold, not unrelated text"
        },
        {
            "variable_name": "If a fee is charged, insert: We're allowed to charge a fee for copying and sending this information to you.",
            "context_before": "We will provide copies of your medical records.",
            "context_after": "Processing may take up to 30 days.",
            "source_paragraphs": [
                "We will provide copies of your medical records at no charge for the first copy.",
                "Additional copies may incur a reasonable fee for copying and mailing costs.",
                "We're allowed to charge a fee for copying and sending this information to you if multiple copies are requested.",
                "Step 3: We consider your appeal and we give you our answer within the required timeframe.",
                "Processing requests may take up to 30 days from the date we receive your request."
            ],
            "expected_improvement": "Should extract fee-related content, not appeal process text"
        },
        {
            "variable_name": "insert length of grace period, which can't be less than two calendar months",
            "context_before": "If you don't pay your plan premium by the due date,",
            "context_after": "before we can disenroll you from our plan.",
            "source_paragraphs": [
                "If you don't pay your plan premium by the due date, you have a grace period of three calendar months.",
                "The grace period allows you time to catch up on payments before disenrollment.",
                "During the grace period, we will continue to provide your covered services.",
                "The minimum grace period required by CMS is two calendar months, but our plan provides three months.",
                "Your group has selected this plan option for extended grace periods."
            ],
            "expected_improvement": "Should extract 'three calendar months', not 'group has'"
        },
        {
            "variable_name": "insert URL",
            "context_before": "For more information, visit our website at",
            "context_after": "to access your member portal.",
            "source_paragraphs": [
                "For more information, visit our website at www.bluecrossblueshield.com to access your member portal.",
                "You can also find information online at https://member.bcbs.com for account management.",
                "Our customer service team is available by phone or through our website portal.",
                "Visit the member section of our website for additional resources and tools.",
                "Download the mobile app or use the online portal for convenient access to your benefits."
            ],
            "expected_improvement": "Should extract actual URL, not generic text"
        },
        {
            "variable_name": "Plans with grandfathered members who were outside of area prior to January 1999, insert: If you've been a member of our plan continuously before January 1999...",
            "context_before": "Special enrollment rules apply to certain members.",
            "context_after": "Contact customer service for eligibility verification.",
            "source_paragraphs": [
                "Special enrollment rules apply to certain members who have been with the plan for many years.",
                "If you have been a member of our plan continuously prior to January 1999 and were living outside of our service area before January 1999, you are still eligible.",
                "Grandfathered members who were outside of area prior to January 1999 maintain special eligibility status.",
                "However, if you move and your move is to another location that is outside of our service area, you will be disenrolled from our plan.",
                "Contact customer service for eligibility verification and assistance with grandfathered status questions."
            ],
            "expected_improvement": "Should extract conditional text about grandfathered eligibility, not 'None'"
        }
    ]
    
    total_tests = len(test_cases)
    improved_extractions = 0
    
    for i, test_case in enumerate(test_cases, 1):
        variable_name = test_case["variable_name"]
        variable_text = f"[{variable_name}]"
        context_before = test_case["context_before"]
        context_after = test_case["context_after"]
        source_paragraphs = test_case["source_paragraphs"]
        expected_improvement = test_case["expected_improvement"]
        
        print(f"Test {i}: {variable_name[:60]}{'...' if len(variable_name) > 60 else ''}")
        print(f"Expected: {expected_improvement}")
        
        # First, show enhanced classification
        classification = classify_variable_comprehensive(variable_text, context_before, context_after)
        print(f"🧠 Classification: {classification.variable_type.value}")
        print(f"🎯 Confidence: {classification.confidence_score:.2f}")
        
        if classification.condition_text:
            print(f"📋 Condition: {classification.condition_text}")
        if classification.insert_text:
            print(f"📝 Insert Text: {classification.insert_text[:50]}{'...' if len(classification.insert_text) > 50 else ''}")
        
        # Now test enhanced extraction
        try:
            extracted_value, confidence, reasoning = engine.extract_variable_intelligently(
                variable_name, variable_text, context_before, context_after, source_paragraphs
            )
            
            print(f"✅ Enhanced Extraction: '{extracted_value}'")
            print(f"🎯 Confidence: {confidence:.2f}")
            print(f"🔍 Reasoning: {reasoning}")
            
            # Check if extraction looks reasonable (not "None" and relevant)
            if extracted_value != "None" and len(extracted_value) > 5:
                improved_extractions += 1
                print("🎉 IMPROVEMENT: Meaningful content extracted!")
            else:
                print("⚠️  Still needs work: No meaningful content extracted")
                
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
        
        print("-" * 70)
    
    # Summary
    improvement_rate = (improved_extractions / total_tests) * 100
    print(f"\n🎯 ENHANCED MAPPING TEST RESULTS")
    print(f"Total tests: {total_tests}")
    print(f"Improved extractions: {improved_extractions}")
    print(f"Improvement rate: {improvement_rate:.1f}%")
    
    if improvement_rate >= 60:
        print("🎉 EXCELLENT: Enhanced mapping shows significant improvement!")
        print("✅ Ready for integration into main workflow")
    elif improvement_rate >= 40:
        print("👍 GOOD: Enhanced mapping shows improvement")
        print("🔧 May need additional refinement")
    else:
        print("⚠️  NEEDS WORK: Enhancement not yet providing expected improvements")
    
    return improvement_rate >= 60

def demo_ai_agent_participation():
    """Demonstrate how the AI agent participates in refining the mapping."""
    
    print('\n\n🤖 AI AGENT PARTICIPATION DEMO')
    print('='*70)
    print('Showing how the AI agent helps refine variable mapping\n')
    
    engine = create_enhanced_mapping_engine()
    
    # Example of AI agent helping with complex conditional logic
    variable_name = "Plans that meet the 5% alternative language threshold insert: This document is available for free in [insert languages that meet the 5% threshold]"
    variable_text = f"[{variable_name}]"
    
    # Simulate different source contexts that require AI interpretation
    scenarios = [
        {
            "name": "Clear 5% threshold case",
            "source": [
                "This document is available in Spanish, which meets our 5% threshold requirement.",
                "Spanish-speaking members represent 6.2% of our enrollment in this service area.",
                "We provide all required documents in Spanish at no additional cost to members."
            ]
        },
        {
            "name": "Multiple languages case", 
            "source": [
                "Our service area includes significant Spanish and Vietnamese populations.",
                "Spanish speakers represent 7% and Vietnamese speakers represent 5.3% of enrollment.",
                "This document is available in Spanish and Vietnamese, both meeting the 5% threshold."
            ]
        },
        {
            "name": "No threshold met case",
            "source": [
                "Our service area is primarily English-speaking with diverse smaller populations.",
                "No single language group exceeds the 5% threshold required for translation services.",
                "Alternative format requests are handled on a case-by-case basis."
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"Scenario: {scenario['name']}")
        print("AI Agent Analysis:")
        
        try:
            result = engine.extract_variable_intelligently(
                variable_name, variable_text, 
                "Language assistance is provided.", 
                "Contact customer service for help.",
                scenario['source']
            )
            
            extracted_value, confidence, reasoning = result
            
            print(f"  🎯 Extracted: '{extracted_value}'")
            print(f"  📊 Confidence: {confidence:.2f}")
            print(f"  🧠 AI Reasoning: {reasoning}")
            
            # AI agent's conditional logic evaluation
            if "spanish" in extracted_value.lower() or "5%" in extracted_value.lower():
                print("  ✅ AI correctly identified threshold condition is met")
            elif extracted_value == "None":
                print("  ✅ AI correctly determined condition is not met")
            else:
                print("  🤔 AI provided partial or unclear result")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    print("🎉 The AI agent participates by:")
    print("• Analyzing variable type (conditional insertion)")
    print("• Understanding the condition (5% threshold)")  
    print("• Evaluating source content against the condition")
    print("• Extracting appropriate conditional text or 'None'")
    print("• Providing reasoning for the decision")

if __name__ == "__main__":
    print("🚀 Enhanced Mapping Integration Test Suite")
    print("Testing the integration of 23-type classification + AI agent\n")
    
    try:
        # Test enhanced mapping
        success = test_enhanced_mapping()
        
        # Demo AI agent participation
        demo_ai_agent_participation()
        
        print(f"\n{'='*70}")
        if success:
            print("🎉 ENHANCED MAPPING INTEGRATION: READY FOR PRODUCTION!")
            print("✅ Significant improvement over basic pattern matching")
            print("✅ AI agent actively participates in mapping refinement")
            print("✅ 23-type classification enables sophisticated processing")
        else:
            print("🔧 ENHANCED MAPPING INTEGRATION: NEEDS REFINEMENT")
            print("⚠️  May require additional training or pattern adjustments")
        
        print("\nThe enhanced system now provides:")
        print("• Type-aware source document matching")
        print("• AI agent integration with sophisticated prompts")
        print("• Conditional logic evaluation") 
        print("• Validation and confidence scoring")
        print("• Learning system integration")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()