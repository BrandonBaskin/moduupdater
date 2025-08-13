#!/usr/bin/env python3
"""
Smart Wizard that handles every [insert x] variable individually.
Each variable gets its own input step with context and suggestions.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import os
from typing import Dict, List, Optional, Tuple
from docx import Document
from config import Config
from logging_config import logger
from enhanced_document_context import create_enhanced_document_context_extractor
from variable_context_manager import get_global_context_manager, initialize_contexts_for_document
from variable_parser import parse_variable, get_variable_display_info
from nested_variable_parser import parse_complex_variable, get_wizard_steps
from knowledge_base_manager import get_knowledge_manager, learn_variable_interaction, get_auto_value_for_variable, predict_value_for_year
from validators import validate_by_type


class SmartWizard:
    """Smart wizard that processes every variable individually."""
    
    def __init__(self, parent, extracted_values: Dict[str, str], model_docx_path: str):
        """
        Initialize the smart wizard.
        
        Args:
            parent: Parent dashboard instance
            extracted_values: Dictionary of extracted variable values
            model_docx_path: Path to the current model DOCX file
        """
        self.parent = parent
        self.extracted_values = extracted_values
        self.model_docx_path = model_docx_path
        
        # Initialize variables
        self.variables = []
        # Prompt navigation helpers
        self.prompt_order: List[int] = []  # List of variable indices that will actually be prompted
        self.current_prompt_pos: int = 0   # Position within prompt_order
        self.current_variable_index = 0    # Index into self.variables of the variable currently displayed
        self.user_responses = {}
        self.skipped_variable_indices = set()  # Track which variable indices we've skipped (for logging only)
        self.current_prompt_number = 1  # Start with prompt number 1 (1-based)
        self.remaining_prompts = 0  # Will be set after prompt_order is built
        # Track variables the user explicitly skipped/left blank (by normalized name)
        self.skipped_norms: set[str] = set()
        
        # Initialize knowledge base manager
        self.knowledge_manager = get_knowledge_manager()
        self.current_year = "2026"  # Default, can be extracted from filename or user input
        
        # Create the wizard window
        self.window = tk.Toplevel(parent)
        self.window.title("🧙‍♂️ Smart CMS Variable Wizard")
        self.window.geometry("900x700")
        self.window.configure(bg=Config.BG_COLOR)
        self.window.transient(parent)
        self.window.grab_set()
        
        # Extract all variables from model document
        self._extract_all_variables()
        self._create_variable_map()
        
        # Build prompt order and UI
        self._build_prompt_order()
        self._build_ui()
        
        # Prefill from provided extracted values (silent) before first render
        try:
            if isinstance(self.extracted_values, dict) and self.extracted_values:
                self._prefill_from_extracted_silent()
        except Exception:
            pass

        # Start with the first variable
        if self.prompt_order:
            self.current_prompt_pos = 0
            self._show_current_variable()
        else:
            messagebox.showwarning("No Variables", "No variables found in the model document.")
            self.window.destroy()
    
    def _extract_all_variables(self):
        """Extract all variables from the model document with their context."""
        try:
            # Initialize enhanced contexts using the context manager
            print("📄 Initializing enhanced contexts for variables...")
            context_success = initialize_contexts_for_document(self.model_docx_path)
            
            if context_success:
                context_manager = get_global_context_manager()
                stats = context_manager.get_context_stats()
                logger.info(f"Smart Wizard: Enhanced context extracted for {stats['total_variables']} variables")
                print(f"✅ Context extraction successful: {stats['enhanced_contexts']} enhanced, {stats['basic_contexts']} basic")
            else:
                logger.warning("Enhanced context extraction failed, will use basic context fallback")
                print("⚠️  Enhanced context extraction failed")
            
            doc = Document(self.model_docx_path)
            
            from variable_utils import iter_all_paragraphs, iter_all_text_nodes
            for para in iter_all_paragraphs(doc):
                text = para.text.strip()
                if not text or '[' not in text:
                    continue
                
                # Find all variables in this paragraph
                variable_matches = list(re.finditer(r'\[([^\]]+)\]', text))
                
                for match in variable_matches:
                    var_name = match.group(1).strip()
                    var_name_normalized = var_name.lower()  # Normalized for duplicate detection
                    var_full_name = f"[{var_name}]"
                    var_start, var_end = match.span()
                    
                    # Keep all variables in organic document order - we'll handle duplicates during navigation
                    # No longer skip duplicates here to preserve document flow
                    
                    # Get enhanced context using the context manager
                    if context_success:
                        context_manager = get_global_context_manager()
                        enhanced_context = context_manager.get_context_for_variable(var_full_name)
                        
                        # Check if we got enhanced context
                        if "📍 DOCUMENT LOCATION" in enhanced_context:
                            full_context = enhanced_context
                            before_context = text[:var_start].strip()
                            after_context = text[var_end:].strip()
                        else:
                            # Fallback to basic context
                            before_context = text[:var_start].strip()
                            after_context = text[var_end:].strip()
                            full_context = text
                    else:
                        # Fallback to basic context extraction
                        before_context = text[:var_start].strip()
                        after_context = text[var_end:].strip()
                        full_context = text
                    
                    # Classify variable type
                    var_type = self._classify_variable_type(var_name)
                    
                    # Get extracted value if available
                    extracted_value = self.extracted_values.get(var_name, "")
                    
                    # Parse the variable for colon-separated content and nested structures
                    parsed_var = parse_variable(var_full_name)
                    display_name, default_content, colon_suggestions = get_variable_display_info(var_full_name)
                    
                    # Check if this is a complex nested variable
                    is_complex_nested = False
                    nested_structure = None
                    wizard_steps = None
                    
                    if ':' in var_full_name and (' OR ' in var_full_name or '[' in var_full_name.split(':', 1)[1]):
                        try:
                            nested_structure = parse_complex_variable(var_full_name)
                            if (nested_structure.conditional_variables or 
                                len(nested_structure.options) > 2 or 
                                nested_structure.nested_variables):
                                is_complex_nested = True
                                wizard_steps = get_wizard_steps(var_full_name)
                        except:
                            pass  # Fall back to simple parsing
                    
                    variable_info = {
                        'name': var_name,  # Original case for display and replacement
                        'name_normalized': var_name_normalized,  # Lowercase for duplicate detection
                        'display_name': display_name,
                        'type': var_type,
                        'before_context': before_context,
                        'after_context': after_context,
                        'full_context': full_context,
                        'extracted_value': extracted_value,
                        'default_content': default_content,
                        'colon_suggestions': colon_suggestions,
                        'parsed_variable': parsed_var,
                        'is_complex_nested': is_complex_nested,
                        'nested_structure': nested_structure,
                        'wizard_steps': wizard_steps,
                        'user_value': default_content  # Don't auto-fill with extracted values - show as suggestions instead
                    }
                    
                    self.variables.append(variable_info)
            
            logger.info(f"Smart Wizard: Found {len(self.variables)} variables")
            
        except Exception as e:
            logger.error(f"Error extracting variables for wizard: {e}")
            self.variables = []
    
    def _create_variable_map(self):
        """
        Create a mapping of variables to track duplicates and calculate remaining prompts.
        """
        try:
            # Group variables by normalized name to identify duplicates (case-insensitive)
            self.variable_counts = {}
            self.duplicate_groups: Dict[str, List[int]] = {}
            for idx, var in enumerate(self.variables):
                var_name_normalized = var['name_normalized']  # Use normalized name for grouping
                if var_name_normalized not in self.variable_counts:
                    self.variable_counts[var_name_normalized] = {
                        'count': 0,
                        'indices': [],
                        'type': var.get('type', 'general'),
                        'original_name': var['name']  # Keep one original name for reference
                    }
                self.variable_counts[var_name_normalized]['count'] += 1
                # Use the current loop index to record the exact occurrence position
                self.variable_counts[var_name_normalized]['indices'].append(idx)
            # Mirror into duplicate_groups for quick lookup
            for norm_name, info in self.variable_counts.items():
                self.duplicate_groups[norm_name] = list(info['indices'])
            
            # Calculate initial remaining prompts (total unique variables)
            # (Will be overridden after prompt order is built)
            self.remaining_prompts = len(self.variable_counts)
            
            logger.info(f"📊 Variable Analysis Complete:")
            logger.info(f"  Total variables: {len(self.variables)}")
            logger.info(f"  Unique variables: {len(self.variable_counts)}")
            logger.info(f"  Initial remaining prompts: {self.remaining_prompts}")
            
        except Exception as e:
            logger.warning(f"Could not create variable map: {e}")
            self.variable_counts = {}
            self.remaining_prompts = len(self.variables)
    
    # Removed efficiency notification method - using original wizard logic only

    def _build_prompt_order(self):
        """Build an ordered list of variable indices that will actually be prompted."""
        self.prompt_order = []
        seen_normalized = set()
        # Duplicates are NOT marked as skipped at build time. Skips occur in real-time when a value is defined.

        # Always prompt the first occurrence of each normalized variable name.
        # Do NOT auto-skip first occurrences based on extracted values or knowledge base.
        for idx, var in enumerate(self.variables):
            norm_name = var['name_normalized']
            if norm_name not in seen_normalized:
                seen_normalized.add(norm_name)
                self.prompt_order.append(idx)

        self.remaining_prompts = len(self.prompt_order)

        logger.info(f"🧮 Prompt order built – {self.remaining_prompts} first-occurrence variables will be prompted.")
    
    def _resolve_auto_value(self, var: Dict) -> Optional[str]:
        """Resolve auto-populated value for a variable using knowledge base."""
        var_name = var['name']
        
        # Try knowledge base first
        auto_value = get_auto_value_for_variable(var_name, self.current_year)
        if auto_value:
            logger.info(f"🎯 Auto-resolved from knowledge base: {var_name} = {auto_value}")
            return auto_value
        
        # Try extracted values (case-insensitive)
        normalized_name = self.knowledge_manager.normalize_variable_name(var_name)
        for extracted_name, extracted_value in self.extracted_values.items():
            if self.knowledge_manager.normalize_variable_name(extracted_name) == normalized_name:
                logger.info(f"🎯 Auto-resolved from extracted values: {var_name} = {extracted_value}")
                return extracted_value
        
        # Try year prediction if we have source year data
        source_year = "2025"  # Could be extracted from filename or user input
        if source_year != self.current_year:
            predicted_value = predict_value_for_year(var_name, source_year, self.current_year)
            if predicted_value:
                logger.info(f"🎯 Auto-resolved from year prediction: {var_name} = {predicted_value}")
                return predicted_value
        
        # For colon-separated variables, try to extract default content
        if ':' in var_name:
            parsed_var = parse_variable(var_name)
            if parsed_var.content and len(parsed_var.content.strip()) > 0:
                # For conditional inserts, the content is what should be inserted
                if parsed_var.variable_type == "conditional_insert":
                    logger.info(f"🎯 Auto-resolved from colon content: {var_name} = {parsed_var.content}")
                    return parsed_var.content
        
        return None
    
    def _classify_variable_type(self, variable_name: str) -> str:
        """Classify the variable type for better input handling."""
        var_lower = variable_name.lower()
        
        if 'plan name' in var_lower:
            return "plan_name"
        elif 'mao name' in var_lower or 'organization' in var_lower:
            return "organization"
        elif ('phone' in var_lower or 'customer service' in var_lower or 
              'customer services' in var_lower or 'contact' in var_lower):
            return "phone_number"
        elif 'tty' in var_lower:
            return "tty_number"
        elif ('hours' in var_lower and 'operation' in var_lower) or ('days' in var_lower and 'hours' in var_lower):
            return "business_hours"
        elif 'address' in var_lower:
            return "address"
        elif 'date' in var_lower or 'day' in var_lower or 'month' in var_lower:
            return "date_time"
        elif 'premium' in var_lower or 'cost' in var_lower or 'amount' in var_lower:
            return "financial"
        elif 'state' in var_lower or 'county' in var_lower or 'zip' in var_lower:
            return "location"
        elif 'remove' in var_lower or 'delete' in var_lower:
            return "removal_instruction"
        elif 'url' in var_lower or 'website' in var_lower:
            return "url"
        else:
            return "general"
    
    def _build_ui(self):
        """Build the wizard user interface."""
        # Main container with padding
        main_frame = tk.Frame(self.window, bg=Config.BG_COLOR, padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header with progress
        header_frame = tk.Frame(main_frame, bg=Config.BG_COLOR)
        header_frame.pack(fill='x', pady=(0, 20))
        
        self.progress_label = tk.Label(
            header_frame,
            text="Variable 1 of 1",
            font=('Arial', 14, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.ACCENT_COLOR
        )
        self.progress_label.pack()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            header_frame,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(5, 0))
        
        # Variable info section
        info_frame = tk.LabelFrame(
            main_frame,
            text="Variable Information",
            font=('Arial', 12, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR,
            padx=10,
            pady=10
        )
        info_frame.pack(fill='x', pady=(0, 15))
        
        # Variable name
        self.variable_label = tk.Label(
            info_frame,
            text="[variable name]",
            font=('Arial', 16, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.ACCENT_COLOR,
            wraplength=800
        )
        self.variable_label.pack(pady=(0, 10))
        
        # Variable type
        self.type_label = tk.Label(
            info_frame,
            text="Type: General",
            font=('Arial', 10),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR
        )
        self.type_label.pack()
        
        # Context display - enhanced for large text blocks
        context_frame = tk.LabelFrame(
            main_frame,
            text="Document Context - Full Paragraph Containing Variable",
            font=('Arial', 12, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR,
            padx=10,
            pady=10
        )
        context_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Create frame for text and scrollbar
        text_scroll_frame = tk.Frame(context_frame, bg=Config.BG_COLOR)
        text_scroll_frame.pack(fill='both', expand=True)
        
        # Create text widget with increased height
        self.context_text = tk.Text(
            text_scroll_frame,
            height=12,  # Increased from 4 to 12 lines for better context display
            wrap=tk.WORD,
            font=('Arial', 10),
            bg='#f8f9fa',
            fg=Config.TEXT_COLOR,
            relief='sunken',
            borderwidth=1
        )
        
        # Add scrollbar for large text blocks
        context_scrollbar = tk.Scrollbar(text_scroll_frame, command=self.context_text.yview)
        self.context_text.config(yscrollcommand=context_scrollbar.set)
        
        # Pack text and scrollbar
        self.context_text.pack(side='left', fill='both', expand=True)
        context_scrollbar.pack(side='right', fill='y')
        
        # Input section
        input_frame = tk.LabelFrame(
            main_frame,
            text="Enter Value",
            font=('Arial', 12, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR,
            padx=10,
            pady=10
        )
        input_frame.pack(fill='x', pady=(0, 15))
        
        # Current value display
        current_frame = tk.Frame(input_frame, bg=Config.BG_COLOR)
        current_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            current_frame,
            text="Current Value:",
            font=('Arial', 10, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR
        ).pack(side='left')
        
        self.current_value_label = tk.Label(
            current_frame,
            text="(none)",
            font=('Arial', 10),
            bg=Config.BG_COLOR,
            fg=Config.ACCENT_COLOR
        )
        self.current_value_label.pack(side='left', padx=(10, 0))
        
        # Input field
        input_field_frame = tk.Frame(input_frame, bg=Config.BG_COLOR)
        input_field_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            input_field_frame,
            text="New Value:",
            font=('Arial', 10, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR
        ).pack(anchor='w')
        
        self.value_entry = tk.Entry(
            input_field_frame,
            font=('Arial', 12),
            width=60,
            relief='sunken',
            borderwidth=2
        )
        self.value_entry.pack(fill='x', pady=(5, 0))
        self.value_entry.bind('<Return>', lambda e: self._next_variable())
        
        # Suggestions section
        suggestions_frame = tk.LabelFrame(
            main_frame,
            text="Smart Suggestions",
            font=('Arial', 12, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR,
            padx=10,
            pady=10
        )
        suggestions_frame.pack(fill='x', pady=(0, 15))
        
        self.suggestions_frame = tk.Frame(suggestions_frame, bg=Config.BG_COLOR)
        self.suggestions_frame.pack(fill='x')
        
        # Buttons section
        buttons_frame = tk.Frame(main_frame, bg=Config.BG_COLOR)
        buttons_frame.pack(fill='x', pady=(10, 0))
        
        # Navigation buttons
        nav_frame = tk.Frame(buttons_frame, bg=Config.BG_COLOR)
        nav_frame.pack(side='left')
        
        self.prev_button = tk.Button(
            nav_frame,
            text="← Previous",
            command=self._previous_variable,
            font=('Arial', 10),
            bg=Config.ACCENT_COLOR,
            fg='white',
            padx=15,
            pady=5,
            state='disabled'
        )
        self.prev_button.pack(side='left', padx=(0, 10))
        
        self.next_button = tk.Button(
            nav_frame,
            text="Next →",
            command=self._next_variable,
            font=('Arial', 10),
            bg=Config.ACCENT_COLOR,
            fg='white',
            padx=15,
            pady=5
        )
        self.next_button.pack(side='left')
        
        # Action buttons
        action_frame = tk.Frame(buttons_frame, bg=Config.BG_COLOR)
        action_frame.pack(side='right')
        
        self.skip_button = tk.Button(
            action_frame,
            text="Skip",
            command=self._skip_variable,
            font=('Arial', 10),
            bg='#6c757d',
            fg='white',
            padx=15,
            pady=5
        )
        self.skip_button.pack(side='left', padx=(0, 10))
        
        self.finish_button = tk.Button(
            action_frame,
            text="Finish & Generate",
            command=self._finish_wizard,
            font=('Arial', 10, 'bold'),
            bg='#28a745',
            fg='white',
            padx=20,
            pady=5
        )
        self.finish_button.pack(side='left')
        
        # Bulk action buttons (at bottom)
        bulk_frame = tk.Frame(main_frame, bg=Config.BG_COLOR)
        bulk_frame.pack(fill='x', pady=(15, 0))
        
        tk.Label(
            bulk_frame,
            text="Bulk Actions:",
            font=('Arial', 10, 'bold'),
            bg=Config.BG_COLOR,
            fg=Config.TEXT_COLOR
        ).pack(side='left')
        
        tk.Button(
            bulk_frame,
            text="Accept All Extracted",
            command=self._accept_all_extracted,
            font=('Arial', 9),
            bg='#17a2b8',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=(10, 5))
        
        tk.Button(
            bulk_frame,
            text="Clear All",
            command=self._clear_all,
            font=('Arial', 9),
            bg='#dc3545',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        # Export form (fillable) and Auto-fill buttons
        tk.Button(
            bulk_frame,
            text="Export Form",
            command=self._export_wizard_form,
            font=('Arial', 9),
            bg='#6c757d',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        tk.Button(
            bulk_frame,
            text="Auto-fill From Old Final",
            command=self._autofill_from_old_final,
            font=('Arial', 9),
            bg='#17a2b8',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        tk.Button(
            bulk_frame,
            text="Smart Auto-fill (LLM)",
            command=self._smart_autofill_llm,
            font=('Arial', 9),
            bg='#198754',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        tk.Button(
            bulk_frame,
            text="Export Context Pack",
            command=self._export_context_pack,
            font=('Arial', 9),
            bg='#495057',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        tk.Button(
            bulk_frame,
            text="Import Filled Answers",
            command=self._import_filled_answers,
            font=('Arial', 9),
            bg='#0d6efd',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        tk.Button(
            bulk_frame,
            text="Apply Answer Pack(s)",
            command=self._apply_multiple_answer_packs,
            font=('Arial', 9),
            bg='#198754',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)

        tk.Button(
            bulk_frame,
            text="Export Key Schema",
            command=self._export_key_schema,
            font=('Arial', 9),
            bg='#6f42c1',
            fg='white',
            padx=10,
            pady=3
        ).pack(side='left', padx=5)
    
    def _show_current_variable(self):
        """Display the current variable for editing."""
        if not self.prompt_order or self.current_prompt_pos >= len(self.prompt_order):
            return
        
        # Determine variable index from prompt order
        self.current_variable_index = self.prompt_order[self.current_prompt_pos]
        var = self.variables[self.current_variable_index]
        
        # Update prompt/remaining counters (real-time)
        self._calculate_remaining_prompts()
        
        # Show current wizard progress against TOTAL unique prompts
        total_unique = len(self.variable_counts)
        progress_text = f"Variable {self.current_prompt_number} of {total_unique}"
        
        # Show auto-skip information if available (real-time)
        skipped_count = len(self.skipped_variable_indices)
        if True:
            # Compute how many unique variables have been defined (by user input only)
            resolved_norms = set()
            for name, val in self.user_responses.items():
                if val and val.strip():
                    resolved_norms.add(self.knowledge_manager.normalize_variable_name(name))
            total_unique = len(self.variable_counts)
            # Show auto-skipped duplicate count and defined unique count
            if skipped_count > 0:
                progress_text += f" (🎯 {skipped_count} auto-skipped dupes; {len(resolved_norms)}/{total_unique} defined)"
            else:
                progress_text += f" ({len(resolved_norms)}/{total_unique} defined)"
        
        # Update UI elements
        self.progress_label.config(text=progress_text)
        
        # Set progress bar maximum to TOTAL unique prompts
        self.progress_bar.config(maximum=max(1, total_unique), value=min(self.current_prompt_number, max(1, total_unique)))
        
        # Update variable info - use display name for colon-separated variables
        display_text = var.get('display_name', var['name'])
        # Occurrence count tag (impact)
        occ = 1
        vc = self.variable_counts.get(var['name_normalized'])
        if vc and isinstance(vc.get('count'), int):
            occ = vc['count']
        occ_tag = f"  (Appears {occ}x in document)" if occ and occ > 1 else ""
        self.variable_label.config(text=f"[{display_text}]" + occ_tag)
        
        # Show type and reuse info from our variable analysis
        type_display = var['type'].replace('_', ' ').title()
        if var['name_normalized'] in self.variable_counts:
            count_info = self.variable_counts[var['name_normalized']]
            if count_info['count'] > 1:
                type_display += f" (🔄 Appears {count_info['count']}x in document)"
        
        self.type_label.config(text=f"Type: {type_display}")
        
        # Show additional info for colon-separated variables
        if var.get('parsed_variable') and var['parsed_variable'].is_colon_separated:
            parsed = var['parsed_variable']
            if parsed.content:
                # Add content info below the type
                content_preview = parsed.content[:50] + "..." if len(parsed.content) > 50 else parsed.content
                type_text = f"Type: {var['type'].replace('_', ' ').title()}\nContent: {content_preview}"
                self.type_label.config(text=type_text)
        
        # Show context with highlighting
        context = var['full_context']
        
        # Enable text widget for editing
        self.context_text.config(state='normal')
        self.context_text.delete('1.0', tk.END)
        
        # Find variable position for highlighting
        var_pattern = f"[{var['name']}]"
        if var_pattern in context:
            before, after = context.split(var_pattern, 1)
            
            self.context_text.insert(tk.END, before)
            self.context_text.insert(tk.END, var_pattern, 'highlight')
            self.context_text.insert(tk.END, after)
            
            # Configure highlight tag
            self.context_text.tag_configure('highlight', 
                                          background=Config.ACCENT_COLOR, 
                                          foreground='white',
                                          font=('Arial', 10, 'bold'))
        else:
            self.context_text.insert(tk.END, context)
        
        self.context_text.config(state='disabled')
        
        # Show current value (use robust lookup: exact -> normalized match fallback)
        current_value = self.user_responses.get(var['name'], "")
        if not current_value:
            try:
                # Fallback: find by normalized key match against stored responses
                norm = self.knowledge_manager.normalize_variable_name(var['name'])
                for k, v in self.user_responses.items():
                    if self.knowledge_manager.normalize_variable_name(k) == norm and v and str(v).strip():
                        current_value = v
                        break
            except Exception:
                pass
        if current_value:
            self.current_value_label.config(text=f'"{current_value}"', fg=Config.ACCENT_COLOR)
        else:
            self.current_value_label.config(text="(none)", fg='#6c757d')
        
        # Set input field - only pre-fill if user has previously entered a value
        self.value_entry.delete(0, tk.END)
        if current_value:
            # Pre-fill with imported/applied value for quick confirmation/edit
            self.value_entry.insert(0, str(current_value))
        elif var.get('default_content') and not current_value:
            # For colon-separated variables, show default content as placeholder or suggestion
            # Don't auto-fill - let it show as suggestion instead
            pass
        
        # Update suggestions
        self._show_suggestions(var)
        
        # Update button states
        self.prev_button.config(state='normal' if self.current_prompt_number > 1 else 'disabled')
        
        # For the "Finish & Generate" button, only allow when all unique prompts are defined
        all_defined = self._are_all_unique_defined()
        self.next_button.config(text=("Finish & Generate" if all_defined else "Next →"))
        self.next_button.config(state=('normal' if not all_defined else 'normal'))
        
        # Focus on input
        self.value_entry.focus_set()
    
    def _calculate_remaining_prompts(self):
        """Calculate remaining prompts after auto-skips."""
        try:
            # Start with total unique variables
            total_unique = len(self.variable_counts)

            # Defined unique variables (by user input only)
            defined_norms = set()
            for name, val in self.user_responses.items():
                if val and val.strip():
                    defined_norms.add(self.knowledge_manager.normalize_variable_name(name))

            # Unique variables to be handled = defined + skipped
            handled_norms = set(defined_norms) | set(self.skipped_norms)

            # Remaining prompts = total unique − handled unique
            self.remaining_prompts = max(0, total_unique - len(handled_norms))

            # Clamp current_prompt_pos within prompt_order bounds
            if self.current_prompt_pos >= len(self.prompt_order):
                self.current_prompt_pos = max(0, len(self.prompt_order) - 1)
            # Current prompt number = handled unique + 1 (or 0 if none)
            self.current_prompt_number = (len(handled_norms) + 1) if self.remaining_prompts > 0 else total_unique
                
        except Exception as e:
            logger.warning(f"Error calculating remaining prompts: {e}")
            self.remaining_prompts = len(self.variable_counts)
            self.current_prompt_number = min(self.current_variable_index + 1, self.remaining_prompts)

    def _are_all_unique_defined(self) -> bool:
        """Return True if all unique first-occurrence variables have values defined by the user."""
        try:
            defined_norms = set()
            for name, val in self.user_responses.items():
                if val and val.strip():
                    defined_norms.add(self.knowledge_manager.normalize_variable_name(name))
            total_unique = len(self.variable_counts)
            return len(defined_norms) >= total_unique
        except Exception:
            return False

    def _export_wizard_form(self):
        """Export a portable, fillable form (JSON + CSV) representing the wizard."""
        try:
            from tkinter import filedialog
            import csv
            export_dir = filedialog.askdirectory(title="Select export folder for Wizard Form")
            if not export_dir:
                return
            # Build form data
            form_items = []
            for idx in self.prompt_order:
                var = self.variables[idx]
                norm = var['name_normalized']
                occ = self.variable_counts.get(norm, {}).get('count', 1)
                form_items.append({
                    'name': var['name'],
                    'type': var.get('type', 'general'),
                    'occurrences': occ,
                    'display_name': var.get('display_name', var['name']),
                    'before_context': var.get('before_context', ''),
                    'after_context': var.get('after_context', ''),
                    'full_context': var.get('full_context', ''),
                    'suggestions': self._get_smart_suggestions(var),
                })
            # Save JSON
            json_path = os.path.join(export_dir, 'wizard_form.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'items': form_items, 'total_unique': len(self.prompt_order)}, f, indent=2)
            # Save CSV
            csv_path = os.path.join(export_dir, 'wizard_form.csv')
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name','type','occurrences','display_name','before_context','after_context','full_context','suggestions'])
                for it in form_items:
                    writer.writerow([
                        it['name'], it['type'], it['occurrences'], it['display_name'],
                        it['before_context'], it['after_context'], it['full_context'],
                        '; '.join(it['suggestions'])
                    ])
            messagebox.showinfo("Export Form", f"Exported wizard form to:\n{json_path}\n{csv_path}")
        except Exception as e:
            messagebox.showerror("Export Form", f"Failed to export form: {e}")

    def _autofill_from_old_final(self):
        """Auto-fill values using extracted values from last year's final (high precision heuristics)."""
        try:
            filled = 0
            for var in self.variables:
                name = var['name']
                if name in self.user_responses and self.user_responses[name]:
                    continue
                # Exact
                val = self.extracted_values.get(name)
                if not val:
                    # Case-insensitive match
                    norm = self.knowledge_manager.normalize_variable_name(name)
                    for k, v in self.extracted_values.items():
                        if self.knowledge_manager.normalize_variable_name(k) == norm and v and v.strip():
                            val = v
                            break
                if val and val.strip():
                    self.user_responses[name] = val
                    filled += 1
            # Recompute counts and refresh
            self._calculate_remaining_prompts()
            self._show_current_variable()
            messagebox.showinfo("Auto-fill", f"Auto-filled {filled} variables from last year's final.")
        except Exception as e:
            messagebox.showerror("Auto-fill", f"Failed to auto-fill: {e}")

    def _prefill_from_extracted_silent(self):
        """Populate user_responses from extracted_values before first render without dialogs.

        This reduces manual prompts dramatically when answer packs or playbook results are available.
        """
        filled = 0
        # Build normalization helper
        def _norm(s: str) -> str:
            try:
                t = s.strip().lower()
                if t.startswith('[') and t.endswith(']'):
                    t = t[1:-1].strip()
                import re as _re
                t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
                t = _re.sub(r"\b(19|20)\d{2}\b", "", t)
                t = _re.sub(r"\s+", " ", t).strip()
                return t
            except Exception:
                return s
        # Index variables by normalized key
        index: Dict[str, List[str]] = {}
        for v in self.variables:
            for cand in (v['name'], v.get('display_name', v['name'])):
                index.setdefault(_norm(cand), []).append(v['name'])
                index.setdefault(_norm(f"[{cand}]"), []).append(v['name'])
        # Apply extracted values
        for k, v in (self.extracted_values or {}).items():
            if v is None:
                continue
            sv = str(v).strip()
            if not sv:
                continue
            nk = _norm(k)
            targets = index.get(nk, [])
            if not targets:
                # Try a light fuzzy: match on tokens subset
                for cand, names in index.items():
                    if nk and cand.startswith(nk):
                        targets = names
                        break
            for name in targets:
                vtype = next((it.get('type','general') for it in self.variables if it['name'] == name), 'general')
                ok, _ = validate_by_type(vtype, sv)
                if ok:
                    self.user_responses[name] = sv
                    filled += 1
        # Recompute counts
        self._calculate_remaining_prompts()

    def _export_context_pack(self):
        """Export a compact context pack for external LLM use (e.g., ChatGPT)."""
        try:
            from tkinter import filedialog
            export_dir = filedialog.askdirectory(title="Select export folder for Context Pack")
            if not export_dir:
                return
            pack = {
                'current_year': self.current_year,
                'total_unique': len(self.prompt_order),
                'items': [],
                'keys': []
            }
            # Enrich with canonical keys and context signatures for stable mapping
            from key_schema import canonicalize_variable_name, build_context_signatures
            for idx in self.prompt_order:
                var = self.variables[idx]
                norm = var['name_normalized']
                occ = self.variable_counts.get(norm, {}).get('count', 1)
                sigs = build_context_signatures(var.get('before_context',''), var.get('after_context',''))
                canonical_key = canonicalize_variable_name(var.get('display_name', var['name']), var.get('type'))
                pack['items'].append({
                    'name': var['name'],
                    'type': var.get('type', 'general'),
                    'occurrences': occ,
                    'full_context': var.get('full_context', ''),
                    'before_context': var.get('before_context', ''),
                    'after_context': var.get('after_context', ''),
                    'canonical_key': canonical_key,
                    **sigs,
                })
                # Prefer canonical keys for strict packs
                pack['keys'].append(canonical_key)
            json_path = os.path.join(export_dir, 'wizard_context_pack.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(pack, f, indent=2)
            # Simple README prompt
            prompt_path = os.path.join(export_dir, 'README_PROMPT.txt')
            prompt = (
                "You are filling a CMS Evidence of Coverage wizard. Given wizard_context_pack.json, return JSON mapping EXACT keys to values.\n"
                "STRICT RULES:\n"
                "- Use EXACT keys from the 'keys' array (character-for-character).\n"
                "- Return ONLY JSON: { \"answers\": { <exact key>: <value>, ... } } — no extra text.\n"
                "- Include a value for every key. If truly unknown, set the value to an empty string (\"\").\n"
                "- Use full_context and before/after for precision; do not invent keys or rename them."
            )
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            messagebox.showinfo("Export Context Pack", f"Exported context pack to:\n{json_path}\n{prompt_path}")
        except Exception as e:
            messagebox.showerror("Export Context Pack", f"Failed to export: {e}")

    def _export_key_schema(self):
        """Export the exact list of wizard keys for strict 1:1 mapping."""
        try:
            from tkinter import filedialog
            export_path = filedialog.asksaveasfilename(title="Save key schema as", defaultextension=".json", filetypes=[("JSON","*.json")], initialfile='wizard_keys.json')
            if not export_path:
                return
            keys = [self.variables[idx]['name'] for idx in self.prompt_order]
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump({'keys': keys}, f, indent=2)
            messagebox.showinfo("Export Key Schema", f"Saved exact keys to:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Export Key Schema", f"Failed to export: {e}")

    def _import_filled_answers(self):
        """Import answers JSON produced by an external LLM to populate the wizard."""
        try:
            from tkinter import filedialog
            path = filedialog.askopenfilename(title="Select filled answers JSON", filetypes=[("JSON","*.json")])
            if not path:
                return
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            answers = self._coerce_answer_pack_to_dict(data)
            strict = messagebox.askyesno("Strict 1:1 Import?", "Require EXACT key matches (no fuzzy)? \nChoose No to allow safe fuzzy matching (>= 0.90).")
            # Expand with context pack when available
            answers_expanded = self._expand_answers_with_context_pack_if_available(answers)
            self._apply_answers_map(answers_expanded, strict)
        except Exception as e:
            messagebox.showerror("Import Answers", f"Failed to import: {e}")

    # Public entry to apply answers without file dialog (used by dashboard flows)
    def apply_answers_map(self, answers: Dict[str, str], strict: bool = False):
        answers_expanded = self._expand_answers_with_context_pack_if_available(answers)
        self._apply_answers_map(answers_expanded, strict)

    def _expand_answers_with_context_pack_if_available(self, answers: Dict[str, str]) -> Dict[str, str]:
        """Expand canonical keys (e.g., mbc_*) into raw names/placeholders using a context pack if found."""
        try:
            candidates = [
                os.path.join('database', 'wizard_context_pack.json'),
                os.path.join('core_files', 'out', 'wizard_context_pack.json'),
                os.path.join('out', 'wizard_context_pack.json')
            ]
            pack_path = next((p for p in candidates if os.path.exists(p)), None)
            if not pack_path:
                return answers
            with open(pack_path, 'r', encoding='utf-8') as f:
                pack = json.load(f)
            items = pack.get('items', []) if isinstance(pack, dict) else []
            expanded: Dict[str, str] = {}
            for it in items:
                raw_name = it.get('name')
                # Prefer canonical keys; also strip year tokens from incoming answers
                key = it.get('canonical_key') or raw_name
                if key in answers and answers[key] not in (None, ""):
                    val = str(answers[key])
                    if raw_name:
                        expanded[raw_name] = val
                    occs = it.get('occurrences')
                    if isinstance(occs, list):
                        for occ in occs:
                            ph = (occ or {}).get('placeholder')
                            if ph:
                                expanded[ph.strip('[]')] = val
            for k, v in answers.items():
                if v not in (None, ""):
                    expanded[k] = str(v)
            return expanded
        except Exception:
            return answers

    def _apply_multiple_answer_packs(self):
        """Allow user to select multiple answer packs and apply them in sequence.
        Merge policy: prompt user to choose overwrite vs fill-empties.
        """
        try:
            from tkinter import filedialog
            paths = filedialog.askopenfilenames(title="Select one or more answers JSON files", filetypes=[("JSON","*.json")])
            if not paths:
                return
            overwrite = messagebox.askyesno("Merge Policy", "Overwrite existing non-empty values if conflicts?\nYes = overwrite, No = fill only empty targets.")
            strict = messagebox.askyesno("Strict 1:1 Import?", "Require EXACT key matches (no fuzzy)? \nChoose No to allow safe fuzzy matching (>= 0.90).")
            merged: Dict[str, str] = {}
            for p in paths:
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    ans = self._coerce_answer_pack_to_dict(data)
                    ans = self._expand_answers_with_context_pack_if_available(ans)
                    # Merge
                    for k, v in ans.items():
                        sv = str(v or '').strip()
                        if not sv:
                            continue
                        if overwrite or k not in merged or not str(merged.get(k) or '').strip():
                            merged[k] = sv
                except Exception as ie:
                    logger.warning(f"Skipping answers file due to error: {p}: {ie}")
                    continue
            if not merged:
                messagebox.showinfo("Apply Answer Pack(s)", "No applicable entries found.")
                return
            self._apply_answers_map(merged, strict)
        except Exception as e:
            messagebox.showerror("Apply Answer Pack(s)", f"Failed: {e}")

    def _coerce_answer_pack_to_dict(self, data: dict) -> Dict[str, str]:
        """Normalize various answer pack schemas into a flat {name: value} mapping.

        Supported:
        - {"answers": {"<key>": "<value>", ...}}
        - {"answers": [{"name":"..","value":".."}, ...], ...}
        - flat dicts already in {key: value}
        Extra fields like current_year/source_year are ignored.
        """
        try:
            if not isinstance(data, dict):
                return {}
            # Primary: explicit dict under 'answers'
            if 'answers' in data and isinstance(data['answers'], dict):
                return {str(k): ('' if v is None else str(v)) for k, v in data['answers'].items()}
            # List-of-pairs form under 'answers'
            if 'answers' in data and isinstance(data['answers'], list):
                out: Dict[str, str] = {}
                for item in data['answers']:
                    if isinstance(item, dict):
                        name = item.get('name') or item.get('key') or item.get('placeholder')
                        value = item.get('value')
                        if name is None:
                            continue
                        sv = '' if value is None else str(value)
                        if sv.strip():
                            out[str(name)] = sv
                return out
            # Fallback: if looks like a flat map, use it as-is (ignore known metadata keys)
            meta_keys = {"current_year", "source_year", "plan"}
            flat_candidates = {k: v for k, v in data.items() if k not in meta_keys}
            # Heuristic: accept only if all values are scalar
            if flat_candidates and all(not isinstance(v, (list, dict)) for v in flat_candidates.values()):
                return {str(k): ('' if v is None else str(v)) for k, v in flat_candidates.items()}
            return {}
        except Exception:
            return {}

    def _apply_answers_map(self, answers: Dict[str, str], strict: bool = False):
        """Core logic to apply answers into wizard with strict/fuzzy matching and 1:1 source enforcement."""
        try:
            # Helper: robust normalization for matching
            import re as _re
            def _norm_key(s: str) -> str:
                t = s.strip().lower()
                # strip surrounding brackets if present
                if t.startswith('[') and t.endswith(']'):
                    t = t[1:-1].strip()
                # collapse whitespace and remove punctuation except spaces
                t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
                # remove standalone year numbers for stability
                import re as _yre
                t = _yre.sub(r"\b(19|20)\d{2}\b", "", t)
                t = _re.sub(r"\s+", " ", t).strip()
                return t

            # Build normalized map of wizard variables -> all original case variants (include display_name)
            norm_to_originals: Dict[str, List[str]] = {}
            for v in self.variables:
                for candidate in (v['name'], v.get('display_name', v['name'])):
                    n = _norm_key(candidate)
                    norm_to_originals.setdefault(n, []).append(v['name'])
                    # Also index bracketed version so packs that use raw placeholders can match
                    bracketed = _norm_key(f"[{candidate}]")
                    norm_to_originals.setdefault(bracketed, []).append(v['name'])

            # Apply with exact normalized key first, then fuzzy fallback
            from difflib import SequenceMatcher
            def _best_match(nkey: str) -> Tuple[Optional[str], float]:
                best_key = None
                best_score = 0.0
                for k in norm_to_originals.keys():
                    score = SequenceMatcher(None, nkey, k).ratio()
                    if score > best_score:
                        best_score = score
                        best_key = k
                return best_key, best_score

            # Build canonical (1:1) values from source extraction when available
            norm_to_extracted: Dict[str, str] = {}
            for k, v in self.extracted_values.items():
                if v and str(v).strip():
                    nk = _norm_key(k)
                    norm_to_extracted[nk] = str(v).strip()

            applied = 0
            fuzzy_applied = 0
            missed: List[str] = []
            mappings: List[Tuple[str,str,float]] = []
            blocked_type = 0

            # Build quick type lookup by variable name
            name_to_type: Dict[str, str] = {}
            for v in self.variables:
                name_to_type[v['name']] = v.get('type', 'general')

            for raw_name, raw_value in answers.items():
                value = str(raw_value).strip()
                if not value:
                    continue
                nkey = _norm_key(raw_name)
                target_key = None
                # exact normalized match
                if nkey in norm_to_originals:
                    target_key = nkey
                else:
                    # fuzzy fallback
                    if not strict:
                        cand, score = _best_match(nkey)
                        # Slightly relaxed fuzzy threshold to accommodate phrasing and section prefixes
                        if cand and score >= 0.82:
                            target_key = cand
                            mappings.append((raw_name, norm_to_originals[cand][0], score))
                            fuzzy_applied += 1
                if target_key:
                    # Enforce 1:1 with source when available: prefer extracted value
                    canonical = norm_to_extracted.get(target_key, value)
                    # Apply only when type validator passes for the specific variable
                    for original in norm_to_originals.get(target_key, []):
                        vtype = name_to_type.get(original, 'general')
                        # Validate per type; do not hardwire values
                        ok, _ = validate_by_type(vtype, canonical)
                        if ok:
                            self.user_responses[original] = canonical
                            applied += 1
                        else:
                            blocked_type += 1
                else:
                    missed.append(raw_name)

            self._calculate_remaining_prompts()
            self._show_current_variable()
            # Summary dialog
            summary_lines = [
                f"Applied entries (incl. duplicates): {applied}",
                f"Fuzzy matched: {fuzzy_applied}",
                f"Type-blocked: {blocked_type}",
                f"Missed keys: {len(missed)}"
            ]
            if mappings:
                preview = "\n".join([f"- '{src}' -> '{dst}' ({score:.2f})" for src,dst,score in mappings[:8]])
                summary_lines.append("\nFuzzy mappings (preview):\n" + preview)
            if missed:
                summary_lines.append("\nFirst missed keys:\n" + "\n".join([f"- {m}" for m in missed[:8]]))
            messagebox.showinfo("Import Answers", "\n".join(summary_lines))
        except Exception as e:
            messagebox.showerror("Import Answers", f"Failed to import: {e}")

    def _smart_autofill_llm(self):
        """Use local Llama 3 via Ollama to infer values with high precision from context."""
        try:
            if not messagebox.askyesno("Smart Auto-fill (LLM)", "Run local Llama 3 to infer values for remaining variables? This may take several minutes."):
                return
            # Ensure Ollama is running
            from ollama_manager import get_ollama_manager
            mgr = get_ollama_manager()
            mgr.ensure_model_available()
            import requests
            url = "http://localhost:11434/api/generate"
            filled = 0
            for idx in self.prompt_order:
                var = self.variables[idx]
                name = var['name']
                if name in self.user_responses and self.user_responses[name]:
                    continue
                ctx = var.get('full_context') or (var.get('before_context','') + " ["+name+"] " + var.get('after_context',''))
                prompt = (
                    f"You fill CMS EOC variables. Return ONLY the value text for [{name}], no prose.\n"
                    f"Context:\n{ctx}\nValue:"
                )
                try:
                    resp = requests.post(url, json={"model":"llama3:latest","prompt":prompt,"stream":False}, timeout=60)
                    if resp.ok:
                        out = resp.json().get('response','').strip()
                        if out and out.lower() != 'none':
                            self.user_responses[name] = out
                            filled += 1
                except Exception:
                    pass
            self._calculate_remaining_prompts()
            self._show_current_variable()
            messagebox.showinfo("Smart Auto-fill (LLM)", f"Auto-filled {filled} variables using Llama 3.")
        except Exception as e:
            messagebox.showerror("Smart Auto-fill (LLM)", f"Failed to run: {e}")
    
    def _show_suggestions(self, var: Dict):
        """Show smart suggestions for the current variable."""
        # Clear existing suggestions
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        
        # Get suggestions - combine regular suggestions with colon-separated suggestions
        suggestions = self._get_smart_suggestions(var)
        
        # Add colon-separated suggestions if available
        if var.get('colon_suggestions'):
            colon_suggestions = var['colon_suggestions']
            # Merge suggestions, giving priority to colon-separated ones
            for suggestion in reversed(colon_suggestions):
                if suggestion and suggestion not in suggestions:
                    suggestions.insert(0, suggestion)
        
        if suggestions:
            for i, suggestion in enumerate(suggestions):
                btn = tk.Button(
                    self.suggestions_frame,
                    text=f'"{suggestion}"',
                    command=lambda s=suggestion: self._apply_suggestion(s),
                    font=('Arial', 9),
                    bg='#e9ecef',
                    fg=Config.TEXT_COLOR,
                    relief='raised',
                    borderwidth=1,
                    padx=10,
                    pady=2
                )
                btn.pack(side='left', padx=(0, 5), pady=2)
        else:
            tk.Label(
                self.suggestions_frame,
                text="No suggestions available",
                font=('Arial', 9, 'italic'),
                bg=Config.BG_COLOR,
                fg='#6c757d'
            ).pack()
    
    def _get_smart_suggestions(self, var: Dict) -> List[str]:
        """Generate smart suggestions for a variable."""
        suggestions = []
        var_type = var['type']
        var_name = var['name'].lower()
        
        # Type-specific suggestions
        if var_type == "tty_number":
            suggestions.append("711")
        
        elif var_type == "plan_name":
            suggestions.extend([
                "Medicare Plus Blue Group PPO",
                "Medicare Plus Blue PPO",
                "Medicare Advantage PPO"
            ])
        
        elif var_type == "organization":
            suggestions.extend([
                "Blue Cross Blue Shield of Michigan",
                "Blue Cross Blue Shield"
            ])
        
        elif var_type == "phone_number":
            suggestions.extend([
                "1-855-669-8040",
                "1-800-555-0199"
            ])
        
        elif var_type == "business_hours":
            suggestions.extend([
                "Monday through Friday, 8 a.m. to 8 p.m.",
                "Monday - Friday, 9:00 AM to 6:00 PM",
                "24 hours a day, 7 days a week"
            ])
        
        elif var_type == "url":
            suggestions.extend([
                "https://www.bcbsm.com/providers",
                "https://www.medicare.gov",
                "https://www.example.com"
            ])
        
        elif "state" in var_name:
            suggestions.extend([
                "Michigan",
                "California", 
                "Texas",
                "Florida"
            ])
        
        elif "year" in var_name or "2026" in var_name:
            suggestions.extend([
                "2026",
                "2025"
            ])
        
        # Add extracted value as the TOP suggestion if available 
        extracted_value = var.get('extracted_value')
        if extracted_value and extracted_value != "None":
            if extracted_value not in suggestions:
                suggestions.insert(0, extracted_value)  # Always put extracted value first as best suggestion
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _apply_suggestion(self, suggestion: str):
        """Apply a suggestion to the current input field."""
        self.value_entry.delete(0, tk.END)
        self.value_entry.insert(0, suggestion)
        self.value_entry.focus_set()
    
    def _previous_variable(self):
        """Go to the previous variable."""
        self._save_current_value()
        
        if self.current_prompt_pos > 0:
            self.current_prompt_pos -= 1
            self._show_current_variable()
    
    def _next_variable(self):
        """Go to the next variable or finish if at the end."""
        self._save_current_value()
        # Recompute remaining prompts and current prompt position after new value
        self._calculate_remaining_prompts()
        # Ensure current_prompt_pos is not out of range
        if self.current_prompt_pos >= len(self.prompt_order):
            self.current_prompt_pos = max(0, len(self.prompt_order) - 1)
        
        # Move forward in prompt order if not all unique defined
        if not self._are_all_unique_defined():
            if self.current_prompt_pos < len(self.prompt_order) - 1:
                self.current_prompt_pos += 1
                self._show_current_variable()
                return
            # If out of prompt_order but not all defined (e.g., user navigated), find next undefined
            for i, idx in enumerate(self.prompt_order):
                name_norm = self.variables[idx]['name_normalized']
                has_value = any(
                    self.knowledge_manager.normalize_variable_name(k) == name_norm and v and v.strip()
                    for k, v in self.user_responses.items()
                )
                if not has_value:
                    self.current_prompt_pos = i
                    self._show_current_variable()
                    return
        
        # All unique defined: finish
        self._finish_wizard()


    
    def _skip_variable(self):
        """Skip the current variable and move to the next (same as Next)."""
        # Treat skip as clearing any value for this variable
        if self.variables and self.current_prompt_pos < len(self.prompt_order):
            idx = self.prompt_order[self.current_prompt_pos]
            var_name = self.variables[idx]['name']
            normalized_name = self.knowledge_manager.normalize_variable_name(var_name)
            # Mark as skipped (handled)
            self.skipped_norms.add(normalized_name)
            # Clear any value
            if var_name in self.user_responses:
                del self.user_responses[var_name]
        # Recompute progress and advance
        self._calculate_remaining_prompts()
        if self.current_prompt_pos < len(self.prompt_order) - 1:
            self.current_prompt_pos += 1
            self._show_current_variable()
        else:
            self._finish_wizard()
    
    def _save_current_value(self):
        """Save the current input value and learn from it."""
        value = self.value_entry.get().strip()
        
        if self.variables and self.current_variable_index < len(self.variables):
            var_name = self.variables[self.current_variable_index]['name']
            if value:
                self.user_responses[var_name] = value
                
                # Learn from this interaction
                var_type = self._classify_variable_type(var_name)
                learn_variable_interaction(var_name, var_type, value, self.current_year)
                
                # Real-time duplicate auto-fill now: populate all duplicates of this variable
                normalized_name = self.knowledge_manager.normalize_variable_name(var_name)
                indices = getattr(self, 'duplicate_groups', {}).get(normalized_name, [])
                for idx in indices:
                    other_name = self.variables[idx]['name']
                    if other_name != var_name:
                        self.user_responses[other_name] = value
                        # mark as skipped now that it's auto-filled due to definition
                        self.skipped_variable_indices.add(idx)
                
                logger.info(f"📚 Learned: {var_name} = {value} (type: {var_type})")
            else:
                # Clearing or skipping: mark this unique variable as handled via skip
                normalized_name = self.knowledge_manager.normalize_variable_name(var_name)
                self.skipped_norms.add(normalized_name)
                # Remove any previously set responses for this group
                indices = getattr(self, 'duplicate_groups', {}).get(normalized_name, [])
                for idx in indices:
                    other_name = self.variables[idx]['name']
                    if other_name in self.user_responses:
                        del self.user_responses[other_name]
    
    def _accept_all_extracted(self):
        """Accept all extracted values for variables that have them."""
        count = 0
        for var in self.variables:
            extracted_value = var.get('extracted_value')
            if extracted_value and extracted_value != "None":
                self.user_responses[var['name']] = extracted_value
                count += 1
        
        messagebox.showinfo("Bulk Action", f"Applied {count} extracted values.")
        self._show_current_variable()  # Refresh display
    
    def _clear_all(self):
        """Clear all user responses."""
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all entered values?"):
            self.user_responses.clear()
            self._show_current_variable()  # Refresh display
    
    def _finish_wizard(self):
        """Finish the wizard and generate the final document."""
        self._save_current_value()
        
        # Count filled variables using UNIQUE variable semantics
        total_unique = len(self.variable_counts)
        defined_norms = set()
        for name, val in self.user_responses.items():
            if val and val.strip():
                defined_norms.add(self.knowledge_manager.normalize_variable_name(name))
        filled_unique = len(defined_norms)
        remaining_unique = max(0, total_unique - filled_unique)
        
        # Show summary
        if remaining_unique > 0:
            if not messagebox.askyesno(
                "Incomplete Variables", 
                f"You have {remaining_unique} unfilled variables out of {total_unique}.\n\n"
                "Do you want to proceed with generating the document?"
            ):
                return
        
        try:
            # Generate the final document
            output_path = self._generate_final_document()
            
            if output_path:
                # Show success message
                success_message = f"Document generated successfully!\n\n"
                success_message += f"Filled {filled_unique} out of {total_unique} unique variables.\n"
                success_message += f"Saved to: {output_path}"
                
                # Show auto-skip statistics
                skipped_count = len(self.skipped_variable_indices)
                if skipped_count > 0:
                    success_message += f"\n\n🎯 Auto-skip Statistics:\n"
                    success_message += f"• Variables auto-skipped: {skipped_count}"
                    denom = max(1, len(self.variables))
                    success_message += f"\n• Efficiency improvement: {(skipped_count / denom * 100):.1f}%"
                
                messagebox.showinfo("Success!", success_message)
                
                self.parent.logmsg(f"✅ Wizard completed: {filled_unique}/{total_unique} unique variables filled")
                if skipped_count > 0:
                    self.parent.logmsg(f"🎯 Auto-skip saved {skipped_count} questions through smart deduplication")
                self.parent.logmsg(f"📄 Final document saved: {output_path}")
                
                # Save knowledge base
                from knowledge_base_manager import save_knowledge_base
                save_knowledge_base()
                self.parent.logmsg(f"📚 Knowledge base updated with new learnings")
                
                self.window.destroy()
            
        except Exception as e:
            logger.error(f"Error generating final document: {e}")
            messagebox.showerror("Error", f"Failed to generate document: {e}")
    
    def _generate_final_document(self) -> Optional[str]:
        """Generate the final document with filled variables."""
        try:
            # Ask user where to save
            output_path = filedialog.asksaveasfilename(
                title="Save Final Document",
                defaultextension=".docx",
                filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")],
                initialfile="Final_CMS_Document.docx"
            )
            
            if not output_path:
                return None
            
            # Load the model document
            doc = Document(self.model_docx_path)
            
            # Replace all variables (case-insensitive) across entire document, including tables
            import re
            from variable_utils import iter_all_paragraphs, iter_all_text_nodes

            # Build replacement map cross-normalized so case variants are included
            replacements: Dict[str, str] = {}
            # Start with user responses
            for k, v in self.user_responses.items():
                if not v:
                    continue
                norm = self.knowledge_manager.normalize_variable_name(k)
                replacements[k] = v
                # add known case variants from variables list
                for var in self.variables:
                    if var['name_normalized'] == norm:
                        replacements.setdefault(var['name'], v)
            # Then add extracted values only where not already defined by user
            for k, v in self.extracted_values.items():
                if not v:
                    continue
                if k not in replacements:
                    norm = self.knowledge_manager.normalize_variable_name(k)
                    replacements[k] = v
                    for var in self.variables:
                        if var['name_normalized'] == norm and var['name'] not in replacements:
                            replacements[var['name']] = v

            # Precompile patterns (handle variations, nested brackets, and flexible whitespace)
            compiled_patterns = []
            for var_name, value in replacements.items():
                # Escape user-provided variable names for regex
                escaped = re.escape(var_name)
                # Flexible whitespace version (match spaces split across runs)
                escaped_flex = re.sub(r"\\\s+", r"\\s+", escaped.replace("\\ ", "\\s+"))
                # Match exact bracketed token possibly with extra brackets from split runs like '[[insert ...]'
                bracketed = re.compile(rf"\[+{escaped}\]+", re.IGNORECASE)
                bracketed_flex = re.compile(rf"\[+{escaped_flex}\]+", re.IGNORECASE)
                # Fallback: unbracketed whole word
                plain = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
                plain_flex = re.compile(rf"\b{escaped_flex}\b", re.IGNORECASE)
                compiled_patterns.append((bracketed, bracketed_flex, plain, plain_flex, str(value)))

            for para in iter_all_paragraphs(doc):
                runs = getattr(para, 'runs', [])
                any_run_change = False
                for run in runs:  # type: ignore[attr-defined]
                    original_text = run.text or ""
                    new_text = original_text
                    for bracketed, bracketed_flex, plain, plain_flex, value in compiled_patterns:
                        replaced = bracketed.sub(value, new_text)
                        if replaced == new_text:
                            replaced = bracketed_flex.sub(value, new_text)
                        if replaced == new_text:
                            replaced = plain.sub(value, new_text)
                        if replaced == new_text:
                            replaced = plain_flex.sub(value, new_text)
                        if replaced != new_text:
                            new_text = replaced
                    if new_text != original_text:
                        run.text = new_text
                        any_run_change = True

                # Fallback for placeholders remaining after run-level changes: replace on full paragraph text
                if runs:
                    combined = "".join(r.text or "" for r in runs)
                    replaced_combined = combined
                    for bracketed, bracketed_flex, plain, plain_flex, value in compiled_patterns:
                        tmp = bracketed.sub(value, replaced_combined)
                        if tmp == replaced_combined:
                            tmp = bracketed_flex.sub(value, replaced_combined)
                        if tmp == replaced_combined:
                            tmp = plain.sub(value, replaced_combined)
                        if tmp == replaced_combined:
                            tmp = plain_flex.sub(value, replaced_combined)
                        replaced_combined = tmp
                    if replaced_combined != combined:
                        # Setting paragraph.text will recreate runs; ensures placeholders are filled
                        para.text = replaced_combined

            # Final XML-level pass on all text nodes (catches shapes/text boxes)
            try:
                for t in iter_all_text_nodes(doc):
                    orig = t.text or ""
                    new = orig
                    for b, bf, p, pf, value in compiled_patterns:
                        temp = b.sub(value, new)
                        if temp == new:
                            temp = bf.sub(value, new)
                        if temp == new:
                            temp = p.sub(value, new)
                        if temp == new:
                            temp = pf.sub(value, new)
                        new = temp
                    if new != orig:
                        t.text = new
            except Exception:
                pass
            
            # Save the final document
            doc.save(output_path)
            
            # Optional: Try updating fields (e.g., TOC) using Word automation on Windows
            try:
                import sys
                if sys.platform == 'win32':
                    import win32com.client  # type: ignore
                    word = win32com.client.Dispatch('Word.Application')
                    word.Visible = False
                    wdDoNotSaveChanges = 0
                    wdFormatXMLDocument = 12
                    doc_app = word.Documents.Open(output_path)
                    doc_app.Fields.Update()
                    for s in doc_app.Sections:
                        s.Headers(1).Range.Fields.Update()
                        s.Footers(1).Range.Fields.Update()
                    doc_app.Save()
                    doc_app.Close(wdDoNotSaveChanges)
                    word.Quit()
            except Exception as _e:
                # If automation not available, user can update fields in Word manually
                pass

            return output_path
            
        except Exception as e:
            logger.error(f"Error in document generation: {e}")
            raise


def test_smart_wizard():
    """Test function for the smart wizard."""
    print("🧪 Testing Smart Wizard")
    
    # Mock extracted values
    extracted_values = {
        "insert 2026 plan name": "Medicare Plus Blue Group PPO",
        "insert MAO name": "Blue Cross Blue Shield of Michigan",
        "insert TTY number": "711"
    }
    
    print(f"Mock extracted values: {extracted_values}")
    print("Smart wizard would show each variable individually for editing.")


if __name__ == "__main__":
    test_smart_wizard() 