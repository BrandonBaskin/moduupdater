#!/usr/bin/env python3
"""
AI Clarification Wizard
Intelligent post-mapping wizard that asks high-level business questions
and infers appropriate variable values based on user responses.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enhanced_variable_classifier import VariableType, VariableClassification
from logic_mapper_llm import classify_variable_comprehensive
from logging_config import logger

@dataclass
class ClarificationQuestion:
    """Represents a high-level clarification question for the user."""
    question_id: str
    question_text: str
    question_type: str  # 'yes_no', 'select_one', 'text_input', 'multi_select'
    options: List[str] = None
    variables_affected: List[str] = None
    business_logic: str = None
    default_answer: Any = None

@dataclass
class VariableGroup:
    """Groups related variables for coherent questioning."""
    group_id: str
    group_name: str
    variables: List[Dict]
    primary_question: ClarificationQuestion
    follow_up_questions: List[ClarificationQuestion] = None

class AIClarificationWizard:
    """
    Intelligent wizard that asks business-logic questions and infers variable values.
    """
    
    def __init__(self, parent, mapping_results: List[Dict], extracted_values: Dict[str, str]):
        self.parent = parent
        self.mapping_results = mapping_results
        self.extracted_values = extracted_values
        self.clarification_questions = []
        self.variable_groups = []
        self.user_answers = {}
        self.final_variable_values = {}
        
        # Initialize the analysis
        self._analyze_mapping_results()
        self._generate_clarification_questions()
        
    def _analyze_mapping_results(self):
        """Analyze mapping results to identify variable patterns and groupings."""
        
        logger.info("🔍 Analyzing mapping results for clarification questions...")
        
        # Group variables by business logic patterns
        provider_directory_vars = []
        premium_vars = []
        conditional_insertion_vars = []
        option_select_vars = []
        plan_info_vars = []
        
        for result in self.mapping_results:
            var_name = result.get('variable', '')
            enhanced_type = result.get('enhanced_type', '')
            
            # Categorize by business domain
            if 'provider' in var_name.lower() or 'directory' in var_name.lower():
                provider_directory_vars.append(result)
            elif 'premium' in var_name.lower() or 'monthly' in var_name.lower():
                premium_vars.append(result)
            elif enhanced_type == 'if_applicable_compound_conditional':
                conditional_insertion_vars.append(result)
            elif enhanced_type in ['select_one', 'select_one_with_embedded_insert']:
                option_select_vars.append(result)
            elif 'plan name' in var_name.lower() or '2025' in var_name.lower():
                plan_info_vars.append(result)
        
        # Create variable groups with primary questions
        if provider_directory_vars:
            self.variable_groups.append(VariableGroup(
                group_id="provider_directory",
                group_name="Provider Directory Information",
                variables=provider_directory_vars,
                primary_question=ClarificationQuestion(
                    question_id="provider_directory_main",
                    question_text="Did you include a copy of your Provider Directory in the envelope with this document?",
                    question_type="yes_no",
                    variables_affected=[var['variable'] for var in provider_directory_vars],
                    business_logic="If yes, include applicable provider directory text",
                    default_answer=True
                )
            ))
            
        if premium_vars:
            self.variable_groups.append(VariableGroup(
                group_id="premium_info",
                group_name="Premium Information",
                variables=premium_vars,
                primary_question=ClarificationQuestion(
                    question_id="premium_structure_main",
                    question_text="How is your plan's monthly premium structured?",
                    question_type="select_one",
                    options=[
                        "Single monthly premium for all regions",
                        "Different premiums by region/state", 
                        "Premium listed in attachment",
                        "No monthly premium (plan pays Part B premium)"
                    ],
                    variables_affected=[var['variable'] for var in premium_vars],
                    business_logic="Select appropriate premium format text",
                    default_answer="Single monthly premium for all regions"
                )
            ))
            
        if conditional_insertion_vars:
            self.variable_groups.append(VariableGroup(
                group_id="conditional_insertions", 
                group_name="Conditional Content",
                variables=conditional_insertion_vars,
                primary_question=ClarificationQuestion(
                    question_id="conditional_content_main",
                    question_text="Which conditional content applies to your plan?",
                    question_type="multi_select",
                    options=[
                        "Part B premium reduction benefit",
                        "5% alternative language threshold met",
                        "Durable medical equipment suppliers listed",
                        "Additional premium reduction benefits"
                    ],
                    variables_affected=[var['variable'] for var in conditional_insertion_vars],
                    business_logic="Include applicable conditional content",
                    default_answer=[]
                )
            ))
            
        if option_select_vars:
            self.variable_groups.append(VariableGroup(
                group_id="option_selections",
                group_name="Option Selections",
                variables=option_select_vars,
                primary_question=ClarificationQuestion(
                    question_id="option_selections_main",
                    question_text="Please review the following option selections for your plan:",
                    question_type="text_input",
                    variables_affected=[var['variable'] for var in option_select_vars],
                    business_logic="Review and confirm option selections",
                    default_answer="Review each option"
                )
            ))
            
        if plan_info_vars:
            self.variable_groups.append(VariableGroup(
                group_id="plan_information",
                group_name="Plan Information",
                variables=plan_info_vars,
                primary_question=ClarificationQuestion(
                    question_id="plan_info_main",
                    question_text="Please confirm your plan information:",
                    question_type="text_input",
                    variables_affected=[var['variable'] for var in plan_info_vars],
                    business_logic="Confirm plan name and year information",
                    default_answer="Confirm plan details"
                )
            ))
            
        logger.info(f"📊 Created {len(self.variable_groups)} variable groups for clarification")
    
    def _generate_clarification_questions(self):
        """Generate intelligent clarification questions based on variable analysis."""
        
        logger.info("💡 Generating clarification questions...")
        
        for group in self.variable_groups:
            if group.group_id == "provider_directory":
                self._generate_provider_directory_questions(group)
            elif group.group_id == "premium_info":
                self._generate_premium_questions(group)
            elif group.group_id == "conditional_insertions":
                self._generate_conditional_questions(group)
            elif group.group_id == "option_selections":
                self._generate_option_selection_questions(group)
            elif group.group_id == "plan_information":
                self._generate_plan_info_questions(group)
    
    def _generate_provider_directory_questions(self, group: VariableGroup):
        """Generate questions for provider directory variables."""
        
        # Example variables from user:
        # "[Insert as applicable: We included a copy of our Provider Directory in the envelope with this document.]"
        # "[insert if applicable: and durable medical equipment suppliers]"
        
        questions = []
        
        # Question 1: Provider Directory Inclusion
        questions.append(ClarificationQuestion(
            question_id="provider_directory_included",
            question_text="Did you include a copy of the Provider Directory in the envelope with this document?",
            question_type="yes_no",
            variables_affected=["Insert as applicable: We included a copy of our Provider Directory in the envelope with this document."],
            business_logic="If yes, include the text. If no, omit the entire section.",
            default_answer=True
        ))
        
        # Question 2: Medical Equipment Suppliers
        questions.append(ClarificationQuestion(
            question_id="medical_equipment_suppliers",
            question_text="Does your Provider Directory also list durable medical equipment suppliers?",
            question_type="yes_no", 
            variables_affected=["insert if applicable: and durable medical equipment suppliers"],
            business_logic="If yes, add 'and durable medical equipment suppliers' to relevant text.",
            default_answer=False
        ))
        
        # Question 3: DME Directory
        questions.append(ClarificationQuestion(
            question_id="dme_directory_included",
            question_text="Did you include a separate Durable Medical Equipment Supplier Directory in the envelope?",
            question_type="yes_no",
            variables_affected=["Insert as applicable: We [insert as applicable: also] included a copy of our Durable Medical Equipment Supplier Directory in the envelope with this document."],
            business_logic="If yes, include this section. The 'also' depends on provider directory inclusion.",
            default_answer=False
        ))
        
        # Question 4: Website Availability
        questions.append(ClarificationQuestion(
            question_id="website_directory_available",
            question_text="Is the provider directory also available on your website?",
            question_type="yes_no",
            variables_affected=["The most recent list of providers [insert as applicable: and suppliers] is [insert as applicable: also] available on our website at [insert URL]."],
            business_logic="If yes, include website reference with URL.",
            default_answer=True
        ))
        
        group.primary_question = questions[0]
        group.follow_up_questions = questions[1:]
        self.clarification_questions.extend(questions)
    
    def _generate_premium_questions(self, group: VariableGroup):
        """Generate questions for premium-related variables."""
        
        # Example from user:
        # "[Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows...]"
        
        premium_options = [
            "Single premium amount for all regions",
            "Different premium amounts by region (table format)",
            "Different premium amounts by plan type (table format)", 
            "Premium amount listed in an attachment"
        ]
        
        question = ClarificationQuestion(
            question_id="premium_structure",
            question_text="How is your plan's monthly premium structured?",
            question_type="select_one",
            options=premium_options,
            variables_affected=["Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows the monthly plan premium amount for each region we serve. OR The table below shows the monthly plan premium amount for each plan we are offering in the service area. OR The monthly premium amount for [insert 2025 plan name] is listed in [describe attachment]."],
            business_logic="Select appropriate premium description format based on plan structure.",
            default_answer=premium_options[0]
        )
        
        # Part B premium reduction question
        part_b_question = ClarificationQuestion(
            question_id="part_b_premium_reduction",
            question_text="Does your plan include a Part B premium reduction benefit?",
            question_type="yes_no",
            variables_affected=["Plans that include a Part B premium reduction benefit may describe the benefit within this section."],
            business_logic="If yes, include Part B premium reduction description.",
            default_answer=False
        )
        
        group.primary_question = question
        group.follow_up_questions = [part_b_question]
        self.clarification_questions.extend([question, part_b_question])
    
    def _generate_conditional_questions(self, group: VariableGroup):
        """Generate questions for conditional insertion variables."""
        
        questions = []
        
        for var_info in group.variables:
            var_name = var_info.get('variable', '')
            enhanced_type = var_info.get('enhanced_type', '')
            
            if enhanced_type == 'if_applicable_compound_conditional':
                # Parse the condition from the variable
                condition_match = re.search(r'Plans that meet ([^,]+)', var_name, re.IGNORECASE)
                if condition_match:
                    condition = condition_match.group(1)
                    
                    question = ClarificationQuestion(
                        question_id=f"condition_{len(questions)}",
                        question_text=f"Does your plan meet the condition: {condition}?",
                        question_type="yes_no",
                        variables_affected=[var_name],
                        business_logic=f"If yes, include conditional content. If no, omit entire section.",
                        default_answer=False
                    )
                    questions.append(question)
        
        if questions:
            group.primary_question = questions[0]
            group.follow_up_questions = questions[1:] if len(questions) > 1 else []
            self.clarification_questions.extend(questions)
    
    def _generate_option_selection_questions(self, group: VariableGroup):
        """Generate questions for option selection variables."""
        
        for var_info in group.variables:
            var_name = var_info.get('variable', '')
            
            # Extract options from "Select one of the following" patterns
            if 'select one' in var_name.lower():
                options_text = var_name.split(':', 1)[1] if ':' in var_name else var_name
                options = [opt.strip() for opt in options_text.split(' OR ') if opt.strip()]
                
                if options:
                    question = ClarificationQuestion(
                        question_id=f"select_option_{var_name[:20]}",
                        question_text=f"Which option applies for this variable?",
                        question_type="select_one",
                        options=options,
                        variables_affected=[var_name],
                        business_logic="Select the appropriate option based on plan characteristics.",
                        default_answer=options[0] if options else None
                    )
                    
                    self.clarification_questions.append(question)
                    if not group.primary_question:
                        group.primary_question = question
    
    def _generate_plan_info_questions(self, group: VariableGroup):
        """Generate questions for plan information variables."""
        
        # These are usually straightforward text inputs
        question = ClarificationQuestion(
            question_id="plan_info_confirmation",
            question_text="Please confirm the extracted plan information is correct:",
            question_type="text_input",
            variables_affected=[var['variable'] for var in group.variables],
            business_logic="Confirm or correct extracted plan details.",
            default_answer="Confirm extracted values"
        )
        
        group.primary_question = question
        self.clarification_questions.append(question)
    
    def launch_wizard(self) -> Dict[str, Any]:
        """Launch the interactive clarification wizard."""
        
        logger.info("🧙‍♂️ Launching AI Clarification Wizard...")
        
        # Create wizard window
        self.wizard_window = tk.Toplevel(self.parent)
        self.wizard_window.title("AI Clarification Wizard")
        self.wizard_window.geometry("800x600")
        self.wizard_window.grab_set()  # Make modal
        
        # Variables for wizard state
        self.current_question_index = 0
        self.answers = {}
        
        # Build wizard UI
        self._build_wizard_ui()
        
        # Start with first question
        self._show_question(0)
        
        # Wait for wizard completion
        self.wizard_window.wait_window()
        
        return self.final_variable_values
    
    def _build_wizard_ui(self):
        """Build the wizard user interface."""
        
        # Header
        header_frame = ttk.Frame(self.wizard_window)
        header_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = ttk.Label(header_frame, text="🧙‍♂️ AI Clarification Wizard", font=('Arial', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Answer high-level questions to configure your document", font=('Arial', 10))
        subtitle_label.pack()
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(header_frame, variable=self.progress_var, maximum=len(self.clarification_questions))
        self.progress_bar.pack(fill='x', pady=(10, 0))
        
        # Question frame
        self.question_frame = ttk.LabelFrame(self.wizard_window, text="Question", padding=20)
        self.question_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Navigation frame
        nav_frame = ttk.Frame(self.wizard_window)
        nav_frame.pack(fill='x', padx=20, pady=10)
        
        self.prev_button = ttk.Button(nav_frame, text="← Previous", command=self._prev_question)
        self.prev_button.pack(side='left')
        
        self.next_button = ttk.Button(nav_frame, text="Next →", command=self._next_question)
        self.next_button.pack(side='right')
        
        self.finish_button = ttk.Button(nav_frame, text="🎉 Finish", command=self._finish_wizard)
        self.finish_button.pack(side='right', padx=(0, 10))
        self.finish_button.pack_forget()  # Hide initially
    
    def _show_question(self, question_index: int):
        """Display a specific question in the wizard."""
        
        if question_index < 0 or question_index >= len(self.clarification_questions):
            return
            
        self.current_question_index = question_index
        question = self.clarification_questions[question_index]
        
        # Clear question frame
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        
        # Update progress
        self.progress_var.set(question_index + 1)
        
        # Question text
        question_label = ttk.Label(self.question_frame, text=question.question_text, font=('Arial', 12, 'bold'), wraplength=700)
        question_label.pack(pady=(0, 20))
        
        # Business logic explanation
        if question.business_logic:
            logic_label = ttk.Label(self.question_frame, text=f"💡 {question.business_logic}", font=('Arial', 9), foreground='gray', wraplength=700)
            logic_label.pack(pady=(0, 15))
        
        # Answer input based on question type
        self.current_answer_var = None
        
        if question.question_type == "yes_no":
            self.current_answer_var = tk.BooleanVar()
            if question.question_id in self.answers:
                self.current_answer_var.set(self.answers[question.question_id])
            elif question.default_answer is not None:
                self.current_answer_var.set(question.default_answer)
                
            yes_radio = ttk.Radiobutton(self.question_frame, text="Yes", variable=self.current_answer_var, value=True)
            yes_radio.pack(anchor='w', pady=5)
            
            no_radio = ttk.Radiobutton(self.question_frame, text="No", variable=self.current_answer_var, value=False)
            no_radio.pack(anchor='w', pady=5)
            
        elif question.question_type == "select_one":
            self.current_answer_var = tk.StringVar()
            if question.question_id in self.answers:
                self.current_answer_var.set(self.answers[question.question_id])
            elif question.default_answer:
                self.current_answer_var.set(question.default_answer)
                
            for option in question.options:
                radio = ttk.Radiobutton(self.question_frame, text=option, variable=self.current_answer_var, value=option)
                radio.pack(anchor='w', pady=2)
                
        elif question.question_type == "text_input":
            self.current_answer_var = tk.StringVar()
            if question.question_id in self.answers:
                self.current_answer_var.set(self.answers[question.question_id])
            elif question.default_answer:
                self.current_answer_var.set(question.default_answer)
                
            entry = ttk.Entry(self.question_frame, textvariable=self.current_answer_var, width=60)
            entry.pack(pady=10)
        
        # Show affected variables
        if question.variables_affected:
            affected_label = ttk.Label(self.question_frame, text="📋 Affected Variables:", font=('Arial', 10, 'bold'))
            affected_label.pack(pady=(20, 5), anchor='w')
            
            for var in question.variables_affected[:3]:  # Show first 3
                var_label = ttk.Label(self.question_frame, text=f"• {var[:80]}{'...' if len(var) > 80 else ''}", font=('Arial', 9), foreground='blue', wraplength=700)
                var_label.pack(anchor='w', padx=20)
        
        # Update navigation buttons
        self.prev_button.config(state='normal' if question_index > 0 else 'disabled')
        
        if question_index == len(self.clarification_questions) - 1:
            self.next_button.pack_forget()
            self.finish_button.pack(side='right', padx=(0, 10))
        else:
            self.finish_button.pack_forget()
            self.next_button.pack(side='right')
    
    def _save_current_answer(self):
        """Save the current question's answer."""
        if self.current_answer_var:
            question = self.clarification_questions[self.current_question_index]
            self.answers[question.question_id] = self.current_answer_var.get()
    
    def _prev_question(self):
        """Go to previous question."""
        self._save_current_answer()
        self._show_question(self.current_question_index - 1)
    
    def _next_question(self):
        """Go to next question."""
        self._save_current_answer()
        self._show_question(self.current_question_index + 1)
    
    def _finish_wizard(self):
        """Complete the wizard and process answers."""
        self._save_current_answer()
        
        logger.info("🎉 Processing wizard answers...")
        
        # Convert answers to variable values
        self._process_answers_to_variables()
        
        # Show completion message
        messagebox.showinfo("Wizard Complete", f"🎉 Wizard completed!\n\nProcessed {len(self.answers)} answers into {len(self.final_variable_values)} variable values.")
        
        self.wizard_window.destroy()
    
    def _process_answers_to_variables(self):
        """Convert user answers into final variable values."""
        
        self.final_variable_values = self.extracted_values.copy()
        
        for question_id, answer in self.answers.items():
            question = next((q for q in self.clarification_questions if q.question_id == question_id), None)
            if not question:
                continue
                
            # Apply business logic based on question type and answer
            for var_name in question.variables_affected:
                if question.question_type == "yes_no":
                    if answer:  # Yes
                        if "Insert as applicable" in var_name:
                            # Remove "Insert as applicable:" prefix and use the content
                            content = var_name.replace("Insert as applicable:", "").strip()
                            self.final_variable_values[var_name] = content
                        elif "insert if applicable" in var_name:
                            # Use the insert text
                            insert_text = var_name.replace("insert if applicable:", "").strip()
                            self.final_variable_values[var_name] = insert_text
                        else:
                            self.final_variable_values[var_name] = "Yes"
                    else:  # No
                        self.final_variable_values[var_name] = "None"  # Omit
                        
                elif question.question_type == "select_one":
                    self.final_variable_values[var_name] = answer
                    
                elif question.question_type == "text_input":
                    self.final_variable_values[var_name] = answer
        
        logger.info(f"💾 Processed {len(self.final_variable_values)} final variable values")


