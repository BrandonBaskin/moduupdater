#!/usr/bin/env python3
"""
Test Template Extraction Fix
Test the enhanced template content extraction for the failing case
"""

from simple_mapper import SimpleMapper

def test_template_extraction_fix():
    """Test the enhanced template extraction on the failing case."""
    print("🔍 TESTING TEMPLATE EXTRACTION FIX")
    print("=" * 70)
    
    # The specific failing case from the user
    variable_text = "Insert if applicable: Your coverage is provided through a contract with your current employer or former employer or union. Contact the employer's or union's benefits administrator for information about our plan premium."
    
    source_content = "Your coverage is provided through a contract with the University of Michigan. Please contact the University of Michiganfor information about your plan premium."
    
    print("📋 TEST CASE:")
    print(f"Variable: [{variable_text[:70]}...]")
    print(f"Source: {source_content}")
    
    # Test the enhanced extraction
    mapper = SimpleMapper()
    
    print(f"\n🧪 ENHANCED EXTRACTION TEST:")
    
    try:
        extracted, confidence = mapper._extract_using_enhanced_patterns(
            variable_text, "", "", source_content
        )
        
        print(f"   Result: '{extracted}'")
        print(f"   Confidence: {confidence:.2f}")
        
        if extracted != "None" and confidence > 0:
            print(f"   ✅ SUCCESS - Template extraction working!")
            
            # Verify the extracted content makes sense
            if "University of Michigan" in extracted:
                print(f"   ✅ Contains specific entity (University of Michigan)")
            if "contract" in extracted.lower():
                print(f"   ✅ Contains core concept (contract)")
            if "premium" in extracted.lower():
                print(f"   ✅ Contains target concept (premium)")
                
        else:
            print(f"   ❌ FAILED - Still not extracting")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    # Test the helper methods directly
    print(f"\n🔧 HELPER METHOD TESTS:")
    
    # Test template detection
    has_template = mapper._has_template_content(variable_text)
    print(f"   Template content detected: {has_template}")
    
    if has_template:
        print(f"   ✅ Template detection working")
    else:
        print(f"   ❌ Template detection failed")
    
    # Test template extraction directly
    try:
        extracted_direct, confidence_direct = mapper._extract_template_content(variable_text, source_content)
        print(f"   Direct template extraction: '{extracted_direct}' (confidence: {confidence_direct:.2f})")
        
        if extracted_direct != "None":
            print(f"   ✅ Direct extraction working")
        else:
            print(f"   ❌ Direct extraction failed")
            
    except Exception as e:
        print(f"   ❌ Direct extraction error: {e}")

def test_additional_template_cases():
    """Test additional template cases to ensure robustness."""
    print(f"\n🧪 TESTING ADDITIONAL TEMPLATE CASES")
    print("=" * 70)
    
    test_cases = [
        {
            "variable": "Insert if applicable: Contact your current employer for benefit details.",
            "source": "Contact IBM Corporation for benefit details and enrollment information.",
            "description": "Simple employer replacement"
        },
        {
            "variable": "Insert if applicable: Your benefits administrator can provide more information.",
            "source": "Your HR department can provide more information about coverage options.",
            "description": "Benefits administrator → HR department"
        },
        {
            "variable": "Insert if applicable: Contact the employer or union for enrollment.",
            "source": "Contact the Teachers Union for enrollment and member services.",
            "description": "Generic union → specific union"
        }
    ]
    
    mapper = SimpleMapper()
    success_count = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {case['description']}")
        print(f"      Variable: {case['variable']}")
        print(f"      Source: {case['source']}")
        
        try:
            extracted, confidence = mapper._extract_using_enhanced_patterns(
                case['variable'], "", "", case['source']
            )
            
            print(f"      Result: '{extracted}' (confidence: {confidence:.2f})")
            
            if extracted != "None" and confidence > 0.5:
                print(f"      ✅ SUCCESS")
                success_count += 1
            else:
                print(f"      ❌ FAILED")
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")
    
    print(f"\n📊 ADDITIONAL CASES SUMMARY:")
    print(f"   Success rate: {success_count}/{len(test_cases)} ({(success_count/len(test_cases))*100:.1f}%)")

def test_template_vs_regular_extraction():
    """Test that regular extraction still works alongside template extraction."""
    print(f"\n⚖️ TESTING TEMPLATE vs REGULAR EXTRACTION")
    print("=" * 70)
    
    test_cases = [
        {
            "variable": "insert Customer Services number",
            "source": "Call Customer Service at 1-855-669-8040 for assistance.",
            "type": "regular",
            "expected": "phone number"
        },
        {
            "variable": "insert direct URL to provider directory", 
            "source": "Visit www.bcbsm.com/providers for provider information.",
            "type": "regular",
            "expected": "URL"
        },
        {
            "variable": "Insert if applicable: Contact your employer for details.",
            "source": "Contact Microsoft Corporation for details about your benefits.",
            "type": "template",
            "expected": "template content"
        }
    ]
    
    mapper = SimpleMapper()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {case['type']} extraction")
        print(f"      Variable: {case['variable']}")
        print(f"      Expected: {case['expected']}")
        
        try:
            extracted, confidence = mapper._extract_using_enhanced_patterns(
                case['variable'], "", "", case['source']
            )
            
            print(f"      Result: '{extracted}' (confidence: {confidence:.2f})")
            
            if extracted != "None" and confidence > 0:
                print(f"      ✅ {case['type'].upper()} EXTRACTION WORKING")
            else:
                print(f"      ❌ {case['type'].upper()} EXTRACTION FAILED")
                
        except Exception as e:
            print(f"      ❌ ERROR: {e}")

if __name__ == "__main__":
    test_template_extraction_fix()
    test_additional_template_cases()
    test_template_vs_regular_extraction()
    print("\n" + "=" * 70)
    print("🎯 TEMPLATE EXTRACTION FIX TEST COMPLETE")