# logic_mapper_llm.py

import re
import requests
import subprocess
import time
import os
import json
from typing import List, Dict, Tuple, Optional
from config import Config
from docx import Document
from document_parser import DocumentParser
from logging_config import logger
from learning_persistence import LearningPersistence
from ollama_manager import get_ollama_manager, start_ollama_persistent
from variable_utils import extract_all_variables
from enhanced_variable_classifier import create_enhanced_classifier, VariableType, VariableClassification

try:
    from fuzzywuzzy import process
except ImportError:
    process = None

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:latest"   # Use the correct model name

def extract_context_aware_variables(text: str) -> List[Tuple[str, str, int, int, str]]:
    """
    Extract variables with their surrounding context for better matching.
    Returns: (variable_name, full_match, start, end, context_before, context_after)
    """
    variables = []
    pattern = r'\[([^\]]+)\]'
    
    for match in re.finditer(pattern, text):
        var_name = match.group(1).strip()
        start, end = match.span()
        
        # Get surrounding context (like yellow highlights in the image)
        context_before = text[max(0, start-100):start].strip()
        context_after = text[end:min(len(text), end+100)].strip()
        
        # Clean up context to get meaningful phrases
        context_before = re.sub(r'\s+', ' ', context_before).strip()
        context_after = re.sub(r'\s+', ' ', context_after).strip()
        
        variables.append((var_name, match.group(0), start, end, context_before, context_after))
    
    return variables


# Enhanced variable classification using the comprehensive heuristics guide
_enhanced_classifier = create_enhanced_classifier()

def classify_variable_comprehensive(variable_text: str, context_before: str = "", context_after: str = "") -> VariableClassification:
    """
    Classify a variable using the enhanced 23-type classification system from the CMS heuristics guide.
    
    Args:
        variable_text: The full bracketed variable text
        context_before: Text appearing before the variable
        context_after: Text appearing after the variable
        
    Returns:
        VariableClassification with detailed type information and metadata
    """
    return _enhanced_classifier.classify_variable(variable_text, context_before, context_after)

def classify_variable_type(variable_name: str) -> str:
    """
    Legacy function for backward compatibility.
    Maps new comprehensive types to old simple types.
    """
    # Use enhanced classification but map to old type names for compatibility
    classification = classify_variable_comprehensive(f"[{variable_name}]")
    
    # Map new types to old types for backward compatibility
    type_mapping = {
        VariableType.INSERT: 'input',
        VariableType.INSERT_URL: 'input',
        VariableType.INSERT_NUMERIC_INLINE: 'input',
        VariableType.INSERT_PLAN_SPECIFICS_COMPOSITE: 'input',
        VariableType.SELECT_ONE: 'option_select',
        VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT: 'option_select',
        VariableType.IF_APPLICABLE: 'conditional',
        VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL: 'conditional',
        VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT: 'conditional',
        VariableType.IF_APPLICABLE_NESTED_MODIFIER: 'conditional',
        VariableType.IF_APPLICABLE_PARALLEL_REFERENCE: 'conditional',
        VariableType.PERMISSIVE_CONDITIONAL_INSERT: 'conditional',
        VariableType.REGULATORY_CONDITIONAL_INSERT: 'conditional',
        VariableType.INSTRUCTIONAL_CROSS_REFERENCE_REQUIREMENT: 'conditional',
        VariableType.DELETE_IF: 'static',
        VariableType.INSTRUCTIONAL_STRUCTURAL_DELETION: 'static',
        VariableType.INSTRUCTIONAL_CLAUSE_OMISSION: 'static',
        VariableType.INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH: 'static',
        VariableType.INSTRUCTIONAL_INLINE_DELETION: 'static',
        VariableType.OPTIONAL: 'conditional',
        VariableType.INSTRUCTION_ONLY: 'static',
        VariableType.COMPLEX_STRUCTURAL_INSERT: 'input',
        VariableType.FREEFORM: 'unknown'
    }
    
    return type_mapping.get(classification.variable_type, 'unknown')


def find_paragraph_by_content_similarity(model_sentence: str, source_paragraphs: List[str]) -> str:
    """
    Find the best matching paragraph using content similarity (like solving a cipher).
    This is the first step - find the right "section" of the document.
    """
    if not source_paragraphs:
        return ""
    
    # Extract key content words from model sentence (ignore variables)
    model_words = re.sub(r'\[[^\]]*\]', '', model_sentence).lower().split()
    model_words = [w for w in model_words if len(w) > 2]  # Filter out short words
    
    best_match = ""
    best_score = 0
    
    for para in source_paragraphs:
        para_lower = para.lower()
        para_words = para_lower.split()
        
        # Calculate word overlap (like cryptographic frequency analysis)
        common_words = 0
        total_checks = 0
        
        for word in model_words:
            if word in para_lower:
                common_words += 1
            total_checks += 1
        
        if total_checks > 0:
            # Calculate similarity score
            word_similarity = common_words / total_checks
            
            # Bonus for exact phrase matches (stronger signal)
            phrase_bonus = 0
            for i in range(len(model_words) - 1):
                phrase = f"{model_words[i]} {model_words[i+1]}"
                if phrase in para_lower:
                    phrase_bonus += 0.2
            
            total_score = word_similarity + phrase_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_match = para
    
    # Only return if we have a reasonable match
    if best_score > 0.3:  # At least 30% word overlap
        return best_match
    
    return ""


