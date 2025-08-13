#!/usr/bin/env python3
"""
Debug Provider Directory Specific Issue
Find the exact paragraph with the provider directory URL and see why it's not being detected.
"""

import re
from docx import Document
from document_parser import DocumentParser

def debug_provider_directory():
    """Debug the specific provider directory issue."""
    
    print("🌐 PROVIDER DIRECTORY SPECIFIC DEBUG")
    print("="*70)
    
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    
    try:
        doc = Document(model_path)
        
        # Search for the specific text from the image
        target_phrases = [
            "most recent list of providers",
            "available on our website",
            "www.bcbsm.com/providersmedicare",
            "bcbsm.com/providersmedicare"
        ]
        
        print("🔍 Searching for provider directory content...")
        
        found_paragraphs = []
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if not text:
                continue
                
            # Check if this paragraph contains the provider directory content
            for phrase in target_phrases:
                if phrase.lower() in text.lower():
                    found_paragraphs.append({
                        "index": i,
                        "text": text,
                        "phrase_found": phrase,
                        "variables": list(re.findall(r'\[([^\]]+)\]', text)),
                        "urls": list(re.findall(r'www\.[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?', text)),
                        "has_insert_url": "[insert url]" in text.lower()
                    })
                    break
        
        print(f"Found {len(found_paragraphs)} relevant paragraphs:")
        
        for para_info in found_paragraphs:
            print(f"\n📍 Paragraph {para_info['index']}:")
            print(f"   Triggered by: '{para_info['phrase_found']}'")
            print(f"   Text: '{para_info['text']}'")
            print(f"   Variables found: {para_info['variables']}")
            print(f"   URLs found: {para_info['urls']}")
            print(f"   Has [insert URL]: {para_info['has_insert_url']}")
            
            # Analyze the structure
            if para_info['urls'] and not para_info['has_insert_url']:
                print(f"   ⚠️  ISSUE: Contains URL but no [insert URL] variable!")
                print(f"       The URL '{para_info['urls'][0]}' is hardcoded in the text")
                print(f"       Expected format: 'available on our website at [insert URL]'")
                print(f"       Actual format: 'available on our website at {para_info['urls'][0]}'")
            elif para_info['variables']:
                print(f"   ✅ Has proper variables: {para_info['variables']}")
            else:
                print(f"   ❓ No variables or URLs detected")
        
        # Also check what the mapping system would see
        print(f"\n🔍 WHAT THE MAPPING SYSTEM SEES:")
        parser = DocumentParser()
        parsed_blocks = parser.parse(model_path)
        
        # Find blocks related to provider directory
        provider_blocks = []
        for block in parsed_blocks:
            block_text = block.get('text', '').lower()
            inner_text = block.get('inner_text', '').lower()
            
            if any(phrase.lower() in block_text for phrase in target_phrases):
                provider_blocks.append(block)
            elif any(phrase.lower() in inner_text for phrase in target_phrases):
                provider_blocks.append(block)
        
        print(f"Found {len(provider_blocks)} blocks related to provider directory:")
        for i, block in enumerate(provider_blocks):
            print(f"\n   Block {i+1}:")
            print(f"      Type: {block.get('type', 'unknown')}")
            print(f"      Variable: [{block.get('inner_text', '')}]")
            print(f"      Context: {block.get('text', '')[:100]}...")
        
        # Specific solution recommendation
        print(f"\n💡 SOLUTION ANALYSIS:")
        
        hardcoded_urls = []
        for para_info in found_paragraphs:
            if para_info['urls'] and not para_info['has_insert_url']:
                hardcoded_urls.append(para_info)
        
        if hardcoded_urls:
            print(f"❌ PROBLEM CONFIRMED: {len(hardcoded_urls)} paragraphs have hardcoded URLs")
            print(f"   This means the source document needs to be corrected to use [insert URL] variables")
            print(f"   OR we need enhanced detection to find hardcoded URLs and suggest them")
            
            print(f"\n🔧 POSSIBLE SOLUTIONS:")
            print(f"   1. Update source document to use [insert URL] instead of hardcoded URLs")
            print(f"   2. Add enhanced pattern detection to find hardcoded URLs")
            print(f"   3. Create a post-processing step to suggest URLs for [insert URL] variables")
            
            # Test solution 2: Enhanced pattern detection
            print(f"\n🧪 TESTING ENHANCED PATTERN DETECTION:")
            for para_info in hardcoded_urls:
                text = para_info['text']
                # Try to detect patterns like "website at URL"
                url_patterns = [
                    r'website\s+at\s+(www\.[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?)',
                    r'visit\s+(www\.[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?)',
                    r'at\s+(www\.[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?:/[^\s]*)?)'
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"      Pattern '{pattern}' found: {matches}")
                        print(f"      Could suggest: Replace with 'website at [insert URL]'")
                        print(f"      Extracted URL for [insert URL]: '{matches[0]}'")
        else:
            print(f"✅ No hardcoded URL issues found")
            
        return len(found_paragraphs), len(provider_blocks), len(hardcoded_urls)
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0

if __name__ == "__main__":
    try:
        found_paras, provider_blocks, hardcoded_urls = debug_provider_directory()
        
        print(f"\n{'='*70}")
        print("🎯 PROVIDER DIRECTORY DEBUG SUMMARY:")
        print(f"   Found paragraphs: {found_paras}")
        print(f"   Provider blocks: {provider_blocks}")  
        print(f"   Hardcoded URLs: {hardcoded_urls}")
        
        if hardcoded_urls > 0:
            print(f"\n❌ ROOT CAUSE IDENTIFIED:")
            print(f"   The source document has hardcoded URLs instead of [insert URL] variables")
            print(f"   This is why our enhanced extraction can't find the URL - there's no variable to extract!")
            
            print(f"\n🚀 NEXT STEPS:")
            print(f"   1. Either update the source document format")
            print(f"   2. Or implement enhanced URL detection for hardcoded URLs")
            print(f"   3. Or create a mapping between [insert URL] variables and nearby hardcoded URLs")
        else:
            print(f"✅ No issues with provider directory URL handling")
            
    except Exception as e:
        print(f"❌ Provider directory debug failed: {e}")