#!/usr/bin/env python3
"""
Intelligent AI Clarification Wizard
Analyzes actual mapping results to generate contextual, meaningful questions
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntelligentQuestion:
    """A contextually-generated question based on actual variable analysis."""
    question_id: str
    question_text: str
    question_type: str  # "yes_no", "select_one", "text_input", "business_logic"
    options: Optional[List[str]] = None
    variables_affected: Optional[List[str]] = None
    business_context: Optional[str] = None
    inference_logic: Optional[str] = None
    default_answer: Any = None
    explanation: Optional[str] = None

@dataclass
class VariableAnalysis:
    """Analysis of a mapped variable's content and context."""
    variable_name: str
    variable_text: str
    variable_type: str
    extracted_value: str
    extracted_options: List[str]
    conditions: List[str]
    business_context: str
    confidence: float

class IntelligentAIClarificationWizard:
    """AI-driven wizard that generates contextual questions from actual mapping analysis."""
    
    def __init__(self, parent, mapping_results: List[Dict], extracted_values: Dict[str, str]):
        self.parent = parent
        self.mapping_results = mapping_results
        self.extracted_values = extracted_values
        
        # Analysis results
        self.variable_analyses = []
        self.intelligent_questions = []
        self.business_contexts = {}
        self.final_variable_values = {}
        self.question_widgets = {}
        self.user_answers = {}
        
        # Perform intelligent analysis
        self._analyze_variables_intelligently()
        self._generate_intelligent_questions()
        
        logger.info(f"🧙‍♂️ Intelligent wizard created with {len(self.intelligent_questions)} contextual questions")
    
    def _analyze_variables_intelligently(self):
        """Analyze each variable to extract meaningful content and context."""
        logger.info("🔍 Analyzing variables intelligently for contextual content...")
        
        for result in self.mapping_results:
            analysis = self._analyze_single_variable(result)
            if analysis:
                self.variable_analyses.append(analysis)
        
        logger.info(f"📊 Analyzed {len(self.variable_analyses)} variables with contextual content")
    
    def _analyze_single_variable(self, result: Dict) -> Optional[VariableAnalysis]:
        """Analyze a single variable to extract content, options, and context."""
        var_name = result.get('variable', '')
        var_type = result.get('enhanced_type', '')
        extracted_value = result.get('extracted_value', '')
        
        if not var_name:
            return None
        
        # Extract variable text (the actual bracketed content)
        variable_text = var_name
        
        # Extract options from variable content
        options = self._extract_options_from_variable(variable_text)
        
        # Extract conditions
        conditions = self._extract_conditions_from_variable(variable_text)
        
        # Determine business context
        business_context = self._determine_business_context(var_name, var_type)
        
        return VariableAnalysis(
            variable_name=var_name,
            variable_text=variable_text,
            variable_type=var_type,
            extracted_value=extracted_value,
            extracted_options=options,
            conditions=conditions,
            business_context=business_context,
            confidence=result.get('confidence', 0.0)
        )
    
    def _extract_options_from_variable(self, variable_text: str) -> List[str]:
        """Extract actual options from variable text."""
        options = []
        
        # Pattern: [insert as applicable: option1 OR option2 OR option3]
        applicable_match = re.search(r'\[insert\s+as\s+applicable:\s*([^\]]+)\]', variable_text, re.IGNORECASE)
        if applicable_match:
            options_text = applicable_match.group(1)
            # Split by OR, AND, or commas
            raw_options = re.split(r'\s+OR\s+|\s+AND\s+|,\s*', options_text, flags=re.IGNORECASE)
            options = [opt.strip() for opt in raw_options if opt.strip()]
        
        # Pattern: [Select one of the following: ...]
        select_match = re.search(r'\[select\s+one\s+of\s+the\s+following:\s*([^\]]+)\]', variable_text, re.IGNORECASE)
        if select_match:
            options_text = select_match.group(1)
            # Look for OR-separated options
            raw_options = re.split(r'\s+OR\s+', options_text, flags=re.IGNORECASE)
            options.extend([opt.strip() for opt in raw_options if opt.strip()])
        
        # Pattern: [insert X OR Y]
        or_match = re.search(r'\[insert\s+([^]]+\s+OR\s+[^]]+)\]', variable_text, re.IGNORECASE)
        if or_match and not applicable_match:  # Don't double-add
            options_text = or_match.group(1)
            raw_options = re.split(r'\s+OR\s+', options_text, flags=re.IGNORECASE)
            options.extend([opt.strip() for opt in raw_options if opt.strip()])
        
        return list(set(options))  # Remove duplicates
    
    def _extract_conditions_from_variable(self, variable_text: str) -> List[str]:
        """Extract conditions from variable text."""
        conditions = []
        
        # Optional information conditions
        optional_match = re.search(r'Optional\s+information:\s*([^:]+)', variable_text, re.IGNORECASE)
        if optional_match:
            conditions.append(optional_match.group(1).strip())
        
        # If applicable conditions
        if_applicable_match = re.search(r'if\s+applicable', variable_text, re.IGNORECASE)
        if if_applicable_match:
            conditions.append("if applicable")
        
        # Plan-specific conditions
        plan_matches = re.findall(r'([^:\[]*plans?[^:\]]*)', variable_text, re.IGNORECASE)
        for match in plan_matches:
            if match.strip() and match.strip() not in conditions:
                conditions.append(match.strip())
        
        return conditions
    
    def _determine_business_context(self, var_name: str, var_type: str) -> str:
        """Determine the business context of a variable."""
        var_lower = var_name.lower()
        
        if any(term in var_lower for term in ['provider', 'directory', 'network']):
            return "Provider Network Management"
        elif any(term in var_lower for term in ['premium', 'cost', 'payment', 'price']):
            return "Premium and Cost Structure"
        elif any(term in var_lower for term in ['plan', 'name', 'title']):
            return "Plan Identification"
        elif any(term in var_lower for term in ['state', 'region', 'area', 'multi-state']):
            return "Geographic Coverage"
        elif any(term in var_lower for term in ['benefit', 'coverage', 'service']):
            return "Benefits and Coverage"
        elif any(term in var_lower for term in ['phone', 'contact', 'address', 'url', 'website']):
            return "Contact Information"
        elif any(term in var_lower for term in ['language', 'translation', 'interpreter']):
            return "Language and Communication"
        elif any(term in var_lower for term in ['appeal', 'grievance', 'complaint']):
            return "Appeals and Grievances"
        elif any(term in var_lower for term in ['date', 'time', 'period', 'day', 'month']):
            return "Timing and Dates"
        else:
            return "General Plan Information"
    
    def _generate_intelligent_questions(self):
        """Generate intelligent, contextual questions based on variable analysis."""
        logger.info("💡 Generating intelligent contextual questions...")
        
        # Group variables by business context
        context_groups = {}
        for analysis in self.variable_analyses:
            context = analysis.business_context
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(analysis)
        
        # Generate questions for each context group
        for context, analyses in context_groups.items():
            context_questions = self._generate_context_questions(context, analyses)
            self.intelligent_questions.extend(context_questions)
        
        logger.info(f"🎯 Generated {len(self.intelligent_questions)} intelligent questions")
    
    def _generate_context_questions(self, context: str, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate questions for a specific business context."""
        questions = []
        
        if context == "Provider Network Management":
            questions.extend(self._generate_provider_network_questions(analyses))
        elif context == "Premium and Cost Structure":
            questions.extend(self._generate_premium_questions(analyses))
        elif context == "Geographic Coverage":
            questions.extend(self._generate_geographic_questions(analyses))
        elif context == "Plan Identification":
            questions.extend(self._generate_plan_identification_questions(analyses))
        elif context == "Benefits and Coverage":
            questions.extend(self._generate_benefits_questions(analyses))
        elif context == "Contact Information":
            questions.extend(self._generate_contact_questions(analyses))
        elif context == "Language and Communication":
            questions.extend(self._generate_language_questions(analyses))
        elif context == "Timing and Dates":
            questions.extend(self._generate_timing_questions(analyses))
        else:
            questions.extend(self._generate_general_questions(analyses))
        
        return questions
    
    def _generate_provider_network_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate provider network questions."""
        questions = []
        
        # Check for provider directory variables
        directory_vars = [a for a in analyses if 'directory' in a.variable_name.lower()]
        if directory_vars:
            questions.append(IntelligentQuestion(
                question_id="provider_directory_included",
                question_text="Did you include a copy of your Provider Directory in the enrollment package?",
                question_type="yes_no",
                variables_affected=[a.variable_name for a in directory_vars],
                business_context="Provider Directory Inclusion",
                inference_logic="If yes, include provider directory text; if no, omit applicable sections",
                explanation="This determines whether provider directory references should be included in your document."
            ))
            
            # Check for DME supplier options
            dme_vars = [a for a in analyses if any(opt in ['suppliers', 'dme', 'equipment'] for opt in a.extracted_options)]
            if dme_vars:
                questions.append(IntelligentQuestion(
                    question_id="dme_suppliers_included",
                    question_text="Does your Provider Directory include durable medical equipment (DME) suppliers?",
                    question_type="yes_no",
                    variables_affected=[a.variable_name for a in dme_vars],
                    business_context="DME Supplier Coverage",
                    inference_logic="If yes, include 'and suppliers' text; if no, omit supplier references",
                    explanation="This affects whether supplier-related text should be included."
                ))
        
        # Check for website/URL variables
        url_vars = [a for a in analyses if 'url' in a.variable_type.lower() or 'website' in a.variable_name.lower()]
        if url_vars:
            questions.append(IntelligentQuestion(
                question_id="provider_directory_website",
                question_text="Is your provider directory available on your website?",
                question_type="text_input",
                variables_affected=[a.variable_name for a in url_vars],
                business_context="Online Provider Directory",
                inference_logic="If provided, insert the URL; if not, omit website references",
                explanation="Provide the full URL where members can access your provider directory online.",
                default_answer="https://www.example.com/providers"
            ))
        
        return questions
    
    def _generate_geographic_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate geographic coverage questions."""
        questions = []
        
        # Check for multi-state variables
        multi_state_vars = [a for a in analyses if any('state' in cond.lower() for cond in a.conditions)]
        if multi_state_vars:
            # Extract actual options from variables
            coverage_options = []
            for analysis in multi_state_vars:
                coverage_options.extend(analysis.extracted_options)
            
            # Clean and deduplicate options
            coverage_options = list(set([opt for opt in coverage_options if opt]))
            
            if not coverage_options:
                coverage_options = ["Single state only", "Several states", "All available states"]
            
            questions.append(IntelligentQuestion(
                question_id="multi_state_coverage",
                question_text="What is the geographic scope of your Medicare plan coverage?",
                question_type="select_one",
                options=coverage_options,
                variables_affected=[a.variable_name for a in multi_state_vars],
                business_context="Geographic Coverage Scope",
                inference_logic="Select appropriate coverage text based on geographic scope",
                explanation="This determines how multi-state coverage information is presented in your document.",
                default_answer=coverage_options[0] if coverage_options else "Single state only"
            ))
        
        return questions
    
    def _generate_premium_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate premium and cost structure questions."""
        questions = []
        
        # Check for premium structure variables
        premium_vars = [a for a in analyses if 'premium' in a.variable_name.lower()]
        if premium_vars:
            # Look for premium structure options
            premium_options = []
            for analysis in premium_vars:
                premium_options.extend(analysis.extracted_options)
            
            if premium_options:
                questions.append(IntelligentQuestion(
                    question_id="premium_structure",
                    question_text="How is your monthly premium structured?",
                    question_type="select_one",
                    options=premium_options,
                    variables_affected=[a.variable_name for a in premium_vars],
                    business_context="Premium Structure",
                    inference_logic="Select appropriate premium presentation format",
                    explanation="Choose how premium information should be displayed in your document."
                ))
            
            # Check for Part B premium reduction
            part_b_vars = [a for a in analyses if 'part b' in a.variable_name.lower()]
            if part_b_vars:
                questions.append(IntelligentQuestion(
                    question_id="part_b_premium_reduction",
                    question_text="Does your plan include Part B premium reduction benefits?",
                    question_type="yes_no",
                    variables_affected=[a.variable_name for a in part_b_vars],
                    business_context="Part B Premium Benefits",
                    inference_logic="If yes, include Part B premium reduction text; if no, omit",
                    explanation="This determines whether Part B premium reduction information should be included."
                ))
        
        return questions
    
    def _generate_plan_identification_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate plan identification questions.""" 
        questions = []
        
        # Plan name variables
        name_vars = [a for a in analyses if 'name' in a.variable_name.lower() and '2025' in a.variable_name]
        if name_vars:
            questions.append(IntelligentQuestion(
                question_id="plan_name_2025",
                question_text="What is your exact Medicare plan name for 2025?",
                question_type="text_input",
                variables_affected=[a.variable_name for a in name_vars],
                business_context="Plan Name",
                inference_logic="Insert exact plan name in all relevant locations",
                explanation="This will be used throughout your document wherever the plan name is referenced.",
                default_answer="Medicare Plus Blue PPO"
            ))
        
        return questions
    
    def _generate_timing_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate timing and date questions."""
        questions = []
        
        # Day/month/period variables
        timing_vars = [a for a in analyses if any(term in a.variable_name.lower() for term in ['day', 'month', 'period', 'grace'])]
        
        for analysis in timing_vars:
            if 'day' in analysis.variable_name.lower():
                questions.append(IntelligentQuestion(
                    question_id=f"timing_{analysis.variable_name.replace(' ', '_')}",
                    question_text=f"What specific day should be used for '{analysis.variable_name}'?",
                    question_type="text_input",
                    variables_affected=[analysis.variable_name],
                    business_context="Timing Specification",
                    inference_logic="Insert specific day number",
                    explanation=f"Specify the day number for {analysis.variable_name}",
                    default_answer="15"
                ))
            elif 'grace period' in analysis.variable_name.lower():
                questions.append(IntelligentQuestion(
                    question_id=f"grace_period_{analysis.variable_name.replace(' ', '_')}",
                    question_text=f"What is the length of your plan's grace period (minimum 2 months)?",
                    question_type="text_input",
                    variables_affected=[analysis.variable_name],
                    business_context="Grace Period",
                    inference_logic="Insert grace period length",
                    explanation="Specify the grace period length in months (cannot be less than 2)",
                    default_answer="2"
                ))
        
        return questions
    
    def _generate_contact_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate contact information questions."""
        questions = []
        
        # URL variables
        url_vars = [a for a in analyses if 'url' in a.variable_type.lower()]
        for analysis in url_vars:
            questions.append(IntelligentQuestion(
                question_id=f"url_{analysis.variable_name.replace(' ', '_')}",
                question_text=f"What is the URL for '{analysis.variable_name}'?",
                question_type="text_input",
                variables_affected=[analysis.variable_name],
                business_context="Website URL",
                inference_logic="Insert complete URL",
                explanation=f"Provide the full website URL for {analysis.variable_name}",
                default_answer="https://www.example.com"
            ))
        
        return questions
    
    def _generate_language_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate language and communication questions."""
        questions = []
        
        # Language threshold variables
        language_vars = [a for a in analyses if 'language' in a.variable_name.lower() or '5%' in a.variable_name]
        if language_vars:
            questions.append(IntelligentQuestion(
                question_id="language_threshold",
                question_text="Does your service area meet the 5% alternative language threshold requirement?",
                question_type="yes_no",
                variables_affected=[a.variable_name for a in language_vars],
                business_context="Language Requirements",
                inference_logic="If yes, include alternative language information; if no, omit",
                explanation="This determines whether alternative language materials information should be included."
            ))
        
        return questions
    
    def _generate_benefits_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate benefits and coverage questions."""
        questions = []
        
        # This is a placeholder for benefit-related questions
        # Can be expanded based on specific benefit variables found
        return questions
    
    def _generate_general_questions(self, analyses: List[VariableAnalysis]) -> List[IntelligentQuestion]:
        """Generate general questions for uncategorized variables."""
        questions = []
        
        # Create specific questions for variables with clear options
        for analysis in analyses:
            if analysis.extracted_options:
                questions.append(IntelligentQuestion(
                    question_id=f"general_{analysis.variable_name.replace(' ', '_')}",
                    question_text=f"Which option applies for '{analysis.variable_name}'?",
                    question_type="select_one",
                    options=analysis.extracted_options,
                    variables_affected=[analysis.variable_name],
                    business_context="General Configuration",
                    inference_logic="Apply selected option to variable",
                    explanation=f"Choose the appropriate option for {analysis.variable_name}"
                ))
        
        return questions
    
    def launch_wizard(self) -> Dict[str, str]:
        """Launch the intelligent clarification wizard GUI."""
        logger.info("🧙‍♂️ Launching Intelligent AI Clarification Wizard...")
        
        # Create wizard window
        self.wizard_window = tk.Toplevel(self.parent)
        self.wizard_window.title("🧙‍♂️ Intelligent AI Clarification Wizard")
        self.wizard_window.geometry("900x700")
        self.wizard_window.grab_set()
        
        # Create scrollable frame
        main_frame = ttk.Frame(self.wizard_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🧙‍♂️ Intelligent AI Clarification Wizard", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_text = f"""
This wizard analyzes your {len(self.variable_analyses)} mapped variables to generate intelligent, 
contextual questions that help configure your document accurately.
Answer the business-level questions below, and the wizard will intelligently 
infer the appropriate values for all related variables.
        """.strip()
        
        desc_label = ttk.Label(main_frame, text=desc_text, font=('Arial', 10), 
                              wraplength=850, justify=tk.LEFT)
        desc_label.pack(pady=(0, 15))
        
        # Create scrollable questions area
        canvas = tk.Canvas(main_frame, height=400)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Generate question widgets
        for i, question in enumerate(self.intelligent_questions):
            self._create_question_widget(scrollable_frame, question, i + 1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(button_frame, text="❌ Cancel", 
                  command=self.wizard_window.destroy).pack(side=tk.LEFT)
        
        ttk.Button(button_frame, text="✅ Complete Configuration", 
                  command=self._complete_wizard).pack(side=tk.RIGHT)
        
        # Wait for window to close
        self.wizard_window.wait_window()
        
        return self.final_variable_values
    
    def _create_question_widget(self, parent, question: IntelligentQuestion, question_num: int):
        """Create a widget for a single intelligent question."""
        q_frame = ttk.LabelFrame(parent, text=f"Question {question_num}: {question.business_context}", 
                                padding="10")
        q_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Question text
        q_label = ttk.Label(q_frame, text=question.question_text, font=('Arial', 11, 'bold'),
                           wraplength=800)
        q_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Create appropriate input widget
        if question.question_type == "yes_no":
            var = tk.StringVar(value="No")
            yes_radio = ttk.Radiobutton(q_frame, text="✅ Yes", variable=var, value="Yes")
            no_radio = ttk.Radiobutton(q_frame, text="❌ No", variable=var, value="No")
            yes_radio.pack(anchor=tk.W, padx=10)
            no_radio.pack(anchor=tk.W, padx=10)
            self.question_widgets[question.question_id] = var
            
        elif question.question_type == "select_one" and question.options:
            var = tk.StringVar(value=question.default_answer or question.options[0])
            for option in question.options:
                radio = ttk.Radiobutton(q_frame, text=f"🔘 {option}", variable=var, value=option)
                radio.pack(anchor=tk.W, padx=10, pady=2)
            self.question_widgets[question.question_id] = var
            
        elif question.question_type == "text_input":
            var = tk.StringVar(value=question.default_answer or "")
            entry = ttk.Entry(q_frame, textvariable=var, width=60)
            entry.pack(anchor=tk.W, padx=10, pady=5)
            self.question_widgets[question.question_id] = var
        
        # Explanation
        if question.explanation:
            exp_label = ttk.Label(q_frame, text=f"💡 {question.explanation}", 
                                 font=('Arial', 9), foreground='gray', wraplength=800)
            exp_label.pack(anchor=tk.W, padx=10, pady=(5, 0))
        
        # Variables affected
        if question.variables_affected:
            vars_text = f"📝 Affects: {', '.join(question.variables_affected[:3])}"
            if len(question.variables_affected) > 3:
                vars_text += f" and {len(question.variables_affected) - 3} more"
            vars_label = ttk.Label(q_frame, text=vars_text, 
                                  font=('Arial', 8), foreground='blue')
            vars_label.pack(anchor=tk.W, padx=10, pady=(2, 0))
    
    def _complete_wizard(self):
        """Complete the wizard and intelligently process all answers."""
        logger.info("🎉 Processing intelligent wizard answers...")
        
        # Collect answers
        for question in self.intelligent_questions:
            widget = self.question_widgets.get(question.question_id)
            if widget:
                answer = widget.get()
                self.user_answers[question.question_id] = answer
                
                # Apply intelligent inference
                if question.variables_affected:
                    for var_name in question.variables_affected:
                        inferred_value = self._apply_intelligent_inference(var_name, answer, question)
                        self.final_variable_values[var_name] = inferred_value
        
        logger.info(f"💾 Intelligently configured {len(self.final_variable_values)} variables")
        
        # Show completion message
        messagebox.showinfo("Complete", 
                           f"🎉 Intelligent configuration complete!\n"
                           f"Configured {len(self.final_variable_values)} variables using business logic.\n"
                           f"Based on {len(self.intelligent_questions)} contextual questions.")
        
        self.wizard_window.destroy()
    
    def _apply_intelligent_inference(self, var_name: str, answer: Any, question: IntelligentQuestion) -> str:
        """Apply intelligent inference to determine variable value from business answer."""
        
        # Find the variable analysis
        analysis = next((a for a in self.variable_analyses if a.variable_name == var_name), None)
        if not analysis:
            return str(answer)
        
        # Apply context-specific inference
        if question.business_context == "Provider Directory Inclusion":
            if str(answer).lower() == "yes":
                if "directory" in var_name.lower():
                    return "We included a copy of our Provider Directory in the envelope with this document."
                else:
                    return "Provider Directory materials included"
            else:
                return "Not applicable - Provider Directory not included"
        
        elif question.business_context == "DME Supplier Coverage":
            if str(answer).lower() == "yes":
                return "and durable medical equipment suppliers"
            else:
                return ""
        
        elif question.business_context == "Geographic Coverage Scope":
            # Use the selected coverage option directly
            return str(answer)
        
        elif question.business_context == "Part B Premium Benefits":
            if str(answer).lower() == "yes":
                return "Part B premium reduction benefit included"
            else:
                return "Not applicable"
        
        elif question.business_context == "Language Requirements":
            if str(answer).lower() == "yes":
                return "Alternative language materials provided as required"
            else:
                return "Not applicable - under 5% threshold"
        
        elif question.question_type == "text_input":
            # For text inputs, use the value directly
            return str(answer)
        
        elif question.question_type == "select_one":
            # For selections, use the chosen option
            return str(answer)
        
        # Default: use answer as-is
        return str(answer)

def create_intelligent_ai_clarification_wizard(parent, mapping_results: List[Dict], extracted_values: Dict[str, str]):
    """Factory function to create the intelligent AI clarification wizard."""
    return IntelligentAIClarificationWizard(parent, mapping_results, extracted_values)