#!/usr/bin/env python3
"""
Quick demo of the Enhanced CMS Variable Classification System
"""

from enhanced_variable_classifier import create_enhanced_classifier
from logic_mapper_llm import classify_variable_comprehensive

print('🧠 ENHANCED CMS VARIABLE CLASSIFICATION SYSTEM - LIVE DEMO')
print('='*60)

classifier = create_enhanced_classifier()

# Demo variables from the heuristics guide
demo_vars = [
    '[insert 2025 plan name]',
    '[select one: Yes/No]', 
    '[Insert if applicable: URLs, notices]',
    '[Plans with no premium, omit: monthly plan premium,]',
    '[Remove terms as needed to reflect plan benefits]',
    '[insert URL]',
    '[insert number of payment options]'
]

for var in demo_vars:
    classification = classify_variable_comprehensive(var)
    behavior = classifier.get_heuristic_behavior(classification)
    
    print(f'\nVariable: {var}')
    print(f'Type: {classification.variable_type.value}')
    print(f'Field ID: {classification.field_id}')
    print(f'Confidence: {classification.confidence_score:.2f}')
    print(f'Behavior: {behavior.get("action", "unknown")}')
    if classification.editor_instruction:
        print('⚠️  Editor Instruction')
    if classification.requires_user_input:
        print('👤 User Input Required')

print('\n✅ Enhanced Classification System: ACTIVE')
print('📱 Main GUI Application: Starting...')
print('🎉 Ready to process CMS variables with 23-type classification!')