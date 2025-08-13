#!/usr/bin/env python3
"""
Simple Mapping Engine - No AI Calls
Fast, basic variable extraction for initial mapping step.
All AI intelligence moved to AI Clarification Wizard.
"""

import re
from typing import Dict, List, Tuple, Optional
from logging_config import logger
from enhanced_variable_classifier import create_enhanced_classifier, VariableType

class SimpleMappingEngine:
    """
    Simple, fast mapping engine with no AI calls.
    Does basic extraction and classification for speed.
    """
    
    def __init__(self):
        self.classifier = create_enhanced_classifier()
        self.processed_count = 0
        
    def extract_variable_simple(self, variable_name: str, variable_text: str, 
                              context_before: str, context_after: str,
                              source_paragraphs: List[str]) -> Tuple[str, float, str, Dict]:
        """
        Extract variable using simple patterns - NO AI CALLS.
        Returns: (extracted_value, confidence, reasoning, metadata)
        """
        
        # Enhanced classification (no AI, just pattern matching)
        classification = self.classifier.classify_variable(variable_text, context_before, context_after)
        
        # Simple extraction based on variable type
        extracted_value = self._extract_simple_value(
            variable_name, variable_text, classification, source_paragraphs, 
            context_before, context_after
        )
        
        # Basic confidence scoring
        confidence = self._calculate_simple_confidence(extracted_value, classification)
        
        # Simple reasoning
        reasoning = f"Basic {classification.variable_type.value} extraction (no AI)"
        
        # Metadata for the wizard
        metadata = {
            'enhanced_type': classification.variable_type.value,
            'behavior': 'simple_extraction',  # Simple behavior type
            'requires_ai_review': True,  # Everything needs wizard review
            'condition_text': classification.condition_text,
            'insert_text': classification.insert_text,
            'simple_extraction': True,
            'requires_user_input': classification.requires_user_input,
            'editor_instruction': classification.editor_instruction
        }
        
        self.processed_count += 1
        logger.info(f"🔧 Simple extraction: {variable_name} → {extracted_value} (confidence: {confidence:.2f})")
        
        return extracted_value, confidence, reasoning, metadata
    
    def _extract_simple_value(self, variable_name: str, variable_text: str, 
                            classification, source_paragraphs: List[str],
                            context_before: str, context_after: str) -> str:
        """
        Simple extraction without AI - just basic patterns.
        """
        
        var_type = classification.variable_type
        
        # URL variables - look for basic URL patterns
        if var_type == VariableType.INSERT_URL:
            return self._extract_simple_url(source_paragraphs)
            
        # Plan name variables - look for plan mentions
        elif 'plan name' in variable_name.lower():
            return self._extract_simple_plan_name(source_paragraphs, context_before, context_after)
            
        # Date variables - look for year patterns
        elif any(word in variable_name.lower() for word in ['year', 'date', '2025', '2026']):
            return self._extract_simple_year()
            
        # Number variables - look for common numbers
        elif any(word in variable_name.lower() for word in ['day', 'amount', 'number', 'period']):
            return self._extract_simple_number(variable_name, source_paragraphs)
            
        # Conditional variables - just return the insert text
        elif var_type == VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL:
            return classification.insert_text or "conditional content"
            
        # Phone numbers
        elif 'phone' in variable_name.lower() or 'tty' in variable_name.lower():
            return self._extract_simple_phone(source_paragraphs)
            
        # Default: return a placeholder
        else:
            return f"[{variable_name}]"
    
    def _extract_simple_url(self, source_paragraphs: List[str]) -> str:
        """Extract basic URL patterns."""
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9.-]+\.com[^\s]*'
        ]
        
        for paragraph in source_paragraphs:
            for pattern in url_patterns:
                matches = re.findall(pattern, paragraph)
                if matches:
                    url = matches[0].rstrip('.')
                    if not url.startswith('http'):
                        url = f"https://{url}" if url.startswith('www.') else f"https://www.{url}"
                    return url
        
        return "https://www.example.com"
    
    def _extract_simple_plan_name(self, source_paragraphs: List[str], 
                                context_before: str, context_after: str) -> str:
        """Extract basic plan name patterns."""
        
        # Look for common plan patterns
        plan_patterns = [
            r'Medicare Plus [^.]+',
            r'Blue Cross [^.]+',
            r'[A-Z][a-z]+ [A-Z][a-z]+ [A-Z]{3}',  # Like "Medicare Plus PPO"
            r'[A-Z][A-Z]+ [A-Z][a-z]+',  # Like "PPO Plan"
        ]
        
        # Check context first
        for context in [context_before, context_after]:
            for pattern in plan_patterns:
                matches = re.findall(pattern, context)
                if matches:
                    return matches[0]
        
        # Check source paragraphs
        for paragraph in source_paragraphs[:5]:  # Just check first 5
            for pattern in plan_patterns:
                matches = re.findall(pattern, paragraph)
                if matches:
                    return matches[0]
        
        return "Medicare Plan"
    
    def _extract_simple_year(self) -> str:
        """Extract or default to current year."""
        return "2025"
    
    def _extract_simple_number(self, variable_name: str, source_paragraphs: List[str]) -> str:
        """Extract simple numbers based on variable type."""
        
        # Common defaults based on variable name
        if 'day' in variable_name.lower():
            if 'grace' in variable_name.lower():
                return "30"
            return "15"
        elif 'amount' in variable_name.lower():
            return "$0"
        elif 'period' in variable_name.lower():
            return "30"
        elif 'number' in variable_name.lower():
            return "1"
        else:
            return "0"
    
    def _extract_simple_phone(self, source_paragraphs: List[str]) -> str:
        """Extract basic phone patterns."""
        phone_patterns = [
            r'\d{3}-\d{3}-\d{4}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{10}'
        ]
        
        for paragraph in source_paragraphs[:10]:  # Check first 10 paragraphs
            for pattern in phone_patterns:
                matches = re.findall(pattern, paragraph)
                if matches:
                    return matches[0]
        
        return "1-800-XXX-XXXX"
    
    def _calculate_simple_confidence(self, extracted_value: str, classification) -> float:
        """Calculate basic confidence score."""
        
        # Default confidence levels
        if extracted_value.startswith('[') and extracted_value.endswith(']'):
            return 0.1  # Placeholder values
        elif extracted_value in ["https://www.example.com", "Medicare Plan", "1-800-XXX-XXXX"]:
            return 0.3  # Default values
        elif classification.variable_type in [VariableType.INSERT_URL, VariableType.INSERT]:
            return 0.7  # Structured extractions
        else:
            return 0.5  # Basic extractions

def create_simple_mapping_engine():
    """Factory function to create a simple mapping engine."""
    return SimpleMappingEngine()