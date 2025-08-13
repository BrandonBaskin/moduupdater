#!/usr/bin/env python3
"""
Debug Enhanced Context Extraction Only
Isolate the enhanced context extraction to find the exact error
"""

from enhanced_document_context import create_enhanced_document_context_extractor

def debug_enhanced_context():
    """Debug just the enhanced context extraction."""
    
    print("🔍 DEBUGGING ENHANCED CONTEXT EXTRACTION")
    print("=" * 50)
    
    model_path = "C:/Users/brand/Downloads/project/ModUpate/assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    
    try:
        print(f"📄 Testing document: {model_path}")
        
        # Create extractor
        print("1. Creating enhanced document context extractor...")
        context_extractor = create_enhanced_document_context_extractor()
        print("   ✅ Extractor created successfully")
        
        # Test extraction
        print("2. Extracting document structure...")
        variable_contexts = context_extractor.extract_document_structure(model_path)
        print(f"   ✅ Extraction successful! Found {len(variable_contexts)} variable contexts")
        
        # Show first few results
        print("\n📊 FIRST 5 VARIABLE CONTEXTS:")
        for i, (var_name, context) in enumerate(list(variable_contexts.items())[:5]):
            print(f"   {i+1}. {var_name}")
            print(f"      Chapter: {context.chapter_title}")
            print(f"      Section: {context.section_title}")
            print(f"      Page: {context.page_estimate}")
            if context.full_paragraph:
                preview = context.full_paragraph[:100] + "..." if len(context.full_paragraph) > 100 else context.full_paragraph
                print(f"      Paragraph: {preview}")
            print()
        
        return variable_contexts
        
    except Exception as e:
        print(f"❌ Error during enhanced context extraction: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    contexts = debug_enhanced_context()