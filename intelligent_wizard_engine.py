#!/usr/bin/env python3
"""
Intelligent Wizard Engine
Enhanced wizard system with variable deduplication and smart option selection
"""

from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import re

@dataclass
class GlobalVariable:
    """A variable that appears across multiple contexts."""
    name: str
    variable_type: str
    contexts: List[str] = field(default_factory=list)
    user_value: Optional[str] = None
    is_collected: bool = False

@dataclass
class OptionBranch:
    """A branch in an option selection with its required variables."""
    option_text: str
    option_index: int
    required_variables: List[str] = field(default_factory=list)
    unique_variables: List[str] = field(default_factory=list)  # Variables unique to this option
    
@dataclass
class WizardStep:
    """Enhanced wizard step with intelligent logic."""
    step_type: str  # 'global_variables', 'option_selection', 'conditional_variables'
    title: str
    description: str
    variables: List[str] = field(default_factory=list)
    options: List[OptionBranch] = field(default_factory=list)
    depends_on_step: Optional[int] = None

class IntelligentWizardEngine:
    """Enhanced wizard engine with deduplication and intelligent workflows."""
    
    def __init__(self):
        self.global_variables: Dict[str, GlobalVariable] = {}
        self.wizard_steps: List[WizardStep] = []
        self.user_responses: Dict[str, str] = {}
        self.current_step = 0
        
    def analyze_document_variables(self, all_variables: List[Dict]) -> None:
        """Analyze all variables in document to identify global vs local variables."""
        exact_variable_counts = defaultdict(int)
        exact_variable_contexts = defaultdict(list)
        normalized_to_exact = defaultdict(set)
        
        # Count both exact matches and normalized matches
        for var_info in all_variables:
            exact_var_name = var_info.get('name', '').strip()
            normalized_var_name = self._normalize_variable_name(exact_var_name)
            
            if exact_var_name:
                # Count exact matches first (highest priority)
                exact_variable_counts[exact_var_name] += 1
                context = var_info.get('full_context', '')[:50]
                exact_variable_contexts[exact_var_name].append(context)
                
                # Track mapping from normalized to exact names
                if normalized_var_name:
                    normalized_to_exact[normalized_var_name].add(exact_var_name)
        
        # Identify global variables - prioritize exact matches
        for exact_var_name, count in exact_variable_counts.items():
            if count > 1:
                # This is an exact duplicate - use original name
                var_type = self._classify_global_variable(exact_var_name)
                self.global_variables[exact_var_name] = GlobalVariable(
                    name=exact_var_name,
                    variable_type=var_type,
                    contexts=exact_variable_contexts[exact_var_name]
                )
        
        # Also check for normalized duplicates (different wording, same meaning)
        for normalized_name, exact_names in normalized_to_exact.items():
            if len(exact_names) > 1:
                # Multiple exact names normalize to the same thing
                # Use the most common exact name as the canonical form
                most_common_exact = max(exact_names, key=lambda x: exact_variable_counts[x])
                if most_common_exact not in self.global_variables:
                    var_type = self._classify_global_variable(most_common_exact)
                    all_contexts = []
                    for exact_name in exact_names:
                        all_contexts.extend(exact_variable_contexts[exact_name])
                    
                    self.global_variables[most_common_exact] = GlobalVariable(
                        name=most_common_exact,
                        variable_type=var_type,
                        contexts=all_contexts
                    )
    
    def create_intelligent_workflow(self, nested_structures: List[Dict], all_variables: List[Dict] = None) -> List[WizardStep]:
        """Create an intelligent workflow with deduplication and smart option selection."""
        self.wizard_steps = []
        processed_variables = set()
        
        # Step 1: Collect global variables first
        if self.global_variables:
            global_vars = list(self.global_variables.keys())
            if global_vars:
                global_step = WizardStep(
                    step_type='global_variables',
                    title='Document-Wide Information',
                    description='Please provide information that will be used throughout the document',
                    variables=global_vars
                )
                self.wizard_steps.append(global_step)
                processed_variables.update(global_vars)
        
        # Step 2: Process nested selections with intelligence
        for structure in nested_structures:
            if structure.get('is_complex_nested', False):
                nested_var = structure.get('nested_structure')
                if nested_var and nested_var.options:
                    option_vars = self._create_intelligent_option_workflow(nested_var)
                    processed_variables.update(option_vars)
        
        # Step 3: Add remaining variables that weren't processed yet
        if all_variables:
            remaining_variables = []
            for var_info in all_variables:
                exact_var_name = var_info.get('name', '').strip()
                
                # Check if this exact variable or any exact variable with the same name was already processed
                if exact_var_name not in processed_variables:
                    # Also check if this variable is a global variable (would be processed in step 1)
                    if exact_var_name not in self.global_variables:
                        remaining_variables.append(exact_var_name)
                        processed_variables.add(exact_var_name)
            
            # Group remaining variables into manageable steps (50 variables per step)
            chunk_size = 50
            for i in range(0, len(remaining_variables), chunk_size):
                chunk = remaining_variables[i:i + chunk_size]
                if chunk:
                    step_num = (i // chunk_size) + 1
                    remaining_step = WizardStep(
                        step_type='remaining_variables',
                        title=f'Additional Variables - Part {step_num}',
                        description=f'Complete the remaining document variables ({len(chunk)} variables)',
                        variables=chunk
                    )
                    self.wizard_steps.append(remaining_step)
        
        return self.wizard_steps
    
    def _create_intelligent_option_workflow(self, nested_var) -> List[str]:
        """Create intelligent workflow for nested option selections."""
        
        # Analyze option branches
        option_branches = []
        all_option_variables = set()
        
        for i, option_text in enumerate(nested_var.options):
            branch = OptionBranch(
                option_text=option_text,
                option_index=i
            )
            
            # Get variables for this option
            if i in nested_var.conditional_variables:
                for var in nested_var.conditional_variables[i]:
                    var_name = self._normalize_variable_name(var.action)
                    branch.required_variables.append(var_name)
                    all_option_variables.add(var_name)
            
            option_branches.append(branch)
        
        # Identify variables unique to each option (not global)
        for branch in option_branches:
            for var_name in branch.required_variables:
                if var_name not in self.global_variables:
                    # Check if this variable appears in other options
                    appears_elsewhere = any(
                        var_name in other_branch.required_variables 
                        for other_branch in option_branches 
                        if other_branch != branch
                    )
                    
                    if not appears_elsewhere:
                        branch.unique_variables.append(var_name)
        
        # Create option selection step
        option_step = WizardStep(
            step_type='option_selection',
            title=f'Selection Required: {nested_var.action}',
            description=self._create_option_description(option_branches),
            options=option_branches
        )
        self.wizard_steps.append(option_step)
        
        # Create conditional variables step (only for unique variables)
        unique_vars_exist = any(branch.unique_variables for branch in option_branches)
        if unique_vars_exist:
            conditional_step = WizardStep(
                step_type='conditional_variables',
                title='Additional Information',
                description='Please provide additional information based on your selection',
                depends_on_step=len(self.wizard_steps) - 1  # Depends on option selection
            )
            self.wizard_steps.append(conditional_step)
        
        # Return all variables processed in this workflow
        return list(all_option_variables)
    
    def _create_option_description(self, option_branches: List[OptionBranch]) -> str:
        """Create intelligent description for option selection."""
        descriptions = []
        
        for i, branch in enumerate(option_branches, 1):
            desc = f"Option {i}: {branch.option_text[:60]}{'...' if len(branch.option_text) > 60 else ''}"
            
            if branch.unique_variables:
                desc += f" (requires: {', '.join(branch.unique_variables)})"
            elif not branch.required_variables:
                desc += " (no additional input needed)"
            else:
                desc += " (uses shared information)"
            
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def get_current_step_info(self) -> Dict:
        """Get information for the current wizard step."""
        if self.current_step >= len(self.wizard_steps):
            return {'completed': True}
        
        step = self.wizard_steps[self.current_step]
        
        step_info = {
            'step_number': self.current_step + 1,
            'total_steps': len(self.wizard_steps),
            'type': step.step_type,
            'title': step.title,
            'description': step.description,
            'completed': False
        }
        
        if step.step_type == 'global_variables':
            # Show global variables that haven't been collected yet
            uncollected_vars = [
                var for var_name, var in self.global_variables.items()
                if not var.is_collected
            ]
            step_info['variables'] = uncollected_vars
            
        elif step.step_type == 'option_selection':
            step_info['options'] = step.options
            step_info['is_mutually_exclusive'] = True
            
        elif step.step_type == 'conditional_variables':
            # Get variables based on previous selection
            if step.depends_on_step is not None:
                prev_step = self.wizard_steps[step.depends_on_step]
                selected_option = self.user_responses.get(f'step_{step.depends_on_step}_selection')
                
                if selected_option is not None:
                    option_index = int(selected_option)
                    if option_index < len(prev_step.options):
                        selected_branch = prev_step.options[option_index]
                        step_info['variables'] = selected_branch.unique_variables
                        step_info['selected_option'] = selected_branch.option_text
        
        return step_info
    
    def process_step_response(self, step_number: int, response: Dict) -> bool:
        """Process user response for a step. Returns True if successful."""
        if step_number != self.current_step:
            return False
        
        step = self.wizard_steps[self.current_step]
        
        if step.step_type == 'global_variables':
            # Collect global variable values
            for var_name, value in response.items():
                if var_name in self.global_variables:
                    self.global_variables[var_name].user_value = value
                    self.global_variables[var_name].is_collected = True
                    
        elif step.step_type == 'option_selection':
            # Store selected option
            selected_option = response.get('selected_option')
            if selected_option is not None:
                self.user_responses[f'step_{self.current_step}_selection'] = selected_option
                
        elif step.step_type == 'conditional_variables':
            # Store conditional variable values
            for var_name, value in response.items():
                self.user_responses[f'variable_{var_name}'] = value
        
        # Move to next step
        self.current_step += 1
        return True
    
    def get_final_variable_values(self) -> Dict[str, str]:
        """Get all variable values for final document generation."""
        final_values = {}
        
        # Add global variable values
        for var_name, global_var in self.global_variables.items():
            if global_var.user_value:
                final_values[var_name] = global_var.user_value
        
        # Add conditional variable values
        for key, value in self.user_responses.items():
            if key.startswith('variable_'):
                var_name = key.replace('variable_', '')
                final_values[var_name] = value
        
        return final_values
    
    def _normalize_variable_name(self, var_name: str) -> str:
        """Normalize variable name for comparison."""
        # Remove common prefixes/suffixes
        normalized = var_name.lower().strip()
        normalized = re.sub(r'^(insert|add|include)\s+', '', normalized)
        normalized = re.sub(r'\s+(here|above|below)$', '', normalized)
        return normalized.strip()
    
    def _classify_global_variable(self, var_name: str) -> str:
        """Classify global variable type."""
        var_lower = var_name.lower()
        
        if 'plan name' in var_lower:
            return 'plan_name'
        elif 'premium' in var_lower:
            return 'premium_amount'
        elif 'phone' in var_lower or 'customer service' in var_lower:
            return 'phone_number'
        elif 'organization' in var_lower or 'mao' in var_lower:
            return 'organization'
        else:
            return 'general'
    
    def get_progress_info(self) -> Dict:
        """Get progress information for the wizard."""
        return {
            'current_step': self.current_step + 1,
            'total_steps': len(self.wizard_steps),
            'progress_percentage': int((self.current_step / len(self.wizard_steps)) * 100) if self.wizard_steps else 0,
            'global_variables_collected': sum(1 for var in self.global_variables.values() if var.is_collected),
            'total_global_variables': len(self.global_variables)
        }

# Global instance
_intelligent_wizard = IntelligentWizardEngine()

def create_intelligent_workflow(all_variables: List[Dict], nested_structures: List[Dict]) -> IntelligentWizardEngine:
    """Create an intelligent wizard workflow."""
    wizard = IntelligentWizardEngine()
    wizard.analyze_document_variables(all_variables)
    wizard.create_intelligent_workflow(nested_structures, all_variables)
    return wizard

def get_deduplication_stats(all_variables: List[Dict]) -> Dict:
    """Get statistics about variable deduplication opportunities."""
    exact_variable_counts = defaultdict(int)
    normalized_to_exact = defaultdict(set)
    
    # Create a temporary engine for normalization
    temp_engine = IntelligentWizardEngine()
    
    for var_info in all_variables:
        exact_var_name = var_info.get('name', '').strip()
        normalized_var_name = temp_engine._normalize_variable_name(exact_var_name)
        
        if exact_var_name:
            # Count exact matches
            exact_variable_counts[exact_var_name] += 1
            
            # Track normalized groupings
            if normalized_var_name:
                normalized_to_exact[normalized_var_name].add(exact_var_name)
    
    # Count exact duplicates
    exact_duplicates = {name: count for name, count in exact_variable_counts.items() if count > 1}
    exact_questions_saved = sum(count - 1 for count in exact_duplicates.values())
    
    # Count normalized duplicates (different exact names that normalize to same thing)
    normalized_duplicates = 0
    normalized_questions_saved = 0
    for normalized_name, exact_names in normalized_to_exact.items():
        if len(exact_names) > 1:
            # Only count if they're not already exact duplicates
            exact_dupes_in_group = sum(1 for name in exact_names if exact_variable_counts[name] > 1)
            if exact_dupes_in_group == 0:  # No exact duplicates in this normalized group
                normalized_duplicates += 1
                normalized_questions_saved += len(exact_names) - 1
    
    total_duplicates = len(exact_duplicates) + normalized_duplicates
    total_questions_saved = exact_questions_saved + normalized_questions_saved
    
    return {
        'total_variables': len(exact_variable_counts),
        'unique_variables': len([name for name, count in exact_variable_counts.items() if count == 1]),
        'exact_duplicate_variables': len(exact_duplicates),
        'normalized_duplicate_variables': normalized_duplicates,
        'duplicate_variables': total_duplicates,
        'exact_questions_saved': exact_questions_saved,
        'normalized_questions_saved': normalized_questions_saved,
        'questions_saved_by_deduplication': total_questions_saved,
        'efficiency_improvement': f"{(total_questions_saved / len(exact_variable_counts)) * 100:.1f}%" if exact_variable_counts else "0%"
    }