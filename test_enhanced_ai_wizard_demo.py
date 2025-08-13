#!/usr/bin/env python3
"""
Demo of the Enhanced AI Clarification Wizard
Shows comprehensive question generation based on 23-variable taxonomy
"""

import tkinter as tk
from enhanced_ai_clarification_wizard import create_enhanced_ai_clarification_wizard

def create_comprehensive_demo_data():
    """Create comprehensive demo data covering all major variable types."""
    
    mapping_results = [
        # Plan Identification Variables
        {
            'variable': 'insert 2025 plan name',
            'enhanced_type': 'select_one_with_embedded_insert',
            'extracted_value': 'Medicare Plus Blue Group PPO',
            'source': 'simple_extraction',
            'confidence': 0.7
        },
        {
            'variable': 'insert organization name',
            'enhanced_type': 'insert',
            'extracted_value': 'Blue Cross Blue Shield',
            'source': 'simple_extraction', 
            'confidence': 0.6
        },
        
        # Provider Network Variables
        {
            'variable': 'insert URL',
            'enhanced_type': 'insert_url',
            'extracted_value': 'https://www.bcbsm.com/providersmedicare',
            'source': 'simple_extraction',
            'confidence': 0.8
        },
        {
            'variable': 'Insert as applicable: We included a copy of our Provider Directory',
            'enhanced_type': 'if_applicable_compound_conditional',
            'extracted_value': 'Provider Directory included',
            'source': 'simple_extraction',
            'confidence': 0.5
        },
        {
            'variable': 'insert as applicable: and durable medical equipment suppliers',
            'enhanced_type': 'if_applicable_nested_modifier',
            'extracted_value': 'and suppliers',
            'source': 'simple_extraction',
            'confidence': 0.4
        },
        
        # Premium Structure Variables
        {
            'variable': 'insert monthly premium amount',
            'enhanced_type': 'insert_numeric_inline',
            'extracted_value': '$0',
            'source': 'simple_extraction',
            'confidence': 0.6
        },
        {
            'variable': 'Plans that include a Part B premium reduction benefit',
            'enhanced_type': 'if_applicable_compound_conditional',
            'extracted_value': 'Part B reduction included',
            'source': 'simple_extraction',
            'confidence': 0.5
        },
        
        # Coverage and Benefits Variables
        {
            'variable': 'Select one: includes prescription drug coverage OR does not include',
            'enhanced_type': 'select_one',
            'extracted_value': 'includes prescription drug coverage',
            'source': 'simple_extraction',
            'confidence': 0.7
        },
        {
            'variable': 'insert supplemental benefits',
            'enhanced_type': 'complex_structural_insert',
            'extracted_value': 'dental, vision, hearing',
            'source': 'simple_extraction',
            'confidence': 0.5
        },
        
        # Enrollment and Eligibility Variables
        {
            'variable': 'insert eligibility requirements',
            'enhanced_type': 'regulatory_conditional_insert',
            'extracted_value': 'Medicare Parts A and B',
            'source': 'simple_extraction',
            'confidence': 0.6
        },
        {
            'variable': 'Plans that serve dual eligible members',
            'enhanced_type': 'if_applicable_compound_conditional',
            'extracted_value': 'dual eligible served',
            'source': 'simple_extraction',
            'confidence': 0.4
        },
        
        # Cost Sharing Variables
        {
            'variable': 'insert annual deductible amount',
            'enhanced_type': 'insert_numeric_inline',
            'extracted_value': '$0',
            'source': 'simple_extraction',
            'confidence': 0.7
        },
        {
            'variable': 'insert maximum out-of-pocket amount',
            'enhanced_type': 'insert_numeric_inline',
            'extracted_value': '$8,850',
            'source': 'simple_extraction',
            'confidence': 0.8
        },
        
        # Communication and Language Variables
        {
            'variable': 'Plans that meet the 5% alternative language threshold',
            'enhanced_type': 'if_applicable_compound_conditional',
            'extracted_value': '5% threshold met',
            'source': 'simple_extraction',
            'confidence': 0.3
        },
        {
            'variable': 'insert languages that meet the 5% threshold',
            'enhanced_type': 'insert',
            'extracted_value': 'Spanish',
            'source': 'simple_extraction',
            'confidence': 0.5
        },
        
        # Contact Information Variables
        {
            'variable': 'insert phone number',
            'enhanced_type': 'insert',
            'extracted_value': '1-800-662-2667',
            'source': 'simple_extraction',
            'confidence': 0.9
        },
        {
            'variable': 'insert TTY number',
            'enhanced_type': 'insert',
            'extracted_value': '711',
            'source': 'simple_extraction',
            'confidence': 0.8
        },
        
        # Appeals and Grievances Variables
        {
            'variable': 'insert appeal timeframe',
            'enhanced_type': 'insert_numeric_inline',
            'extracted_value': '60 days',
            'source': 'simple_extraction',
            'confidence': 0.7
        },
        
        # Regulatory and Compliance Variables
        {
            'variable': 'Plans that CMS has granted permission to use exception',
            'enhanced_type': 'regulatory_conditional_insert',
            'extracted_value': 'No exceptions granted',
            'source': 'simple_extraction',
            'confidence': 0.2
        },
        
        # Document Structure Variables
        {
            'variable': 'Omit if not applicable',
            'enhanced_type': 'instructional_structural_deletion',
            'extracted_value': 'Section omitted',
            'source': 'simple_extraction',
            'confidence': 0.3
        }
    ]
    
    extracted_values = {result['variable']: result['extracted_value'] for result in mapping_results}
    
    return mapping_results, extracted_values

