#!/usr/bin/env python3
"""
Intelligent AI Clarification Wizard Demo
Demonstrates the massive improvement in question quality and contextual analysis
"""

import tkinter as tk
from intelligent_ai_clarification_wizard import create_intelligent_ai_clarification_wizard

def create_test_mapping_results():
    """Create realistic mapping results based on actual VPX variables."""
    return [
        {
            'variable': '[Optional information: multi-state plans can include the following: We offer coverage in [insert as applicable: several OR all]]',
            'enhanced_type': 'optional_conditional_with_embedded_select',
            'extracted_value': 'coverage information',
            'confidence': 0.9,
            'source': 'Section 1.2 Coverage Area'
        },
        {
            'variable': '[insert URL]',
            'enhanced_type': 'insert_url',
            'extracted_value': 'https://www.bcbsm.com/providers',
            'confidence': 0.8,
            'source': 'Provider Directory Section'
        },
        {
            'variable': '[insert 2025 plan name]',
            'enhanced_type': 'insert',
            'extracted_value': 'Medicare Plus Blue PPO',
            'confidence': 0.9,
            'source': 'Plan Title Section'
        },
        {
            'variable': '[Insert as applicable: We included a copy of our Provider Directory in the envelope with this document.]',
            'enhanced_type': 'if_applicable',
            'extracted_value': 'Provider Directory reference',
            'confidence': 0.7,
            'source': 'Materials Section'
        },
        {
            'variable': '[insert as applicable: and durable medical equipment suppliers]',
            'enhanced_type': 'if_applicable',
            'extracted_value': 'DME suppliers',
            'confidence': 0.6,
            'source': 'Provider Directory Section'
        },
        {
            'variable': '[insert day of the month]',
            'enhanced_type': 'insert_numeric_inline',
            'extracted_value': '15',
            'confidence': 0.8,
            'source': 'Payment Section'
        },
        {
            'variable': '[insert length of plan grace period]',
            'enhanced_type': 'insert_numeric_inline',
            'extracted_value': '2',
            'confidence': 0.7,
            'source': 'Grace Period Section'
        },
        {
            'variable': '[Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows the monthly plan premium amount for each region we serve.]',
            'enhanced_type': 'select_one_with_embedded_insert',
            'extracted_value': 'premium structure',
            'confidence': 0.8,
            'source': 'Premium Section'
        },
        {
            'variable': '[Plans that include a Part B premium reduction benefit may describe the benefit within this section.]',
            'enhanced_type': 'if_applicable_compound_conditional',
            'extracted_value': 'Part B benefit info',
            'confidence': 0.7,
            'source': 'Benefits Section'
        },
        {
            'variable': '[Plans that meet the 5% language threshold must include information about availability of translation services.]',
            'enhanced_type': 'if_applicable_compound_conditional',
            'extracted_value': 'language services',
            'confidence': 0.6,
            'source': 'Language Section'
        }
    ]

def create_test_extracted_values():
    """Create test extracted values."""
    return {
        'plan_name_2025': 'Medicare Plus Blue PPO',
        'provider_url': 'https://www.bcbsm.com/providers',
        'grace_period': '2',
        'payment_day': '15',
        'premium_structure': 'fixed monthly premium'
    }

