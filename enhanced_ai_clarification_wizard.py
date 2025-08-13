#!/usr/bin/env python3
"""
Enhanced AI Clarification Wizard
Comprehensive question generation based on 23-variable taxonomy and CMS document structure
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
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
    follow_up_questions: List['ClarificationQuestion'] = None

@dataclass
class VariableGroup:
    """Groups related variables for coherent questioning."""
    group_id: str
    group_name: str
    variables: List[Dict]
    primary_question: ClarificationQuestion
    follow_up_questions: List[ClarificationQuestion] = None

class EnhancedAIClarificationWizard:
    """
    Comprehensive AI wizard that generates detailed questions based on the 23-variable taxonomy
    and CMS document structure for thorough document understanding.
    """
    
    def __init__(self, parent, mapping_results: List[Dict], extracted_values: Dict[str, str]):
        self.parent = parent
        self.mapping_results = mapping_results
        self.extracted_values = extracted_values
        
        # Comprehensive variable categorization
        self.variable_taxonomy = self._create_comprehensive_taxonomy()
        self.variable_groups = []
        self.clarification_questions = []
        self.user_answers = {}
        self.final_variable_values = {}
        
        # Analyze mapping results comprehensively
        self._analyze_mapping_results_comprehensive()
        self._generate_comprehensive_questions()
        
        logger.info(f"🧙‍♂️ Enhanced wizard created with {len(self.variable_groups)} groups and {len(self.clarification_questions)} questions")
    
    def _create_comprehensive_taxonomy(self) -> Dict[str, Dict]:
        """Create comprehensive taxonomy mapping for all 23 variable types."""
        return {
            # CORE PLAN INFORMATION
            "plan_identification": {
                "types": ["insert", "select_one_with_embedded_insert"],
                "keywords": ["plan name", "2025", "2026", "contract", "organization"],
                "questions": [
                    "What is your exact Medicare plan name for 2025?",
                    "What is your organization's legal name?", 
                    "What is your contract number with CMS?",
                    "Do you operate in multiple service areas?"
                ]
            },
            
            # PROVIDER NETWORK MANAGEMENT  
            "provider_network": {
                "types": ["insert_url", "if_applicable_compound_conditional", "optional"],
                "keywords": ["provider", "directory", "network", "supplier", "dme"],
                "questions": [
                    "Did you include a Provider Directory in the enrollment package?",
                    "Does your Provider Directory list durable medical equipment suppliers?", 
                    "Is your provider directory available on your website?",
                    "Do you have separate directories for different provider types?",
                    "Do you operate provider networks in multiple states?",
                    "Are there different access standards for different regions?"
                ]
            },
            
            # PREMIUM AND COST STRUCTURE
            "premium_structure": {
                "types": ["select_one", "if_applicable_compound_conditional", "insert_numeric_inline"],
                "keywords": ["premium", "monthly", "cost", "amount", "reduction"],
                "questions": [
                    "How is your monthly premium structured?",
                    "Does your plan include Part B premium reduction benefits?",
                    "Are premiums different by geographic region?",
                    "Does your plan have $0 premium options?",
                    "Are there premium discounts for certain populations?",
                    "Do you offer low-income subsidy benefits?"
                ]
            },
            
            # COVERAGE AND BENEFITS  
            "coverage_benefits": {
                "types": ["select_one", "optional", "complex_structural_insert"],
                "keywords": ["coverage", "benefit", "service", "medical", "drug"],
                "questions": [
                    "Does your plan include prescription drug coverage (Part D)?",
                    "Do you offer supplemental benefits beyond Original Medicare?",
                    "Are there coverage differences by plan option?",
                    "Do you provide telehealth services?",
                    "Are there special benefits for chronic conditions?",
                    "Do you cover dental, vision, or hearing services?"
                ]
            },
            
            # ENROLLMENT AND ELIGIBILITY
            "enrollment_eligibility": {
                "types": ["if_applicable_compound_conditional", "regulatory_conditional_insert"],
                "keywords": ["eligible", "enroll", "qualify", "member", "dual"],
                "questions": [
                    "Do you serve dual-eligible members (Medicare-Medicaid)?",
                    "Are there special eligibility requirements for your plan?",
                    "Do you have enrollment restrictions by geography?",
                    "Are there work-related or union-specific eligibility rules?",
                    "Do you serve members with End-Stage Renal Disease (ESRD)?",
                    "Are there age-related eligibility considerations?"
                ]
            },
            
            # COST SHARING AND FINANCIAL
            "cost_sharing": {
                "types": ["insert_numeric_inline", "select_one", "complex_structural_insert"],
                "keywords": ["copay", "coinsurance", "deductible", "out-of-pocket", "cost"],
                "questions": [
                    "What is your plan's annual deductible amount?",
                    "What is the maximum out-of-pocket limit?",
                    "Do you have different cost-sharing by service type?",
                    "Are there $0 cost-sharing benefits for certain services?",
                    "Do cost-sharing amounts vary by provider tier?",
                    "Are there special cost-sharing rules for generics vs. brand drugs?"
                ]
            },
            
            # PHARMACY AND DRUG COVERAGE
            "pharmacy_drugs": {
                "types": ["select_one", "if_applicable_compound_conditional"],
                "keywords": ["pharmacy", "drug", "formulary", "tier", "medication"],
                "questions": [
                    "How many pharmacy tiers does your formulary have?",
                    "Do you cover both retail and mail-order pharmacy?",
                    "Are there preferred pharmacy networks with lower costs?",
                    "Do you have special coverage for diabetic supplies?",
                    "Are there step therapy or prior authorization requirements?",
                    "Do you provide medication therapy management?"
                ]
            },
            
            # APPEALS AND GRIEVANCES
            "appeals_grievances": {
                "types": ["insert_numeric_inline", "select_one", "instructional_inline_deletion"],
                "keywords": ["appeal", "grievance", "complaint", "review", "decision"],
                "questions": [
                    "What are your standard appeal timeframes?",
                    "Do you offer expedited appeal processes?",
                    "Are there different appeal procedures for different situations?",
                    "Do you have special appeal rights for dual-eligible members?",
                    "What external review options do you provide?",
                    "Are there specific forms required for appeals?"
                ]
            },
            
            # COMMUNICATION AND LANGUAGE
            "communication_language": {
                "types": ["if_applicable_compound_conditional", "permissive_conditional_insert"],
                "keywords": ["language", "translation", "interpreter", "5%", "threshold"],
                "questions": [
                    "Does your service area meet the 5% alternative language threshold?",
                    "What languages do you provide translation services for?",
                    "Do you offer interpreter services for member communications?",
                    "Are your member materials available in multiple languages?",
                    "Do you have bilingual customer service representatives?",
                    "Are there specific language requirements by state regulation?"
                ]
            },
            
            # CONTACT INFORMATION
            "contact_information": {
                "types": ["insert", "insert_url"],
                "keywords": ["phone", "tty", "website", "address", "contact"],
                "questions": [
                    "What is your main member services phone number?",
                    "Do you have a separate TTY number for hearing impaired?",
                    "What is your plan's primary website URL?",
                    "Do you have 24/7 customer service availability?",
                    "Are there different contact numbers for different services?",
                    "Do you provide online member portals or mobile apps?"
                ]
            },
            
            # REGULATORY AND COMPLIANCE
            "regulatory_compliance": {
                "types": ["regulatory_conditional_insert", "instructional_cross_reference_requirement"],
                "keywords": ["CMS", "regulation", "CFR", "requirement", "compliance"],
                "questions": [
                    "Do you have any CMS-granted regulatory exceptions?",
                    "Are there state-specific regulatory requirements that apply?",
                    "Do you participate in CMS demonstration projects?",
                    "Are there special reporting requirements for your plan type?",
                    "Do you have accreditation from NCQA or other organizations?",
                    "Are there specific quality reporting requirements?"
                ]
            },
            
            # DOCUMENT STRUCTURE AND REFERENCES
            "document_structure": {
                "types": ["instructional_replacement_prior_paragraph", "instructional_structural_deletion"],
                "keywords": ["chapter", "section", "omit", "include", "reference"],
                "questions": [
                    "Are there sections that should be omitted for your plan type?",
                    "Do you need to include additional state-required disclosures?",
                    "Are there cross-references between different document sections?",
                    "Do you have plan-specific attachments or appendices?",
                    "Are there modifications needed for different member populations?",
                    "Do you need to include additional federal or state disclosures?"
                ]
            },
            
            # OPTIONAL CONDITIONAL COMPLEX VARIABLES
            "optional_conditional_complex": {
                "types": ["optional_conditional_with_embedded_select", "optional_information_compound"],
                "keywords": ["optional information", "multi-state", "can include", "several or all", "applicable"],
                "questions": [
                    "Is your plan a multi-state plan?",
                    "Do you offer coverage in several states or all available states?",
                    "Should optional information sections be included for your plan type?",
                    "Are there conditional content blocks that apply to your plan?",
                    "Do you need to include state-specific coverage information?",
                    "Are there biconditional logic requirements for your plan structure?"
                ]
            }
        }
    
    def _analyze_mapping_results_comprehensive(self):
        """Comprehensively analyze mapping results using the 23-variable taxonomy."""
        logger.info("🔍 Comprehensive analysis of mapping results for detailed questions...")
        
        # Initialize comprehensive variable groups
        variable_groups_data = {}
        
        for result in self.mapping_results:
            var_name = result.get('variable', '').lower()
            enhanced_type = result.get('enhanced_type', '')
            
            # Match against comprehensive taxonomy
            for group_id, taxonomy in self.variable_taxonomy.items():
                
                # Check if variable matches this taxonomy group
                type_match = enhanced_type in taxonomy.get('types', [])
                keyword_match = any(keyword in var_name for keyword in taxonomy.get('keywords', []))
                
                if type_match or keyword_match:
                    if group_id not in variable_groups_data:
                        variable_groups_data[group_id] = {
                            'variables': [],
                            'taxonomy': taxonomy
                        }
                    variable_groups_data[group_id]['variables'].append(result)
        
        # Create comprehensive variable groups
        for group_id, group_data in variable_groups_data.items():
            if group_data['variables']:  # Only create groups with variables
                taxonomy = group_data['taxonomy']
                group_name = group_id.replace('_', ' ').title()
                
                # Create primary question based on taxonomy
                primary_questions = taxonomy.get('questions', [])
                if primary_questions:
                    primary_question = ClarificationQuestion(
                        question_id=f"{group_id}_primary",
                        question_text=primary_questions[0],
                        question_type="yes_no" if "did you" in primary_questions[0].lower() or "do you" in primary_questions[0].lower() else "select_one",
                        variables_affected=[var['variable'] for var in group_data['variables']],
                        business_logic=f"Primary question for {group_name} configuration",
                        default_answer=True if "yes_no" in primary_questions[0].lower() else None,
                        follow_up_questions=[
                            ClarificationQuestion(
                                question_id=f"{group_id}_followup_{i}",
                                question_text=q,
                                question_type="yes_no" if "do you" in q.lower() or "are there" in q.lower() else "text_input",
                                business_logic=f"Follow-up question {i+1} for {group_name}"
                            ) for i, q in enumerate(primary_questions[1:6])  # Up to 5 follow-up questions
                        ]
                    )
                    
                    self.variable_groups.append(VariableGroup(
                        group_id=group_id,
                        group_name=group_name,
                        variables=group_data['variables'],
                        primary_question=primary_question,
                        follow_up_questions=primary_question.follow_up_questions
                    ))
        
        logger.info(f"📊 Created {len(self.variable_groups)} comprehensive variable groups")
    
    def _generate_comprehensive_questions(self):
        """Generate comprehensive clarification questions for all variable groups."""
        logger.info("💡 Generating comprehensive clarification questions...")
        
        for group in self.variable_groups:
            # Add primary question
            self.clarification_questions.append(group.primary_question)
            
            # Add follow-up questions
            if group.follow_up_questions:
                self.clarification_questions.extend(group.follow_up_questions)
            
            # Generate variable-specific questions for complex variables
            for variable in group.variables:
                var_name = variable.get('variable', '')
                enhanced_type = variable.get('enhanced_type', '')
                
                # Generate specific questions for complex variable types
                specific_question = self._generate_variable_specific_question(var_name, enhanced_type, group.group_id)
                if specific_question:
                    self.clarification_questions.append(specific_question)
        
        logger.info(f"🎯 Generated {len(self.clarification_questions)} comprehensive questions")
    
    def _generate_variable_specific_question(self, var_name: str, enhanced_type: str, group_id: str) -> Optional[ClarificationQuestion]:
        """Generate specific questions for individual variables based on their type."""
        
        # Complex conditional variables need specific questions
        if enhanced_type == "if_applicable_compound_conditional":
            return ClarificationQuestion(
                question_id=f"{group_id}_{var_name}_conditional",
                question_text=f"Does the condition for '{var_name}' apply to your plan?",
                question_type="yes_no",
                variables_affected=[var_name],
                business_logic=f"Determine if conditional content should be included",
                default_answer=False
            )
        
        # Select one variables need option clarification
        elif enhanced_type in ["select_one", "select_one_with_embedded_insert"]:
            return ClarificationQuestion(
                question_id=f"{group_id}_{var_name}_selection",
                question_text=f"Which option applies for '{var_name}'?",
                question_type="select_one",
                options=["Option 1", "Option 2", "Option 3", "Custom"],
                variables_affected=[var_name],
                business_logic=f"Select appropriate option for variable",
                default_answer="Option 1"
            )
        
        # URL variables need specific URL input
        elif enhanced_type == "insert_url":
            return ClarificationQuestion(
                question_id=f"{group_id}_{var_name}_url",
                question_text=f"What is the specific URL for '{var_name}'?",
                question_type="text_input",
                variables_affected=[var_name],
                business_logic=f"Specify exact URL for inclusion",
                default_answer="https://www.example.com"
            )
        
        # Numeric variables need amount specification
        elif enhanced_type == "insert_numeric_inline":
            return ClarificationQuestion(
                question_id=f"{group_id}_{var_name}_numeric",
                question_text=f"What is the specific amount/number for '{var_name}'?",
                question_type="text_input",
                variables_affected=[var_name],
                business_logic=f"Specify exact numeric value",
                default_answer="0"
            )
        
        # Optional conditional with embedded select - complex biconditional logic
        elif enhanced_type == "optional_conditional_with_embedded_select":
            return ClarificationQuestion(
                question_id=f"{group_id}_{var_name}_optional_conditional",
                question_text=f"Is your plan a multi-state plan that should include coverage information?",
                question_type="select_one",
                options=["No - single state plan", "Yes - several states", "Yes - all available states", "Not applicable"],
                variables_affected=[var_name],
                business_logic=f"Determine multi-state coverage scope and embedded selection",
                default_answer="No - single state plan"
            )
        
        # Optional information compound - conditional informational blocks
        elif enhanced_type == "optional_information_compound":
            return ClarificationQuestion(
                question_id=f"{group_id}_{var_name}_optional_info",
                question_text=f"Should the optional information block for '{var_name}' be included?",
                question_type="yes_no",
                variables_affected=[var_name],
                business_logic=f"Determine if optional informational content applies to your plan type",
                default_answer=False
            )
        
        return None
    
    def launch_wizard(self) -> Dict[str, str]:
        """Launch the comprehensive AI clarification wizard GUI."""
        logger.info("🧙‍♂️ Launching comprehensive AI Clarification Wizard...")
        
        # Create wizard window
        self.wizard_window = tk.Toplevel(self.parent)
        self.wizard_window.title("🧙‍♂️ Enhanced AI Clarification Wizard")
        self.wizard_window.geometry("800x600")
        self.wizard_window.configure(bg='#f0f0f0')
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(self.wizard_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="🧙‍♂️ Comprehensive CMS Document Configuration", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Info label
        info_text = f"Answer {len(self.clarification_questions)} intelligent questions to configure your document comprehensively"
        info_label = ttk.Label(main_frame, text=info_text, font=('Arial', 10))
        info_label.pack(pady=(0, 20))
        
        # Questions frame with scrollbar
        canvas = tk.Canvas(main_frame, bg='white')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Add questions to scrollable frame
        self.question_widgets = {}
        for i, question in enumerate(self.clarification_questions):
            self._create_question_widget(scrollable_frame, question, i)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="Complete Configuration", 
                  command=self._complete_wizard).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", 
                  command=self.wizard_window.destroy).pack(side=tk.RIGHT)
        
        # Wait for window to close
        self.wizard_window.wait_window()
        
        return self.final_variable_values
    
    def _create_question_widget(self, parent, question: ClarificationQuestion, index: int):
        """Create a widget for a single question."""
        
        # Question frame
        q_frame = ttk.LabelFrame(parent, text=f"Question {index + 1}: {question.question_text}")
        q_frame.pack(fill=tk.X, padx=5, pady=5)
        
        if question.question_type == "yes_no":
            var = tk.BooleanVar(value=question.default_answer or False)
            ttk.Checkbutton(q_frame, text="Yes", variable=var).pack(anchor=tk.W, padx=10, pady=5)
            self.question_widgets[question.question_id] = var
            
        elif question.question_type == "select_one":
            var = tk.StringVar(value=question.default_answer or question.options[0] if question.options else "")
            for option in (question.options or ["Option 1", "Option 2"]):
                ttk.Radiobutton(q_frame, text=option, variable=var, value=option).pack(anchor=tk.W, padx=10, pady=2)
            self.question_widgets[question.question_id] = var
            
        elif question.question_type == "text_input":
            var = tk.StringVar(value=question.default_answer or "")
            ttk.Entry(q_frame, textvariable=var, width=50).pack(anchor=tk.W, padx=10, pady=5)
            self.question_widgets[question.question_id] = var
        
        # Add business logic explanation
        if question.business_logic:
            ttk.Label(q_frame, text=f"💡 {question.business_logic}", 
                     font=('Arial', 8), foreground='gray').pack(anchor=tk.W, padx=10, pady=(0, 5))
    
    def _complete_wizard(self):
        """Complete the wizard and process all answers."""
        logger.info("🎉 Processing comprehensive wizard answers...")
        
        # Collect all answers
        for question in self.clarification_questions:
            widget = self.question_widgets.get(question.question_id)
            if widget:
                answer = widget.get()
                self.user_answers[question.question_id] = answer
                
                # Apply answer to affected variables
                if question.variables_affected:
                    for var_name in question.variables_affected:
                        self._apply_answer_to_variable(var_name, answer, question)
        
        logger.info(f"💾 Processed {len(self.final_variable_values)} final variable values")
        
        # Show completion message
        messagebox.showinfo("Complete", 
                           f"🎉 Comprehensive configuration complete!\n"
                           f"Configured {len(self.final_variable_values)} variables intelligently.")
        
        self.wizard_window.destroy()
    
    def _apply_answer_to_variable(self, var_name: str, answer: Any, question: ClarificationQuestion):
        """Apply user answer to configure variable value intelligently."""
        
        # Apply based on question type and business logic
        if question.question_type == "yes_no":
            if answer:
                # For yes answers, include appropriate content
                if "provider directory" in question.question_text.lower():
                    self.final_variable_values[var_name] = "Provider Directory included in enrollment package"
                elif "premium" in question.question_text.lower():
                    self.final_variable_values[var_name] = "Part B premium reduction benefit included"
                elif "language" in question.question_text.lower():
                    self.final_variable_values[var_name] = "Alternative language materials provided"
                elif "optional information" in question.question_text.lower():
                    self.final_variable_values[var_name] = "Optional information block included"
                else:
                    self.final_variable_values[var_name] = "Applicable content included"
            else:
                self.final_variable_values[var_name] = "Not applicable - content omitted"
                
        elif question.question_type == "select_one":
            # Handle complex multi-state plan logic
            if "multi-state" in question.question_text.lower():
                if "single state" in str(answer).lower():
                    self.final_variable_values[var_name] = "Single state coverage - optional information omitted"
                elif "several states" in str(answer).lower():
                    self.final_variable_values[var_name] = "We offer coverage in several states"
                elif "all available" in str(answer).lower():
                    self.final_variable_values[var_name] = "We offer coverage in all available states"
                elif "not applicable" in str(answer).lower():
                    self.final_variable_values[var_name] = "Multi-state information not applicable"
                else:
                    self.final_variable_values[var_name] = str(answer)
            else:
                self.final_variable_values[var_name] = str(answer)
            
        elif question.question_type == "text_input":
            self.final_variable_values[var_name] = str(answer)

def create_enhanced_ai_clarification_wizard(parent, mapping_results: List[Dict], extracted_values: Dict[str, str]):
    """Factory function to create the enhanced AI clarification wizard."""
    return EnhancedAIClarificationWizard(parent, mapping_results, extracted_values)