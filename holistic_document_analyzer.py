#!/usr/bin/env python3
"""
Holistic Document Analyzer - Provides complete understanding of variable patterns in CMS documents.

This module analyzes the entire document to understand:
- Where each variable occurs (exact locations)
- How many times each variable appears
- Context and relationships between variables
- Logical groupings for efficient user interaction
"""

import os
import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
from docx import Document

from logging_config import logger


@dataclass
class VariableOccurrence:
    """Represents a single occurrence of a variable in the document."""
    variable_name: str
    paragraph_index: int
    paragraph_text: str
    position_in_paragraph: int
    surrounding_context: str
    section_title: str = ""


@dataclass
class VariablePattern:
    """Represents the complete pattern of a variable across the document."""
    variable_name: str
    normalized_name: str
    total_occurrences: int
    locations: List[VariableOccurrence]
    variable_type: str
    extraction_confidence: float = 0.0
    suggested_value: str = ""


@dataclass
class DocumentSection:
    """Represents a logical section of the document."""
    title: str
    start_paragraph: int
    end_paragraph: int
    variables: List[str]


class HolisticDocumentAnalyzer:
    """
    Analyzes CMS documents holistically to understand variable patterns and enable
    intelligent deduplication and sequencing.
    """
    
    def __init__(self, model_docx_path: str):
        self.model_docx_path = model_docx_path
        self.variable_patterns: Dict[str, VariablePattern] = {}
        self.document_sections: List[DocumentSection] = []
        self.total_variables_found = 0
        self.unique_variables = 0
        self.duplication_savings = 0
        
    def analyze_document(self) -> Dict:
        """
        Perform complete holistic analysis of the document.
        
        Returns:
            Dict: Complete analysis results including patterns, sections, and optimization stats
        """
        logger.info(f"🔍 Starting holistic analysis of {os.path.basename(self.model_docx_path)}")
        
        try:
            # Load the document
            doc = Document(self.model_docx_path)
            
            # Step 1: Extract all variable occurrences with full context
            logger.info("📊 Extracting variable occurrences...")
            all_occurrences = self._extract_all_variable_occurrences(doc)
            logger.info(f"📊 Found {len(all_occurrences)} total variable occurrences")
            
            # Step 2: Analyze patterns and create variable mappings
            logger.info("🎯 Analyzing variable patterns...")
            self._analyze_variable_patterns(all_occurrences)
            logger.info(f"🎯 Identified {len(self.variable_patterns)} unique variable patterns")
            
            # Step 3: Identify document sections for logical grouping
            logger.info("📑 Identifying document sections...")
            self._identify_document_sections(doc)
            logger.info(f"📑 Mapped {len(self.document_sections)} document sections")
            
            # Step 4: Calculate optimization opportunities
            logger.info("⚡ Calculating optimization stats...")
            optimization_stats = self._calculate_optimization_stats()
            logger.info(f"⚡ Potential savings: {optimization_stats['questions_saved']} questions ({optimization_stats['efficiency_percentage']:.1f}%)")
            
            return {
                'variable_patterns': self.variable_patterns,
                'document_sections': self.document_sections,
                'optimization_stats': optimization_stats,
                'total_variables': self.total_variables_found,
                'unique_variables': self.unique_variables,
                'analysis_successful': True
            }
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Holistic analysis failed: {e}")
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            return {
                'analysis_successful': False,
                'error': str(e),
                'total_variables': 0,
                'unique_variables': 0
            }
    
    def _extract_all_variable_occurrences(self, doc: Document) -> List[VariableOccurrence]:
        """Extract every variable occurrence with complete context information."""
        occurrences = []
        # Use the exact pattern from working wizard builder
        variable_pattern = re.compile(r"\\[([^\\[\\]]+)\\]")
        
        for para_idx, paragraph in enumerate(doc.paragraphs):
            para_text = paragraph.text.strip()
            if not para_text:
                continue
                
            # Find all variables in this paragraph
            for match in variable_pattern.finditer(para_text):
                variable_name = match.group(1).strip()
                position = match.start()
                
                # Extract surrounding context (50 chars before and after)
                context_start = max(0, position - 50)
                context_end = min(len(para_text), position + len(match.group(0)) + 50)
                surrounding_context = para_text[context_start:context_end]
                
                # Determine section title (look backwards for headings)
                section_title = self._find_section_title(doc, para_idx)
                
                occurrence = VariableOccurrence(
                    variable_name=variable_name,
                    paragraph_index=para_idx,
                    paragraph_text=para_text,
                    position_in_paragraph=position,
                    surrounding_context=surrounding_context,
                    section_title=section_title
                )
                
                occurrences.append(occurrence)
                
        self.total_variables_found = len(occurrences)
        return occurrences
    
    def _find_section_title(self, doc: Document, para_idx: int) -> str:
        """Find the section title for a given paragraph by looking backwards."""
        # Look backwards up to 10 paragraphs to find a heading-style paragraph
        for i in range(max(0, para_idx - 10), para_idx):
            para = doc.paragraphs[i]
            para_text = para.text.strip()
            
            # Check if this looks like a heading (short, no variables, possibly styled)
            if (para_text and 
                len(para_text) < 100 and 
                not re.search(r'\\[[^\\]]+\\]', para_text) and
                (para_text.isupper() or 
                 para_text.startswith('Chapter') or 
                 para_text.startswith('Section') or
                 len(para_text.split()) <= 8)):
                return para_text
        
        return "Unknown Section"
    
    def _analyze_variable_patterns(self, occurrences: List[VariableOccurrence]):
        """Analyze all occurrences to create comprehensive variable patterns."""
        # Group occurrences by variable name
        grouped_occurrences = defaultdict(list)
        for occurrence in occurrences:
            grouped_occurrences[occurrence.variable_name].append(occurrence)
        
        self.unique_variables = len(grouped_occurrences)
        
        # Create pattern analysis for each unique variable
        for var_name, var_occurrences in grouped_occurrences.items():
            # Normalize variable name for comparison
            normalized_name = self._normalize_variable_name(var_name)
            
            # Classify variable type based on content
            var_type = self._classify_variable_type(var_name)
            
            # Create the pattern
            pattern = VariablePattern(
                variable_name=var_name,
                normalized_name=normalized_name,
                total_occurrences=len(var_occurrences),
                locations=var_occurrences,
                variable_type=var_type
            )
            
            self.variable_patterns[var_name] = pattern
    
    def _normalize_variable_name(self, var_name: str) -> str:
        """Normalize variable names for duplicate detection."""
        # Convert to lowercase and remove common prefixes/suffixes
        normalized = var_name.lower().strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['insert ', 'enter ', 'add ', 'include ']
        for prefix in prefixes_to_remove:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        # Remove year variations for comparison
        normalized = re.sub(r'\\b(2024|2025|2026)\\b', 'YEAR', normalized)
        
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^a-zA-Z0-9\\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def _classify_variable_type(self, var_name: str) -> str:
        """Classify variables into logical types for better organization."""
        var_lower = var_name.lower()
        
        # Plan and coverage information
        if any(term in var_lower for term in ['plan name', 'plan', 'coverage']):
            return 'plan_info'
        
        # Contact information
        elif any(term in var_lower for term in ['phone', 'number', 'contact', 'customer service', 'tty']):
            return 'contact_info'
        
        # Dates and times
        elif any(term in var_lower for term in ['date', 'year', '2024', '2025', '2026', 'hours', 'days']):
            return 'temporal_info'
        
        # Financial information
        elif any(term in var_lower for term in ['premium', 'cost', 'copay', 'deductible', 'amount']):
            return 'financial_info'
        
        # URLs and links
        elif any(term in var_lower for term in ['url', 'website', 'link', 'directory']):
            return 'web_info'
        
        # Conditional content
        elif any(term in var_lower for term in ['if applicable', 'optional', 'select one']):
            return 'conditional_content'
        
        # Location information
        elif any(term in var_lower for term in ['state', 'region', 'area', 'territory']):
            return 'location_info'
        
        else:
            return 'general_content'
    
    def _identify_document_sections(self, doc: Document):
        """Identify logical sections in the document for organized variable presentation."""
        current_section = None
        section_start = 0
        
        for para_idx, paragraph in enumerate(doc.paragraphs):
            para_text = paragraph.text.strip()
            
            # Check if this paragraph looks like a section header
            if self._is_section_header(para_text):
                # Save the previous section if it exists
                if current_section:
                    section = DocumentSection(
                        title=current_section,
                        start_paragraph=section_start,
                        end_paragraph=para_idx - 1,
                        variables=self._get_variables_in_range(section_start, para_idx - 1)
                    )
                    self.document_sections.append(section)
                
                # Start new section
                current_section = para_text
                section_start = para_idx
        
        # Add the final section
        if current_section:
            section = DocumentSection(
                title=current_section,
                start_paragraph=section_start,
                end_paragraph=len(doc.paragraphs) - 1,
                variables=self._get_variables_in_range(section_start, len(doc.paragraphs) - 1)
            )
            self.document_sections.append(section)
    
    def _is_section_header(self, para_text: str) -> bool:
        """Determine if a paragraph is likely a section header."""
        if not para_text or len(para_text) > 150:
            return False
        
        # Check for common section header patterns
        header_patterns = [
            r'^Chapter \\d+',
            r'^Section \\d+',
            r'^\\d+\\.\\d+',
            r'^[A-Z\\s]{10,}$',  # ALL CAPS headers
            r'^Benefits\\s',
            r'^Coverage\\s',
            r'^Member\\s',
            r'^Plan\\s'
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, para_text, re.IGNORECASE):
                return True
        
        # Check if it's short and has no variables
        if (len(para_text.split()) <= 8 and 
            not re.search(r'\\[[^\\]]+\\]', para_text) and
            para_text[0].isupper()):
            return True
        
        return False
    
    def _get_variables_in_range(self, start_para: int, end_para: int) -> List[str]:
        """Get all unique variables in a paragraph range."""
        variables = set()
        for pattern in self.variable_patterns.values():
            for occurrence in pattern.locations:
                if start_para <= occurrence.paragraph_index <= end_para:
                    variables.add(pattern.variable_name)
        return list(variables)
    
    def _calculate_optimization_stats(self) -> Dict:
        """Calculate potential optimization from smart deduplication."""
        total_questions = self.total_variables_found
        unique_questions = self.unique_variables
        questions_saved = total_questions - unique_questions
        efficiency_percentage = (questions_saved / total_questions * 100) if total_questions > 0 else 0
        
        # Identify the most duplicated variables
        top_duplicates = sorted(
            [(name, pattern.total_occurrences) for name, pattern in self.variable_patterns.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'total_questions_original': total_questions,
            'unique_questions_optimized': unique_questions,
            'questions_saved': questions_saved,
            'efficiency_percentage': efficiency_percentage,
            'top_duplicate_variables': top_duplicates,
            'sections_identified': len(self.document_sections),
            'variable_types_found': len(set(p.variable_type for p in self.variable_patterns.values()))
        }
    
    def get_optimized_variable_sequence(self) -> List[Dict]:
        """
        Generate an optimized sequence of variables for the wizard.
        
        This eliminates duplicates and presents variables in a logical order:
        1. Plan information (most reused)
        2. Contact information
        3. Financial information  
        4. Section-by-section unique variables
        
        Returns:
            List[Dict]: Optimized variable list with context and occurrence info
        """
        optimized_sequence = []
        processed_variables = set()
        
        # Priority order for variable types
        type_priority = [
            'plan_info',
            'contact_info', 
            'temporal_info',
            'financial_info',
            'web_info',
            'location_info',
            'general_content',
            'conditional_content'
        ]
        
        # Process variables by type priority
        for var_type in type_priority:
            type_variables = [
                (name, pattern) for name, pattern in self.variable_patterns.items() 
                if pattern.variable_type == var_type and name not in processed_variables
            ]
            
            # Sort by occurrence count (most duplicated first)
            type_variables.sort(key=lambda x: x[1].total_occurrences, reverse=True)
            
            for var_name, pattern in type_variables:
                optimized_var = {
                    'name': var_name,
                    'type': pattern.variable_type,
                    'occurrences': pattern.total_occurrences,
                    'sections': list(set(occ.section_title for occ in pattern.locations)),
                    'first_occurrence_context': pattern.locations[0].surrounding_context,
                    'is_duplicate': pattern.total_occurrences > 1,
                    'optimization_impact': pattern.total_occurrences - 1  # Questions saved
                }
                
                optimized_sequence.append(optimized_var)
                processed_variables.add(var_name)
        
        logger.info(f"✨ Generated optimized sequence: {len(optimized_sequence)} unique variables (reduced from {self.total_variables_found})")
        return optimized_sequence


def test_holistic_analyzer():
    """Test the holistic document analyzer with a sample document."""
    import sys
    import os
    
    # Look for a test document
    test_paths = [
        '../assets/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx',
        '../assets/DRAFT_CY2026_8_PPO_MA_EOC_FINAL (2).docx',
        'assets/templates/DRAFT_CY2026_8_PPO_MA_EOC_FINAL.docx'
    ]
    
    test_doc = None
    for path in test_paths:
        if os.path.exists(path):
            test_doc = path
            break
    
    if not test_doc:
        print("❌ No test document found")
        return
    
    print(f"🧪 Testing Holistic Document Analyzer with: {os.path.basename(test_doc)}")
    
    analyzer = HolisticDocumentAnalyzer(test_doc)
    results = analyzer.analyze_document()
    
    if results['analysis_successful']:
        print(f"✅ Analysis completed successfully!")
        print(f"📊 Total variables found: {results['total_variables']}")
        print(f"🎯 Unique variables: {results['unique_variables']}")
        print(f"⚡ Questions saved: {results['optimization_stats']['questions_saved']}")
        print(f"📈 Efficiency improvement: {results['optimization_stats']['efficiency_percentage']:.1f}%")
        
        # Show optimized sequence
        optimized = analyzer.get_optimized_variable_sequence()
        print(f"\\n🚀 Optimized wizard sequence ({len(optimized)} steps):")
        for i, var in enumerate(optimized[:10], 1):  # Show first 10
            duplicate_info = f" ({var['occurrences']}x)" if var['is_duplicate'] else ""
            print(f"  {i}. [{var['name']}] - {var['type']}{duplicate_info}")
        
        if len(optimized) > 10:
            print(f"  ... and {len(optimized) - 10} more variables")
    else:
        print(f"❌ Analysis failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    test_holistic_analyzer()