def extract_variable_with_contextual_clues(variable_name: str, model_sentence: str, source_sentence: str, 
                                         learned_patterns: Optional[Dict] = None) -> Tuple[str, str, float]:
    """
    Enhanced extraction using the comprehensive 23-type classification system and heuristic behaviors.
    
    This function now integrates the CMS Model Prompt Heuristics Guide for sophisticated
    variable prompt analysis and extraction with context-aware processing.
    """
    try:
        # Extract before and after context from model sentence
        before_context, after_context = _extract_context_around_variable(variable_name, model_sentence)
        variable_text = f"[{variable_name}]"
        
        # Use enhanced classification
        classification = classify_variable_comprehensive(variable_text, before_context, after_context)
        behavior = _enhanced_classifier.get_heuristic_behavior(classification)
        
        # Log enhanced classification details
        logger.info(f"🧠 Enhanced Classification for '{variable_name}':")
        logger.info(f"   Type: {classification.variable_type.value}")
        logger.info(f"   Field ID: {classification.field_id}")
        logger.info(f"   Confidence: {classification.confidence_score:.2f}")
        logger.info(f"   Behavior: {behavior.get('action', 'unknown')}")
        
        # Apply heuristic-based extraction strategy
        if behavior.get("action") == "prompt_user_input":
            # Variables requiring user input - try to extract or indicate manual needed
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            reasoning = f"Enhanced extraction using {classification.variable_type.value} heuristics"
            confidence = classification.confidence_score * 0.8  # Adjust for extraction uncertainty
            
        elif behavior.get("action") == "present_options":
            # SELECT_ONE types - use enhanced option analysis
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            # Validate against known options if available
            if classification.options and extracted_value not in classification.options:
                # Try to find closest match
                closest_match = _find_closest_option(extracted_value, classification.options)
                if closest_match:
                    extracted_value = closest_match
            
            reasoning = f"Option selection from: {', '.join(classification.options) if classification.options else 'detected options'}"
            confidence = classification.confidence_score * 0.9
            
        elif behavior.get("action") == "conditional_insertion":
            # IF_APPLICABLE types - check conditions
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            reasoning = f"Conditional insertion: {classification.condition_text or 'condition analysis'}"
            confidence = classification.confidence_score * 0.7  # Lower confidence for conditionals
            
        elif behavior.get("action") == "regulatory_check":
            # REGULATORY_CONDITIONAL_INSERT types
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            reasoning = f"Regulatory compliance check: {classification.condition_text}"
            confidence = classification.confidence_score * 0.6  # Requires careful validation
            
        elif behavior.get("action") == "structured_input_form":
            # COMPLEX_STRUCTURAL_INSERT types
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            reasoning = f"Structured data extraction: {', '.join(classification.insert_fields or [])}"
            confidence = classification.confidence_score * 0.8
            
        elif behavior.get("action") == "url_input":
            # INSERT_URL types
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            # Additional URL validation
            extracted_value = _validate_url(extracted_value)
            reasoning = "URL extraction and validation"
            confidence = classification.confidence_score * 0.9
            
        elif behavior.get("action") == "numeric_input":
            # INSERT_NUMERIC_INLINE types
            extracted_value = call_ollama_llm_enhanced(
                model_sentence, source_sentence, variable_text, 
                before_context, after_context
            )
            # Ensure numeric format
            extracted_value = _extract_numeric_value(extracted_value)
            reasoning = "Numeric value extraction"
            confidence = classification.confidence_score * 0.9
            
        else:
            # Fallback to traditional extraction with enhanced context
            strategies = [
                _extract_using_before_context,
                _extract_using_after_context,
                _extract_using_both_contexts,
                _extract_using_learned_patterns,
                _extract_using_smart_patterns
            ]
            
            best_value = "None"
            best_confidence = 0.0
            best_reasoning = "No suitable extraction method found"
            
            for strategy in strategies:
                try:
                    value, reasoning, confidence = strategy(
                        variable_name, model_sentence, source_sentence, 
                        before_context, after_context, learned_patterns
                    )
                    
                    if confidence > best_confidence and value != "None":
                        best_value = value
                        best_confidence = confidence
                        best_reasoning = reasoning
                        
                        # If we get high confidence, stop searching
                        if confidence >= 0.9:
                            break
                            
                except Exception as e:
                    logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                    continue
            
            extracted_value = best_value
            reasoning = best_reasoning
            confidence = best_confidence
        
        # Apply enhanced post-processing based on classification
        if extracted_value != "None":
            extracted_value = _enhanced_post_process_value(extracted_value, classification)
            
        # Adjust confidence based on classification quality
        final_confidence = min(confidence * classification.confidence_score, 1.0)
        
        logger.info(f"🎯 Enhanced Extraction Result: '{extracted_value}' (confidence: {final_confidence:.2f})")
        
        return extracted_value, reasoning, final_confidence
        
    except Exception as e:
        error_msg = f"Error in enhanced contextual extraction: {e}"
        logger.error(error_msg)
        return "None", error_msg, 0.0

def _find_closest_option(extracted_value: str, options: List[str]) -> Optional[str]:
    """Find the closest matching option from a list."""
    if not extracted_value or not options:
        return None
    
    extracted_lower = extracted_value.lower()
    
    # Try exact matches first
    for option in options:
        if option.lower() == extracted_lower:
            return option
    
    # Try partial matches
    for option in options:
        if extracted_lower in option.lower() or option.lower() in extracted_lower:
            return option
    
    return None

def _validate_url(value: str) -> str:
    """Validate and clean URL values."""
    if not value or value == "None":
        return "None"
    
    cleaned = value.strip().strip('"\'')
    
    # Basic URL validation
    if not cleaned.startswith(('http://', 'https://')):
        if '.' in cleaned and ' ' not in cleaned:  # Looks like a domain
            cleaned = 'https://' + cleaned
        else:
            return "None"
    
    return cleaned

def _extract_numeric_value(value: str) -> str:
    """Extract numeric value from text."""
    if not value or value == "None":
        return "None"
    
    import re
    numbers = re.findall(r'\d+', value)
    return numbers[0] if numbers else "None"

def _enhanced_post_process_value(value: str, classification: VariableClassification) -> str:
    """Enhanced post-processing based on variable classification."""
    if not value or value == "None":
        return "None"
    
    var_type = classification.variable_type
    
    # Type-specific post-processing
    if var_type == VariableType.INSERT_URL:
        return _validate_url(value)
    elif var_type == VariableType.INSERT_NUMERIC_INLINE:
        return _extract_numeric_value(value)
    elif var_type in [VariableType.SELECT_ONE, VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT]:
        if classification.options:
            closest = _find_closest_option(value, classification.options)
            return closest if closest else value
    
    # Standard cleanup
    cleaned = value.strip().strip('"\'')
    
    # Handle common "omit" indicators
    if cleaned.lower() in ['none', 'n/a', 'not applicable', 'omit', 'remove', 'delete']:
        return "None"
    
    return cleaned


def _extract_context_around_variable(variable_name: str, model_sentence: str) -> Tuple[str, str]:
    """Extract the context words before and after a variable in the model sentence."""
    # Find the variable pattern in the model sentence
    patterns = [
        rf'\[{re.escape(variable_name)}\]',
        rf'\[{re.escape(variable_name.lower())}\]',
        rf'\[{re.escape(variable_name.title())}\]',
        rf'\[{re.escape(variable_name.upper())}\]'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, model_sentence, re.IGNORECASE)
        if match:
            start, end = match.span()
            
            # Extract 3-5 significant words before the variable
            before_text = model_sentence[:start].strip()
            before_words = before_text.split()
            before_context = " ".join(before_words[-4:]) if len(before_words) >= 4 else before_text
            
            # Extract 3-5 significant words after the variable
            after_text = model_sentence[end:].strip()
            after_words = after_text.split()
            after_context = " ".join(after_words[:4]) if len(after_words) >= 4 else after_text
            
            return before_context.strip(), after_context.strip()
    
    return "", ""


