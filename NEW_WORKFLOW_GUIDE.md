# CMS Model Updater - New Workflow Guide

## Overview

The CMS Model Updater has been enhanced with a new workflow that ensures models are mapped to each other BEFORE building the wizard, and the wizard pulls suggestions from the "Map to Final" phase to pre-populate responses.

## New Workflow Steps

### 1. Load Last Year Model (DOCX)
- Load the previous year's model document
- This contains the template structure and variables from last year

### 2. Load Last Year Final (DOCX)  
- Load the filled/final document from last year
- This contains the actual values that were used to fill the template

### 3. Map Final to Model
- Extract values from the final document and map them to the model variables
- This creates the "answer key" with actual values from last year
- Results are saved to `database/answers.json`

### 4. Load Current Year Model (DOCX)
- Load the current year's model document
- This contains the updated template structure and variables

### 5. Map Models to Each Other ⭐ **NEW STEP**
- Intelligently map variables between last year's model and current year's model
- Handle year updates (2025 → 2026), static variables, and complex relationships
- Create wizard suggestions based on the extracted values from step 3
- Results are saved to `model_mapping_results.json`

### 6. Build Wizard Tree
- Parse the current year model to create the wizard structure
- **Pre-populate with suggestions from step 5**
- Save wizard tree to `database/wizard.json`

### 7. Run Wizard
- Launch the interactive wizard with pre-populated suggestions
- Users can accept, modify, or reject suggestions
- Generate the final filled template

## Key Improvements

### 🔄 **Model Mapping Before Wizard Building**
- **Before**: Wizard was built first, then suggestions were loaded separately
- **After**: Models are mapped to each other first, then wizard is built with integrated suggestions

### 📋 **Pre-populated Suggestions**
- **Before**: Wizard started with empty fields
- **After**: Wizard starts with intelligent suggestions from model mapping

### 🎯 **Intelligent Variable Mapping**
- Handles year updates automatically (2025 → 2026)
- Preserves static variables (phone numbers, plan names)
- Maps complex relationships between different variable formats

### 💾 **Persistent Learning**
- The system learns from each mapping session
- Improves accuracy over time
- Stores patterns in `learning_data/` directory

## Technical Details

### Model Mapping Process

1. **Variable Extraction**: Extract all variables from both models
2. **Fuzzy Matching**: Use intelligent heuristics to match variables
3. **Year Updates**: Automatically update year-specific variables
4. **Suggestion Creation**: Create wizard suggestions based on extracted values
5. **Validation**: Validate mapping quality and coverage

### Wizard Integration

The wizard now receives suggestions in this format:
```json
{
  "insert plan name": "Updated Plan Name 2026",
  "insert phone number": "1-800-PLAN-2026", 
  "insert languages that meet the 5% threshold": "Spanish, French, German"
}
```

### File Structure

```
cms_model_update/
├── database/
│   ├── answers.json          # Extracted values from final document
│   └── wizard.json          # Wizard tree structure
├── learning_data/           # Learning system data
├── model_mapping_results.json # Model mapping results
└── main.py                  # Main application entry point
```

## Usage Instructions

### Starting the Application
```bash
python main.py
```

### Workflow Execution
1. Click "1. Load Last Year Model (DOCX)"
2. Click "2. Load Last Year Final (DOCX)" 
3. Click "3. Map Final to Model" (extracts values)
4. Click "4. Load Current Year Model (DOCX)"
5. Click "5. Map Models to Each Other" ⭐ **NEW**
6. Click "6. Build Wizard Tree" (with suggestions)
7. Click "7. Run Wizard" (pre-populated)

### Additional Features

- **Learning Stats**: Click "🧠 Learning Stats" to view system learning progress
- **Validate Mapping**: Click "🔍 Validate Model Mapping" to check mapping quality
- **Progress Tracking**: Real-time progress bar and status updates

## Benefits

### 🚀 **Improved Efficiency**
- Pre-populated wizard reduces manual entry
- Intelligent suggestions reduce errors
- Faster template completion

### 🎯 **Better Accuracy**
- Model mapping ensures consistency
- Learning system improves over time
- Validation prevents mapping errors

### 🔄 **Enhanced Workflow**
- Logical step progression
- Clear status indicators
- Comprehensive error handling

## Troubleshooting

### Common Issues

1. **"No wizard steps found"**
   - Ensure current model has logic fields (variables, options, conditionals)
   - Check that the DOCX file is properly formatted

2. **"Model mapping failed"**
   - Verify both models are loaded
   - Check that "Map Final to Model" was completed first
   - Ensure files are accessible and not corrupted

3. **"No suggestions available"**
   - Complete "Map Final to Model" step first
   - Check that the final document contains actual values (not template variables)

### Debug Information

- Check `cms_wizard_log.txt` for detailed logs
- Review `model_mapping_results.json` for mapping details
- Examine `learning_data/` for learning system status

## Future Enhancements

- **Batch Processing**: Process multiple documents simultaneously
- **Advanced Mapping**: More sophisticated variable matching algorithms
- **Export Options**: Additional output formats (PDF, HTML)
- **Collaboration**: Multi-user support with shared learning data

---

*This new workflow ensures that the CMS Model Updater provides intelligent, pre-populated suggestions while maintaining the flexibility for users to customize as needed.* 