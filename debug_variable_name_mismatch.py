#!/usr/bin/env python3
"""
Debug Variable Name Mismatch
Compare variable names between Smart Wizard and Enhanced Context Extractor
"""

import re
from docx import Document
from enhanced_document_context import create_enhanced_document_context_extractor

def debug_variable_name_mismatch():
    """Debug variable name matching between Smart Wizard and Enhanced Context."""
    
    print("🔍 DEBUGGING VARIABLE NAME MISMATCH")
    print("=" * 60)
    
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    
    # 1. Get variable names from Enhanced Context Extractor
    print("1. Getting variable names from Enhanced Context Extractor...")
    context_extractor = create_enhanced_document_context_extractor()
    variable_contexts = context_extractor.extract_document_structure(model_path)
    
    enhanced_vars = set(variable_contexts.keys())
    print(f"   ✅ Enhanced Context found: {len(enhanced_vars)} variables")
    
    # 2. Get variable names using Smart Wizard logic (simplified)
    print("2. Getting variable names using Smart Wizard logic...")
    doc = Document(model_path)
    smart_wizard_vars = set()
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text or '[' not in text:
            continue
            
        # Find all variables in this paragraph (same regex as Smart Wizard)
        variable_matches = list(re.finditer(r'\[([^\]]+)\]', text))
        
        for match in variable_matches:
            var_name = match.group(1).strip()
            var_full_name = f"[{var_name}]"
            smart_wizard_vars.add(var_full_name)
    
    print(f"   ✅ Smart Wizard logic found: {len(smart_wizard_vars)} variables")
    
    # 3. Compare the two sets
    print("\n📊 COMPARISON RESULTS:")
    print("-" * 40)
    
    # Variables in enhanced context but not in smart wizard
    enhanced_only = enhanced_vars - smart_wizard_vars
    print(f"Enhanced Context Only: {len(enhanced_only)} variables")
    if enhanced_only:
        print("   Examples:")
        for var in list(enhanced_only)[:5]:
            print(f"     {var}")
    
    # Variables in smart wizard but not in enhanced context
    smart_only = smart_wizard_vars - enhanced_vars
    print(f"\nSmart Wizard Only: {len(smart_only)} variables")
    if smart_only:
        print("   Examples:")
        for var in list(smart_only)[:5]:
            print(f"     {var}")
    
    # Variables in both
    common_vars = enhanced_vars & smart_wizard_vars
    print(f"\nCommon Variables: {len(common_vars)} variables")
    
    # 4. Test a few lookups
    print("\n🔍 TESTING LOOKUPS:")
    print("-" * 30)
    
    test_vars = list(common_vars)[:3] if common_vars else list(enhanced_vars)[:3]
    
    for var in test_vars:
        print(f"\nTesting: {var}")
        
        # Test direct lookup
        context = variable_contexts.get(var)
        if context:
            print(f"   ✅ Direct lookup successful")
            # Test format_context_for_display
            formatted = context_extractor.format_context_for_display(context, var)
            preview = formatted[:150] + "..." if len(formatted) > 150 else formatted
            print(f"   Context preview: {preview}")
        else:
            print(f"   ❌ Direct lookup failed")
    
    return enhanced_vars, smart_wizard_vars, variable_contexts

if __name__ == "__main__":
    enhanced_vars, smart_vars, contexts = debug_variable_name_mismatch()