def _extract_using_before_context(variable_name: str, model_sentence: str, source_sentence: str,
                                before_context: str, after_context: str, learned_patterns: Dict) -> Tuple[str, str, float]:
    """Extract value using words that come before the variable."""
    if not before_context or len(before_context.split()) < 2:
        return "None", "Insufficient before context", 0.0
    
    # Look for the before context in the source sentence
    source_lower = source_sentence.lower()
    context_lower = before_context.lower()
    
    # Try exact match first
    context_pos = source_lower.find(context_lower)
    if context_pos >= 0:
        # Found exact context! Extract what comes after it
        context_end = context_pos + len(context_lower)
        remaining_text = source_sentence[context_end:].strip()
        
        # Remove leading punctuation/whitespace
        remaining_text = re.sub(r'^[^\w]+', '', remaining_text)
        
        # Extract based on variable type
        extracted_value = _extract_by_variable_type(variable_name, remaining_text, after_context)
        
        if extracted_value and extracted_value != "None":
            confidence = 0.95
            reasoning = f"Found exact before context '{before_context}' → extracted '{extracted_value}'"
            return extracted_value, reasoning, confidence
    
    # Try partial word matching if exact failed
    context_words = before_context.lower().split()
    if len(context_words) >= 2:
        # Look for sequences of 2-3 context words
        for i in range(len(context_words) - 1):
            partial_context = " ".join(context_words[i:i+2])
            context_pos = source_lower.find(partial_context)
            if context_pos >= 0:
                context_end = context_pos + len(partial_context)
                remaining_text = source_sentence[context_end:].strip()
                remaining_text = re.sub(r'^[^\w]+', '', remaining_text)
                
                extracted_value = _extract_by_variable_type(variable_name, remaining_text, after_context)
                if extracted_value and extracted_value != "None":
                    confidence = 0.8
                    reasoning = f"Found partial before context '{partial_context}' → extracted '{extracted_value}'"
                    return extracted_value, reasoning, confidence
    
    return "None", "Before context not found in source", 0.0


def _extract_using_after_context(variable_name: str, model_sentence: str, source_sentence: str,
                               before_context: str, after_context: str, learned_patterns: Dict) -> Tuple[str, str, float]:
    """Extract value using words that come after the variable."""
    if not after_context or len(after_context.split()) < 2:
        return "None", "Insufficient after context", 0.0
    
    source_lower = source_sentence.lower()
    context_lower = after_context.lower()
    
    # Find the after context in the source
    context_pos = source_lower.find(context_lower)
    if context_pos >= 0:
        # Found context! Extract what comes before it
        preceding_text = source_sentence[:context_pos].strip()
        
        # Extract the value that precedes the context
        extracted_value = _extract_preceding_value(variable_name, preceding_text, before_context)
        
        if extracted_value and extracted_value != "None":
            confidence = 0.9
            reasoning = f"Found after context '{after_context}' → extracted preceding '{extracted_value}'"
            return extracted_value, reasoning, confidence
    
    return "None", "After context not found in source", 0.0


def _extract_using_both_contexts(variable_name: str, model_sentence: str, source_sentence: str,
                               before_context: str, after_context: str, learned_patterns: Dict) -> Tuple[str, str, float]:
    """Extract value using both before and after context to pinpoint the exact location."""
    if not before_context or not after_context:
        return "None", "Need both contexts for this strategy", 0.0
    
    source_lower = source_sentence.lower()
    before_lower = before_context.lower()
    after_lower = after_context.lower()
    
    # Find both contexts in the source
    before_pos = source_lower.find(before_lower)
    after_pos = source_lower.find(after_lower)
    
    if before_pos >= 0 and after_pos >= 0 and after_pos > before_pos:
        # Found both contexts! Extract what's between them
        before_end = before_pos + len(before_lower)
        between_text = source_sentence[before_end:after_pos].strip()
        
        # Clean up the extracted text
        between_text = re.sub(r'^[^\w]+|[^\w]+$', '', between_text)
        
        if between_text:
            confidence = 0.98  # Very high confidence when both contexts match
            reasoning = f"Found both contexts '{before_context}' ... '{after_context}' → extracted '{between_text}'"
            return between_text, reasoning, confidence
    
    return "None", "Could not find both contexts in source", 0.0


def _extract_using_learned_patterns(variable_name: str, model_sentence: str, source_sentence: str,
                                  before_context: str, after_context: str, learned_patterns: Dict) -> Tuple[str, str, float]:
    """Extract using patterns learned from previous successful extractions."""
    if not learned_patterns:
        return "None", "No learned patterns available", 0.0
    
    # Look for similar variable patterns in learned data
    variable_type = classify_variable_type(variable_name)
    
    # Check if we have successful patterns for this variable type
    if variable_type in learned_patterns.get('variable_type_rules', {}):
        rules = learned_patterns['variable_type_rules'][variable_type]
        
        # Apply learned extraction rules
        for rule in rules.get('extraction_patterns', []):
            try:
                pattern = rule.get('pattern', '')
                if pattern:
                    match = re.search(pattern, source_sentence, re.IGNORECASE)
                    if match:
                        extracted_value = match.group(1) if match.groups() else match.group(0)
                        confidence = rule.get('confidence', 0.7)
                        reasoning = f"Applied learned pattern '{pattern[:30]}...' → extracted '{extracted_value}'"
                        return extracted_value, reasoning, confidence
            except Exception as e:
                continue
    
    return "None", "No applicable learned patterns", 0.0


def _extract_using_smart_patterns(variable_name: str, model_sentence: str, source_sentence: str,
                                before_context: str, after_context: str, learned_patterns: Dict) -> Tuple[str, str, float]:
    """Extract using intelligent pattern matching for specific variable types."""
    variable_type = classify_variable_type(variable_name)
    
    if 'plan name' in variable_name.lower():
        return _extract_plan_name_smart(source_sentence, before_context, after_context)
    elif 'mao name' in variable_name.lower() or 'organization' in variable_name.lower():
        return _extract_organization_smart(source_sentence, before_context, after_context)
    elif 'phone' in variable_name.lower():
        return _extract_phone_smart(source_sentence)
    elif 'tty' in variable_name.lower():
        return _extract_tty_smart(source_sentence)
    elif 'remove terms' in variable_name.lower():
        return _extract_removal_terms_smart(source_sentence)
    
    return "None", "No smart pattern for this variable type", 0.0


