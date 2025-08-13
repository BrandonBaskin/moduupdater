#!/usr/bin/env python3
"""
Test AI Clarification Wizard Demo
Demonstrates the enhanced workflow with AI clarification wizard.
"""

import tkinter as tk
from ai_clarification_wizard import create_ai_clarification_wizard

def demo_ai_clarification_wizard():
    """Demo the AI clarification wizard with real CMS variable examples."""
    
    print("🧙‍♂️ AI CLARIFICATION WIZARD DEMO")
    print("="*70)
    print("Demonstrating intelligent business-logic questions for CMS variables\n")
    
    # Mock mapping results with real CMS variables from user examples
    mock_mapping_results = [
        {
            "variable": "Insert as applicable: We included a copy of our Provider Directory in the envelope with this document.",
            "enhanced_type": "if_applicable_compound_conditional",
            "extracted_value": "None",
            "confidence": 0.0,
            "source": "enhanced_ai_extraction"
        },
        {
            "variable": "insert if applicable: and durable medical equipment suppliers",
            "enhanced_type": "insert_conditional",
            "extracted_value": "None",
            "confidence": 0.0,
            "source": "enhanced_ai_extraction"
        },
        {
            "variable": "Insert as applicable: We [insert as applicable: also] included a copy of our Durable Medical Equipment Supplier Directory in the envelope with this document.",
            "enhanced_type": "if_applicable_compound_conditional",
            "extracted_value": "None",
            "confidence": 0.0,
            "source": "enhanced_ai_extraction"
        },
        {
            "variable": "The most recent list of providers [insert as applicable: and suppliers] is [insert as applicable: also] available on our website at [insert URL].",
            "enhanced_type": "complex_conditional_with_url",
            "extracted_value": "None",
            "confidence": 0.0,
            "source": "enhanced_ai_extraction"
        },
        {
            "variable": "Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows the monthly plan premium amount for each region we serve. OR The table below shows the monthly plan premium amount for each plan we are offering in the service area. OR The monthly premium amount for [insert 2025 plan name] is listed in [describe attachment].",
            "enhanced_type": "select_one",
            "extracted_value": "None",
            "confidence": 0.0,
            "source": "enhanced_ai_extraction"
        },
        {
            "variable": "Plans that include a Part B premium reduction benefit may describe the benefit within this section.",
            "enhanced_type": "if_applicable_compound_conditional",
            "extracted_value": "None",
            "confidence": 0.0,
            "source": "enhanced_ai_extraction"
        },
        {
            "variable": "Plans that meet the 5% alternative language threshold insert: This document is available for free in [insert languages that meet the 5% threshold]",
            "enhanced_type": "if_applicable_compound_conditional",
            "extracted_value": "This document is available for free in Spanish.",
            "confidence": 0.80,
            "source": "enhanced_ai_extraction"
        }
    ]
    
    # Mock extracted values from enhanced mapping
    mock_extracted_values = {
        "insert 2025 plan name": "Medicare Plus Blue Group PPO",
        "insert URL": "https://www.bcbsm.com/providersmedicare",
        "insert monthly premium amount": "$45.50",
        "insert languages that meet the 5% threshold": "Spanish"
    }
    
    print("📊 Input Data:")
    print(f"   Mapping Results: {len(mock_mapping_results)} variables")
    print(f"   Extracted Values: {len(mock_extracted_values)} pre-extracted")
    print("\n🤖 Expected Questions:")
    print("   1. Did you include a Provider Directory in the envelope?")
    print("   2. Does your Provider Directory list medical equipment suppliers?")
    print("   3. Did you include a separate DME Supplier Directory?")
    print("   4. Is the provider directory available on your website?")
    print("   5. How is your monthly premium structured? (Select one)")
    print("   6. Does your plan include Part B premium reduction?")
    print("   7. Does your plan meet the 5% language threshold?")
    
    print("\n🎯 Expected Business Logic:")
    print("   • If Provider Directory included → Include applicable text")
    print("   • If DME suppliers listed → Add 'and suppliers' to text")
    print("   • If website available → Include URL reference") 
    print("   • For premium structure → Select appropriate format")
    print("   • For language threshold → Include conditional content")
    
    # Create root window for demo
    root = tk.Tk()
    root.title("AI Clarification Wizard Demo")
    root.geometry("400x300")
    
    # Add demo button
    demo_button = tk.Button(
        root, 
        text="🧙‍♂️ Launch AI Clarification Wizard",
        command=lambda: launch_demo_wizard(root, mock_mapping_results, mock_extracted_values),
        font=("Arial", 12),
        bg="#4a90e2",
        fg="white",
        padx=20,
        pady=10
    )
    demo_button.pack(expand=True)
    
    # Instructions
    instructions = tk.Label(
        root,
        text="Click the button above to launch the AI Clarification Wizard\nand experience intelligent business-logic questions!",
        font=("Arial", 10),
        wraplength=350,
        justify="center"
    )
    instructions.pack(pady=20)
    
    print(f"\n🚀 Demo ready! Click the button in the GUI to launch the wizard.")
    
    root.mainloop()

def launch_demo_wizard(parent, mapping_results, extracted_values):
    """Launch the demo wizard."""
    try:
        wizard = create_ai_clarification_wizard(parent, mapping_results, extracted_values)
        final_values = wizard.launch_wizard()
        
        if final_values:
            # Show results
            result_window = tk.Toplevel(parent)
            result_window.title("🎉 Wizard Results")
            result_window.geometry("600x400")
            
            tk.Label(result_window, text="🎉 AI Clarification Wizard Results", font=("Arial", 14, "bold")).pack(pady=10)
            
            # Results text
            results_text = tk.Text(result_window, height=20, width=70, font=("Courier", 9))
            results_text.pack(padx=20, pady=10)
            
            results_text.insert("1.0", f"📊 FINAL VARIABLE VALUES ({len(final_values)} total):\n\n")
            
            for var, value in final_values.items():
                status = "✅" if value != "None" else "⚠️"
                results_text.insert("end", f"{status} {var}:\n   → {value}\n\n")
            
            results_text.config(state="disabled")
            
            print(f"\n🎉 Demo completed! {len(final_values)} variables configured.")
        else:
            print("ℹ️ Demo wizard was cancelled.")
            
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_ai_clarification_wizard()