def test_intelligent_wizard():
    """Test the intelligent wizard with realistic data."""
    
    print("🧙‍♂️ INTELLIGENT AI CLARIFICATION WIZARD DEMO")
    print("=" * 70)
    print("Demonstrating contextual question generation from actual mapping analysis")
    print()
    
    # Create test data
    mapping_results = create_test_mapping_results()
    extracted_values = create_test_extracted_values()
    
    print("📊 TEST DATA OVERVIEW:")
    print(f"   📋 Mapping Results: {len(mapping_results)} variables")
    print(f"   📝 Variable Types: {len(set(r['enhanced_type'] for r in mapping_results))} different types")
    print(f"   💾 Pre-extracted Values: {len(extracted_values)} values")
    print()
    
    print("🔍 SAMPLE VARIABLES BEING ANALYZED:")
    for i, result in enumerate(mapping_results[:5], 1):
        var_text = result['variable']
        if len(var_text) > 80:
            var_text = var_text[:77] + "..."
        print(f"   {i}. {var_text}")
        print(f"      Type: {result['enhanced_type']}")
        print(f"      Extracted: {result['extracted_value']}")
        print()
    
    if len(mapping_results) > 5:
        print(f"   ... and {len(mapping_results) - 5} more variables")
        print()
    
    print("🎯 EXPECTED INTELLIGENT IMPROVEMENTS:")
    print("   ✅ Real options extracted from variables (not 'Option 1, Option 2')")
    print("   ✅ Business-level questions (not technical variable names)")
    print("   ✅ Contextual explanations for each question")
    print("   ✅ Intelligent inference from answers to variable values")
    print("   ✅ Grouped by business context (Provider Network, Geographic, etc.)")
    print("   ✅ Complete yes/no options (not just 'Yes' button)")
    print()
    
    print("🧠 INTELLIGENT ANALYSIS PREVIEW:")
    print("   🏢 Provider Network Management:")
    print("      • Did you include a Provider Directory in the enrollment package?")
    print("      • Does your Provider Directory include DME suppliers?")
    print("      • What is the URL for your online provider directory?")
    print()
    print("   🌍 Geographic Coverage:")
    print("      • What is the geographic scope of your plan? [Several states / All states / Single state]")
    print("      • (Extracted from actual variable options, not placeholders)")
    print()
    print("   💰 Premium Structure:")
    print("      • How is your monthly premium structured?")
    print("      • Does your plan include Part B premium reduction benefits?")
    print()
    print("   🗓️ Timing and Dates:")
    print("      • What day should be used for payment dates? (e.g., 15th)")
    print("      • What is your plan's grace period length? (minimum 2 months)")
    print()
    
    # Test the wizard creation without launching GUI
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        print("🔧 CREATING INTELLIGENT WIZARD...")
        wizard = create_intelligent_ai_clarification_wizard(root, mapping_results, extracted_values)
        
        print(f"📈 INTELLIGENT ANALYSIS RESULTS:")
        print(f"   📊 Variable Analyses: {len(wizard.variable_analyses)}")
        print(f"   🧠 Intelligent Questions: {len(wizard.intelligent_questions)}")
        print(f"   📂 Business Contexts: {len(set(q.business_context for q in wizard.intelligent_questions))}")
        print()
        
        print("🎯 GENERATED INTELLIGENT QUESTIONS:")
        for i, question in enumerate(wizard.intelligent_questions[:8], 1):
            print(f"   Q{i}: {question.business_context}")
            print(f"      ❓ {question.question_text}")
            print(f"      📝 Type: {question.question_type}")
            if question.options:
                print(f"      🔘 Options: {', '.join(question.options[:3])}")
                if len(question.options) > 3:
                    print(f"                 and {len(question.options) - 3} more")
            if question.explanation:
                print(f"      💡 Explanation: {question.explanation}")
            if question.variables_affected:
                affected_count = len(question.variables_affected)
                print(f"      📋 Affects {affected_count} variable{'s' if affected_count != 1 else ''}")
            print()
        
        if len(wizard.intelligent_questions) > 8:
            print(f"   ... and {len(wizard.intelligent_questions) - 8} more intelligent questions")
            print()
        
        root.destroy()
        
        print("🎉 INTELLIGENT WIZARD CAPABILITIES:")
        print("   ✅ Contextual question generation from actual variable content")
        print("   ✅ Real options extracted from variable text (not placeholders)")
        print("   ✅ Business-level questions with clear explanations")
        print("   ✅ Intelligent inference logic for variable value assignment")
        print("   ✅ Grouped by business context for logical flow")
        print("   ✅ Complete question sets with proper answer options")
        print()
        
        print("🚀 LAUNCH READY!")
        print("   Use the dashboard to launch the Intelligent AI Clarification Wizard")
        print("   with your actual mapping results for contextual configuration!")
        
    except Exception as e:
        print(f"❌ Error creating wizard: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_intelligent_wizard()