def _extract_by_variable_type(variable_name: str, text: str, after_context: str) -> str:
    """Extract value from text based on the variable type."""
    if 'plan name' in variable_name.lower():
        # Look for plan name patterns: capitalized words, possibly ending with PPO/HMO/Group
        patterns = [
            r'([A-Z][a-z]+(?:\s+(?:Plus|&|and)\s+[A-Z][a-z]+)*(?:\s+(?:Group|PPO|HMO|Blue))*)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+(?:PPO|HMO|Group))*)',
            r'(Medicare\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                # Stop at the after context if present
                if after_context:
                    after_words = after_context.split()[:2]
                    for word in after_words:
                        if word.lower() in value.lower():
                            value = value.split(word)[0].strip()
                            break
                return value
    
    elif 'mao name' in variable_name.lower():
        # Look for organization names: usually multiple capitalized words
        pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s+of\s+[A-Z][a-z]+)*)'
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    else:
        # General extraction: take the next meaningful phrase
        # Stop at punctuation or after context
        value_match = re.match(r'([^.!?;,\[\]]+)', text)
        if value_match:
            value = value_match.group(1).strip()
            
            # Stop at after context
            if after_context:
                after_words = after_context.split()[:2]
                for word in after_words:
                    if word.lower() in value.lower():
                        value = value.split(word)[0].strip()
                        break
            
            return value
    
    return "None"


def _extract_plan_name_smart(source_sentence: str, before_context: str, after_context: str) -> Tuple[str, str, float]:
    """Smart extraction for plan names."""
    # Plan names usually follow patterns like "Medicare Plus Blue Group PPO"
    plan_patterns = [
        r'(Medicare\s+Plus\s+Blue\s+(?:Group\s+)?PPO)',
        r'(Medicare\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:PPO|HMO|Group))',
        r'([A-Z][a-z]+\s+Plus\s+[A-Z][a-z]+\s+(?:Group\s+)?PPO)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:PPO|HMO|Group))'
    ]
    
    for pattern in plan_patterns:
        match = re.search(pattern, source_sentence, re.IGNORECASE)
        if match:
            plan_name = match.group(1).strip()
            confidence = 0.95
            reasoning = f"Smart plan name pattern matched: '{plan_name}'"
            return plan_name, reasoning, confidence
    
    return "None", "No plan name pattern found", 0.0


def _extract_organization_smart(source_sentence: str, before_context: str, after_context: str) -> Tuple[str, str, float]:
    """Smart extraction for organization/MAO names."""
    # Organizations usually have multiple capitalized words
    org_patterns = [
        r'(Blue\s+Cross\s+Blue\s+Shield\s+of\s+[A-Z][a-z]+)',
        r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:Insurance|Health|Medical|Corporation))',
        r'([A-Z][a-z]+\s+(?:Insurance|Health|Medical)\s+[A-Z][a-z]+)'
    ]
    
    for pattern in org_patterns:
        match = re.search(pattern, source_sentence, re.IGNORECASE)
        if match:
            org_name = match.group(1).strip()
            confidence = 0.9
            reasoning = f"Smart organization pattern matched: '{org_name}'"
            return org_name, reasoning, confidence
    
    return "None", "No organization pattern found", 0.0


def _extract_phone_smart(source_sentence: str) -> Tuple[str, str, float]:
    """Smart extraction for phone numbers."""
    phone_patterns = [
        r'(\d{1}-\d{3}-\d{3}-\d{4})',
        r'(\(\d{3}\)\s*\d{3}-\d{4})',
        r'(\d{3}-\d{3}-\d{4})',
        r'(\d{10})'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, source_sentence)
        if match:
            phone = match.group(1).strip()
            confidence = 0.98
            reasoning = f"Phone number pattern matched: '{phone}'"
            return phone, reasoning, confidence
    
    return "None", "No phone number found", 0.0


def _extract_tty_smart(source_sentence: str) -> Tuple[str, str, float]:
    """Smart extraction for TTY numbers."""
    # TTY is almost always 711
    if '711' in source_sentence:
        confidence = 0.99
        reasoning = "Found standard TTY number: '711'"
        return "711", reasoning, confidence
    
    return "None", "TTY number not found", 0.0


def _extract_removal_terms_smart(source_sentence: str) -> Tuple[str, str, float]:
    """Smart extraction for 'remove terms as needed' variables."""
    # These usually refer to benefit terms, premiums, copayments, etc.
    removal_patterns = [
        r'((?:Benefit|Premium|Copayment|Coinsurance|Deductible)s?[^.]*)',
        r'((?:benefit|premium|copayment|coinsurance|deductible)s?[^.]*)',
        r'(Benefits?,?\s+premiums?,?\s+(?:and/or\s+)?(?:copayments?|coinsurance))'
    ]
    
    for pattern in removal_patterns:
        match = re.search(pattern, source_sentence, re.IGNORECASE)
        if match:
            terms = match.group(1).strip()
            confidence = 0.85
            reasoning = f"Removal terms pattern matched: '{terms}'"
            return terms, reasoning, confidence
    
    return "None", "No removal terms found", 0.0


def _extract_preceding_value(variable_name: str, preceding_text: str, before_context: str) -> str:
    """Extract value that comes before the after context."""
    words = preceding_text.split()
    if not words:
        return "None"
    
    if 'plan name' in variable_name.lower():
        # Take the last 2-4 words that could form a plan name
        plan_words = []
        for word in reversed(words):
            if word[0].isupper() or word.lower() in ['ppo', 'hmo', 'group', 'plus', 'blue', 'medicare']:
                plan_words.insert(0, word)
                if len(plan_words) >= 4:
                    break
            else:
                break
        
        return " ".join(plan_words) if len(plan_words) >= 2 else "None"
    
    else:
        # Take the last few meaningful words
        return " ".join(words[-3:]) if len(words) >= 3 else " ".join(words)


def _post_process_extracted_value(value: str, variable_name: str) -> str:
    """Clean up and validate the extracted value."""
    if not value or value == "None":
        return "None"
    
    # Remove extra whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    
    # Remove trailing punctuation
    value = re.sub(r'[.,;:!?]+$', '', value)
    
    # Specific processing for plan names
    if 'plan name' in variable_name.lower():
        # Ensure proper capitalization
        words = value.split()
        processed_words = []
        for word in words:
            if word.lower() in ['ppo', 'hmo', 'group']:
                processed_words.append(word.upper())
            elif word.lower() in ['of', 'and', 'the', 'a', 'an']:
                processed_words.append(word.lower())
            else:
                processed_words.append(word.title())
        value = " ".join(processed_words)
    
    return value


