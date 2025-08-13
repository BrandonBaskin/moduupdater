#!/usr/bin/env python3
"""
Test Improved Smart Wizard Context Management
Test the Smart Wizard with the new Variable Context Manager
"""

from smart_wizard import SmartWizard

def test_improved_smart_wizard():
    """Test the improved Smart Wizard with enhanced context management."""
    
    print("🧙‍♂️ TESTING IMPROVED SMART WIZARD")
    print("=" * 55)
    print("Testing Smart Wizard with Variable Context Manager")
    print()
    
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    extracted_values = {}
    
    try:
        print("📊 Creating Smart Wizard with enhanced context management...")
        wizard = SmartWizard(None, extracted_values, model_path)
        
        print(f"\n✅ Smart Wizard created successfully!")
        print(f"📋 Found {len(wizard.variables)} variables")
        
        if len(wizard.variables) > 0:
            print("\n🔍 TESTING CONTEXT FOR FIRST 3 VARIABLES:")
            print("-" * 50)
            
            for i, var in enumerate(wizard.variables[:3]):
                print(f"\n📋 Variable {i+1}: [{var['name']}]")
                print(f"   Type: {var['type']}")
                
                # Check the full_context
                full_context = var.get('full_context', 'None')
                
                if "📍 DOCUMENT LOCATION" in str(full_context):
                    print("   ✅ Enhanced context detected!")
                    # Show first 200 chars
                    preview = str(full_context)[:200] + "..." if len(str(full_context)) > 200 else str(full_context)
                    print(f"   Context preview: {preview}")
                else:
                    print(f"   ❌ Basic context only: {str(full_context)[:100]}...")
            
            # Overall statistics
            enhanced_count = sum(1 for var in wizard.variables if "📍 DOCUMENT LOCATION" in str(var.get('full_context', '')))
            basic_count = len(wizard.variables) - enhanced_count
            
            print(f"\n📊 CONTEXT STATISTICS:")
            print(f"   Enhanced Context: {enhanced_count} variables ({enhanced_count/len(wizard.variables)*100:.1f}%)")
            print(f"   Basic Context: {basic_count} variables ({basic_count/len(wizard.variables)*100:.1f}%)")
            print(f"   Total: {len(wizard.variables)} variables")
            
            if enhanced_count > 0:
                print("\n🎉 SUCCESS: Enhanced context is working!")
                print("   Variables now have meaningful document location information.")
            else:
                print("\n❌ ISSUE: No enhanced context found")
                print("   Variables are still using basic context.")
        else:
            print("❌ No variables found!")
            
    except Exception as e:
        print(f"❌ Error testing Smart Wizard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_smart_wizard()