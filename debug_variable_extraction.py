#!/usr/bin/env python3
"""
Debug script to understand why variable extraction is failing
"""

import sys
import os
import re
from docx import Document
from document_parser import DocumentParser
from logic_mapper_llm import find_sentences_containing_variables, find_sentences_containing_variables_aggressive

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_variable_extraction():
    """Debug the variable extraction process."""
    
    # Test with the actual documents
    model_path = "../assets/previous/CY2025_8_PPO MA_EOC_Correcting URLs_11042024.docx"
    final_path = "../assets/previous/11.2 v15 UOM BCBSM PPO Evidence of Coverage_FINAL-77[1301].docx"
    
    print("🔍 Debugging Variable Extraction")
    print("=" * 50)
    
    # Check if files exist
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return
    
    if not os.path.exists(final_path):
        print(f"❌ Final file not found: {final_path}")
        return
    
    print(f"✅ Model file: {model_path}")
    print(f"✅ Final file: {final_path}")
    
    # Parse the model document
    parser = DocumentParser()
    model_blocks = parser.parse(model_path)
    
    print(f"\n📊 Model Document Analysis:")
    print(f"  Total blocks: {len(model_blocks)}")
    
    # Count different block types
    block_types = {}
    variables = []
    
    for block in model_blocks:
        block_type = block.get('type', 'unknown')
        block_types[block_type] = block_types.get(block_type, 0) + 1
        
        if block_type == 'variable':
            var_name = block.get('inner_text', '')
            variables.append(var_name)
    
    print(f"  Block types: {block_types}")
    print(f"  Variables found: {len(variables)}")
    
    # Show first 10 variables
    print(f"  First 10 variables:")
    for i, var in enumerate(variables[:10]):
        print(f"    {i+1}. {var}")
    
    # Test the sentence finding functions
    print(f"\n🔍 Testing Sentence Finding Functions:")
    
    # Test find_sentences_containing_variables
    sentences_with_vars = find_sentences_containing_variables(model_blocks)
    print(f"  find_sentences_containing_variables: {len(sentences_with_vars)} sentences")
    
    # Test aggressive method
    sentences_aggressive = find_sentences_containing_variables_aggressive(model_path)
    print(f"  find_sentences_containing_variables_aggressive: {len(sentences_aggressive)} sentences")
    
    # Test direct document reading
    print(f"\n📄 Direct Document Analysis:")
    doc = Document(model_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    print(f"  Total paragraphs: {len(paragraphs)}")
    
    # Count variables in paragraphs
    total_vars_in_paras = 0
    for para in paragraphs:
        vars_in_para = re.findall(r'\[([^\]]+)\]', para)
        total_vars_in_paras += len(vars_in_para)
    
    print(f"  Variables found in paragraphs: {total_vars_in_paras}")
    
    # Show some sample paragraphs with variables
    print(f"\n📝 Sample Paragraphs with Variables:")
    sample_count = 0
    for para in paragraphs:
        vars_in_para = re.findall(r'\[([^\]]+)\]', para)
        if vars_in_para and sample_count < 5:
            print(f"  Paragraph {sample_count + 1}:")
            print(f"    Variables: {vars_in_para}")
            print(f"    Text: {para[:100]}...")
            print()
            sample_count += 1
    
    # Test the aggressive function logic
    print(f"\n🔧 Testing Aggressive Function Logic:")
    aggressive_sentences = []
    
    for para in paragraphs:
        variables = re.findall(r'\[([^\]]+)\]', para)
        for var_name in variables:
            aggressive_sentences.append({
                'type': 'sentence_with_variable',
                'text': para,
                'variable': var_name,
                'variable_text': f'[{var_name}]'
            })
    
    print(f"  Manual aggressive count: {len(aggressive_sentences)}")
    
    # Show why the original function might be failing
    print(f"\n❌ Potential Issues:")
    print(f"  1. DocumentParser might not be extracting variables correctly")
    print(f"  2. Block types might not include 'variable' type")
    print(f"  3. Variable text matching might be failing")
    
    return {
        'model_blocks': len(model_blocks),
        'variables_found': len(variables),
        'sentences_with_vars': len(sentences_with_vars),
        'aggressive_sentences': len(sentences_aggressive),
        'manual_aggressive': len(aggressive_sentences),
        'total_vars_in_paras': total_vars_in_paras
    }

if __name__ == "__main__":
    results = debug_variable_extraction()
    print(f"\n📊 Summary:")
    for key, value in results.items():
        print(f"  {key}: {value}") 