def check_ollama_running() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_ollama() -> bool:
    """Start Ollama if not running."""
    try:
        if check_ollama_running():
            logger.info("Ollama is already running")
            return True
        
        logger.info("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to start
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            if check_ollama_running():
                logger.info("Ollama started successfully")
                return True
        
        logger.error("Failed to start Ollama")
        return False
        
    except Exception as e:
        logger.error(f"Error starting Ollama: {e}")
        return False


def ensure_model_available(model_name: str = OLLAMA_MODEL) -> bool:
    """Ensure the required model is available."""
    try:
        if not check_ollama_running():
            if not start_ollama():
                return False
        
        # Check if model is available
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [model["name"] for model in models]
            
            if model_name in available_models:
                logger.info(f"Model {model_name} is already available")
                return True
        
        # Pull the model if not available
        logger.info(f"Pulling model {model_name}...")
        pull_response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name}
        )
        
        if pull_response.status_code == 200:
            logger.info(f"Model {model_name} pulled successfully")
            return True
        else:
            logger.error(f"Failed to pull model {model_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error ensuring model availability: {e}")
        return False


def get_context_for_variable(text: str, var_start: int, var_end: int, context_chars: int = 50) -> Tuple[str, str]:
    """Get context before and after a variable."""
    context_before = text[max(0, var_start - context_chars):var_start].strip()
    context_after = text[var_end:min(len(text), var_end + context_chars)].strip()
    return context_before, context_after


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings."""
    if not text1 or not text2:
        return 0.0
    
    # Simple word overlap similarity
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


def find_best_source_block_cryptographic(model_sentence: str, source_paragraphs: List[str]) -> str:
    """
    Find the best matching source block using cryptographic-style analysis.
    Enhanced to handle different variable types and provide better matching.
    """
    if not source_paragraphs:
        return ""
    
    # Extract key content words from model sentence (ignore variables)
    model_words = re.sub(r'\[[^\]]*\]', '', model_sentence).lower().split()
    model_words = [w for w in model_words if len(w) > 2]  # Filter out short words
    
    best_match = ""
    best_score = 0
    
    for para in source_paragraphs:
        para_lower = para.lower()
        para_words = para_lower.split()
        
        # Calculate word overlap (like cryptographic frequency analysis)
        common_words = 0
        total_checks = 0
        
        for word in model_words:
            if word in para_lower:
                common_words += 1
            total_checks += 1
        
        if total_checks > 0:
            # Calculate similarity score
            word_similarity = common_words / total_checks
            
            # Bonus for exact phrase matches (stronger signal)
            phrase_bonus = 0
            for i in range(len(model_words) - 1):
                phrase = f"{model_words[i]} {model_words[i+1]}"
                if phrase in para_lower:
                    phrase_bonus += 0.2
            
            # Bonus for structural similarity
            structural_bonus = 0
            if len(model_words) > 3:
                # Check for similar sentence structure
                model_structure = [len(word) for word in model_words[:5]]
                para_structure = [len(word) for word in para_words[:5]]
                if model_structure == para_structure:
                    structural_bonus += 0.1
            
            total_score = word_similarity + phrase_bonus + structural_bonus
            
            if total_score > best_score:
                best_score = total_score
                best_match = para
    
    # Only return if we have a reasonable match
    if best_score > 0.3:  # At least 30% word overlap
        return best_match
    
    return ""


def call_ollama_llm_enhanced(model_sentence: str, source_sentence: str, variable_text: str, 
                           context_before: str = "", context_after: str = "", model=OLLAMA_MODEL) -> str:
    """
    Enhanced LLM call using the comprehensive 23-type classification system and heuristic behaviors.
    """
    try:
        # Ensure model is available
        if not ensure_model_available(model):
            logger.error(f"Model {model} not available")
            return "None"
        
        # Get comprehensive classification
        classification = classify_variable_comprehensive(variable_text, context_before, context_after)
        behavior = _enhanced_classifier.get_heuristic_behavior(classification)
        
        # Create sophisticated prompt based on variable type and heuristic behavior
        prompt = _create_enhanced_extraction_prompt(
            variable_text, model_sentence, source_sentence, 
            classification, behavior, context_before, context_after
        )
        
        # Call Ollama API
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Lower temperature for more consistent results
                    "top_p": 0.9,
                    "max_tokens": 200  # Increased for more complex responses
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            extracted_value = result.get("response", "").strip()
            
            # Apply post-processing based on variable type
            extracted_value = _post_process_extraction(extracted_value, classification, behavior)
            
            # Enhanced logging with classification details
            logger.info(f"🧠 [AI-{classification.variable_type.value.upper()}] Variable: '{variable_text}'")
            logger.info(f"📊 Confidence: {classification.confidence_score:.2f}")
            logger.info(f"🎯 Extracted: '{extracted_value}'")
            logger.info(f"📄 Source: '{source_sentence[:100]}...'")
            if classification.editor_instruction:
                logger.info(f"⚠️  Editor Instruction Required")
            
            return extracted_value
        else:
            logger.error(f"Ollama API error: {response.status_code}")
            return "None"
            
    except Exception as e:
        logger.error(f"Error calling enhanced Ollama LLM: {e}")
        return "None"

def call_ollama_llm(model_sentence: str, source_sentence: str, variable_name: str, model=OLLAMA_MODEL) -> str:
    """
    Legacy function for backward compatibility.
    Wraps the enhanced LLM call with simplified parameters.
    """
    return call_ollama_llm_enhanced(
        model_sentence, source_sentence, f"[{variable_name}]", 
        "", "", model
    )

def _create_enhanced_extraction_prompt(variable_text: str, model_sentence: str, source_sentence: str,
                                     classification: VariableClassification, behavior: Dict, 
                                     context_before: str, context_after: str) -> str:
    """Create sophisticated extraction prompt based on variable type and heuristic behavior."""
    
    var_type = classification.variable_type
    prompt_parts = []
    
    # Base prompt
    prompt_parts.append(f"""
You are a CMS document expert specializing in variable prompt extraction according to the official CMS Model Prompt Heuristics Guide.

VARIABLE ANALYSIS:
- Variable: {variable_text}
- Type: {var_type.value.upper()}
- Field ID: {classification.field_id}
- Confidence: {classification.confidence_score:.2f}

CONTEXT:
- Model sentence: "{model_sentence}"
- Source sentence: "{source_sentence}"
- Before context: "{context_before}"
- After context: "{context_after}"
""")
    
    # Type-specific instructions based on heuristics guide
    if var_type == VariableType.INSERT:
        prompt_parts.append(f"""