# Factory function
def create_ai_clarification_wizard(parent, mapping_results: List[Dict], extracted_values: Dict[str, str]) -> AIClarificationWizard:
    """Create and return an AI clarification wizard instance."""
    return AIClarificationWizard(parent, mapping_results, extracted_values)


# Demo function
if __name__ == "__main__":
    # Mock data for testing
    mock_mapping_results = [
        {
            "variable": "Insert as applicable: We included a copy of our Provider Directory in the envelope with this document.",
            "enhanced_type": "if_applicable_compound_conditional",
            "extracted_value": "None"
        },
        {
            "variable": "insert if applicable: and durable medical equipment suppliers",
            "enhanced_type": "insert_conditional",
            "extracted_value": "None"
        },
        {
            "variable": "Select one of the following: For 2025, the monthly premium for [insert 2025 plan name] is [insert monthly premium amount]. OR The table below shows the monthly plan premium amount for each region we serve.",
            "enhanced_type": "select_one",
            "extracted_value": "None"
        }
    ]
    
    mock_extracted_values = {
        "insert 2025 plan name": "Medicare Plus Blue Group PPO",
        "insert URL": "https://www.bcbsm.com/providersmedicare"
    }
    
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    wizard = create_ai_clarification_wizard(root, mock_mapping_results, mock_extracted_values)
    final_values = wizard.launch_wizard()
    
    print("🎉 Final variable values:")
    for var, value in final_values.items():
        print(f"  {var}: {value}")
    
    root.destroy()