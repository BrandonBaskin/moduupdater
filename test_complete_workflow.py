#!/usr/bin/env python3
"""
Test script for the complete workflow:
1. Extract variables from last year's final document
2. Map variables between last year and current year models
3. Create wizard suggestions
4. Validate the mapping
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_workflow():
    """Test the complete workflow from extraction to wizard creation."""
    
    print("🧪 Testing Complete CMS Model Updater Workflow")
    print("=" * 60)
    
    # File paths
    last_year_model = "../assets/previous/CY2025_8_PPO MA_EOC_Correcting URLs_11042024.docx"
    last_year_final = "../assets/previous/11.2 v15 UOM BCBSM PPO Evidence of Coverage_FINAL-77[1301].docx"
    current_year_model = "../assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx"
    
    # Check if files exist
    for path in [last_year_model, last_year_final, current_year_model]:
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return False
    
    print("✅ All required files found")
    
    try:
        # Step 1: Extract variables from last year's final document
        print("\n📋 Step 1: Extracting variables from last year's final document...")
        from logic_mapper_llm import LogicMapper
        
        mapper = LogicMapper()
        
        # Parse the model document
        from document_parser import DocumentParser
        parser = DocumentParser()
        model_blocks = parser.parse(last_year_model)
        
        print(f"📊 Found {len(model_blocks)} blocks in model document")
        
        # Extract variables
        def progress_callback(progress):
            print(f"🔄 Progress: {progress:.1f}%")
        
        def log_callback(message):
            print(f"📝 {message}")
        
        mapping, source_paragraphs = mapper.map_final_to_model(
            model_blocks, last_year_final, progress_callback, log_callback
        )
        
        successful_extractions = len([v for v in mapping.values() if v and v.strip()])
        print(f"✅ Extracted {successful_extractions}/{len(mapping)} variables successfully")
        
        # Step 2: Map variables between models
        print("\n🔄 Step 2: Mapping variables between last year and current year models...")
        from model_mapper import ModelVariableMapper
        
        model_mapper = ModelVariableMapper()
        variable_mapping = model_mapper.map_variables_between_models(
            last_year_model, current_year_model, log_callback
        )
        
        print(f"✅ Mapped {len(variable_mapping)} variables between models")
        
        # Step 3: Create wizard suggestions
        print("\n💡 Step 3: Creating wizard suggestions...")
        wizard_suggestions = model_mapper.create_wizard_suggestions(
            last_year_model, current_year_model, mapping, log_callback
        )
        
        print(f"✅ Created {len(wizard_suggestions)} wizard suggestions")
        
        # Step 4: Validate the mapping
        print("\n🔍 Step 4: Validating the mapping...")
        validation = model_mapper.validate_mapping(
            variable_mapping, last_year_model, current_year_model
        )
        
        print(f"📊 Validation Results:")
        print(f"  • Coverage: {validation['mapping_coverage']*100:.1f}%")
        print(f"  • Mapped: {validation['mapped_variables']}/{validation['total_old_variables']}")
        print(f"  • Unmapped old: {len(validation['unmapped_old'])}")
        print(f"  • Unmapped new: {len(validation['unmapped_new'])}")
        
        # Save results
        results = {
            'extracted_values': mapping,
            'variable_mapping': variable_mapping,
            'wizard_suggestions': wizard_suggestions,
            'validation': validation,
            'timestamp': str(datetime.now())
        }
        
        with open('complete_workflow_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 Complete workflow test successful!")
        print(f"💾 Results saved to 'complete_workflow_results.json'")
        
        # Show summary
        print(f"\n📋 Summary:")
        print(f"  • Variables extracted: {successful_extractions}")
        print(f"  • Variables mapped: {len(variable_mapping)}")
        print(f"  • Wizard suggestions: {len(wizard_suggestions)}")
        print(f"  • Mapping coverage: {validation['mapping_coverage']*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_workflow()
    sys.exit(0 if success else 1) 