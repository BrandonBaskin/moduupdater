#!/usr/bin/env python3
"""
Enhanced Document Context System
Extracts meaningful structural context for variables including sections, headings, and location info
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
try:
    from docx import Document
    from docx.shared import Inches
except ImportError:
    Document = None

@dataclass
class DocumentContext:
    """Rich context information for a document location."""
    section_title: Optional[str] = None
    chapter_title: Optional[str] = None
    subsection_title: Optional[str] = None
    paragraph_number: Optional[str] = None
    page_estimate: Optional[int] = None
    content_type: str = "text"  # text, table, list, etc.
    before_text: str = ""
    after_text: str = ""
    full_paragraph: str = ""
    structural_path: List[str] = None

    def __post_init__(self):
        if self.structural_path is None:
            self.structural_path = []

class EnhancedDocumentContextExtractor:
    """Enhanced extractor that captures document structure and meaningful context."""
    
    def __init__(self):
        if not Document:
            raise ImportError("python-docx is required for enhanced context extraction")
        
        # Patterns for detecting structural elements
        self.heading_patterns = [
            r'^Chapter\s+(\d+|\w+):\s*(.+)$',
            r'^Section\s+(\d+(?:\.\d+)*):\s*(.+)$',
            r'^(\d+)\.\s*(.+)$',
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headings
            r'^([A-Z][a-z\s]+):?\s*$'  # Title case headings
        ]
        
        self.current_chapter = None
        self.current_section = None
        self.current_subsection = None
    
    def extract_document_structure(self, file_path: str) -> Dict[str, DocumentContext]:
        """Extract structure and context for all variables in a document."""
        try:
            doc = Document(file_path)
            variable_contexts = {}
            
            # Track document structure as we parse
            for para_idx, para in enumerate(doc.paragraphs):
                para_text = para.text.strip()
                if not para_text:
                    continue
                
                # Update current structural context
                self._update_structural_context(para, para_text)
                
                # Find variables in this paragraph
                variables = self._extract_variables_from_text(para_text)
                
                for var_name in variables:
                    context = self._create_context_for_variable(
                        var_name, para_text, para_idx, doc.paragraphs
                    )
                    variable_contexts[var_name] = context
            
            return variable_contexts
            
        except Exception as e:
            print(f"Error extracting document structure: {e}")
            return {}
    
    def _update_structural_context(self, para, para_text: str):
        """Update current chapter/section/subsection based on paragraph style and content."""
        
        # Check if this is a heading based on style
        if hasattr(para, 'style') and para.style.name:
            style_name = para.style.name.lower()
            if 'heading' in style_name:
                level = self._extract_heading_level(para.style.name)
                self._assign_heading_by_level(para_text, level)
                return
        
        # Check if this is a heading based on text patterns
        for pattern in self.heading_patterns:
            match = re.match(pattern, para_text.strip(), re.IGNORECASE)
            if match:
                self._process_heading_match(match, para_text, pattern)
                return
    
    def _extract_heading_level(self, style_name: str) -> int:
        """Extract heading level from style name."""
        match = re.search(r'heading\s*(\d+)', style_name.lower())
        return int(match.group(1)) if match else 1
    
    def _assign_heading_by_level(self, text: str, level: int):
        """Assign text to appropriate structural level based on heading level."""
        if level == 1:
            self.current_chapter = text
            self.current_section = None
            self.current_subsection = None
        elif level == 2:
            self.current_section = text
            self.current_subsection = None
        elif level >= 3:
            self.current_subsection = text
    
    def _process_heading_match(self, match, para_text: str, pattern: str):
        """Process a heading match and update structural context."""
        if 'Chapter' in pattern:
            self.current_chapter = para_text
            self.current_section = None
            self.current_subsection = None
        elif 'Section' in pattern:
            self.current_section = para_text
            self.current_subsection = None
        elif r'(\d+)\.' in pattern:
            # Numbered section
            if self.current_section is None:
                self.current_section = para_text
            else:
                self.current_subsection = para_text
        else:
            # General heading
            if self.current_chapter is None:
                self.current_chapter = para_text
            elif self.current_section is None:
                self.current_section = para_text
            else:
                self.current_subsection = para_text
    
    def _extract_variables_from_text(self, text: str) -> List[str]:
        """Extract variable names from text."""
        pattern = r'\[([^\]]+)\]'
        matches = re.findall(pattern, text)
        return [f"[{match}]" for match in matches]
    
    def _create_context_for_variable(self, var_name: str, para_text: str, 
                                   para_idx: int, all_paragraphs) -> DocumentContext:
        """Create rich context for a specific variable."""
        
        # Extract surrounding text
        before_text, after_text = self._extract_surrounding_text(var_name, para_text)
        
        # Get additional context from nearby paragraphs
        context_paragraphs = self._get_context_paragraphs(para_idx, all_paragraphs)
        
        # Build structural path
        structural_path = []
        if self.current_chapter:
            structural_path.append(self.current_chapter)
        if self.current_section:
            structural_path.append(self.current_section)
        if self.current_subsection:
            structural_path.append(self.current_subsection)
        
        # Estimate page number (rough estimate: 35 lines per page)
        page_estimate = (para_idx // 35) + 1
        
        return DocumentContext(
            chapter_title=self.current_chapter,
            section_title=self.current_section,
            subsection_title=self.current_subsection,
            page_estimate=page_estimate,
            content_type=self._detect_content_type(para_text),
            before_text=before_text,
            after_text=after_text,
            full_paragraph=para_text,
            structural_path=structural_path
        )
    
    def _extract_surrounding_text(self, var_name: str, para_text: str) -> Tuple[str, str]:
        """Extract text before and after the variable."""
        if var_name in para_text:
            parts = para_text.split(var_name, 1)
            before = parts[0].strip()
            after = parts[1].strip() if len(parts) > 1 else ""
            
            # Limit length for readability
            before = before[-100:] if len(before) > 100 else before
            after = after[:100] if len(after) > 100 else after
            
            return before, after
        return "", ""
    
    def _get_context_paragraphs(self, para_idx: int, all_paragraphs, 
                               context_range: int = 2) -> List[str]:
        """Get surrounding paragraphs for additional context."""
        start_idx = max(0, para_idx - context_range)
        end_idx = min(len(all_paragraphs), para_idx + context_range + 1)
        
        context_paras = []
        for i in range(start_idx, end_idx):
            if i != para_idx and all_paragraphs[i].text.strip():
                context_paras.append(all_paragraphs[i].text.strip())
        
        return context_paras
    
    def _detect_content_type(self, text: str) -> str:
        """Detect the type of content (table, list, text, etc.)."""
        text_lower = text.lower()
        
        if 'table' in text_lower or 'column' in text_lower:
            return "table"
        elif re.match(r'^\s*[\•\-\*]\s+', text) or re.match(r'^\s*\d+\.\s+', text):
            return "list"
        elif len(text.split('.')) > 3:
            return "paragraph"
        else:
            return "text"
    
    def format_context_for_display(self, context: DocumentContext, var_name: str) -> str:
        """Format context information for user-friendly display with full paragraph content."""
        
        # Build location path
        location_parts = []
        if context.structural_path:
            location_parts.extend(context.structural_path)
        
        location_str = " → ".join(location_parts) if location_parts else "Document"
        
        # Build context display
        context_lines = []
        
        # Location information header
        context_lines.append("=" * 60)
        context_lines.append("📍 DOCUMENT LOCATION & CONTEXT")
        context_lines.append("=" * 60)
        
        if location_str != "Document":
            context_lines.append(f"📍 Section: {location_str}")
        
        if context.page_estimate:
            context_lines.append(f"📄 Estimated Page: {context.page_estimate}")
        
        if context.content_type != "text":
            context_lines.append(f"📝 Content Type: {context.content_type}")
        
        context_lines.append("")
        context_lines.append("📄 FULL PARAGRAPH CONTAINING VARIABLE:")
        context_lines.append("-" * 60)
        
        # Show the complete paragraph with variable highlighted
        if context.full_paragraph:
            # Replace the variable with highlighted version
            display_paragraph = context.full_paragraph
            if var_name in display_paragraph:
                display_paragraph = display_paragraph.replace(var_name, f">>> {var_name} <<<")
            context_lines.append(display_paragraph)
        else:
            # Fallback: construct from before/after if full paragraph not available
            paragraph_parts = []
            if context.before_text:
                paragraph_parts.append(context.before_text)
            paragraph_parts.append(f">>> {var_name} <<<")
            if context.after_text:
                paragraph_parts.append(context.after_text)
            context_lines.append(" ".join(paragraph_parts))
        
        context_lines.append("-" * 60)
        
        return "\n".join(context_lines)

def create_enhanced_document_context_extractor():
    """Factory function to create enhanced document context extractor."""
    return EnhancedDocumentContextExtractor()

# Example usage and testing
if __name__ == "__main__":
    # This would be used to test the context extraction
    print("Enhanced Document Context Extractor - Test Mode")
    print("Use create_enhanced_document_context_extractor() to create an instance")