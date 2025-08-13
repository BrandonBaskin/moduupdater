#!/usr/bin/env python3
"""
Test the specific [insert URL] variable through our enhanced mapping system
to see why it's not finding the provider directory URL.
"""

from enhanced_mapping_integration import create_enhanced_mapping_engine
from enhanced_variable_classifier import create_enhanced_classifier, VariableType
from logic_mapper_llm import classify_variable_comprehensive

def test_insert_url_variable():
    """Test the specific [insert URL] variable that should find the provider directory URL."""
    
    print("🌐 TESTING [INSERT URL] VARIABLE SPECIFICALLY")
    print("="*70)
    
    # The exact variable from the document
    variable_name = "insert URL"
    variable_text = f"[{variable_name}]"
    
    # Context from the document (from our debug output)
    context_before = "Get the most recent list of providers and suppliers on our website at"
    context_after = ""
    
    print(f"Variable: {variable_text}")
    print(f"Context Before: '{context_before}'")
    print(f"Context After: '{context_after}'")
    
    # Mock source paragraphs that should contain the URL
    # Based on the user's image showing www.bcbsm.com/providersmedicare
    source_paragraphs = [
        "The most recent list of providers is also available on our website at www.bcbsm.com/providersmedicare.",
        "Visit our provider directory at www.bcbsm.com/providersmedicare for the most up-to-date information.",
        "You can find current provider information on our website at www.bcbsm.com/providersmedicare",
        "Our provider network is available online at https://www.bcbsm.com/providersmedicare",
        "For provider directory, visit www.bcbsm.com/providersmedicare or call customer service.",
        "Provider information is available at bcbsm.com/providersmedicare online.",
        "Additional provider details can be found at our website www.bcbsm.com/providersmedicare",
        "The provider directory website is www.bcbsm.com/providersmedicare for member access.",
    ]
    
    print(f"\nSource paragraphs available: {len(source_paragraphs)}")
    for i, para in enumerate(source_paragraphs):
        print(f"   {i+1}: {para}")
    
    # Test the enhanced classification
    print(f"\n🧠 ENHANCED CLASSIFICATION:")
    classification = classify_variable_comprehensive(variable_text, context_before, context_after)
    print(f"   Type: {classification.variable_type.value}")
    print(f"   Confidence: {classification.confidence_score:.2f}")
    print(f"   Field ID: {classification.field_id}")
    print(f"   Expected Data Type: {classification.expected_data_type}")
    
    # Test the enhanced extraction
    print(f"\n🤖 ENHANCED EXTRACTION TEST:")
    engine = create_enhanced_mapping_engine()
    
    try:
        extracted_value, confidence, reasoning = engine.extract_variable_intelligently(
            variable_name, variable_text, context_before, context_after, source_paragraphs
        )
        
        print(f"   ✅ Extracted: '{extracted_value}'")
        print(f"   📊 Confidence: {confidence:.2f}")
        print(f"   🔍 Reasoning: {reasoning}")
        
        # Check if the extraction makes sense
        if "bcbsm.com" in extracted_value.lower() or "www." in extracted_value.lower():
            print(f"   🎉 SUCCESS: Found provider directory URL!")
        elif extracted_value == "None":
            print(f"   ❌ FAILED: No URL extracted")
            print(f"   💡 Debugging why...")
            
            # Test each source paragraph individually
            print(f"\n   🔍 Testing individual source paragraphs:")
            for i, para in enumerate(source_paragraphs):
                try:
                    test_result = engine.extract_variable_intelligently(
                        variable_name, variable_text, context_before, context_after, [para]
                    )
                    print(f"      Para {i+1}: '{test_result[0]}' (confidence: {test_result[1]:.2f})")
                except Exception as e:
                    print(f"      Para {i+1}: Error - {e}")
        else:
            print(f"   🤔 PARTIAL: Got '{extracted_value}' but expected provider directory URL")
            
    except Exception as e:
        print(f"   ❌ EXTRACTION ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test what happens with different context variations
    print(f"\n🔧 TESTING CONTEXT VARIATIONS:")
    
    context_variations = [
        {
            "before": "Get the most recent list of providers on our website at",
            "after": "",
            "description": "Simplified context"
        },
        {
            "before": "provider directory available at",
            "after": "",
            "description": "Direct provider directory context"
        },
        {
            "before": "visit our website at",
            "after": "for provider information",
            "description": "Generic website context"
        },
        {
            "before": "",
            "after": "",
            "description": "No context (worst case)"
        }
    ]
    
    for variation in context_variations:
        print(f"\n   Testing: {variation['description']}")
        print(f"      Before: '{variation['before']}'")
        print(f"      After: '{variation['after']}'")
        
        try:
            result = engine.extract_variable_intelligently(
                variable_name, variable_text, 
                variation['before'], variation['after'], 
                source_paragraphs[:3]  # Use top 3 paragraphs
            )
            print(f"      Result: '{result[0]}' (confidence: {result[1]:.2f})")
        except Exception as e:
            print(f"      Error: {e}")

def test_manual_url_patterns():
    """Test manual URL pattern detection."""
    
    print(f"\n🔍 MANUAL URL PATTERN DETECTION TEST:")
    print("="*50)
    
    # Test paragraphs
    test_paragraphs = [
        "The most recent list of providers is also available on our website at www.bcbsm.com/providersmedicare.",
        "Visit https://www.bcbsm.com/providersmedicare for provider information.",
        "Provider directory: bcbsm.com/providersmedicare",
        "See www.example.com for details",
    ]
    
    # URL patterns to test
    url_patterns = [
        r'https?://[^\s]+',
        r'www\.[^\s]+',
        r'[a-zA-Z0-9.-]+\.com[^\s]*',
        r'bcbsm\.com[^\s]*'
    ]
    
    for i, para in enumerate(test_paragraphs):
        print(f"\nParagraph {i+1}: {para}")
        for j, pattern in enumerate(url_patterns):
            import re
            matches = re.findall(pattern, para)
            print(f"   Pattern {j+1} ({pattern}): {matches}")

if __name__ == "__main__":
    try:
        print("🚀 TESTING [INSERT URL] VARIABLE EXTRACTION")
        test_insert_url_variable()
        test_manual_url_patterns()
        
        print(f"\n{'='*70}")
        print("🎯 INSERT URL TEST CONCLUSIONS:")
        print("1. If extraction worked: Enhanced system is functioning correctly")
        print("2. If extraction failed: Need to debug source paragraph matching")
        print("3. If partial results: Need to refine URL detection patterns")
        print("4. Check if source document actually contains the expected URL")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()