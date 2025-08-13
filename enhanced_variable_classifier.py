#!/usr/bin/env python3
"""
Enhanced Variable Classifier for CMS Model Documents
Based on the comprehensive CMS Model Prompt Heuristics Guide

Implements all 23 variable prompt types with sophisticated pattern recognition
and heuristic behavior rules for accurate variable classification and processing.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VariableType(Enum):
    """Enumeration of all 23 variable prompt types from the heuristics guide."""
    INSERT = "insert"
    SELECT_ONE = "select_one"
    OPTIONAL = "optional"
    DELETE_IF = "delete_if"
    IF_APPLICABLE = "if_applicable"
    INSTRUCTION_ONLY = "instruction_only"
    FREEFORM = "freeform"
    IF_APPLICABLE_COMPOUND_CONDITIONAL = "if_applicable_compound_conditional"
    IF_APPLICABLE_INSTRUCTIONAL_INSERT = "if_applicable_instructional_insert"
    INSTRUCTIONAL_INLINE_DELETION = "instructional_inline_deletion"
    COMPLEX_STRUCTURAL_INSERT = "complex_structural_insert"
    REGULATORY_CONDITIONAL_INSERT = "regulatory_conditional_insert"
    IF_APPLICABLE_NESTED_MODIFIER = "if_applicable_nested_modifier"
    IF_APPLICABLE_PARALLEL_REFERENCE = "if_applicable_parallel_reference"
    INSERT_URL = "insert_url"
    INSTRUCTIONAL_STRUCTURAL_DELETION = "instructional_structural_deletion"
    SELECT_ONE_WITH_EMBEDDED_INSERT = "select_one_with_embedded_insert"
    INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH = "instructional_replacement_prior_paragraph"
    PERMISSIVE_CONDITIONAL_INSERT = "permissive_conditional_insert"
    INSTRUCTIONAL_CLAUSE_OMISSION = "instructional_clause_omission"
    INSTRUCTIONAL_CROSS_REFERENCE_REQUIREMENT = "instructional_cross_reference_requirement"
    INSERT_NUMERIC_INLINE = "insert_numeric_inline"
    INSERT_PLAN_SPECIFICS_COMPOSITE = "insert_plan_specifics_composite"
    OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT = "optional_conditional_with_embedded_select"
    OPTIONAL_INFORMATION_COMPOUND = "optional_information_compound"


@dataclass
class VariableClassification:
    """Complete classification result for a variable prompt."""
    variable_type: VariableType
    field_id: str
    confidence_score: float
    insert_text: Optional[str] = None
    condition_text: Optional[str] = None
    requires_user_input: bool = False
    editor_instruction: bool = False
    affects_prior_paragraph: bool = False
    modifies_text_right_of_vpx: bool = False
    requires_structured_input: bool = False
    has_multiple_subfields: bool = False
    insert_fields: List[str] = None
    options: List[str] = None
    target_text: Optional[str] = None
    replacement_text: Optional[str] = None
    requires_validation: bool = False
    requires_drafting: bool = False
    requires_pruning: bool = False
    prunable_terms: List[str] = None
    requires_regulatory_awareness: bool = False
    appendix_allowed: bool = False
    format_examples: Optional[str] = None
    renumber_required: bool = False
    instruction_scope: Optional[str] = None
    target_phrase: Optional[str] = None
    allow_table: bool = False
    allow_attachment_reference: bool = False
    enforce_structural_completeness: bool = False
    required_action: Optional[str] = None
    expected_data_type: Optional[str] = None
    insert_position: Optional[str] = None
    retain_rest_of_sentence: bool = False
    data_sources: List[str] = None


class EnhancedVariableClassifier:
    """
    Enhanced classifier implementing all 23 variable types from the CMS heuristics guide.
    """
    
    def __init__(self):
        self.pattern_matchers = self._initialize_pattern_matchers()
        self.classification_cache = {}
        
    def _initialize_pattern_matchers(self) -> Dict[VariableType, List[Dict]]:
        """Initialize pattern matchers for each variable type."""
        return {
            VariableType.INSERT: [
                {
                    "pattern": r"^\[insert\s+([^]]+)\]$",
                    "keywords": ["insert"],
                    "examples": ["[insert 2025 plan name]", "[insert monthly premium amount]"]
                }
            ],
            
            VariableType.SELECT_ONE: [
                {
                    "pattern": r"^\[select\s+one:\s*([^]]+)\]$",
                    "keywords": ["select one"],
                    "examples": ["[select one: Yes/No]", "[select one: A/B/C]"]
                }
            ],
            
            VariableType.OPTIONAL: [
                {
                    "pattern": r"^\[Optional[:\]]?([^]]*)\]$",
                    "keywords": ["optional"],
                    "examples": ["[Optional]", "[Optional: You may also request a printed copy]"]
                }
            ],
            
            VariableType.DELETE_IF: [
                {
                    "pattern": r"^\[Delete\s+if\s+([^]]+)\]$",
                    "keywords": ["delete if", "remove if"],
                    "examples": ["[Delete if not applicable]"]
                }
            ],
            
            VariableType.IF_APPLICABLE: [
                {
                    "pattern": r"^\[insert\s+if\s+applicable:\s*([^]]+)\]$",
                    "keywords": ["insert if applicable"],
                    "examples": ["[insert if applicable: or territory]", "[Insert if applicable: URLs, notices]"]
                },
                {
                    "pattern": r"^\[Insert\s+if\s+applicable:\s*([^]]+)\]$",
                    "keywords": ["insert if applicable"],
                    "examples": ["[Insert if applicable: URLs, notices]"]
                },
                {
                    "pattern": r"^\[[^]]*if\s+applicable[^]]*\]$",
                    "keywords": ["if applicable"],
                    "examples": ["[if applicable: ...]"]
                }
            ],
            
            VariableType.INSTRUCTION_ONLY: [
                {
                    "pattern": r"^\[(?:Plans\s+may\s+include|Remove\s+the\s+following\s+if)([^]]+)\]$",
                    "keywords": ["plans may include", "remove the following if"],
                    "examples": ["[Plans may include: ...]", "[Remove the following if ...]"]
                }
            ],
            
            VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL: [
                {
                    "pattern": r"^\[([^,]+),\s*insert:\s*([^]]+)\]$",
                    "keywords": ["plans with", ", insert:"],
                    "examples": ["[Plans with grandfathered members who were outside of area prior to January 1999, insert: If you have been a member...]"]
                },
                {
                    "pattern": r"^\[([^]]+)\s+insert:\s*(.+)\]$",
                    "keywords": ["plans that", "plans with", "insert:"],
                    "examples": ["[Plans that meet the 5% alternative language threshold insert: This document is available...]"]
                },
                {
                    "pattern": r"^\[([^]]+)\s+should\s+insert:\s*([^]]+)\]$",
                    "keywords": ["should insert:"],
                    "examples": ["[Plans should insert: specific text]"]
                }
            ],
            
            VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT: [
                {
                    "pattern": r"^\[if\s+([^,]+),\s*insert:\s*([^]]+)\]$",
                    "keywords": ["if", "insert:", "generally here", "add a sentence"],
                    "examples": ["[if a continuation area is offered under 42 CFR 422.54, insert: generally here and add a sentence describing the continuation area]"]
                }
            ],
            
            VariableType.INSTRUCTIONAL_INLINE_DELETION: [
                {
                    "pattern": r"^\[Remove\s+terms\s+as\s+needed\s+to\s+reflect\s+([^]]+)\]$",
                    "keywords": ["remove terms as needed", "reflect plan benefits"],
                    "examples": ["[Remove terms as needed to reflect plan benefits]"]
                }
            ],
            
            VariableType.COMPLEX_STRUCTURAL_INSERT: [
                {
                    "pattern": r"^\[Insert\s+([^]]+).*service\s+area.*states.*counties.*zip\s+codes.*\]$",
                    "keywords": ["service area", "states", "counties", "zip codes", "appendix"],
                    "examples": ["[Insert plan service area here or within an appendix. Plans may include references to territories...]"]
                }
            ],
            
            VariableType.REGULATORY_CONDITIONAL_INSERT: [
                {
                    "pattern": r"^\[([^]]+)that\s+CMS\s+has\s+granted\s+([^]]+)\s+insert:\s*([^]]+)\]$",
                    "keywords": ["CMS has granted", "permission", "exception", "§", "CFR"],
                    "examples": ["[Regional PPOs that CMS has granted permission to use the exception in § 422.112(a)(1)(ii) to meet access requirements should insert: ...]"]
                }
            ],
            
            VariableType.IF_APPLICABLE_NESTED_MODIFIER: [
                {
                    "pattern": r"^\[insert\s+as\s+applicable:\s*(also|and|or)\]$",
                    "keywords": ["insert as applicable:", "also", "and", "or"],
                    "examples": ["[insert as applicable: also]"]
                }
            ],
            
            VariableType.IF_APPLICABLE_PARALLEL_REFERENCE: [
                {
                    "pattern": r"^\[([^]]+)\s*\[insert\s+as\s+applicable:\s*and\s+([^]]+)\]\s*([^]]+)\]$",
                    "keywords": ["providers", "suppliers", "insert as applicable: and"],
                    "examples": ["[The most recent list of providers [insert as applicable: and suppliers] is...]"]
                }
            ],
            
            VariableType.INSERT_URL: [
                {
                    "pattern": r"^\[insert\s+URL\]$",
                    "keywords": ["insert URL", "website", "url"],
                    "examples": ["[insert URL]"]
                }
            ],
            
            VariableType.INSTRUCTIONAL_STRUCTURAL_DELETION: [
                {
                    "pattern": r"^\[Delete\s+([^]]+)\s+if\s+([^]]+)\.\s*Renumber\s+remaining\s+sections\s+as\s+appropriate\.\]$",
                    "keywords": ["delete", "if", "renumber remaining sections"],
                    "examples": ["[Delete Optional Supplemental Benefit Premium bullet if your plan doesn't offer optional supplemental benefits. Renumber remaining sections as appropriate.]"]
                }
            ],
            
            VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT: [
                {
                    "pattern": r"^\[Select\s+one\s+of\s+the\s+following:.*\[insert\s+([^]]+)\].*OR.*\]$",
                    "keywords": ["select one of the following", "OR"],
                    "examples": ["[Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows...]"]
                }
            ],
            
            VariableType.INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH: [
                {
                    "pattern": r"^\[Plans\s+with\s+([^]]+)\s+should\s+replace\s+the\s+preceding\s+paragraph\s+with:\s*([^]]+)\]$",
                    "keywords": ["replace the preceding paragraph with", "plans with"],
                    "examples": ["[Plans with no premium should replace the preceding paragraph with: You do not pay a separate monthly plan premium for [insert 2025 plan name].]"]
                }
            ],
            
            VariableType.PERMISSIVE_CONDITIONAL_INSERT: [
                {
                    "pattern": r"^\[Plans\s+that\s+include\s+([^]]+)\s+may\s+describe\s+the\s+benefit\s+within\s+this\s+section\.\]$",
                    "keywords": ["plans that include", "may describe", "within this section"],
                    "examples": ["[Plans that include a Part B premium reduction benefit may describe the benefit within this section.]"]
                }
            ],
            
            VariableType.INSTRUCTIONAL_CLAUSE_OMISSION: [
                {
                    "pattern": r"^\[Plans\s+with\s+([^]]+),\s*omit:\s*([^]]+)\]$",
                    "keywords": ["plans with", "omit:"],
                    "examples": ["[Plans with no monthly premium, omit: In addition to paying the monthly plan premium,]"]
                }
            ],
            
            VariableType.INSTRUCTIONAL_CROSS_REFERENCE_REQUIREMENT: [
                {
                    "pattern": r"^\[If\s+([^]]+),\s*then\s+([^]]+)\]$",
                    "keywords": ["if", "then", "chapter", "section"],
                    "examples": ["[If the plan describes optional supplemental benefits within Chapter 4, then the plan must include the premium amounts for those benefits in this section.]"]
                }
            ],
            
            VariableType.INSERT_NUMERIC_INLINE: [
                {
                    "pattern": r"^\[insert\s+number\s+of\s+([^]]+)\]$",
                    "keywords": ["insert number of"],
                    "examples": ["[insert number of payment options]"]
                },
                {
                    "pattern": r"^\[insert\s+phone\s+number\]$",
                    "keywords": ["insert phone number", "phone", "contact"],
                    "examples": ["[insert phone number]"]
                },
                {
                    "pattern": r"^\[insert\s+TTY\s+number\]$",
                    "keywords": ["insert TTY number", "TTY", "hearing"],
                    "examples": ["[insert TTY number]"]
                },
                {
                    "pattern": r"^\[insert\s+Customer\s+Services?\s+number\]$",
                    "keywords": ["insert Customer Service number", "insert Customer Services number", "customer service", "customer services"],
                    "examples": ["[insert Customer Services number]", "[insert Customer Service number]"]
                },
                {
                    "pattern": r"^\[insert\s+([^]]*(?:phone|service|contact|number)[^]]*)\]$",
                    "keywords": ["phone", "service", "contact", "number"],
                    "examples": ["[insert phone number]", "[insert service number]", "[insert contact number]"]
                }
            ],
            
            VariableType.INSERT_PLAN_SPECIFICS_COMPOSITE: [
                {
                    "pattern": r"^\[Insert\s+plan\s+specifics\s+regarding\s+([^]]+)\]$",
                    "keywords": ["insert plan specifics regarding", "multiple elements", "payment intervals", "address"],
                    "examples": ["[Insert plan specifics regarding premium/penalty payment intervals...]"]
                }
            ],
            
            VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT: [
                {
                    "pattern": r"^\[Optional\s+information:\s*([^:\[]+):\s*([^\[]+)\[insert\s+as\s+applicable:\s*([^\]]+)\]([^\]]*)\]$",
                    "keywords": ["optional information", "can include", "insert as applicable", "OR", "several", "all", "following"],
                    "examples": ["[Optional information: multi-state plans can include the following: We offer coverage in [insert as applicable: several OR all]]"],
                    "requires_embedded_insert": True
                }
            ],
            
            VariableType.OPTIONAL_INFORMATION_COMPOUND: [
                {
                    "pattern": r"^\[Optional\s+information:\s*([^:\]]+)(?::\s*([^\]]+))?\]$",
                    "keywords": ["optional information", "multi-state", "plans can include", "following"],
                    "examples": ["[Optional information: multi-state plans can include the following]", "[Optional information: Additional details may be provided]"]
                }
            ]
        }
    
    def classify_variable(self, variable_text: str, context_before: str = "", context_after: str = "") -> VariableClassification:
        """
        Classify a variable prompt using comprehensive pattern matching and heuristics.
        
        Args:
            variable_text: The full bracketed variable text
            context_before: Text appearing before the variable
            context_after: Text appearing after the variable
            
        Returns:
            VariableClassification with detailed type information and metadata
        """
        # Check cache first
        cache_key = f"{variable_text}|{context_before[:50]}|{context_after[:50]}"
        if cache_key in self.classification_cache:
            return self.classification_cache[cache_key]
        
        # Clean and normalize the variable text
        normalized_text = self._normalize_variable_text(variable_text)
        
        # Try pattern matching for each type
        classification = self._pattern_match_classification(normalized_text, context_before, context_after)
        
        # If no pattern match, use heuristic analysis
        if classification.variable_type == VariableType.FREEFORM:
            classification = self._heuristic_classification(normalized_text, context_before, context_after)
        
        # Enhance classification with additional metadata
        classification = self._enhance_classification_metadata(classification, normalized_text, context_before, context_after)
        
        # Cache the result
        self.classification_cache[cache_key] = classification
        
        return classification
    
    def _normalize_variable_text(self, text: str) -> str:
        """Normalize variable text for consistent processing."""
        return text.strip()
    
    def _pattern_match_classification(self, text: str, context_before: str, context_after: str) -> VariableClassification:
        """Attempt to classify using pattern matching with priority order."""
        text_lower = text.lower()
        
        # Priority matching - check specific patterns first, then general ones
        priority_order = [
            # NEW: Complex nested variables must match before simpler ones
            VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT,
            VariableType.OPTIONAL_INFORMATION_COMPOUND,
            VariableType.INSERT_NUMERIC_INLINE,
            VariableType.INSERT_URL,
            VariableType.SELECT_ONE,
            VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL,
            # FIXED: IF_APPLICABLE should come BEFORE IF_APPLICABLE_INSTRUCTIONAL_INSERT
            VariableType.IF_APPLICABLE,
            VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT,
            VariableType.INSTRUCTIONAL_INLINE_DELETION,
            VariableType.INSTRUCTIONAL_STRUCTURAL_DELETION,
            VariableType.INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH,
            VariableType.INSTRUCTIONAL_CLAUSE_OMISSION,
            VariableType.INSTRUCTIONAL_CROSS_REFERENCE_REQUIREMENT,
            VariableType.REGULATORY_CONDITIONAL_INSERT,
            VariableType.COMPLEX_STRUCTURAL_INSERT,
            VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT,
            VariableType.PERMISSIVE_CONDITIONAL_INSERT,
            VariableType.INSERT_PLAN_SPECIFICS_COMPOSITE,
            VariableType.IF_APPLICABLE_NESTED_MODIFIER,
            VariableType.IF_APPLICABLE_PARALLEL_REFERENCE,
            VariableType.DELETE_IF,
            VariableType.OPTIONAL,
            VariableType.INSTRUCTION_ONLY,
            VariableType.INSERT,
            VariableType.FREEFORM
        ]
        
        # Check each type in priority order
        for var_type in priority_order:
            if var_type in self.pattern_matchers:
                patterns = self.pattern_matchers[var_type]
                for pattern_info in patterns:
                    pattern = pattern_info["pattern"]
                    keywords = pattern_info["keywords"]
                    
                    # Try regex pattern match first
                    # Use re.match for complex nested patterns to ensure full-string matching
                    if var_type in [VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT, 
                                   VariableType.OPTIONAL_INFORMATION_COMPOUND]:
                        if re.match(pattern, text, re.IGNORECASE | re.DOTALL):
                            # For complex patterns, ensure embedded insert is actually present
                            if var_type == VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT:
                                if "[insert as applicable:" in text.lower():
                                    return self._create_basic_classification(var_type, text, 0.9)
                            else:
                                # For simple optional information, ensure NO embedded insert
                                if "[insert as applicable:" not in text.lower():
                                    return self._create_basic_classification(var_type, text, 0.9)
                    else:
                        # Use re.search for simpler patterns
                        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                            return self._create_basic_classification(var_type, text, 0.9)
                    
                    # Enhanced keyword matching with better logic
                    # For complex optional variables, require strict matching to avoid misclassification
                    if var_type == VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT:
                        # Must have embedded insert for keyword match to be valid
                        if "[insert as applicable:" in text.lower() and self._enhanced_keyword_match(text_lower, keywords, var_type):
                            return self._create_basic_classification(var_type, text, 0.8)
                    elif var_type == VariableType.OPTIONAL_INFORMATION_COMPOUND:
                        # Must NOT have embedded insert for keyword match to be valid  
                        if "[insert as applicable:" not in text.lower() and self._enhanced_keyword_match(text_lower, keywords, var_type):
                            return self._create_basic_classification(var_type, text, 0.8)
                    else:
                        # Normal keyword matching for other types
                        if self._enhanced_keyword_match(text_lower, keywords, var_type):
                            return self._create_basic_classification(var_type, text, 0.8)
        
        # No pattern matched
        return self._create_basic_classification(VariableType.FREEFORM, text, 0.3)
    
    def _enhanced_keyword_match(self, text_lower: str, keywords: List[str], var_type: VariableType) -> bool:
        """Enhanced keyword matching with type-specific logic."""
        
        # For IF_APPLICABLE types, require both "if" and "applicable" or "insert if applicable"
        if var_type == VariableType.IF_APPLICABLE:
            return ("insert if applicable" in text_lower or 
                    ("if" in text_lower and "applicable" in text_lower))
        
        # For INSERT_NUMERIC_INLINE, check for phone/service/numeric patterns
        elif var_type == VariableType.INSERT_NUMERIC_INLINE:
            return ("insert number" in text_lower or 
                    "insert phone" in text_lower or
                    "insert tty" in text_lower or
                    "customer service" in text_lower or
                    "customer services" in text_lower or
                    ("insert" in text_lower and any(term in text_lower for term in ["phone", "service", "contact", "number"])))
        
        # For COMPOUND_CONDITIONAL, look for various conditional patterns with "insert:"
        elif var_type == VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL:
            return (("plans with" in text_lower or "plans that" in text_lower or "should insert:" in text_lower) 
                    and "insert:" in text_lower)
        
        # For INSTRUCTIONAL types, require specific instruction keywords
        elif "instructional" in var_type.value:
            return any(keyword.lower() in text_lower for keyword in keywords)
        
        # For IF_APPLICABLE_INSTRUCTIONAL_INSERT, require very specific pattern
        elif var_type == VariableType.IF_APPLICABLE_INSTRUCTIONAL_INSERT:
            # Must have "if" + "insert:" but NOT "insert if applicable"
            return ("if" in text_lower and "insert:" in text_lower and 
                    "insert if applicable" not in text_lower)
        
        # For SELECT_ONE, require "select one"
        elif var_type == VariableType.SELECT_ONE:
            return "select one" in text_lower
        
        # For URL insertion
        elif var_type == VariableType.INSERT_URL:
            return ("insert url" in text_lower or 
                    (text_lower == "[insert url]"))
        
        # Default keyword matching
        else:
            return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _heuristic_classification(self, text: str, context_before: str, context_after: str) -> VariableClassification:
        """Use heuristic analysis when pattern matching fails."""
        text_lower = text.lower()
        
        # Heuristic rules based on content analysis
        if "insert" in text_lower and "url" in text_lower:
            return self._create_basic_classification(VariableType.INSERT_URL, text, 0.8)
        elif "select one" in text_lower:
            return self._create_basic_classification(VariableType.SELECT_ONE, text, 0.8)
        elif "optional" in text_lower:
            return self._create_basic_classification(VariableType.OPTIONAL, text, 0.8)
        elif "delete if" in text_lower or "remove if" in text_lower:
            return self._create_basic_classification(VariableType.DELETE_IF, text, 0.8)
        elif "insert" in text_lower:
            return self._create_basic_classification(VariableType.INSERT, text, 0.6)
        else:
            return self._create_basic_classification(VariableType.FREEFORM, text, 0.4)
    
    def _create_basic_classification(self, var_type: VariableType, text: str, confidence: float) -> VariableClassification:
        """Create a basic classification result."""
        field_id = self._generate_field_id(text, var_type)
        
        return VariableClassification(
            variable_type=var_type,
            field_id=field_id,
            confidence_score=confidence,
            insert_fields=[],
            options=[],
            prunable_terms=[],
            data_sources=[]
        )
    
    def _enhance_classification_metadata(self, classification: VariableClassification, 
                                       text: str, context_before: str, context_after: str) -> VariableClassification:
        """Enhance classification with detailed metadata based on variable type."""
        var_type = classification.variable_type
        
        if var_type == VariableType.INSERT:
            classification.requires_user_input = True
            classification.expected_data_type = self._detect_data_type(text)
            
        elif var_type == VariableType.SELECT_ONE:
            classification.options = self._extract_options(text)
            classification.requires_user_input = True
            
        elif var_type == VariableType.IF_APPLICABLE:
            # Extract the content after "if applicable:"
            classification.insert_text = self._extract_if_applicable_content(text)
            classification.editor_instruction = True
            classification.requires_user_input = True
            
        elif var_type == VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL:
            classification.condition_text, classification.insert_text = self._extract_condition_and_insert(text)
            classification.editor_instruction = True
            classification.requires_regulatory_awareness = "threshold" in text.lower() or "cms" in text.lower()
            classification.requires_user_input = True  # Usually needs plan-specific evaluation
            
        elif var_type == VariableType.INSTRUCTIONAL_INLINE_DELETION:
            classification.modifies_text_right_of_vpx = True
            classification.requires_pruning = True
            classification.editor_instruction = True
            classification.prunable_terms = self._extract_prunable_terms(context_after)
            
        elif var_type == VariableType.COMPLEX_STRUCTURAL_INSERT:
            classification.requires_structured_input = True
            classification.has_multiple_subfields = True
            classification.appendix_allowed = True
            classification.insert_fields = ["state", "county", "zip codes"]
            
        elif var_type == VariableType.REGULATORY_CONDITIONAL_INSERT:
            classification.requires_regulatory_awareness = True
            classification.editor_instruction = True
            
        elif var_type == VariableType.INSERT_URL:
            classification.requires_validation = True
            classification.expected_data_type = "url"
            
        elif var_type == VariableType.INSTRUCTIONAL_STRUCTURAL_DELETION:
            classification.renumber_required = True
            classification.editor_instruction = True
            classification.instruction_scope = self._detect_instruction_scope(text)
            
        elif var_type == VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT:
            classification.options = self._extract_complex_options(text)
            classification.allow_table = True
            classification.allow_attachment_reference = True
            classification.editor_instruction = True
            
        elif var_type == VariableType.INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH:
            classification.affects_prior_paragraph = True
            classification.condition_text, classification.replacement_text = self._extract_replacement_info(text)
            classification.editor_instruction = True
            
        elif var_type == VariableType.PERMISSIVE_CONDITIONAL_INSERT:
            classification.requires_user_input = True
            classification.editor_instruction = True
            
        elif var_type == VariableType.INSTRUCTIONAL_CLAUSE_OMISSION:
            classification.retain_rest_of_sentence = True
            classification.editor_instruction = True
            classification.condition_text, classification.target_text = self._extract_omission_info(text)
            
        elif var_type == VariableType.INSTRUCTIONAL_CROSS_REFERENCE_REQUIREMENT:
            classification.enforce_structural_completeness = True
            classification.editor_instruction = True
            classification.condition_text, classification.required_action = self._extract_cross_ref_info(text)
            
        elif var_type == VariableType.INSERT_NUMERIC_INLINE:
            classification.expected_data_type = "integer"
            classification.insert_position = "inline"
            classification.requires_user_input = True
            
        elif var_type == VariableType.INSERT_PLAN_SPECIFICS_COMPOSITE:
            classification.requires_structured_input = True
            classification.data_sources = ["billing setup", "ops", "customer service", "compliance"]
            classification.requires_user_input = True
            
        return classification
    
    def _generate_field_id(self, text: str, var_type: VariableType) -> str:
        """Generate a unique field ID for the variable."""
        # Extract key words and create camelCase ID
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words
        filtered_words = [w for w in words if w not in ['insert', 'select', 'one', 'if', 'applicable', 'the', 'a', 'an', 'and', 'or']]
        
        if not filtered_words:
            filtered_words = [var_type.value.replace('_', '')]
        
        # Convert to camelCase
        field_id = filtered_words[0]
        for word in filtered_words[1:]:
            field_id += word.capitalize()
        
        return field_id
    
    def _detect_data_type(self, text: str) -> str:
        """Detect the expected data type for insert variables."""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['phone', 'number', 'tty']):
            return "phone_number"
        elif any(keyword in text_lower for keyword in ['url', 'website']):
            return "url"
        elif any(keyword in text_lower for keyword in ['email']):
            return "email"
        elif any(keyword in text_lower for keyword in ['date', 'year']):
            return "date"
        elif any(keyword in text_lower for keyword in ['name']):
            return "text"
        elif any(keyword in text_lower for keyword in ['amount', 'cost', 'premium']):
            return "currency"
        else:
            return "text"
    
    def _extract_options(self, text: str) -> List[str]:
        """Extract options from select_one variables."""
        # Look for patterns like "A/B/C" or "Yes/No"
        pattern = r':\s*([^]]+)$'
        match = re.search(pattern, text)
        if match:
            options_text = match.group(1)
            return [opt.strip() for opt in re.split(r'[/|]', options_text)]
        return []
    
    def _extract_condition_and_insert(self, text: str) -> Tuple[str, str]:
        """Extract condition and insert text from compound conditionals."""
        # Try pattern with comma first (legacy format)
        pattern_with_comma = r'^\[([^,]+),\s*insert:\s*([^]]+)\]$'
        match = re.search(pattern_with_comma, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Try pattern without comma (new format like "Plans that meet... insert:")
        # Handle nested brackets in the insert text
        pattern_without_comma = r'^\[([^]]+)\s+insert:\s*(.+)\]$'
        match = re.search(pattern_without_comma, text, re.IGNORECASE | re.DOTALL)
        if match:
            condition_part = match.group(1).strip()
            insert_part = match.group(2).strip()
            # Remove the last ] if it's just the closing bracket of the main variable
            if insert_part.endswith(']') and not insert_part.endswith(']]'):
                insert_part = insert_part[:-1].strip()
            return condition_part, insert_part
        
        # Try pattern with "should insert:"
        pattern_should_insert = r'^\[([^]]+)\s+should\s+insert:\s*([^]]+)\]$'
        match = re.search(pattern_should_insert, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        return "", ""
    
    def _extract_prunable_terms(self, context_after: str) -> List[str]:
        """Extract terms that can be pruned from inline deletion instructions."""
        # Look for comma-separated lists in the following text
        if not context_after:
            return []
        
        # Find the first sentence after the variable
        first_sentence = context_after.split('.')[0]
        # Extract terms that might be in a list
        terms = re.findall(r'\b[a-zA-Z]+(?:\s+[a-zA-Z]+)*\b', first_sentence)
        return terms[:5]  # Limit to first 5 terms
    
    def _detect_instruction_scope(self, text: str) -> str:
        """Detect the scope of instruction (bullet, section, chapter, etc.)."""
        text_lower = text.lower()
        
        if "bullet" in text_lower:
            return "bullet list"
        elif "section" in text_lower:
            return "section"
        elif "chapter" in text_lower:
            return "chapter"
        elif "paragraph" in text_lower:
            return "paragraph"
        else:
            return "text block"
    
    def _extract_complex_options(self, text: str) -> List[str]:
        """Extract options from complex select_one_with_embedded_insert variables."""
        # Split on "OR" to get different options
        options = re.split(r'\s+OR\s+', text, flags=re.IGNORECASE)
        return [opt.strip() for opt in options if opt.strip()]
    
    def _extract_replacement_info(self, text: str) -> Tuple[str, str]:
        """Extract condition and replacement text from replacement instructions."""
        pattern = r'Plans\s+with\s+([^]]+)\s+should\s+replace\s+the\s+preceding\s+paragraph\s+with:\s*([^]]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return "", ""
    
    def _extract_omission_info(self, text: str) -> Tuple[str, str]:
        """Extract condition and target text from omission instructions."""
        pattern = r'Plans\s+with\s+([^,]+),\s*omit:\s*([^]]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return "", ""
    
    def _extract_cross_ref_info(self, text: str) -> Tuple[str, str]:
        """Extract condition and required action from cross-reference requirements."""
        pattern = r'If\s+([^,]+),\s*then\s+([^]]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        return "", ""
    
    def _extract_if_applicable_content(self, text: str) -> Optional[str]:
        """Extract the content after 'if applicable:' from IF_APPLICABLE variables."""
        # Pattern: [insert if applicable: CONTENT] or [Insert if applicable: CONTENT]
        patterns = [
            r'\[insert\s+if\s+applicable:\s*([^\]]+)\]',
            r'\[Insert\s+if\s+applicable:\s*([^\]]+)\]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def get_heuristic_behavior(self, classification: VariableClassification) -> Dict[str, Any]:
        """
        Get the heuristic behavior rules for a classified variable.
        
        Returns a dictionary with behavior instructions based on the variable type.
        """
        var_type = classification.variable_type
        
        behaviors = {
            VariableType.INSERT: {
                "action": "prompt_user_input",
                "validation": classification.expected_data_type,
                "required": True
            },
            
            VariableType.SELECT_ONE: {
                "action": "present_options",
                "options": classification.options,
                "required": True,
                "exclusive": True
            },
            
            VariableType.OPTIONAL: {
                "action": "conditional_inclusion",
                "default": "omit",
                "user_choice": True
            },
            
            VariableType.DELETE_IF: {
                "action": "conditional_deletion",
                "prompt": f"Should this content be deleted? Condition: {classification.condition_text}",
                "affects_structure": True
            },
            
            VariableType.IF_APPLICABLE: {
                "action": "conditional_insertion",
                "condition": classification.condition_text,
                "insert_text": classification.insert_text,
                "user_confirmation_required": True
            },
            
            VariableType.IF_APPLICABLE_COMPOUND_CONDITIONAL: {
                "action": "conditional_insertion",
                "condition": classification.condition_text,
                "insert_text": classification.insert_text,
                "user_confirmation_required": True,
                "description": "Evaluate condition and conditionally insert specified text",
                "processing_note": "Content after colon ':' should be inserted if condition is met",
                "condition_type": "plan_characteristic_check"
            },
            
            VariableType.INSTRUCTIONAL_INLINE_DELETION: {
                "action": "prune_terms",
                "target_text": "text_right_of_variable",
                "prunable_terms": classification.prunable_terms,
                "present_as_checkboxes": True
            },
            
            VariableType.COMPLEX_STRUCTURAL_INSERT: {
                "action": "structured_input_form",
                "fields": classification.insert_fields,
                "hierarchical": True,
                "allow_appendix": classification.appendix_allowed
            },
            
            VariableType.REGULATORY_CONDITIONAL_INSERT: {
                "action": "regulatory_check",
                "condition": classification.condition_text,
                "insert_text": classification.insert_text,
                "requires_cms_compliance": True
            },
            
            VariableType.INSTRUCTIONAL_STRUCTURAL_DELETION: {
                "action": "structural_deletion",
                "scope": classification.instruction_scope,
                "renumber": classification.renumber_required,
                "condition": classification.condition_text
            },
            
            VariableType.SELECT_ONE_WITH_EMBEDDED_INSERT: {
                "action": "complex_selection",
                "options": classification.options,
                "embedded_inserts": True,
                "allow_table": classification.allow_table,
                "allow_attachment": classification.allow_attachment_reference
            },
            
            VariableType.INSTRUCTIONAL_REPLACEMENT_PRIOR_PARAGRAPH: {
                "action": "paragraph_replacement",
                "condition": classification.condition_text,
                "replacement_text": classification.replacement_text,
                "affects_prior_paragraph": True
            },
            
            VariableType.INSERT_URL: {
                "action": "url_input",
                "validation": "url_format",
                "required": True
            },
            
            VariableType.INSERT_NUMERIC_INLINE: {
                "action": "numeric_input",
                "data_type": "integer",
                "position": "inline",
                "preserve_grammar": True
            },
            
            VariableType.INSERT_PLAN_SPECIFICS_COMPOSITE: {
                "action": "composite_input",
                "data_sources": classification.data_sources,
                "output_format": "narrative_paragraph",
                "multiple_fields": True
            },
            
            VariableType.OPTIONAL_CONDITIONAL_WITH_EMBEDDED_SELECT: {
                "action": "conditional_selection",
                "primary_condition": "plan_type_check",
                "embedded_selection": True,
                "conditional_text": classification.condition_text,
                "selection_options": classification.options,
                "requires_biconditional_logic": True,
                "wizard_question_type": "compound_conditional"
            },
            
            VariableType.OPTIONAL_INFORMATION_COMPOUND: {
                "action": "optional_compound_content",
                "conditional_inclusion": True,
                "condition_type": "plan_characteristic",
                "content_structure": "informational_block",
                "requires_user_decision": True,
                "wizard_question_type": "optional_conditional"
            }
        }
        
        return behaviors.get(var_type, {"action": "manual_review", "reason": "unhandled_type"})


# Factory function for easy instantiation
def create_enhanced_classifier() -> EnhancedVariableClassifier:
    """Create and return an enhanced variable classifier instance."""
    return EnhancedVariableClassifier()


# Example usage and testing
if __name__ == "__main__":
    classifier = create_enhanced_classifier()
    
    # Test cases from the heuristics guide
    test_cases = [
        "[insert 2025 plan name]",
        "[select one: Yes/No]",
        "[Optional] You may also request a printed copy.",
        "[Delete if not applicable]",
        "[Insert if applicable: URLs, notices]",
        "[Plans with grandfathered members who were outside of area prior to January 1999, insert: If you have been a member of our plan continuously since before January 1999...]",
        "[Remove terms as needed to reflect plan benefits]",
        "[insert URL]",
        "[insert number of payment options]",
        "[Delete Optional Supplemental Benefit Premium bullet if your plan doesn't offer optional supplemental benefits. Renumber remaining sections as appropriate.]"
    ]
    
    print("Enhanced Variable Classifier Test Results:")
    print("=" * 60)
    
    for test_case in test_cases:
        classification = classifier.classify_variable(test_case)
        behavior = classifier.get_heuristic_behavior(classification)
        
        print(f"\nVariable: {test_case}")
        print(f"Type: {classification.variable_type.value}")
        print(f"Field ID: {classification.field_id}")
        print(f"Confidence: {classification.confidence_score:.2f}")
        print(f"Behavior: {behavior['action']}")
        if classification.editor_instruction:
            print("⚠️  Editor Instruction: True")
        if classification.requires_user_input:
            print("👤 Requires User Input: True")