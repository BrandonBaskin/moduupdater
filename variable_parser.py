#!/usr/bin/env python3
"""
Enhanced Variable Parser for Colon-Separated VPX Entries
Properly parses variables with content after colons
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ParsedVariable:
    """Represents a parsed variable with all its components."""
    full_text: str          # Original [bracketed] text
    action: str             # Part before colon (e.g., "insert if applicable")
    content: Optional[str]  # Part after colon (e.g., "and durable medical equipment suppliers")
    nested_variables: List[str]  # Variables found within content
    options: List[str]      # OR-separated options
    is_colon_separated: bool
    variable_type: str      # Classified type for wizard

class EnhancedVariableParser:
    """Parser that handles colon-separated variables properly."""
    
    def parse_variable(self, variable_text: str) -> ParsedVariable:
        """
        Parse a variable into its components.
        
        Args:
            variable_text: Full bracketed variable like "[insert if applicable: content]"
            
        Returns:
            ParsedVariable with all components parsed
        """
        # Remove outer brackets and clean
        inner_text = variable_text.strip('[]').strip()
        
        # Check if it has colon-separated content
        if ':' not in inner_text:
            return ParsedVariable(
                full_text=variable_text,
                action=inner_text,
                content=None,
                nested_variables=[],
                options=[],
                is_colon_separated=False,
                variable_type=self._classify_simple_variable(inner_text)
            )
        
        # Split on first colon only
        colon_index = inner_text.find(':')
        action = inner_text[:colon_index].strip()
        content = inner_text[colon_index + 1:].strip()
        
        # Parse nested variables in content
        nested_vars = self._extract_nested_variables(content)
        
        # Parse OR options
        options = self._parse_options(content)
        
        # Classify the variable type
        var_type = self._classify_colon_variable(action, content)
        
        return ParsedVariable(
            full_text=variable_text,
            action=action,
            content=content,
            nested_variables=nested_vars,
            options=options,
            is_colon_separated=True,
            variable_type=var_type
        )
    
    def _extract_nested_variables(self, content: str) -> List[str]:
        """Extract nested variables from content."""
        if not content:
            return []
        
        # Find all [bracketed] content within the content
        nested_matches = re.findall(r'\[([^\]]+)\]', content)
        return [match.strip() for match in nested_matches]
    
    def _parse_options(self, content: str) -> List[str]:
        """Parse OR-separated options from content."""
        if not content or ' OR ' not in content:
            return []
        
        # Split on OR and clean up options
        options = []
        parts = content.split(' OR ')
        
        for part in parts:
            # Clean up each option
            option = part.strip()
            # Remove trailing punctuation that might be part of sentence structure
            option = re.sub(r'[.,:;)}\]]+$', '', option).strip()
            if option:
                options.append(option)
        
        return options
    
    def _classify_simple_variable(self, action: str) -> str:
        """Classify simple variables without colons."""
        action_lower = action.lower()
        
        if 'phone' in action_lower or 'customer service' in action_lower:
            return "phone_number"
        elif 'url' in action_lower or 'website' in action_lower:
            return "url"
        elif 'hours' in action_lower and 'operation' in action_lower:
            return "business_hours"
        elif 'tty' in action_lower:
            return "tty_number"
        else:
            return "general"
    
    def _classify_colon_variable(self, action: str, content: str) -> str:
        """Classify colon-separated variables."""
        action_lower = action.lower()
        
        if 'insert if applicable' in action_lower:
            return "conditional_insert"
        elif 'optional information' in action_lower:
            return "optional_content"
        elif 'select one' in action_lower:
            return "select_option"
        elif 'insert plan specifics' in action_lower:
            return "plan_specifics"
        elif 'delete' in action_lower:
            return "conditional_delete"
        else:
            return "colon_separated_general"
    
    def get_display_name_for_wizard(self, parsed_var: ParsedVariable) -> str:
        """Get a clean display name for the wizard."""
        if not parsed_var.is_colon_separated:
            return parsed_var.action
        
        # For colon-separated variables, use the action part
        return parsed_var.action
    
    def get_default_content_for_wizard(self, parsed_var: ParsedVariable) -> str:
        """Get default content to pre-fill in wizard."""
        if not parsed_var.is_colon_separated or not parsed_var.content:
            return ""
        
        # For conditional inserts, the content is what should be inserted
        if parsed_var.variable_type == "conditional_insert":
            return parsed_var.content
        
        # For optional content, the content describes what's optional
        if parsed_var.variable_type == "optional_content":
            return parsed_var.content
        
        # For select options, return the first option as default
        if parsed_var.variable_type == "select_option" and parsed_var.options:
            return parsed_var.options[0]
        
        return parsed_var.content
    
    def get_suggestions_for_wizard(self, parsed_var: ParsedVariable) -> List[str]:
        """Get suggestions based on the parsed variable."""
        suggestions = []
        
        # Add options if available
        if parsed_var.options:
            suggestions.extend(parsed_var.options)
        
        # Add default content if not already in suggestions
        default_content = self.get_default_content_for_wizard(parsed_var)
        if default_content and default_content not in suggestions:
            suggestions.insert(0, default_content)
        
        # Add type-specific suggestions
        if parsed_var.variable_type == "conditional_insert":
            if not suggestions:
                suggestions.extend([
                    "Include if applicable",
                    "Not applicable",
                    ""
                ])
        elif parsed_var.variable_type == "optional_content":
            if not suggestions:
                suggestions.extend([
                    "Include optional information",
                    "Not applicable",
                    ""
                ])
        
        return suggestions[:5]

# Create a global parser instance
_parser = EnhancedVariableParser()

def parse_variable(variable_text: str) -> ParsedVariable:
    """Global function to parse a variable."""
    return _parser.parse_variable(variable_text)

def get_variable_display_info(variable_text: str) -> Tuple[str, str, List[str]]:
    """
    Get display information for a variable in the wizard.
    
    Returns:
        (display_name, default_content, suggestions)
    """
    parsed = parse_variable(variable_text)
    
    display_name = _parser.get_display_name_for_wizard(parsed)
    default_content = _parser.get_default_content_for_wizard(parsed)
    suggestions = _parser.get_suggestions_for_wizard(parsed)
    
    return display_name, default_content, suggestions