EXTRACTION TASK: STANDARD INSERT
This is a placeholder requiring a specific value to be inserted.
Expected data type: {classification.expected_data_type}
Look for the exact value that should replace this variable in the source content.
""")
    
    elif var_type == VariableType.SELECT_ONE:
        options_text = " / ".join(classification.options) if classification.options else "multiple options"
        prompt_parts.append(f"""
EXTRACTION TASK: SELECT ONE
One value must be selected from: {options_text}
Analyze the source content to determine which option applies.
Return ONLY the selected option.
""")
    
    elif var_type == VariableType.IF_APPLICABLE:
        prompt_parts.append(f"""
EXTRACTION TASK: CONDITIONAL INSERTION
Condition: {classification.condition_text}
Insert text: {classification.insert_text}
Determine if the condition applies based on the source content.
If condition applies: Return the insert text
If condition does not apply: Return "None"
""")
    
    elif var_type == VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL:
        prompt_parts.append(f"""
EXTRACTION TASK: COMPOUND CONDITIONAL INSERTION
Condition: {classification.condition_text}
Insert clause: {classification.insert_text}
Processing Rule: Content after the colon ':' should be conditionally inserted
This requires checking if a specific plan characteristic applies (e.g., language thresholds, plan features).

INSTRUCTIONS:
1. Evaluate if the condition applies based on source content
2. If condition is met: Return the full insert clause text
3. If condition is not met: Return "None"
4. The insert clause contains the exact text to be inserted when condition is true

Example: "Plans that meet 5% threshold insert: This document is available..."
→ If plan meets 5% threshold: Return "This document is available..."
→ If plan doesn't meet threshold: Return "None"
""")
    
    elif var_type == VariableType.INSTRUCTIONAL_INLINE_DELETION:
        prompt_parts.append(f"""
EXTRACTION TASK: INLINE TERM DELETION
This instruction modifies text immediately following the variable.
Prunable terms: {', '.join(classification.prunable_terms) if classification.prunable_terms else 'terms in following text'}
Analyze which terms should be kept vs. removed based on plan characteristics.
Return: Comma-separated list of terms to KEEP
""")
    
    elif var_type == VariableType.COMPLEX_STRUCTURAL_INSERT:
        prompt_parts.append(f"""
EXTRACTION TASK: STRUCTURED SERVICE AREA
Extract hierarchical geographic data: states, counties, zip codes
Look for service area definitions in the source content.
Return in format: "State: [state]; Counties: [counties]; Zip codes: [zips]"
""")
    
    elif var_type == VariableType.REGULATORY_CONDITIONAL_INSERT:
        prompt_parts.append(f"""
EXTRACTION TASK: REGULATORY COMPLIANCE
Condition: {classification.condition_text}
This requires CMS regulatory permission/exception.
Check if source mentions the specific regulatory exception.
If regulatory condition is met: Return "INSERT_CLAUSE"
If not applicable: Return "None"
""")
    
    elif var_type == VariableType.INSERT_URL:
        prompt_parts.append(f"""
