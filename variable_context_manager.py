#!/usr/bin/env python3
"""
Variable Context Manager
Store and retrieve enhanced context for each variable (VPX)
"""

import json
import os
from typing import Dict, Optional
from enhanced_document_context import create_enhanced_document_context_extractor, DocumentContext

class VariableContextManager:
    """Manages enhanced context storage and retrieval for variables."""
    
    def __init__(self):
        self.variable_contexts: Dict[str, str] = {}
        self.context_extractor = None
        
    def extract_and_store_contexts(self, model_path: str) -> bool:
        """Extract enhanced contexts for all variables and store them."""
        try:
            print(f"📄 Extracting contexts from: {model_path}")
            
            # Create extractor
            self.context_extractor = create_enhanced_document_context_extractor()
            
            # Extract raw contexts
            raw_contexts = self.context_extractor.extract_document_structure(model_path)
            print(f"📊 Extracted {len(raw_contexts)} variable contexts")
            
            # Convert to formatted text for storage
            self.variable_contexts = {}
            
            for var_name, context in raw_contexts.items():
                try:
                    # Format context for display
                    formatted_context = self.context_extractor.format_context_for_display(context, var_name)
                    self.variable_contexts[var_name] = formatted_context
                except Exception as e:
                    print(f"⚠️  Error formatting context for {var_name}: {e}")
                    # Fallback to basic context
                    self.variable_contexts[var_name] = f"Variable: {var_name}\nFull Paragraph: {context.full_paragraph}"
            
            print(f"✅ Successfully stored {len(self.variable_contexts)} formatted contexts")
            return True
            
        except Exception as e:
            print(f"❌ Error extracting contexts: {e}")
            return False
    
    def get_context_for_variable(self, var_name: str) -> str:
        """Get the enhanced context for a specific variable."""
        
        # Try exact match first
        if var_name in self.variable_contexts:
            return self.variable_contexts[var_name]
        
        # Try with brackets if not already present
        var_with_brackets = f"[{var_name}]" if not var_name.startswith('[') else var_name
        if var_with_brackets in self.variable_contexts:
            return self.variable_contexts[var_with_brackets]
        
        # Try without brackets if they are present
        var_without_brackets = var_name[1:-1] if var_name.startswith('[') and var_name.endswith(']') else var_name
        bracketed_version = f"[{var_without_brackets}]"
        if bracketed_version in self.variable_contexts:
            return self.variable_contexts[bracketed_version]
        
        # Fallback
        return f"❌ No enhanced context available for: {var_name}\n\nThis variable was not found in the document context extraction."
    
    def get_context_stats(self) -> Dict[str, int]:
        """Get statistics about stored contexts."""
        return {
            'total_variables': len(self.variable_contexts),
            'enhanced_contexts': sum(1 for ctx in self.variable_contexts.values() if '📍 DOCUMENT LOCATION' in ctx),
            'basic_contexts': sum(1 for ctx in self.variable_contexts.values() if '📍 DOCUMENT LOCATION' not in ctx)
        }
    
    def save_contexts_to_file(self, filepath: str) -> bool:
        """Save contexts to a JSON file for debugging."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.variable_contexts, f, indent=2, ensure_ascii=False)
            print(f"💾 Contexts saved to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving contexts: {e}")
            return False

# Global instance for use across the application
_global_context_manager = None

def get_global_context_manager() -> VariableContextManager:
    """Get or create the global context manager instance."""
    global _global_context_manager
    if _global_context_manager is None:
        _global_context_manager = VariableContextManager()
    return _global_context_manager

def initialize_contexts_for_document(model_path: str) -> bool:
    """Initialize contexts for a document using the global manager."""
    manager = get_global_context_manager()
    return manager.extract_and_store_contexts(model_path)

def get_context_for_variable(var_name: str) -> str:
    """Get context for a variable using the global manager."""
    manager = get_global_context_manager()
    return manager.get_context_for_variable(var_name)