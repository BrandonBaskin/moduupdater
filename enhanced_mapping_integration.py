#!/usr/bin/env python3
"""
Enhanced Mapping Integration
Integrates the 23-type classification system with AI agent for better extraction.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from enhanced_variable_classifier import create_enhanced_classifier, VariableType, VariableClassification
from logic_mapper_llm import classify_variable_comprehensive, call_ollama_llm_enhanced
from logging_config import logger


class EnhancedMappingEngine:
    """
    Integrates enhanced classification with AI agent for sophisticated variable extraction.
    """
    
    def __init__(self):
        self.classifier = create_enhanced_classifier()
        self.extraction_cache = {}
        
    def extract_variable_intelligently(self, variable_name: str, variable_text: str, 
                                     context_before: str, context_after: str,
                                     source_paragraphs: List[str]) -> Tuple[str, float, str]:
        """
        Extract variable using enhanced classification + AI agent integration.
        
        Returns:
            Tuple of (extracted_value, confidence, reasoning)
        """
        
        # Step 1: Enhanced Classification
        classification = classify_variable_comprehensive(variable_text, context_before, context_after)
        behavior = self.classifier.get_heuristic_behavior(classification)
        
        logger.info(f"🧠 Enhanced classification for '{variable_name}':")
        logger.info(f"   Type: {classification.variable_type.value}")
        logger.info(f"   Behavior: {behavior.get('action', 'unknown')}")
        logger.info(f"   Confidence: {classification.confidence_score:.2f}")
        
        # Step 2: Type-Specific Source Matching
        relevant_paragraphs = self._find_relevant_paragraphs_by_type(
            classification, variable_text, context_before, context_after, source_paragraphs
        )
        
        if not relevant_paragraphs:
            logger.warning(f"   ⚠️  No relevant paragraphs found for {variable_name}")
            return "None", 0.0, "No relevant source content found"
        
        # Step 3: Type-Specific Extraction
        return self._extract_by_variable_type(
            classification, behavior, variable_name, variable_text,
            context_before, context_after, relevant_paragraphs
        )
    
    def _find_relevant_paragraphs_by_type(self, classification: VariableClassification, 
                                        variable_text: str, context_before: str, context_after: str,
                                        source_paragraphs: List[str]) -> List[str]:
        """
        Find relevant paragraphs based on variable type and heuristic behavior.
        """
        var_type = classification.variable_type
        
        if var_type == VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL:
            # For conditional insertions, look for paragraphs that might contain the condition
            return self._find_conditional_relevant_paragraphs(classification, source_paragraphs)
            
        elif var_type == VariableType.INSERT_URL:
            # For URLs, look for paragraphs containing website references
            return self._find_url_relevant_paragraphs(source_paragraphs)
            
        elif var_type == VariableType.INSERT_NUMERIC_INLINE:
            # For numbers, look for paragraphs with relevant numeric content
            return self._find_numeric_relevant_paragraphs(variable_text, source_paragraphs)
            
        elif var_type in [VariableType.INSERT, VariableType.SELECT_ONE]:
            # For standard inserts, use enhanced context matching
            return self._find_context_relevant_paragraphs(
                context_before, context_after, source_paragraphs
            )
            
        else:
            # Generic fallback with improved matching
            return self._find_generic_relevant_paragraphs(
                variable_text, context_before, context_after, source_paragraphs
            )
    
    def _find_conditional_relevant_paragraphs(self, classification: VariableClassification, 
                                            source_paragraphs: List[str]) -> List[str]:
        """Find paragraphs relevant to conditional insertion variables."""
        condition = classification.condition_text.lower()
        relevant = []
        
        # Extract key terms from the condition
        condition_terms = []
        if "5% threshold" in condition or "language threshold" in condition:
            condition_terms = ["language", "threshold", "5%", "percent", "alternative"]
        elif "grandfathered" in condition:
            condition_terms = ["grandfathered", "1999", "prior", "continuously", "member"]
        elif "pace" in condition:
            condition_terms = ["pace", "program", "all-inclusive", "elderly"]
        elif "premium" in condition:
            condition_terms = ["premium", "reduction", "benefit", "cost"]
        
        # Score paragraphs based on condition relevance
        scored_paragraphs = []
        for para in source_paragraphs:
            para_lower = para.lower()
            score = 0
            
            for term in condition_terms:
                if term in para_lower:
                    score += 1
            
            if score > 0:
                scored_paragraphs.append((para, score))
        
        # Return top scoring paragraphs
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        return [para for para, score in scored_paragraphs[:3]]
    
    def _find_url_relevant_paragraphs(self, source_paragraphs: List[str]) -> List[str]:
        """Find paragraphs containing URLs or website references."""
        url_patterns = [
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9.-]+\.(com|org|gov|edu|net)[^\s]*',
            r'website',
            r'online',
            r'internet',
            r'web'
        ]
        
        relevant = []
        for para in source_paragraphs:
            for pattern in url_patterns:
                if re.search(pattern, para, re.IGNORECASE):
                    relevant.append(para)
                    break
        
        return relevant[:5]  # Limit to top 5
    
    def _find_numeric_relevant_paragraphs(self, variable_text: str, source_paragraphs: List[str]) -> List[str]:
        """Find paragraphs with numeric content relevant to the variable."""
        # Extract context from variable name
        var_lower = variable_text.lower()
        numeric_context = []
        
        if "payment" in var_lower:
            numeric_context = ["payment", "pay", "option", "method"]
        elif "month" in var_lower:
            numeric_context = ["month", "monthly", "calendar"]
        elif "day" in var_lower:
            numeric_context = ["day", "daily", "business"]
        
        relevant = []
        for para in source_paragraphs:
            # Must contain numbers
            if re.search(r'\b\d+\b', para):
                para_lower = para.lower()
                # Check for context relevance
                for context in numeric_context:
                    if context in para_lower:
                        relevant.append(para)
                        break
        
        return relevant[:3]
    
    def _find_context_relevant_paragraphs(self, context_before: str, context_after: str, 
                                        source_paragraphs: List[str]) -> List[str]:
        """Enhanced context-based paragraph matching."""
        # Extract key phrases from context
        before_words = [w.lower() for w in context_before.split() if len(w) > 3]
        after_words = [w.lower() for w in context_after.split() if len(w) > 3]
        
        scored_paragraphs = []
        for para in source_paragraphs:
            para_lower = para.lower()
            score = 0
            
            # Score based on before context
            for word in before_words:
                if word in para_lower:
                    score += 2
            
            # Score based on after context
            for word in after_words:
                if word in para_lower:
                    score += 2
            
            # Bonus for phrase matches
            if len(before_words) >= 2:
                before_phrase = " ".join(before_words[:2])
                if before_phrase in para_lower:
                    score += 5
            
            if len(after_words) >= 2:
                after_phrase = " ".join(after_words[:2])
                if after_phrase in para_lower:
                    score += 5
            
            if score > 0:
                scored_paragraphs.append((para, score))
        
        # Return top scoring paragraphs
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        return [para for para, score in scored_paragraphs[:3]]
    
    def _find_generic_relevant_paragraphs(self, variable_text: str, context_before: str, 
                                        context_after: str, source_paragraphs: List[str]) -> List[str]:
        """Generic fallback paragraph matching with improved scoring."""
        # Combine all context
        all_context = f"{context_before} {context_after}"
        context_words = [w.lower() for w in all_context.split() if len(w) > 2]
        
        scored_paragraphs = []
        for para in source_paragraphs:
            para_lower = para.lower()
            
            # Calculate word overlap
            common_words = sum(1 for word in context_words if word in para_lower)
            total_words = len(context_words)
            
            if total_words > 0:
                score = common_words / total_words
                if score > 0.2:  # At least 20% overlap
                    scored_paragraphs.append((para, score))
        
        # Return top scoring paragraphs
        scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
        return [para for para, score in scored_paragraphs[:3]]
    
    def _extract_by_variable_type(self, classification: VariableClassification, behavior: Dict[str, Any],
                                variable_name: str, variable_text: str, context_before: str, 
                                context_after: str, relevant_paragraphs: List[str]) -> Tuple[str, float, str]:
        """
        Extract variable value using type-specific logic + AI agent.
        """
        var_type = classification.variable_type
        
        # Combine the most relevant paragraphs for AI analysis
        combined_source = "\n\n".join(relevant_paragraphs[:2])  # Use top 2 paragraphs
        
        if not combined_source.strip():
            return "None", 0.0, "No relevant source content found"
        
        # Use enhanced AI extraction with type-specific prompting
        logger.info(f"   🤖 Calling enhanced AI extraction for {var_type.value}")
        extracted_value = call_ollama_llm_enhanced(
            f"{context_before} {variable_text} {context_after}",
            combined_source,
            variable_text,
            context_before,
            context_after
        )
        
        # Type-specific post-processing and confidence calculation
        confidence = self._calculate_extraction_confidence(
            classification, extracted_value, combined_source
        )
        
        reasoning = f"Enhanced {var_type.value} extraction using AI agent"
        
        # Apply type-specific validation
        if var_type == VariableType.INSERT_URL and extracted_value != "None":
            if not self._is_valid_url(extracted_value):
                logger.warning(f"   ⚠️  Invalid URL extracted: {extracted_value}")
                extracted_value = "None"
                confidence = 0.1
        
        elif var_type == VariableType.INSERT_NUMERIC_INLINE and extracted_value != "None":
            if not re.search(r'\d+', extracted_value):
                logger.warning(f"   ⚠️  No numeric content in: {extracted_value}")
                extracted_value = "None"
                confidence = 0.1
        
        logger.info(f"   ✅ Extracted: '{extracted_value}' (confidence: {confidence:.2f})")
        
        return extracted_value, confidence, reasoning
    
    def _calculate_extraction_confidence(self, classification: VariableClassification, 
                                       extracted_value: str, source_text: str) -> float:
        """Calculate confidence score for extracted value."""
        if extracted_value == "None":
            return 0.0
        
        base_confidence = classification.confidence_score
        
        # Boost confidence if extracted value appears in source
        if extracted_value.lower() in source_text.lower():
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        # Variable type specific adjustments
        var_type = classification.variable_type
        
        if var_type == VariableType.INSERT_URL:
            if self._is_valid_url(extracted_value):
                base_confidence = min(base_confidence + 0.1, 1.0)
        
        elif var_type == VariableType.INSERT_NUMERIC_INLINE:
            if re.search(r'\d+', extracted_value):
                base_confidence = min(base_confidence + 0.1, 1.0)
        
        return base_confidence
    
    def _is_valid_url(self, value: str) -> bool:
        """Validate if a value is a valid URL."""
        url_pattern = r'^https?://[^\s]+|^www\.[^\s]+|^[a-zA-Z0-9.-]+\.(com|org|gov|edu|net)'
        return bool(re.match(url_pattern, value, re.IGNORECASE))


# Factory function
def create_enhanced_mapping_engine() -> EnhancedMappingEngine:
    """Create and return an enhanced mapping engine instance."""
    return EnhancedMappingEngine()


# Example usage
if __name__ == "__main__":
    engine = create_enhanced_mapping_engine()
    
    # Test with the problematic variable from the log
    variable_name = "Plans that meet the 5% alternative language threshold insert: This document is available for free in [insert languages that meet the 5% threshold]"
    variable_text = f"[{variable_name}]"
    context_before = "Language assistance is provided at no cost."
    context_after = "Contact customer service for language help."
    
    # Mock source paragraphs
    source_paragraphs = [
        "This document is available in Spanish, which meets our 5% threshold requirement.",
        "Language assistance services are provided free of charge to members.",
        "We offer translation services for documents in multiple languages including Spanish.",
        "The plan serves areas where Spanish-speaking members represent more than 5% of enrollment."
    ]
    
    result = engine.extract_variable_intelligently(
        variable_name, variable_text, context_before, context_after, source_paragraphs
    )
    
    print(f"Extracted: {result[0]}")
    print(f"Confidence: {result[1]:.2f}")
    print(f"Reasoning: {result[2]}")