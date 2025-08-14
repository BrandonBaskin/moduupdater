import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Optional
import re

from docx import Document
from config import Config
from ui_utils import UIUtils
from document_parser import DocumentParser
from validators import validate_by_type
from variable_utils import (
    normalize_variable_name,
    iter_all_paragraphs,
    iter_all_text_nodes,
)
# Wizard UI
class WizardUI(tk.Toplevel):
    """Wizard UI for interactive logic block processing."""
    def __init__(self, parent: tk.Tk, logic_blocks: List[Dict], doc_paragraphs: List[str], suggestions: Dict):
        super().__init__(parent)
        self.title("CMS Template Wizard")
        self.geometry(Config.WINDOW_SIZE_WIZARD)
        self.config(bg=Config.BG_COLOR)
        self.parent = parent
        self.logic_blocks = logic_blocks
        self.doc_paragraphs = doc_paragraphs or []
        self.suggestions = suggestions or {}
        self.block_list = DocumentParser.flatten_tree(logic_blocks)
        self.var_answers = {}
        self.var_instances = {}
        self.user_responses = {}
        self.current = 0
        # Build a frozen denominator: unique normalized variable names in this session
        self._unique_var_keys = self._build_unique_variable_keys()
        self.total_prompts = len(self._unique_var_keys)
        # Review queue for invalid/missing
        self._review_queue: List[Dict] = []
        self._build_ui()
        if not self.block_list:
            messagebox.showerror("Error", "No wizard steps found! Ensure your DOCX has logic fields.")
            self.destroy()

    def _build_ui(self):
        """Build the wizard UI."""
        self.label = UIUtils.create_label(self, "", font=Config.FONT)
        self.label.pack(pady=8)
        self.context = UIUtils.create_label(
            self, "", font=Config.FONT_SMALL, wraplength=800
        )
        self.context.pack(pady=(0, 5))
        self.suggest = UIUtils.create_label(
            self, "", font=Config.FONT_SMALL, wraplength=800
        )
        self.suggest.pack()
        self.input_var = tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.input_var, width=62, font=Config.FONT
        )
        self.choice_frame = tk.Frame(self, bg=Config.BG_COLOR)
        self.choice_frame.pack()
        self.opt_vars = []
        self.toggle_var = tk.BooleanVar()
        self.toggle_chk = tk.Checkbutton(
            self, text="Remove this section", variable=self.toggle_var,
            bg=Config.BG_COLOR, fg=Config.ACCENT_COLOR, font=Config.FONT
        )
        self._build_buttons()
        self.progress = ttk.Progressbar(
            self, length=740, mode='determinate', style="Custom.Horizontal.TProgressbar",
            maximum=max(1, self.total_prompts)
        )
        self.progress.pack(pady=6)
        self.status = UIUtils.create_label(self, "", font=Config.FONT_SMALL)
        self.status.pack()
        self.show_step()

    def _build_unique_variable_keys(self) -> List[str]:
        """Compute unique normalized variable names present in the wizard flow."""
        seen = set()
        order: List[str] = []
        for blk in self.block_list:
            if blk.get('type') != 'variable':
                continue
            name = self.safe_get_variable_name(blk)
            n = normalize_variable_name(name)
            if n and n not in seen:
                seen.add(n)
                order.append(n)
        return order

    def _classify_type(self, var_name: str) -> str:
        n = (var_name or '').lower()
        if 'tty' in n:
            return 'tty_number'
        if 'customer service' in n or 'phone' in n:
            return 'phone_number'
        if 'url' in n or 'website' in n or 'directory' in n:
            return 'url'
        if 'address' in n:
            return 'address'
        if ('hours' in n and 'operation' in n) or ('days' in n and 'hours' in n):
            return 'business_hours'
        if any(k in n for k in ['premium', 'copay', 'coinsurance', 'deductible', 'amount', 'cost']):
            return 'financial'
        return 'general'

    def _build_buttons(self):
        """Build navigation buttons."""
        btn_frame = tk.Frame(self, bg=Config.BG_COLOR)
        btn_frame.pack(pady=2)
        
        # First row of buttons - Navigation
        row1_frame = tk.Frame(btn_frame, bg=Config.BG_COLOR)
        row1_frame.pack(pady=2)
        buttons_row1 = [
            ("Back", self.back),
            ("Skip", self.skip),
            ("Delete/Remove", self.delete),
            ("Next", self.next_step)
        ]
        for text, cmd in buttons_row1:
            UIUtils.create_button(row1_frame, text, cmd).pack(side="left", padx=3)
        
        # Second row of buttons - Suggestion actions
        row2_frame = tk.Frame(btn_frame, bg=Config.BG_COLOR)
        row2_frame.pack(pady=2)
        buttons_row2 = [
            ("Accept Suggestion", self.accept_suggestion),
            ("Re-answer Variable", self.re_answer)
        ]
        for text, cmd in buttons_row2:
            UIUtils.create_button(row2_frame, text, cmd).pack(side="left", padx=3)
        
        # Third row of buttons - Bulk actions
        row3_frame = tk.Frame(btn_frame, bg=Config.BG_COLOR)
        row3_frame.pack(pady=2)
        buttons_row3 = [
            ("Accept All Suggestions", self.accept_all_suggestions),
            ("Skip All Remaining", self.skip_all_remaining)
        ]
        for text, cmd in buttons_row3:
            UIUtils.create_button(row3_frame, text, cmd).pack(side="left", padx=3)

    def get_paragraph_text(self, para_idx: Optional[int]) -> str:
        """Get paragraph text by index."""
        if para_idx is None or not self.doc_paragraphs:
            return ""
        try:
            paragraph = self.doc_paragraphs[para_idx]
            # Ensure we have a string
            if isinstance(paragraph, str):
                return paragraph.strip()
            elif isinstance(paragraph, dict):
                # Fallback for dict objects
                return paragraph.get('text', f"Block {paragraph.get('id', para_idx)}")
            else:
                return str(paragraph)
        except (IndexError, AttributeError):
            return ""

    def safe_get_variable_name(self, block: Dict) -> str:
        """Safely get variable name from block with fallback."""
        inner_text = block.get('inner_text', '')
        if inner_text is None or not isinstance(inner_text, str):
            # Fallback: try to extract from text field
            text = block.get('text', '')
            if isinstance(text, str) and '[' in text and ']' in text:
                import re
                match = re.search(r'\[([^\]]+)\]', text)
                inner_text = match.group(1).strip() if match else 'unknown_variable'
            else:
                inner_text = 'unknown_variable'
        return inner_text.strip()

    def get_variable_key(self, block: Dict) -> str:
        """Create a unique variable key."""
        var_name = self.safe_get_variable_name(block).lower()
        para_idx = block.get('para_idx', '')
        return f"{var_name}::{para_idx}"

    def show_step(self):
        """Display the current wizard step."""
        while self.current < len(self.block_list):
            block = self.block_list[self.current]
            if block['type'] == 'variable':
                var_key = self.get_variable_key(block)
                if var_key in self.var_answers:
                    self.parent.logmsg(
                        f"Skipping answered variable: {block['inner_text']} (para {block.get('para_idx', 'N/A')})"
                    )
                    self.current += 1
                    continue
            break

        if self.current >= len(self.block_list):
            self.finish()
            return

        block = self.block_list[self.current]
        
        # Create display text based on block type
        if block['type'] == 'variable':
            # For variables, show the variable name prominently and simplified context
            variable_name = f"[{self.safe_get_variable_name(block)}]"
            
            # Extract a clean context snippet (limit to ~100 chars)
            full_context = block.get('text', '')
            if len(full_context) > 200:
                # Find the variable in the context and show surrounding text
                var_pattern = rf"\[{re.escape(self.safe_get_variable_name(block))}\]"
                match = re.search(var_pattern, full_context, re.IGNORECASE)
                if match:
                    start_pos = max(0, match.start() - 50)
                    end_pos = min(len(full_context), match.end() + 50)
                    context_snippet = full_context[start_pos:end_pos].strip()
                    if start_pos > 0:
                        context_snippet = "..." + context_snippet
                    if end_pos < len(full_context):
                        context_snippet = context_snippet + "..."
                else:
                    context_snippet = full_context[:150] + "..." if len(full_context) > 150 else full_context
            else:
                context_snippet = full_context
            
            # Format the display
            display_text = f"{variable_name}\n\nDocument context:\n{context_snippet}"
        else:
            # For other block types, show the full text
            display_text = block['text']
        
        # Compute current prompt number among variables only
        completed_norms = set()
        for i, b in enumerate(self.block_list[:self.current]):
            if b.get('type') == 'variable':
                completed_norms.add(normalize_variable_name(self.safe_get_variable_name(b)))
        current_norm = normalize_variable_name(self.safe_get_variable_name(block)) if block.get('type') == 'variable' else ''
        current_index = (self._unique_var_keys.index(current_norm) + 1) if current_norm in self._unique_var_keys else len(completed_norms) + 1
        self.label.config(
            text=f"Step {current_index}/{self.total_prompts}  —  Type: {block['type'].capitalize()}\n\n{display_text}"
        )
        para = self.get_paragraph_text(block.get('para_idx'))
        self.context.config(text=f"Document context:\n{para}")
        self.input_var.set("")
        for widget in self.choice_frame.winfo_children():
            widget.destroy()
        self.entry.pack_forget()
        self.toggle_chk.pack_forget()
        self.opt_vars = []
        self.suggest.config(text="")

        if block['type'] == 'variable':
            var_key = self.get_variable_key(block)
            var_name = self.safe_get_variable_name(block)
            
            # Look for suggestions with multiple fallback keys
            auto_filled = None
            suggestion_keys = [
                var_name,  # Exact match
                var_name.lower(),  # Lowercase
                var_key,  # With para index
                var_name.replace(' ', ''),  # No spaces
                var_name.title(),  # Title case
            ]
            
            for key in suggestion_keys:
                if key in self.suggestions:
                    auto_filled = self.suggestions[key]
                    break
            
            prior = self.var_answers.get(var_key, auto_filled or "")
            if prior and prior != "None":
                self.suggest.config(text=f"Auto-filled: {prior}")
                self.input_var.set(prior)
            else:
                self.suggest.config(text="Auto-filled: None")
            self.entry.pack(pady=5)
        elif block['type'] == 'option':
            opts = block.get('options', [])
            if len(opts) > 2:
                self.opt_vars = []
                for opt in opts:
                    v = tk.BooleanVar()
                    cb = tk.Checkbutton(
                        self.choice_frame, text=opt, variable=v, bg=Config.BG_COLOR,
                        fg=Config.ACCENT_COLOR, font=Config.FONT
                    )
                    cb.pack(anchor="w")
                    self.opt_vars.append((opt, v))
            else:
                self.opt_var = tk.StringVar()
                for opt in opts:
                    rb = tk.Radiobutton(
                        self.choice_frame, text=opt, variable=self.opt_var, value=opt,
                        bg=Config.BG_COLOR, fg=Config.ACCENT_COLOR, font=Config.FONT
                    )
                    rb.pack(anchor="w")
        elif block['type'] == 'conditional':
            self.cond_var = tk.StringVar()
            for val in ("Yes", "No"):
                rb = tk.Radiobutton(
                    self.choice_frame, text=val, variable=self.cond_var, value=val,
                    bg=Config.BG_COLOR, fg=Config.ACCENT_COLOR, font=Config.FONT
                )
                rb.pack(anchor="w")
        elif block['type'] in ("optional", "delete"):
            self.toggle_chk.pack()
        self.progress['value'] = min(current_index, self.total_prompts)
        self.status.config(text=f"({current_index} of {self.total_prompts})")

    def accept_suggestion(self):
        """Accept the suggested value."""
        block = self.block_list[self.current]
        if block['type'] == 'variable':
            var_name = self.safe_get_variable_name(block)
            suggestion = self.suggestions.get(var_name, "")
            # Validate before applying
            vtype = self._classify_type(var_name)
            ok, _ = validate_by_type(vtype, suggestion)
            if ok:
                self.input_var.set(suggestion)
            else:
                messagebox.showwarning("Validation", f"Suggestion failed validation for type '{vtype}'.")

    def re_answer(self):
        """Allow re-answering a deduplicated variable."""
        block = self.block_list[self.current]
        if block['type'] == 'variable':
            var_key = self.get_variable_key(block)
            if var_key in self.var_answers:
                del self.var_answers[var_key]
                self.parent.logmsg(f"Re-answering variable: {block['inner_text']}")
                self.input_var.set("")
                self.suggest.config(text="")

    def accept_all_suggestions(self):
        """Accept all suggestions for remaining variables."""
        try:
            remaining_variables = 0
            accepted_count = 0
            rejected_count = 0
            self._review_queue.clear()
            
            # Count remaining variables and accept suggestions
            for i in range(self.current, len(self.block_list)):
                block = self.block_list[i]
                if block['type'] == 'variable':
                    remaining_variables += 1
                    var_key = self.get_variable_key(block)
                    var_name = self.safe_get_variable_name(block)
                    
                    # Check if we have a suggestion for this variable
                    if var_name in self.suggestions and self.suggestions[var_name]:
                        val = self.suggestions[var_name]
                        vtype = self._classify_type(var_name)
                        ok, reason = validate_by_type(vtype, val)
                        if ok:
                            self.var_answers[var_key] = val
                            accepted_count += 1
                            self.parent.logmsg(f"✅ Auto-accepted: {block['inner_text']} → {val}")
                        else:
                            rejected_count += 1
                            self._review_queue.append({
                                'name': var_name,
                                'reason': 'schema_error',
                                'suggested_value': val,
                                'source_hint': 'suggestion',
                                'confidence': 0.7
                            })
            
            if remaining_variables > 0:
                self.parent.logmsg(f"🎯 Accepted {accepted_count}/{remaining_variables} suggestions (rejected {rejected_count})")
                messagebox.showinfo("Accept All", f"Accepted {accepted_count} suggestions (rejected {rejected_count}).")
                self.finish()
            else:
                messagebox.showinfo("Accept All", "No remaining variables to accept suggestions for.")
                
        except Exception as e:
            self.parent.logmsg(f"❌ Error accepting all suggestions: {e}")
            messagebox.showerror("Error", f"Failed to accept all suggestions: {e}")

    def skip_all_remaining(self):
        """Skip all remaining variables."""
        try:
            remaining_count = len(self.block_list) - self.current
            if remaining_count > 0:
                self.current = len(self.block_list)
                self.parent.logmsg(f"⏭️ Skipped {remaining_count} remaining variables")
                messagebox.showinfo("Skip All", f"Skipped {remaining_count} remaining variables.")
                self.finish()
            else:
                messagebox.showinfo("Skip All", "No remaining variables to skip.")
                
        except Exception as e:
            self.parent.logmsg(f"❌ Error skipping all remaining: {e}")
            messagebox.showerror("Error", f"Failed to skip all remaining: {e}")

    def record_step(self, action: str):
        """Record the user's response."""
        block = self.block_list[self.current]
        if block['type'] == 'variable':
            var_key = self.get_variable_key(block)
            answer = self.input_var.get()
            if answer:
                self.var_answers[var_key] = answer
                if var_key not in self.var_instances:
                    self.var_instances[var_key] = []
                self.var_instances[var_key].append(block['id'])
        elif block['type'] == 'option':
            opts = block.get('options', [])
            bid = block['id']
            if len(opts) > 2:
                selected = [opt for opt, v in self.opt_vars if v.get()]
                self.user_responses[bid] = selected
            else:
                answer = getattr(self, 'opt_var', tk.StringVar()).get()
                self.user_responses[bid] = answer
        elif block['type'] == 'conditional':
            bid = block['id']
            answer = getattr(self, 'cond_var', tk.StringVar()).get()
            self.user_responses[bid] = (answer == "Yes")
        elif block['type'] in ("optional", "delete"):
            bid = block['id']
            self.user_responses[bid] = self.toggle_var.get()

    def next_step(self):
        """Move to the next step."""
        self.record_step("filled")
        if self.current < len(self.block_list) - 1:
            self.current += 1
            self.show_step()
        else:
            self.finish()

    def skip(self):
        """Skip the current step."""
        if self.current < len(self.block_list) - 1:
            self.current += 1
            self.show_step()
        else:
            self.finish()

    def back(self):
        """Go back to the previous step."""
        if self.current > 0:
            self.current -= 1
            self.show_step()

    def delete(self):
        """Mark the step for deletion."""
        block = self.block_list[self.current]
        if block['type'] in ("optional", "delete"):
            self.toggle_var.set(True)
        self.next_step()

    def finish(self):
        """Finish the wizard, fill template, and save results."""
        try:
            # Save user responses
            responses = {
                "var_answers": self.var_answers,
                "user_responses": self.user_responses,
                "var_instances": self.var_instances
            }
            os.makedirs(os.path.dirname(Config.USER_RESPONSE_PATH), exist_ok=True)
            with open(Config.USER_RESPONSE_PATH, "w", encoding="utf-8") as f:
                json.dump(responses, f, indent=2)
            
            self.parent.logmsg(f"💾 Wizard responses saved to {Config.USER_RESPONSE_PATH}")

            # Build answers and review artifacts (validated only)
            answers: Dict[str, str] = {}
            missing: List[str] = []
            # Aggregate by normalized name
            grouped: Dict[str, Dict[str, str]] = {}
            for key, val in self.var_answers.items():
                raw = key.split('::')[0]
                n = normalize_variable_name(raw)
                grouped.setdefault(n, {})[raw] = val
            # Validate and choose canonical raw key per group
            for nkey, variants in grouped.items():
                # Pick the longest raw key (most specific)
                raw_key = max(variants.keys(), key=len)
                value = variants[raw_key]
                vtype = self._classify_type(raw_key)
                ok, reason = validate_by_type(vtype, value)
                if ok:
                    answers[raw_key] = value
                else:
                    self._review_queue.append({
                        'name': raw_key,
                        'reason': 'schema_error',
                        'suggested_value': value,
                        'source_hint': 'wizard_input',
                        'confidence': 0.8
                    })
            # Detect missing for unique keys
            for n in self._unique_var_keys:
                if not any(normalize_variable_name(k) == n for k in answers.keys()):
                    missing.append(n)
                    self._review_queue.append({
                        'name': n,
                        'reason': 'missing',
                        'suggested_value': '',
                        'source_hint': 'wizard_unanswered',
                        'confidence': 0.0
                    })

            # Write artifacts
            artifacts_dir = os.path.join('assets', 'processsed', 'wizard_artifacts')
            os.makedirs(artifacts_dir, exist_ok=True)
            with open(os.path.join(artifacts_dir, 'answers.json'), 'w', encoding='utf-8') as f:
                json.dump({'answers': answers}, f, indent=2)
            with open(os.path.join(artifacts_dir, 'review_queue.json'), 'w', encoding='utf-8') as f:
                json.dump(self._review_queue, f, indent=2)
            # Coverage summary
            answered_total = len({normalize_variable_name(k) for k in answers.keys()})
            required_total = self.total_prompts
            coverage_rate = (answered_total / max(1, required_total)) * 100.0
            coverage = {
                'required_total': required_total,
                'answered_total': answered_total,
                'coverage_rate': round(coverage_rate, 2)
            }
            with open(os.path.join(artifacts_dir, 'coverage_summary.json'), 'w', encoding='utf-8') as f:
                json.dump(coverage, f, indent=2)
            # QA report
            schema_issues = sum(1 for r in self._review_queue if r['reason'] == 'schema_error')
            needs_review = len(self._review_queue)
            qa_lines = [
                f"Coverage: {answered_total} / {required_total} ({coverage_rate:.1f}%)",
                f"Schema issues: {schema_issues}",
                f"Needs review: {needs_review}"
            ]
            with open(os.path.join(artifacts_dir, 'qa_report.md'), 'w', encoding='utf-8') as f:
                f.write('\n'.join(qa_lines))
            
            # Fill the template with the selected values
            filled_template_path = self.fill_template_with_values()
            
            if filled_template_path:
                self.parent.logmsg(f"✅ Template filled and saved to: {filled_template_path}")
                messagebox.showinfo("Wizard Complete", 
                                  f"Wizard completed successfully!\n\n"
                                  f"Filled template saved to:\n{filled_template_path}")
            else:
                messagebox.showinfo("Wizard Complete", "Wizard completed successfully!")
            
            self.parent.logmsg("Wizard session completed")
            self.destroy()
        except Exception as e:
            self.parent.logmsg(f"Error finishing wizard: {e}")
            messagebox.showerror("Error", f"Failed to finish wizard: {e}")

    def fill_template_with_values(self) -> Optional[str]:
        """Fill the template with the selected values and save to user-selected location."""
        try:
            from tkinter import filedialog
            from docx import Document
            import os
            import re
            from variable_utils import iter_all_paragraphs, iter_all_text_nodes
            
            # Ask user for save location
            save_path = filedialog.asksaveasfilename(
                title="Save Filled Template",
                defaultextension=".docx",
                filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
            )
            
            if not save_path:
                return None
            
            # Load the current model template
            if hasattr(self.parent, '_filepaths') and self.parent._filepaths.get('current_model'):
                template_path = self.parent._filepaths['current_model']
            else:
                messagebox.showerror("Error", "No current model template found!")
                return None
            
            # Load the template
            doc = Document(template_path)

            # Fill the template with user responses
            filled_count = 0
            # Build patterns once for efficiency (flexible whitespace and nested brackets)
            compiled_patterns = []
            for var_key, value in self.var_answers.items():
                var_name = var_key.split('::')[0]
                if not value:
                    continue
                esc = re.escape(var_name)
                esc_flex = re.sub(r"\\\s+", r"\\s+", esc.replace("\\ ", "\\s+"))
                b = re.compile(rf"\[+{esc}\]+", re.IGNORECASE)
                bf = re.compile(rf"\[+{esc_flex}\]+", re.IGNORECASE)
                p = re.compile(rf"\b{esc}\b", re.IGNORECASE)
                pf = re.compile(rf"\b{esc_flex}\b", re.IGNORECASE)
                compiled_patterns.append((b, bf, p, pf, str(value)))

            # Iterate paragraphs including those in tables and replace within runs (preserve formatting)
            for para in iter_all_paragraphs(doc):
                runs = getattr(para, 'runs', [])
                for run in runs:
                    original_text = run.text or ""
                    new_text = original_text
                    for b, bf, p, pf, value in compiled_patterns:
                        t = b.sub(value, new_text)
                        if t == new_text:
                            t = bf.sub(value, new_text)
                        if t == new_text:
                            t = p.sub(value, new_text)
                        if t == new_text:
                            t = pf.sub(value, new_text)
                        if t != new_text:
                            new_text = t
                    if new_text != original_text:
                        run.text = new_text
                        filled_count += 1
            
            # Final XML-level pass for all text nodes (catches shapes/text boxes)
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

            # Leftover scan: warn if placeholders remain
            leftovers = []
            pattern_left = re.compile(r"\[[^\]]+\]")
            for para in iter_all_paragraphs(doc):
                txt = (para.text or '').strip()
                if pattern_left.search(txt):
                    leftovers.append(txt[:120])
                    if len(leftovers) >= 10:
                        break
            if not leftovers:
                try:
                    for t in iter_all_text_nodes(doc):
                        s = (t.text or '').strip()
                        if pattern_left.search(s):
                            leftovers.append(s[:120])
                            if len(leftovers) >= 10:
                                break
                except Exception:
                    pass
            if leftovers:
                messagebox.showwarning("Leftover Placeholders", "Some placeholders remain unfilled. Examples:\n\n" + "\n".join(f"- {x}" for x in leftovers))

            # Save the filled template
            doc.save(save_path)
            
            # Optional: Try updating fields (e.g., TOC) via Word automation on Windows
            try:
                import sys
                if sys.platform == 'win32':
                    import win32com.client  # type: ignore
                    word = win32com.client.Dispatch('Word.Application')
                    word.Visible = False
                    wdDoNotSaveChanges = 0
                    doc_app = word.Documents.Open(save_path)
                    doc_app.Fields.Update()
                    for s in doc_app.Sections:
                        s.Headers(1).Range.Fields.Update()
                        s.Footers(1).Range.Fields.Update()
                    doc_app.Save()
                    doc_app.Close(wdDoNotSaveChanges)
                    word.Quit()
            except Exception:
                pass

            self.parent.logmsg(f"📄 Template filled with {filled_count} values")
            return save_path
            
        except Exception as e:
            self.parent.logmsg(f"❌ Error filling template: {e}")
            messagebox.showerror("Error", f"Failed to fill template: {e}")
            return None