EXTRACTION TASK: URL INSERTION
Look for website URLs in the source content.
Return ONLY valid URLs (starting with http:// or https://)
If no URL found: Return "None"
""")
    
    elif var_type == VariableType.INSERT_NUMERIC_INLINE:
        prompt_parts.append(f"""
EXTRACTION TASK: NUMERIC VALUE
Look for numbers related to: {variable_text}
Return ONLY the numeric value (integer).
If no relevant number found: Return "None"
""")
    
    elif var_type == VariableType.OPTIONAL:
        prompt_parts.append(f"""
EXTRACTION TASK: OPTIONAL CONTENT
This content is conditionally included based on plan characteristics.
Analyze if the optional content should be included.
If should be included: Return "INCLUDE"
If should be omitted: Return "None"
""")
    
    elif var_type == VariableType.DELETE_IF:
        prompt_parts.append(f"""
EXTRACTION TASK: CONDITIONAL DELETION
Condition: {classification.condition_text or 'if not applicable'}
Determine if the deletion condition is met.
If should delete: Return "DELETE"
If should keep: Return "KEEP"
""")
    
    else:
        # Generic handling for other types
        prompt_parts.append(f"""
EXTRACTION TASK: GENERAL ANALYSIS
Analyze the variable requirements and extract appropriate value from source.
Consider the variable type ({var_type.value}) when determining the response.
""")
    
    # Add behavior-specific instructions
    if behavior.get("action") == "prompt_user_input":
        prompt_parts.append("USER INPUT REQUIRED: This variable needs manual user input.")
    elif behavior.get("action") == "conditional_inclusion":
        prompt_parts.append("CONDITIONAL: Determine if content should be included or omitted.")
    elif behavior.get("action") == "regulatory_check":
        prompt_parts.append("REGULATORY: Requires CMS compliance verification.")
    
    # Final instructions
    prompt_parts.append(f"""
EXTRACTION RULES:
1. Follow CMS Model Prompt Heuristics Guide specifications
2. Return ONLY the extracted value, no explanations
3. Use "None" if no appropriate value is found
4. For conditional variables, evaluate the condition carefully
5. Maintain CMS document compliance standards

RESPONSE FORMAT: Return only the extracted value.""")
    
    return "\n".join(prompt_parts)

def _post_process_extraction(extracted_value: str, classification: VariableClassification, behavior: Dict) -> str:
    """Post-process extracted value based on variable type and behavior."""
    
    if not extracted_value:
        return "None"
    
    # Clean up common variations
    cleaned = extracted_value.strip().strip('"\'')
    
    # Type-specific post-processing
    var_type = classification.variable_type
    
    if var_type == VariableType.INSERT_URL:
        # Validate URL format
        if cleaned and not cleaned.startswith(('http://', 'https://')):
            if '.' in cleaned:  # Looks like a domain
                cleaned = 'https://' + cleaned
            else:
                cleaned = "None"
    
    elif var_type == VariableType.INSERT_NUMERIC_INLINE:
        # Extract numeric value
        import re
        numbers = re.findall(r'\d+', cleaned)
        cleaned = numbers[0] if numbers else "None"
    
    elif var_type == VariableType.SELECT_ONE:
        # Ensure selection is from valid options
        if classification.options and cleaned not in classification.options:
            # Try to find closest match
            cleaned_lower = cleaned.lower()
            for option in classification.options:
                if option.lower() in cleaned_lower or cleaned_lower in option.lower():
                    cleaned = option
                    break
    
    # Handle standard "omit" responses
    if cleaned.lower() in ['none', 'n/a', 'not applicable', 'omit', 'remove', 'delete']:
        cleaned = "None"
    
    return cleaned


class LogicMapper:
    """Enhanced Logic Mapper with persistent learning and improved heuristics."""
    
    def __init__(self):
        self.learning_persistence = LearningPersistence()
        self.extraction_history = []
        self.patterns = {}
        self.confidence_scores = {}
        
        # Load existing learning data
        self.learning_persistence.load_learning_state(self)
        
        # Start Ollama in background
        self._start_ollama_background()
    
    def _start_ollama_background(self):
        """Start Ollama in background if not running."""
        def status_callback(message):
            logger.info(f"Ollama: {message}")
        
        start_ollama_persistent(status_callback)
    
    def _save_learning_state(self):
        """Save current learning state."""
        self.learning_persistence.save_learning_state(self)
    
    def get_learning_stats(self):
        """Get learning statistics."""
        return self.learning_persistence.get_learning_stats()


def map_final_to_model(model_blocks: List[Dict], final_paragraphs: List[str], 
                      progress_callback=None, log_callback=None) -> Tuple[Dict[str, str], List[Dict]]:
    """
    Enhanced mapping using 23-type classification system + AI agent integration.
    """
    extraction_logs = []
    extracted_values = {}
    total_variables = 0
    successful_extractions = 0
    
    # Initialize enhanced mapping engine and learning system  
    from enhanced_mapping_integration import create_enhanced_mapping_engine
    mapping_engine = create_enhanced_mapping_engine()
    from learning_persistence import LearningPersistence
    learner = LearningPersistence()
    
    try:
        if log_callback:
            log_callback("🧠 Starting ENHANCED variable extraction with 23-type classification + AI agent...")
        
        # Process each block individually for better isolation
        for i, block in enumerate(model_blocks):
            if progress_callback:
                progress = (i / len(model_blocks)) * 100
                progress_callback(progress)
            
            if block.get('type') != 'variable':
                continue
                
            variable_name = block.get('inner_text', '').strip()
            if not variable_name:
                continue
                
            total_variables += 1
            
            # Get context from the new enhanced block structure
            before_context = block.get('before_context', '')
            after_context = block.get('after_context', '')
            full_context = block.get('text', '')
            variable_text = f"[{variable_name}]"
            
            if log_callback:
                log_callback(f"🔍 Processing variable: [{variable_name}]")
                log_callback(f"   📍 Before context: '{before_context[:50]}...'")
                log_callback(f"   📍 After context: '{after_context[:50]}...'")
            
            best_value = "None"
            best_confidence = 0.0
            best_reasoning = "No extraction attempted"
            best_source = "none"
            
            # Try smart suggestions first (quick wins from learning)
            smart_suggestions = learner.get_smart_suggestions(variable_name, before_context, after_context)
            
            if smart_suggestions:
                suggestion = smart_suggestions[0]  # Best suggestion
                if suggestion['confidence'] > 0.8:  # Higher threshold for auto-accept
                    best_value = suggestion['value']
                    best_confidence = suggestion['confidence']
                    best_reasoning = f"Smart suggestion: {suggestion['reasoning']}"
                    best_source = "learned_pattern"
                    
                    if log_callback:
                        log_callback(f"   💡 Used learned pattern: {best_value} (confidence: {best_confidence:.2f})")
            
            # If no high-confidence learned pattern, use ENHANCED EXTRACTION
            if best_confidence < 0.8:
                if log_callback:
                    log_callback(f"   🤖 Using enhanced AI extraction...")
                
                # Use the enhanced mapping engine with 23-type classification + AI agent
                extracted_value, confidence, reasoning = mapping_engine.extract_variable_intelligently(
                    variable_name, variable_text, before_context, after_context, final_paragraphs
                )
                
                if confidence > best_confidence:
                    best_value = extracted_value
                    best_confidence = confidence
                    best_reasoning = reasoning
                    best_source = "enhanced_ai_extraction"
                    
                    if log_callback:
                        log_callback(f"   🎯 Enhanced extraction: {best_value} (confidence: {confidence:.2f})")
                        log_callback(f"   🔍 Reasoning: {reasoning}")
            
            # Save the extraction experience for learning
            learner.save_extraction_experience(
                variable_name=variable_name,
                context_before=before_context,
                context_after=after_context,
                extracted_value=best_value,
                confidence=best_confidence,
                reasoning=best_reasoning,
                extraction_method=best_source
            )
            
            # Store the result
            extracted_values[variable_name] = best_value
            
            # Create detailed log entry with enhanced classification
            classification = classify_variable_comprehensive(variable_text, before_context, after_context)
            
            log_entry = {
                'variable': variable_name,
                'type': classify_variable_type(variable_name),  # Legacy type for compatibility
                'enhanced_type': classification.variable_type.value,
                'field_id': classification.field_id,
                'classification_confidence': classification.confidence_score,
                'extracted_value': best_value,
                'source': best_source,
                'confidence': best_confidence,
                'reasoning': best_reasoning,
                'before_context': before_context[:100],  # Limit for readability
                'after_context': after_context[:100],
                'editor_instruction': classification.editor_instruction,
                'requires_user_input': classification.requires_user_input,
                'expected_data_type': classification.expected_data_type,
                'condition_text': classification.condition_text,
                'insert_text': classification.insert_text
            }
            extraction_logs.append(log_entry)
            
            if best_value != "None" and best_confidence > 0.5:
                successful_extractions += 1
            
            if log_callback:
                log_callback(f"   ✅ Result: '{best_value}' (confidence: {best_confidence:.2f})")
                if classification.editor_instruction:
                    log_callback(f"   ⚠️  Editor instruction required for this variable")
                log_callback("")  # Empty line for readability
        
        # Final summary
        if log_callback:
            success_rate = (successful_extractions / total_variables * 100) if total_variables > 0 else 0
            log_callback(f"🎯 ENHANCED EXTRACTION SUMMARY:")
            log_callback(f"   📊 Total variables: {total_variables}")
            log_callback(f"   ✅ Successful extractions: {successful_extractions}")
            log_callback(f"   📈 Success rate: {success_rate:.1f}%")
            log_callback(f"   🧠 Using 23-type classification + AI agent integration")
        
        return extracted_values, extraction_logs
        
    except Exception as e:
        error_msg = f"Error in enhanced mapping: {e}"
        logger.error(error_msg)
        if log_callback:
            log_callback(f"❌ {error_msg}")
        return {}, []
    
    def _learn_from_extraction(self, var_name: str, extracted_value: str, var_type: str, 
                              context: str, source_para: str):
        """Learn from successful extractions to improve future performance."""
        try:
            # Store pattern
            if var_type not in self.patterns:
                self.patterns[var_type] = {'examples': [], 'success_rate': 0.0}
            
            pattern_info = {
                'variable_name': var_name,
                'extracted_value': extracted_value,
                'context': context,
                'source_paragraph': source_para,
                'timestamp': time.time()
            }
            
            self.patterns[var_type]['examples'].append(pattern_info)
            
            # Update success rate
            total_examples = len(self.patterns[var_type]['examples'])
            successful_examples = len([ex for ex in self.patterns[var_type]['examples'] 
                                    if ex['extracted_value'] != 'None'])
            self.patterns[var_type]['success_rate'] = successful_examples / total_examples
            
            # Store in extraction history
            self.extraction_history.append(pattern_info)
            
            # Update confidence score
            self.confidence_scores[var_name] = {
                'value': extracted_value,
                'confidence': 0.8,  # Base confidence
                'type': var_type,
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error learning from extraction: {e}")
    
    def _fallback_to_original_mapper(self, model_blocks: List[Dict], final_doc_path: str,
                                   progress_callback: callable, log_callback: callable) -> Tuple[Dict, List[str]]:
        """Fallback to original mapping method."""
        log_callback("Using fallback mapping method...")
        # Implementation of fallback method
        return {}, []
    
    def _fallback_to_regex_mapper(self, model_blocks: List[Dict], final_doc_path: str,
                                 progress_callback: callable, log_callback: callable) -> Tuple[Dict, List[str]]:
        """Fallback to regex-based mapping."""
        log_callback("Using regex fallback mapping...")
        # Implementation of regex fallback
        return {}, []


class VariablePatternLearner:
    """Enhanced learner for variable patterns with improved heuristics."""
    
    def __init__(self):
        self.patterns = {}
        self.extraction_history = []
        self.confidence_scores = {}
        self.variable_types = {}
        
        # Load existing patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load existing patterns from file."""
        try:
            if os.path.exists('learning_data/learned_patterns.json'):
                with open('learning_data/learned_patterns.json', 'r') as f:
                    data = json.load(f)
                    self.patterns = data.get('patterns', {})
                    self.extraction_history = data.get('history', [])
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
    
    def classify_variable_type(self, variable_name: str) -> str:
        """Enhanced variable type classification."""
        var_lower = variable_name.lower()
        
        # Check for option selects
        if any(keyword in var_lower for keyword in ['or', 'either', 'choose', 'select', 'option']):
            return 'option_select'
        
        # Check for conditionals
        if any(keyword in var_lower for keyword in ['if', 'when', 'unless', 'provided', 'as applicable']):
            return 'conditional'
        
        # Check for static values
        if any(keyword in var_lower for keyword in ['omit', 'remove', 'delete', 'none', 'nothing']):
            return 'static'
        
        # Check for input fields
        if any(keyword in var_lower for keyword in ['insert', 'add', 'include', 'enter', 'fill']):
            return 'input'
        
        return 'unknown'
    
    def calculate_confidence(self, extracted_value: str, variable_type: str) -> float:
        """Calculate confidence score for extracted value."""
        if not extracted_value or extracted_value == "None":
            return 0.0
        
        base_confidence = 0.5
        
        # Adjust based on variable type
        if variable_type == 'static':
            base_confidence += 0.3
        elif variable_type == 'option_select':
            base_confidence += 0.2
        elif variable_type == 'conditional':
            base_confidence += 0.1
        
        # Adjust based on value characteristics
        if len(extracted_value) > 10:
            base_confidence += 0.1
        if any(char.isdigit() for char in extracted_value):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def learn_from_success(self, variable_name: str, extracted_value: str, was_correct: bool):
        """Learn from successful extractions."""
        var_type = self.classify_variable_type(variable_name)
        
        if var_type not in self.patterns:
            self.patterns[var_type] = []
        
        pattern = {
            'variable_name': variable_name,
            'extracted_value': extracted_value,
            'was_correct': was_correct,
            'timestamp': time.time()
        }
        
        self.patterns[var_type].append(pattern)
        self.extraction_history.append(pattern)


def find_paragraph_with_confidence(model_sentence: str, source_paragraphs: List[str], 
                                 learner: VariablePatternLearner, variable_name: str) -> Tuple[str, float]:
    """Find best paragraph with confidence score."""
    best_para = find_best_source_block_cryptographic(model_sentence, source_paragraphs)
    confidence = calculate_text_similarity(model_sentence, best_para)
    return best_para, confidence


def extract_variable_with_learning(model_sentence: str, source_sentence: str, 
                                 variable_name: str, learner: VariablePatternLearner) -> Tuple[str, float]:
    """Extract variable with learning capabilities."""
    var_type = learner.classify_variable_type(variable_name)
    
    # Use AI extraction
    extracted_value = extract_variable_with_contextual_clues(variable_name, model_sentence, source_sentence, learner.patterns)
    
    # Calculate confidence
    confidence = learner.calculate_confidence(extracted_value, var_type)
    
    # Learn from this extraction
    learner.learn_from_success(variable_name, extracted_value, True)
    
    return extracted_value, confidence


def find_sentences_containing_variables(model_blocks: List[Dict]) -> List[Dict]:
    """Find sentences containing variables for extraction."""
    sentences_with_vars = []
    
    for block in model_blocks:
        if 'variables' in block:
            variables = extract_all_variables(block['text'])
            if variables:
                sentences_with_vars.append({
                    'text': block['text'],
                    'variables': variables,
                    'block_type': block.get('type', 'unknown')
                })
    
    return sentences_with_vars


def find_sentences_containing_variables_aggressive(model_path: str) -> List[Dict]:
    """Aggressively find all sentences containing variables."""
    try:
        doc = Document(model_path)
        sentences_with_vars = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                variables = extract_all_variables(text)
                if variables:
                    sentences_with_vars.append({
                        'text': text,
                        'variables': variables,
                        'paragraph_index': len(sentences_with_vars)
                    })
        
        return sentences_with_vars
        
    except Exception as e:
        logger.error(f"Error in aggressive variable finding: {e}")
        return []


def force_start_ollama():
    """Force start Ollama if not running."""
    try:
        if not check_ollama_running():
            logger.info("Forcing Ollama start...")
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(5)  # Wait for startup
        
        return check_ollama_running()
    except Exception as e:
        logger.error(f"Error forcing Ollama start: {e}")
        return False

