#!/usr/bin/env python3
"""
Enhanced Nested Variable Parser
Handles complex nested VPX structures with conditional variables
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class NestedVariable:
    """Represents a variable that can contain other variables."""
    text: str                           # Full bracketed text
    action: str                         # Primary action (e.g., "Select one of the following")
    content: str                        # Content after colon
    is_colon_separated: bool
    variable_type: str                  # Type classification
    options: List[str] = field(default_factory=list)           # OR-separated options
    nested_variables: List['NestedVariable'] = field(default_factory=list)  # Variables within content
    conditional_variables: Dict[int, List['NestedVariable']] = field(default_factory=dict)  # Variables per option
    instruction_blocks: List[str] = field(default_factory=list)  # Instruction/guidance blocks
    depth: int = 0                      # Nesting depth

class EnhancedNestedParser:
    """Parser for complex nested variable structures."""
    
    def __init__(self):
        self.instruction_patterns = [
            r"Plans can insert",
            r"Plans must insert", 
            r"Plans may include",
            r"Insert plan specific",
            r"Include if applicable"
        ]
    
    def parse_nested_variable(self, variable_text: str, depth: int = 0) -> NestedVariable:
        """
        Parse a potentially nested variable structure.
        
        Args:
            variable_text: Full bracketed variable text
            depth: Current nesting depth
            
        Returns:
            NestedVariable with full nested structure parsed
        """
        # Remove outer brackets and clean
        inner_text = variable_text.strip('[]').strip()
        
        # Check if it has colon-separated content
        if ':' not in inner_text:
            return self._parse_simple_variable(variable_text, inner_text, depth)
        
        # Split on first colon only
        colon_index = inner_text.find(':')
        action = inner_text[:colon_index].strip()
        content = inner_text[colon_index + 1:].strip()
        
        # Create base nested variable
        nested_var = NestedVariable(
            text=variable_text,
            action=action,
            content=content,
            is_colon_separated=True,
            variable_type=self._classify_nested_variable(action, content),
            depth=depth
        )
        
        # Parse OR options if they exist
        if ' OR ' in content:
            nested_var.options = self._parse_complex_options(content)
            
            # Parse conditional variables for each option
            nested_var.conditional_variables = self._parse_conditional_variables(
                nested_var.options, depth + 1
            )
        
        # Parse nested variables in the content
        nested_var.nested_variables = self._extract_nested_variables(content, depth + 1)
        
        # Extract instruction blocks
        nested_var.instruction_blocks = self._extract_instruction_blocks(content)
        
        return nested_var
    
    def _parse_simple_variable(self, full_text: str, inner_text: str, depth: int) -> NestedVariable:
        """Parse a simple variable without colons."""
        return NestedVariable(
            text=full_text,
            action=inner_text,
            content="",
            is_colon_separated=False,
            variable_type=self._classify_simple_variable(inner_text),
            depth=depth
        )
    
    def _parse_complex_options(self, content: str) -> List[str]:
        """Parse OR-separated options, handling nested brackets properly."""
        options = []
        current_option = ""
        bracket_depth = 0
        i = 0
        
        while i < len(content):
            char = content[i]
            
            if char == '[':
                bracket_depth += 1
            elif char == ']':
                bracket_depth -= 1
            elif content[i:i+4] == ' OR ' and bracket_depth == 0:
                # Found an OR separator at the top level
                if current_option.strip():
                    options.append(current_option.strip())
                current_option = ""
                i += 3  # Skip the ' OR '
                continue
            
            current_option += char
            i += 1
        
        # Add the last option
        if current_option.strip():
            options.append(current_option.strip())
        
        return options
    
    def _parse_conditional_variables(self, options: List[str], depth: int) -> Dict[int, List[NestedVariable]]:
        """Parse variables that are conditional on option selection."""
        conditional_vars = {}
        
        for i, option in enumerate(options):
            option_variables = []
            
            # Find all variables in this option
            variable_matches = re.finditer(r'\[([^\]]+(?:\[[^\]]*\][^\]]*)*)\]', option)
            
            for match in variable_matches:
                var_text = match.group(0)
                
                # Skip instruction blocks
                if self._is_instruction_block(var_text):
                    continue
                
                # Recursively parse nested variable
                nested_var = self.parse_nested_variable(var_text, depth)
                option_variables.append(nested_var)
            
            if option_variables:
                conditional_vars[i] = option_variables
        
        return conditional_vars
    
    def _extract_nested_variables(self, content: str, depth: int) -> List[NestedVariable]:
        """Extract all nested variables from content."""
        nested_vars = []
        
        # Find all bracketed content
        variable_matches = re.finditer(r'\[([^\]]+(?:\[[^\]]*\][^\]]*)*)\]', content)
        
        for match in variable_matches:
            var_text = match.group(0)
            
            # Skip instruction blocks
            if self._is_instruction_block(var_text):
                continue
            
            # Skip if it's part of an OR option (handled separately)
            match_start = match.start()
            or_context = content[max(0, match_start-20):match_start+20]
            if ' OR ' in or_context:
                continue
            
            # Recursively parse nested variable
            nested_var = self.parse_nested_variable(var_text, depth)
            nested_vars.append(nested_var)
        
        return nested_vars
    
    def _extract_instruction_blocks(self, content: str) -> List[str]:
        """Extract instruction blocks from content."""
        instruction_blocks = []
        
        # Find all bracketed content that matches instruction patterns
        variable_matches = re.finditer(r'\[([^\]]+)\]', content)
        
        for match in variable_matches:
            var_text = match.group(0)
            inner_text = match.group(1)
            
            if self._is_instruction_block(var_text):
                instruction_blocks.append(inner_text)
        
        return instruction_blocks
    
    def _is_instruction_block(self, text: str) -> bool:
        """Determine if text is an instruction block rather than a variable."""
        inner_text = text.strip('[]').lower()
        
        # Check against instruction patterns
        for pattern in self.instruction_patterns:
            if pattern.lower() in inner_text:
                return True
        
        # Additional heuristics for instruction blocks
        if len(inner_text) > 80:  # Very long text is likely instruction
            return True
        
        if 'eoc' in inner_text and ('plans can' in inner_text or 'plans may' in inner_text):
            return True
            
        if 'plans can also include' in inner_text:
            return True
            
        # Text that gives guidance rather than requesting insertion
        if inner_text.startswith('plans can') or inner_text.startswith('plans may'):
            return True
            
        # Additional instruction indicators
        if 'premium amount for each area' in inner_text and 'eoc' in inner_text:
            return True
        
        return False
    
    def _classify_nested_variable(self, action: str, content: str) -> str:
        """Classify nested variables."""
        action_lower = action.lower()
        
        if 'select one' in action_lower:
            return "nested_selection"
        elif 'insert if applicable' in action_lower:
            return "nested_conditional_insert"
        elif 'optional information' in action_lower:
            return "nested_optional_content"
        else:
            return "nested_general"
    
    def _classify_simple_variable(self, action: str) -> str:
        """Classify simple variables."""
        action_lower = action.lower()
        
        if 'plan name' in action_lower:
            return "plan_name"
        elif 'premium' in action_lower:
            return "premium_amount"
        elif 'describe' in action_lower:
            return "description_request"
        elif 'insert' in action_lower:
            return "direct_insert"
        else:
            return "general"
    
    def flatten_for_wizard(self, nested_var: NestedVariable) -> List[Dict]:
        """
        Flatten nested structure for wizard presentation.
        
        Returns list of wizard steps with conditional logic.
        """
        wizard_steps = []
        
        # Step 1: Primary variable
        primary_step = {
            'type': 'primary_selection',
            'variable': nested_var.action,
            'full_text': nested_var.text,
            'options': nested_var.options,
            'has_conditionals': bool(nested_var.conditional_variables),
            'instruction_blocks': nested_var.instruction_blocks
        }
        wizard_steps.append(primary_step)
        
        # Step 2: Conditional variables based on selection
        if nested_var.conditional_variables:
            conditional_step = {
                'type': 'conditional_variables',
                'depends_on': 0,  # Depends on primary selection
                'conditional_map': {}
            }
            
            for option_index, variables in nested_var.conditional_variables.items():
                conditional_step['conditional_map'][option_index] = [
                    {
                        'variable': var.action,
                        'type': var.variable_type,
                        'full_text': var.text,
                        'is_required': True
                    }
                    for var in variables
                ]
            
            wizard_steps.append(conditional_step)
        
        # Step 3: Any additional nested variables
        for nested in nested_var.nested_variables:
            if nested not in [var for vars_list in nested_var.conditional_variables.values() for var in vars_list]:
                additional_step = {
                    'type': 'additional_variable',
                    'variable': nested.action,
                    'full_text': nested.text,
                    'variable_type': nested.variable_type
                }
                wizard_steps.append(additional_step)
        
        return wizard_steps

# Global parser instance
_nested_parser = EnhancedNestedParser()

def parse_complex_variable(variable_text: str) -> NestedVariable:
    """Parse a complex nested variable."""
    return _nested_parser.parse_nested_variable(variable_text)

def get_wizard_steps(variable_text: str) -> List[Dict]:
    """Get wizard steps for a complex variable."""
    nested_var = parse_complex_variable(variable_text)
    return _nested_parser.flatten_for_wizard(nested_var)