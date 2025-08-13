#!/usr/bin/env python3
"""
Debug Context Display in Smart Wizard
Check what's actually stored in full_context and how it's displayed
"""

from smart_wizard import SmartWizard

def debug_context_display():
    """Debug the context display for specific variables."""
    
    print("🔍 DEBUGGING CONTEXT DISPLAY IN SMART WIZARD")
    print("=" * 65)
    print("Checking what's stored in full_context and how it displays")
    print()
    
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    extracted_values = {}
    
    try:
        print("📊 Creating Smart Wizard...")
        wizard = SmartWizard(None, extracted_values, model_path)
        
        print(f"✅ Found {len(wizard.variables)} variables")
        
        if len(wizard.variables) >= 3:
            print("\n🔍 DETAILED CONTEXT ANALYSIS FOR FIRST 3 VARIABLES:")
            print("=" * 60)
            
            for i, var in enumerate(wizard.variables[:3]):
                print(f"\n📋 VARIABLE {i+1}: [{var['name']}]")
                print(f"   Type: {var['type']}")
                
                # Get the full_context
                full_context = var.get('full_context', 'None')
                
                print(f"   Context Type: {type(full_context)}")
                print(f"   Context Length: {len(str(full_context))} characters")
                
                # Check for enhanced context markers
                context_str = str(full_context)
                if "📍 DOCUMENT LOCATION" in context_str:
                    print("   ✅ Enhanced context detected")
                else:
                    print("   ❌ Enhanced context NOT detected")
                
                # Show the actual context content (first 300 chars)
                print(f"   First 300 chars:")
                print(f"   '{context_str[:300]}{'...' if len(context_str) > 300 else ''}'")
                
                # Test the highlighting logic
                var_pattern = f"[{var['name']}]"
                print(f"   Variable pattern: '{var_pattern}'")
                print(f"   Pattern in context: {var_pattern in context_str}")
                
                if var_pattern in context_str:
                    try:
                        before, after = context_str.split(var_pattern, 1)
                        print(f"   Split successful - Before: {len(before)} chars, After: {len(after)} chars")
                    except:
                        print("   ❌ Split failed")
                else:
                    print("   ⚠️  Pattern not found - highlighting won't work")
                
                print("-" * 50)
        
        print(f"\n📊 SUMMARY:")
        enhanced_count = 0
        basic_count = 0
        
        for var in wizard.variables:
            context_str = str(var.get('full_context', ''))
            if "📍 DOCUMENT LOCATION" in context_str:
                enhanced_count += 1
            else:
                basic_count += 1
        
        print(f"   Enhanced contexts: {enhanced_count}")
        print(f"   Basic contexts: {basic_count}")
        print(f"   Total variables: {len(wizard.variables)}")
        
        if enhanced_count == len(wizard.variables):
            print("\n✅ All variables have enhanced context!")
            print("   The issue must be in the GUI display logic.")
        else:
            print(f"\n⚠️  Only {enhanced_count}/{len(wizard.variables)} have enhanced context")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_context_display()