def launch_demo_wizard():
    """Launch the enhanced AI clarification wizard demo."""
    
    # Create demo data
    mapping_results, extracted_values = create_comprehensive_demo_data()
    
    print("🧙‍♂️ ENHANCED AI CLARIFICATION WIZARD DEMO")
    print("=" * 70)
    print("Demonstrating comprehensive question generation based on 23-variable taxonomy")
    print()
    print("📊 Input Data:")
    print(f"   Mapping Results: {len(mapping_results)} variables")
    print(f"   Variable Types Covered: {len(set(r['enhanced_type'] for r in mapping_results))} different types")
    print()
    print("🎯 Expected Comprehensive Questions:")
    print("   PLAN IDENTIFICATION:")
    print("   • What is your exact Medicare plan name for 2025?")
    print("   • What is your organization's legal name?")
    print("   • Do you operate in multiple service areas?")
    print()
    print("   PROVIDER NETWORK:")
    print("   • Did you include a Provider Directory in the enrollment package?")
    print("   • Does your Provider Directory list durable medical equipment suppliers?")
    print("   • Is your provider directory available on your website?")
    print("   • Do you have separate directories for different provider types?")
    print("   • Do you operate provider networks in multiple states?")
    print()
    print("   PREMIUM STRUCTURE:")
    print("   • How is your monthly premium structured?")
    print("   • Does your plan include Part B premium reduction benefits?")
    print("   • Are premiums different by geographic region?")
    print("   • Does your plan have $0 premium options?")
    print()
    print("   COVERAGE AND BENEFITS:")
    print("   • Does your plan include prescription drug coverage (Part D)?")
    print("   • Do you offer supplemental benefits beyond Original Medicare?")
    print("   • Are there coverage differences by plan option?")
    print("   • Do you provide telehealth services?")
    print()
    print("   ENROLLMENT AND ELIGIBILITY:")
    print("   • Do you serve dual-eligible members (Medicare-Medicaid)?")
    print("   • Are there special eligibility requirements for your plan?")
    print("   • Do you have enrollment restrictions by geography?")
    print()
    print("   COST SHARING:")
    print("   • What is your plan's annual deductible amount?")
    print("   • What is the maximum out-of-pocket limit?")
    print("   • Do you have different cost-sharing by service type?")
    print()
    print("   COMMUNICATION AND LANGUAGE:")
    print("   • Does your service area meet the 5% alternative language threshold?")
    print("   • What languages do you provide translation services for?")
    print("   • Do you offer interpreter services for member communications?")
    print()
    print("   CONTACT INFORMATION:")
    print("   • What is your main member services phone number?")
    print("   • Do you have a separate TTY number for hearing impaired?")
    print("   • What is your plan's primary website URL?")
    print()
    print("   APPEALS AND GRIEVANCES:")
    print("   • What are your standard appeal timeframes?")
    print("   • Do you offer expedited appeal processes?")
    print()
    print("   REGULATORY AND COMPLIANCE:")
    print("   • Do you have any CMS-granted regulatory exceptions?")
    print("   • Are there state-specific regulatory requirements that apply?")
    print()
    print("   DOCUMENT STRUCTURE:")
    print("   • Are there sections that should be omitted for your plan type?")
    print("   • Do you need to include additional state-required disclosures?")
    print()
    print("🎯 Expected to generate 50+ comprehensive questions!")
    print()
    print("🚀 Demo ready! Click the button in the GUI to launch the enhanced wizard.")
    
    try:
        # Create main window for demo
        root = tk.Tk()
        root.title("Enhanced AI Clarification Wizard Demo")
        root.geometry("400x300")
        
        # Demo info
        info_text = f"""Enhanced AI Clarification Wizard Demo
        
📊 Demo Data:
• {len(mapping_results)} variables across {len(set(r['enhanced_type'] for r in mapping_results))} types
• Comprehensive taxonomy coverage
• 50+ intelligent questions expected

🧙‍♂️ This wizard will generate questions for:
• Plan identification and structure
• Provider network management
• Premium and cost structure
• Coverage and benefits
• Enrollment and eligibility
• Cost sharing and financial
• Communication and language
• Contact information
• Appeals and grievances
• Regulatory compliance
• Document structure
"""
        
        info_label = tk.Label(root, text=info_text, justify=tk.LEFT, padx=20, pady=20)
        info_label.pack()
        
        def launch_wizard():
            try:
                # Create and launch the enhanced wizard
                wizard = create_enhanced_ai_clarification_wizard(root, mapping_results, extracted_values)
                clarified_values = wizard.launch_wizard()
                
                print(f"🎉 Demo completed! {len(clarified_values)} variables configured.")
                
            except Exception as e:
                print(f"❌ Demo error: {e}")
                import traceback
                traceback.print_exc()
        
        # Launch button
        launch_btn = tk.Button(root, text="🧙‍♂️ Launch Enhanced Wizard", 
                              command=launch_wizard, bg='#4CAF50', fg='white',
                              font=('Arial', 12, 'bold'), padx=20, pady=10)
        launch_btn.pack(pady=20)
        
        # Start the demo
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Demo setup error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    launch_demo_wizard()