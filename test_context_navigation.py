#!/usr/bin/env python3
"""
Test Context Navigation in Smart Wizard
Simulate navigation between variables to test context updating
"""

import tkinter as tk
from smart_wizard import SmartWizard

def test_context_navigation():
    """Test that context updates when navigating between variables."""
    
    print("🧙‍♂️ TESTING CONTEXT NAVIGATION")
    print("=" * 50)
    print("Testing context updates during variable navigation")
    print()
    
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    extracted_values = {}
    
    try:
        # Create a hidden root window for Tkinter
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        print("📊 Creating Smart Wizard for navigation test...")
        wizard = SmartWizard(root, extracted_values, model_path)
        
        if len(wizard.variables) >= 3:
            print(f"✅ Found {len(wizard.variables)} variables")
            print("\n🔍 TESTING NAVIGATION BETWEEN FIRST 3 VARIABLES:")
            print("-" * 55)
            
            # Test navigation between variables
            for i in range(3):
                print(f"\n📋 VARIABLE {i+1}: [{wizard.variables[i]['name']}]")
                
                # Set current variable index
                wizard.current_variable_index = i
                
                # Manually call _show_current_variable (this is what navigation buttons do)
                wizard._show_current_variable()
                
                # Get the context from the text widget
                context_content = wizard.context_text.get('1.0', tk.END).strip()
                
                print(f"   Context Length: {len(context_content)} characters")
                
                # Check if enhanced context is displayed
                if "📍 DOCUMENT LOCATION" in context_content:
                    print("   ✅ Enhanced context displayed correctly")
                    
                    # Check if variable is highlighted
                    var_pattern = f"[{wizard.variables[i]['name']}]"
                    if var_pattern in context_content:
                        print("   ✅ Variable found in displayed context")
                    else:
                        print("   ❌ Variable NOT found in displayed context")
                        
                    # Show a preview of the displayed content
                    preview = context_content[:150] + "..." if len(context_content) > 150 else context_content
                    print(f"   Preview: {preview}")
                    
                else:
                    print("   ❌ Enhanced context NOT displayed")
                    print(f"   Actual content: {context_content[:100]}...")
            
            print(f"\n🎯 NAVIGATION TEST COMPLETE")
            print("   Each variable should show different enhanced context")
            
        else:
            print("❌ Not enough variables for navigation test")
        
        # Clean up
        wizard.window.destroy()
        root.destroy()
        
    except Exception as e:
        print(f"❌ Error during navigation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_navigation()