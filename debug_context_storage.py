#!/usr/bin/env python3
"""
Debug Context Storage in Smart Wizard
Check if enhanced context is being properly stored and retrieved for each variable
"""

import json
from smart_wizard import SmartWizard
from enhanced_document_context import create_enhanced_document_context_extractor

def debug_context_storage():
    """Debug the context storage and retrieval for variables."""
    
    print("🔍 DEBUGGING CONTEXT STORAGE IN SMART WIZARD")
    print("=" * 65)
    print("Checking if enhanced context is properly stored for each variable")
    print()
    
    # Test document paths
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    extracted_values = {}
    
    try:
        # Create Smart Wizard instance (this should extract variables with context)
        print("📊 Creating Smart Wizard and extracting variables...")
        wizard = SmartWizard(None, model_path, extracted_values)
        
        print(f"✅ Found {len(wizard.variables)} variables")
        print()
        
        # Check the first few variables to see their context
        print("🔍 CONTEXT ANALYSIS FOR FIRST 5 VARIABLES:")
        print("-" * 60)
        
        for i, var in enumerate(wizard.variables[:5]):
            print(f"\n📋 Variable {i+1}: [{var['name']}]")
            print(f"   Type: {var['type']}")
            
            # Check the full_context field
            full_context = var.get('full_context', 'None')
            if isinstance(full_context, str):
                # Show first 200 characters of context
                context_preview = full_context[:200] + "..." if len(full_context) > 200 else full_context
                print(f"   Context Preview: {context_preview}")
                
                # Check if it contains enhanced context markers
                if "📍 DOCUMENT LOCATION" in full_context:
                    print("   ✅ Enhanced context detected!")
                elif "2026 EOC model" in full_context or "2025 EOC model" in full_context:
                    print("   ❌ Still showing basic context (model name)")
                else:
                    print(f"   ⚠️  Unknown context format")
            else:
                print(f"   ❌ Context type: {type(full_context)}")
        
        print("\n" + "=" * 60)
        print("🎯 SUMMARY:")
        
        enhanced_count = 0
        basic_count = 0
        
        for var in wizard.variables:
            full_context = var.get('full_context', '')
            if "📍 DOCUMENT LOCATION" in str(full_context):
                enhanced_count += 1
            else:
                basic_count += 1
        
        print(f"   Enhanced Context: {enhanced_count} variables")
        print(f"   Basic Context: {basic_count} variables")
        print(f"   Total: {len(wizard.variables)} variables")
        
        if enhanced_count == 0:
            print("\n❌ ISSUE FOUND: No variables have enhanced context!")
            print("   This means the enhanced context lookup is failing.")
        elif enhanced_count < len(wizard.variables):
            print(f"\n⚠️  PARTIAL SUCCESS: Only {enhanced_count}/{len(wizard.variables)} variables have enhanced context")
        else:
            print("\n✅ SUCCESS: All variables have enhanced context!")
            
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_context_storage()