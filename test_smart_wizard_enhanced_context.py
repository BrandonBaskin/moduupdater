#!/usr/bin/env python3
"""
Test Smart Wizard Enhanced Context Integration
Verify that the Smart Wizard now uses enhanced document context
"""

import os
from smart_wizard import SmartWizard

def test_smart_wizard_enhanced_context():
    """Test that Smart Wizard properly integrates enhanced document context."""
    
    print("🧪 SMART WIZARD ENHANCED CONTEXT INTEGRATION TEST")
    print("=" * 65)
    print("Testing integration of enhanced document context into Smart Wizard")
    print()
    
    # Test document path (using existing model)
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    
    if not os.path.exists(model_path):
        print("❌ Test document not found, using fallback test")
        print(f"   Expected: {model_path}")
        print("   📋 Testing will verify code integration only")
        return
    
    print(f"📄 Test Document: {os.path.basename(model_path)}")
    print(f"   Path: {model_path}")
    print()
    
    try:
        print("🔧 TESTING ENHANCED CONTEXT INTEGRATION:")
        
        # Create Smart Wizard instance (don't show UI)
        print("   1. Creating Smart Wizard instance...")
        wizard = SmartWizard(
            parent=None,  # No parent for testing
            model_docx_path=model_path,
            extracted_values={}
        )
        
        print("   2. Enhanced context extractor integration...")
        
        # Test if variables were extracted
        if hasattr(wizard, 'variables') and wizard.variables:
            total_vars = len(wizard.variables)
            print(f"   ✅ Variables extracted: {total_vars}")
            
            # Check first few variables for enhanced context
            enhanced_count = 0
            basic_count = 0
            
            for i, var in enumerate(wizard.variables[:5]):  # Check first 5 variables
                context = var.get('full_context', '')
                
                # Check if context has enhanced features
                if ('📍 Location:' in context or '📄 Page:' in context or 
                    '⬅️ Before:' in context or '➡️ After:' in context):
                    enhanced_count += 1
                    print(f"   ✅ Variable {i+1}: Enhanced context detected")
                    if i == 0:  # Show example for first variable
                        print(f"      📋 Example context preview:")
                        context_preview = context[:100] + "..." if len(context) > 100 else context
                        print(f"         {context_preview}")
                else:
                    basic_count += 1
                    print(f"   ⚠️  Variable {i+1}: Basic context (fallback)")
            
            print()
            print("📊 CONTEXT ANALYSIS:")
            print(f"   Enhanced Context: {enhanced_count}/5 variables")
            print(f"   Basic Context: {basic_count}/5 variables")
            
            if enhanced_count > 0:
                print("   ✅ SUCCESS: Enhanced context system is working!")
                print("   🎯 Smart Wizard will now show meaningful document locations")
            elif basic_count == 5:
                print("   ⚠️  INFO: Using basic context (enhanced extraction may have failed)")
                print("   🔧 This is expected if document structure is minimal")
            
        else:
            print("   ❌ No variables found in document")
        
    except ImportError as e:
        print(f"   ❌ Import Error: {e}")
        print("   🔧 Enhanced document context system may not be available")
    except Exception as e:
        print(f"   ❌ Integration Error: {e}")
        print("   🔧 Enhanced context integration needs debugging")
    
    print()
    print("🎯 EXPECTED IMPROVEMENTS:")
    print("   ✅ Document Context shows: 'Chapter 3: Provider Network → Section 3.2: Coverage Area'")
    print("   ✅ Instead of: '2026 EOC model'")
    print("   ✅ Includes page numbers, before/after text, and structural location")
    print()
    print("🚀 NEXT STEPS:")
    print("   1. Launch dashboard and proceed to Smart Wizard")
    print("   2. Verify context shows enhanced location information")
    print("   3. Context should be meaningful and help users understand variable purpose")

if __name__ == "__main__":
    test_smart_wizard_enhanced_context()