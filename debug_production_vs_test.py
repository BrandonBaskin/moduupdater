#!/usr/bin/env python3
"""
Debug Production vs Test Discrepancy
Compare what the production system is actually processing vs. our test scenarios.
"""

import json
from pathlib import Path
from document_parser import DocumentParser
from enhanced_mapping_integration import create_enhanced_mapping_engine

def debug_production_data():
    """Debug what the production system is actually processing."""
    
    print("🔍 PRODUCTION VS TEST DEBUGGING")
    print("="*70)
    
    # Check recent mapping results
    results_file = "model_mapping_results.json"
    if Path(results_file).exists():
        print(f"📊 Found recent mapping results: {results_file}")
        
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            print(f"   Total results: {len(results)}")
            
            # Look for URL-related variables
            url_variables = []
            provider_variables = []
            
            for result in results:
                var_name = result.get('variable', '').lower()
                extracted_value = result.get('extracted_value', '')
                
                if 'url' in var_name:
                    url_variables.append(result)
                elif 'provider' in var_name:
                    provider_variables.append(result)
            
            print(f"\n🌐 URL-related variables found: {len(url_variables)}")
            for var in url_variables:
                print(f"   Variable: '{var.get('variable', 'unknown')}'")
                print(f"   Extracted: '{var.get('extracted_value', 'None')}'")
                print(f"   Source: {var.get('source', 'unknown')}")
                print(f"   Confidence: {var.get('confidence', 0.0)}")
                print()
            
            print(f"🏥 Provider-related variables found: {len(provider_variables)}")
            for var in provider_variables[:5]:  # Show first 5
                print(f"   Variable: '{var.get('variable', 'unknown')}' -> '{var.get('extracted_value', 'None')}'")
            
            # Check if our specific insert URL variable is there
            insert_url_vars = [v for v in results if 'insert url' in v.get('variable', '').lower()]
            print(f"\n🎯 'insert URL' variables specifically: {len(insert_url_vars)}")
            
            for var in insert_url_vars:
                print(f"   Variable: '{var.get('variable', '')}'")
                print(f"   Extracted: '{var.get('extracted_value', '')}'")
                print(f"   Enhanced Type: {var.get('enhanced_type', 'unknown')}")
                print(f"   Confidence: {var.get('confidence', 0.0)}")
                print(f"   Source: {var.get('source', 'unknown')}")
                print(f"   Before Context: '{var.get('before_context', '')}'")
                print(f"   After Context: '{var.get('after_context', '')}'")
                print()
                
                # This is the key question: what was the source data?
                if var.get('extracted_value') == 'None':
                    print(f"   ❌ ISSUE: This variable extracted 'None' in production!")
                elif 'bcbsm.com' in var.get('extracted_value', ''):
                    print(f"   ✅ SUCCESS: Found provider directory URL in production")
                else:
                    print(f"   🤔 UNEXPECTED: Got '{var.get('extracted_value')}' instead of provider URL")
            
        except Exception as e:
            print(f"   ❌ Error reading results: {e}")
    else:
        print(f"❌ No recent mapping results found at {results_file}")
    
    # Check extracted values
    extracted_file = "extracted_values.json"
    if Path(extracted_file).exists():
        print(f"\n📋 Checking extracted values: {extracted_file}")
        
        try:
            with open(extracted_file, 'r') as f:
                extracted = json.load(f)
            
            print(f"   Total extracted variables: {len(extracted)}")
            
            # Look for URL variables
            url_keys = [k for k in extracted.keys() if 'url' in k.lower()]
            print(f"   URL-related keys: {len(url_keys)}")
            
            for key in url_keys:
                value = extracted[key]
                print(f"      '{key}' -> '{value}'")
                
                if 'bcbsm.com' in str(value):
                    print(f"         ✅ Contains provider directory URL")
                elif value == 'None':
                    print(f"         ❌ No value extracted")
                else:
                    print(f"         🤔 Unexpected value")
                    
        except Exception as e:
            print(f"   ❌ Error reading extracted values: {e}")
    else:
        print(f"❌ No extracted values found at {extracted_file}")

def debug_document_paths():
    """Check what document paths are being used."""
    
    print(f"\n📁 DOCUMENT PATH DEBUGGING")
    print("="*50)
    
    # Common document paths from the codebase
    possible_paths = [
        "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx",
        "../ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx",
        "assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx",
        "DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    ]
    
    print("Checking for source documents:")
    
    for path in possible_paths:
        path_obj = Path(path)
        if path_obj.exists():
            print(f"   ✅ Found: {path}")
            try:
                # Quick variable count
                parser = DocumentParser()
                blocks = parser.parse(str(path_obj))
                var_blocks = [b for b in blocks if b.get('type') == 'variable']
                print(f"      Variables: {len(var_blocks)}")
                
                # Check for insert URL specifically
                insert_url_blocks = [b for b in var_blocks if 'insert url' in b.get('inner_text', '').lower()]
                print(f"      Insert URL blocks: {len(insert_url_blocks)}")
                
            except Exception as e:
                print(f"      ❌ Error parsing: {e}")
        else:
            print(f"   ❌ Missing: {path}")

def debug_source_content():
    """Check what source content is available for extraction."""
    
    print(f"\n📄 SOURCE CONTENT DEBUGGING")
    print("="*50)
    
    # The user mentioned they see the URL in the image, so let's check if it exists in source
    # We need to identify what source document is being used for extraction
    
    # Check for recent source files that might contain the provider URL
    possible_source_files = [
        "cms_answer_key_lastyear.json",
        "extracted_values.json", 
        "model_mapping_results.json"
    ]
    
    print("Searching for provider directory URLs in source files:")
    
    for file_name in possible_source_files:
        if Path(file_name).exists():
            print(f"\n   📁 Checking {file_name}:")
            
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Search for various URL patterns
                import re
                url_patterns = [
                    r'bcbsm\.com[^\s]*',
                    r'www\.bcbsm\.com[^\s]*',
                    r'https?://[^\s]*bcbsm[^\s]*',
                    r'providersmedicare',
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        print(f"      Pattern '{pattern}': {len(matches)} matches")
                        for match in matches[:3]:  # Show first 3
                            print(f"         {match}")
                
            except Exception as e:
                print(f"      ❌ Error reading: {e}")
        else:
            print(f"   ❌ Missing: {file_name}")

if __name__ == "__main__":
    try:
        debug_production_data()
        debug_document_paths()
        debug_source_content()
        
        print(f"\n{'='*70}")
        print("🎯 PRODUCTION DEBUGGING CONCLUSIONS:")
        print("1. Check if production is using different source documents")
        print("2. Verify the extraction pipeline is using enhanced mapping")
        print("3. Look for caching issues with old results")
        print("4. Confirm source content actually contains expected URLs")
        print("\n💡 NEXT STEPS:")
        print("1. Run fresh mapping with enhanced system")
        print("2. Clear any cached results")
        print("3. Verify source document content")
        
    except Exception as e:
        print(f"❌ Production debugging failed: {e}")
        import traceback
        traceback.print_exc()