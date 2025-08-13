# dashboard.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import json
import os
import re
import csv
import zipfile
from docx import Document
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from config import Config
from logging_config import logger
from document_parser import DocumentParser
from logic_mapper_llm import LogicMapper
from learning_persistence import LearningPersistence
from ollama_manager import get_ollama_manager
from logic_variable_reviewer import ReviewGUI
from ui_utils import UIUtils
from wizard import WizardUI
from datetime import datetime

@dataclass
class AppState:
    doc2025: Optional[str] = None       # path to 2025 final EOC
    doc2026: Optional[str] = None       # path to 2026 model
    pack: Optional[str] = None          # context pack JSON (wizard_context_pack.json)
    answers: Optional[str] = None       # answers.json
    outdir: Optional[str] = None        # chosen output folder
    use_llm_fallback: bool = False      # checkbox/toggle
    qa_artifacts: Dict[str, str] = field(default_factory=dict)  # report file paths

# Main Dashboard UI
class DashboardUI(tk.Tk):
    """Main dashboard for the CMS Wizard."""
    def __init__(self):
        super().__init__()
        self.title("CMS Wizard Dashboard")
        self.geometry(Config.WINDOW_SIZE_MAIN)
        self.configure(bg=Config.BG_COLOR)
        self.resizable(True, True)
        # New centralized app state
        self.state = AppState()
        # Legacy filepaths kept for backwards compatibility with existing flows
        self._filepaths = {
            'last_model': None,
            'last_final': None,
            'current_model': None
        }
        # Recent files (persisted)
        self.recent_files_path = os.path.join('database', 'recent_files.json')
        self.recent_files = self._load_recent_files()
        self.logic_tree = None
        self.doc_paragraphs = None
        self.suggestions = {}
        self.model_mapping_results = {}
        self.extracted_values = None  # Store extracted values from map_final_to_model
        
        # Initialize components
        self.parser = DocumentParser()
        self.mapper = LogicMapper()  # This now includes persistent learning and Ollama
        self.learning_persistence = LearningPersistence()
        self.ollama_manager = get_ollama_manager()
        # Track applied update packs summary
        self.updates_applied = []  # list of {path, applied, overwritten, considered, timestamp}
        
        # Load learning statistics
        self.learning_stats = self.learning_persistence.get_learning_stats()
        self._build_ui()
        self._validate_methods()

    def _validate_methods(self):
        """Validate required methods."""
        required = [
            'load_last_model', 'load_last_final', 'map_final_to_model',
            'load_current_model', 'map_models_to_each_other', 'build_wizard', 'run_wizard'
        ]
        for method in required:
            if not hasattr(self, method):
                raise AttributeError(f"Missing method: {method}")
        logger.info("All required methods validated")

    def import_answer_pack(self):
        """Import an external answer pack and either populate the Wizard or fill a template directly."""
        try:
            from tkinter import filedialog
            import zipfile, tempfile
            sel = filedialog.askopenfilename(title="Select Answer Pack (JSON or ZIP)", filetypes=[("Answer Pack","*.json;*.zip"), ("JSON","*.json"), ("ZIP","*.zip")])
            if not sel:
                return
            temp_dir = None
            answers = {}
            if sel.lower().endswith('.zip'):
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(sel, 'r') as z:
                    z.extractall(temp_dir)
                # Locate context pack
                ctx_path = None
                for cand in [
                    os.path.join(temp_dir, 'wizard_context_pack.json'),
                    os.path.join(temp_dir, 'context', 'wizard_context_pack.json')
                ]:
                    if os.path.exists(cand):
                        ctx_path = cand
                        break
                if ctx_path:
                    if not hasattr(self, '_state'):
                        self._state = {}
                    self._state['context_pack_path'] = ctx_path
                # Locate answers
                answers_path = None
                for cand in [
                    'answers.json',
                    'wizard_answers_matched_keys_v5.json',
                    'wizard_answers_full_v7.json',
                    'wizard_answers.json'
                ]:
                    p = os.path.join(temp_dir, cand)
                    if os.path.exists(p):
                        answers_path = p
                        break
                if not answers_path:
                    answers_path = filedialog.askopenfilename(title="Select answers JSON", initialdir=temp_dir, filetypes=[("JSON","*.json")])
                    if not answers_path:
                        return
                with open(answers_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                answers = data.get('answers', data)
                self._state['answers_path'] = answers_path
                self._state['imported_pack'] = sel
                self.state.answers = answers_path
            else:
                with open(sel, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                answers = data.get('answers', data)
                if not hasattr(self, '_state'):
                    self._state = {}
                self._state['answers_path'] = sel
                if not self._state.get('context_pack_path'):
                    ctx = filedialog.askopenfilename(title="Select Context Pack (wizard_context_pack.json)", filetypes=[("JSON","*.json")])
                    if ctx:
                        self._state['context_pack_path'] = ctx
                self._state['imported_pack'] = sel
                self.state.answers = sel
            # Ensure context pack available; if missing and we have doc2026, auto-generate
            try:
                ctx_path = getattr(self, '_state', {}).get('context_pack_path') or self.state.pack
                if (not ctx_path or not os.path.exists(ctx_path)) and self.state.doc2026:
                    from document_parser import parse_unique_items
                    items = parse_unique_items(self.state.doc2026)
                    os.makedirs('database', exist_ok=True)
                    ctx_path = os.path.join('database', 'wizard_context_pack.json')
                    with open(ctx_path, 'w', encoding='utf-8') as cf:
                        json.dump({'items': items}, cf, indent=2)
                    if not hasattr(self, '_state'):
                        self._state = {}
                    self._state['context_pack_path'] = ctx_path
                    self.state.pack = ctx_path
                    self.logmsg(f"🧩 Auto-generated context pack for import: {ctx_path}")
                # If we have a context pack, expand canonical keys (e.g., mbc_*) to raw names/placeholders
                if ctx_path and os.path.exists(ctx_path):
                    with open(ctx_path, 'r', encoding='utf-8') as cf:
                        pack = json.load(cf)
                    expanded = {}
                    items = pack.get('items', []) if isinstance(pack, dict) else []
                    mapped = 0
                    for it in items:
                        raw_name = it.get('name')
                        key = it.get('canonical_key') or raw_name
                        if key in answers and answers[key] not in (None, ""):
                            val = str(answers[key])
                            # add raw variable name
                            if raw_name:
                                expanded[raw_name] = val
                            # add occurrence placeholders if present
                            for occ in it.get('occurrences', []) or []:
                                ph = occ.get('placeholder')
                                if ph:
                                    expanded[ph.strip('[]')] = val
                            mapped += 1
                    # merge: keep already provided exact keys too
                    for k, v in answers.items():
                        if v not in (None, ""):
                            expanded[k] = str(v)
                    answers = expanded
                    self.logmsg(f"🧩 Expanded canonical keys via context pack: {mapped} items mapped")
            except Exception:
                pass
            # Ask user what to do
            choice = messagebox.askyesno("Import Answer Pack", "Populate the Smart Wizard now? (Yes)\nOr fill a template directly? (No)")
            if choice:
                # Populate wizard session
                if not self._filepaths.get('current_model'):
                    messagebox.showwarning("Import", "Please load the current year model before populating the Wizard.")
                    return
                # Launch wizard and apply answers
                from smart_wizard import SmartWizard
                wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
                strict = True if getattr(self, '_state', {}).get('context_pack_path') else False
                if not strict:
                    strict = messagebox.askyesno("Strict Mode", "Enforce exact keys (1:1) when applying answers?")
                wiz.apply_answers_map(answers, strict=strict)
                self.logmsg("✅ Imported answers applied to wizard.")
                self.update_button_states()
            else:
                # Fill a template directly
                model_path = filedialog.askopenfilename(title="Select Model DOCX to fill", filetypes=[("Word DOCX","*.docx")])
                if not model_path:
                    return
                save_path = filedialog.asksaveasfilename(title="Save Filled Template As", defaultextension=".docx", filetypes=[("Word DOCX","*.docx")], initialfile="Final_CMS_Document_from_pack.docx")
                if not save_path:
                    return
                # Use wizard's replacement engine without UI
                from smart_wizard import SmartWizard
                wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=model_path)
                strict = True if getattr(self, '_state', {}).get('context_pack_path') else False
                if not strict:
                    strict = messagebox.askyesno("Strict Mode", "Enforce exact keys (1:1) when applying answers?")
                wiz.apply_answers_map(answers, strict=strict)
                # Generate document using wizard's generator
                # Temporarily assign user_responses and call internal generation
                path = None
                try:
                    # Bypass dialog by setting destination and calling generator directly
                    # We'll mimic the _generate_final_document flow but write to save_path
                    from docx import Document as _Doc
                    from variable_utils import iter_all_paragraphs
                    import re
                    doc = _Doc(model_path)
                    # Build replacements
                    replacements = {}
                    for k, v in wiz.user_responses.items():
                        if v:
                            norm = wiz.knowledge_manager.normalize_variable_name(k)
                            replacements[k] = v
                            for var in wiz.variables:
                                if var['name_normalized'] == norm:
                                    replacements.setdefault(var['name'], v)
                    compiled = []
                    for var_name, value in replacements.items():
                        esc = re.escape(var_name)
                        esc_flex = re.sub(r"\\\s+", r"\\s+", esc.replace("\\ ", "\\s+"))
                        b = re.compile(rf"\[+{esc}\]+", re.IGNORECASE)
                        bf = re.compile(rf"\[+{esc_flex}\]+", re.IGNORECASE)
                        p = re.compile(rf"\b{esc}\b", re.IGNORECASE)
                        pf = re.compile(rf"\b{esc_flex}\b", re.IGNORECASE)
                        compiled.append((b,bf,p,pf,str(value)))
                    for para in iter_all_paragraphs(doc):
                        runs = getattr(para, 'runs', [])
                        any_change=False
                        for run in runs:
                            t = run.text or ""
                            new=t
                            for b,bf,p,pf,val in compiled:
                                r=b.sub(val,new)
                                if r==new: r=bf.sub(val,new)
                                if r==new: r=p.sub(val,new)
                                if r==new: r=pf.sub(val,new)
                                if r!=new: new=r
                            if new!=t:
                                run.text=new
                                any_change=True
                        if not any_change and runs:
                            combined = ''.join(r.text or '' for r in runs)
                            newc=combined
                            for b,bf,p,pf,val in compiled:
                                r=b.sub(val,newc)
                                if r==newc: r=bf.sub(val,newc)
                                if r==newc: r=p.sub(val,newc)
                                if r==newc: r=pf.sub(val,newc)
                                newc=r
                            if newc!=combined:
                                para.text=newc
                    doc.save(save_path)
                    path = save_path
                except Exception as e:
                    messagebox.showerror("Fill Template", f"Failed to fill: {e}")
                    return
                self.logmsg(f"✅ Filled template saved: {path}")
                messagebox.showinfo("Import Answer Pack", f"Filled template saved to:\n{path}")
                self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Import Answer Pack error: {e}")
            messagebox.showerror("Import Answer Pack", f"Failed: {e}")

    def run_playbook_flow(self):
        """Run high-precision extraction: produces answers, review list, and QA summary."""
        try:
            from tkinter import filedialog
            prior = self.state.doc2025 or filedialog.askopenfilename(title="Select Prior Final (DOCX)", filetypes=[("Word DOCX","*.docx")])
            if not prior:
                return
            model = self.state.doc2026 or self._filepaths.get('current_model') or filedialog.askopenfilename(title="Select Current Model (DOCX)", filetypes=[("Word DOCX","*.docx")])
            if not model:
                return
            ctx = self.state.pack or filedialog.askopenfilename(title="Select Context Pack (JSON)", filetypes=[("JSON","*.json")])
            if not ctx:
                return
            out_dir = self.state.outdir or filedialog.askdirectory(title="Select output folder for Playbook results")
            if not out_dir:
                return
            from playbook_runner import run_playbook
            outputs = run_playbook(prior, model, ctx, out_dir, client_rules=self._default_client_rules())
            self.logmsg(f"✅ Playbook completed. Answers: {outputs['answers_path']}")
            # Update state
            self.state.answers = outputs['answers_path']
            self.state.pack = ctx
            self.state.outdir = out_dir
            self.update_button_states()
            # Offer next steps
            if messagebox.askyesno("Playbook Complete", "Populate Wizard with results now? (Yes)\nOr just open the output folder? (No)"):
                with open(outputs['answers_path'], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                answers = data.get('answers', {})
                if not self._filepaths.get('current_model'):
                    self._filepaths['current_model'] = model
                from smart_wizard import SmartWizard
                wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
                wiz.apply_answers_map(answers, strict=False)
                self.logmsg("✅ Playbook answers applied to wizard.")
            else:
                os.startfile(out_dir) if hasattr(os, 'startfile') else None
        except Exception as e:
            self.logmsg(f"❌ Playbook error: {e}")
            messagebox.showerror("Playbook", f"Failed: {e}")

    def export_context_pack_bundle(self):
        """Generate a context pack and companion files (form JSON/CSV, README) from the current model, with an optional zip bundle."""
        try:
            # Ensure model is loaded or prompt for it
            model_path = self._filepaths.get('current_model') or self._filepaths.get('last_model')
            if not model_path:
                model_path = self._load_docx("Select MODEL DOCX to build Context Pack from")
                if not model_path:
                    return

            export_dir = filedialog.askdirectory(title="Select export folder for Context Pack")
            if not export_dir:
                return
            self.state.outdir = export_dir

            # Extract variables and contexts from model
            from docx import Document as _Doc
            from variable_utils import iter_all_paragraphs, iter_all_text_nodes

            def _classify_type(name: str) -> str:
                n = name.lower()
                if 'plan name' in n:
                    return 'plan_name'
                if 'mao name' in n or 'organization' in n:
                    return 'organization'
                if 'customer service' in n or 'phone' in n:
                    return 'phone_number'
                if 'tty' in n:
                    return 'tty_number'
                if ('hours' in n and 'operation' in n) or ('days' in n and 'hours' in n):
                    return 'business_hours'
                if 'address' in n:
                    return 'address'
                if 'url' in n or 'website' in n or 'directory' in n:
                    return 'url'
                if any(k in n for k in ['premium', 'copay', 'coinsurance', 'deductible', 'amount', 'cost']):
                    return 'financial'
                if 'state' in n or 'county' in n or 'zip' in n:
                    return 'location'
                return 'general'

            doc = _Doc(model_path)
            items = []
            counts = {}
            seen_keys = set()

            # Helper to add item and count
            def _add_item(name: str, vtype: str, full_context: str, before: str, after: str):
                key_norm = name.lower()
                items.append({
                    'name': name,
                    'type': vtype,
                    'occurrences': 1,
                    'full_context': full_context,
                    'before_context': before,
                    'after_context': after
                })
                counts[key_norm] = counts.get(key_norm, 0) + 1
                seen_keys.add(key_norm)

            # Paragraphs (body/headers/footers)
            for para in iter_all_paragraphs(doc):
                text = (para.text or '').strip()
                if '[' not in text or ']' not in text:
                    # Also capture unbracketed explicit insert instructions for visibility (optional keys)
                    if 'insert' in text.lower():
                        # Create a descriptive key from the immediate phrase after 'insert'
                        m2 = re.search(r"insert\s+([^\[\].:;]{3,80})", text, re.I)
                        if m2:
                            raw = m2.group(1).strip()
                            # Build a stable key
                            key_name = f"insert {raw}".strip()
                            if key_name.lower() not in seen_keys:
                                _add_item(key_name, _classify_type(key_name), text, text[:m2.start()].strip(), text[m2.end():].strip())
                    continue
                for m in re.finditer(r"\[([^\]]+)\]", text):
                    var_name = m.group(1).strip()
                    start, end = m.span()
                    before = text[:start].strip()
                    after = text[end:].strip()
                    vtype = _classify_type(var_name)
                    _add_item(var_name, vtype, text, before, after)

            # XML text nodes (shapes/text boxes)
            try:
                for t in iter_all_text_nodes(doc):
                    s = (t.text or '').strip()
                    if not s or '[' not in s or ']' not in s:
                        continue
                    for m in re.finditer(r"\[([^\]]+)\]", s):
                        var_name = m.group(1).strip()
                        if var_name.lower() in seen_keys:
                            continue
                        before = s[:m.start()].strip()
                        after = s[m.end():].strip()
                        vtype = _classify_type(var_name)
                        _add_item(var_name, vtype, s, before, after)
            except Exception:
                pass

            # MBC: derive per-row variables for two-column benefit chart tables
            def _normalize_label(txt: str) -> str:
                txt2 = re.sub(r"\[[^\]]*\]", " ", txt)
                txt2 = re.split(r"coverage|covered", txt2, flags=re.I)[0]
                txt2 = ' '.join(txt2.split())
                return txt2

            def _slugify(text: str) -> str:
                t = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
                t = re.sub(r"_+", "_", t).strip('_')
                return t[:60]

            for tbl in doc.tables:
                try:
                    if not tbl.rows or max(len(r.cells) for r in tbl.rows) < 2:
                        continue
                    for r in tbl.rows[1:]:
                        cells = r.cells
                        if len(cells) < 2:
                            continue
                        left = (cells[0].text or '').strip()
                        right = (cells[1].text or '').strip()
                        if not left:
                            continue
                        # Only create when right cell looks like placeholder/instruction or is empty
                        if ('[' in right and ']' in right) or ('insert' in right.lower()) or right.strip() == '':
                            label = _normalize_label(left)
                            if not label:
                                continue
                            key = f"mbc_{_slugify(label)}_cost_share"
                            if key.lower() in seen_keys:
                                continue
                            full_ctx = f"Service: {left} | What you pay: {right}".strip()
                            _add_item(key, 'financial', full_ctx, left, right)
                except Exception:
                    continue

            # Consolidate occurrences
            for it in items:
                it['occurrences'] = counts.get(it['name'].lower(), 1)

            # Build pack
            pack = {
                'current_year': '2026',
                'total_unique': len({it['name'].lower() for it in items}),
                'items': items,
                'keys': [it['name'] for it in items]
            }

            # Write files
            ctx_path = os.path.join(export_dir, 'wizard_context_pack.json')
            with open(ctx_path, 'w', encoding='utf-8') as f:
                json.dump(pack, f, indent=2)

            form_json_path = os.path.join(export_dir, 'wizard_form.json')
            with open(form_json_path, 'w', encoding='utf-8') as f:
                json.dump({'items': items, 'total_unique': pack['total_unique']}, f, indent=2)

            form_csv_path = os.path.join(export_dir, 'wizard_form.csv')
            with open(form_csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['name','type','occurrences','before_context','after_context','full_context'])
                for it in items:
                    writer.writerow([it['name'], it['type'], it['occurrences'], it['before_context'], it['after_context'], it['full_context']])

            readme_path = os.path.join(export_dir, 'README_PROMPT.txt')
            readme = (
                "Return ONLY JSON with exact keys from wizard_context_pack.json.\n"
                "Format: { \"answers\": { <exact key>: <value>, ... } }\n"
                "No extra prose. Include every key; if unknown, use an empty string.\n"
            )
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme)

            # Optional bundle zip
            bundle_zip = os.path.join(export_dir, 'wizard_answer_pack.zip')
            # Create answers.json for installable packs
            answers_path = os.path.join(export_dir, 'answers.json')
            try:
                generated_answers = {}
                # Prefer extracted values if available; otherwise create blanks
                if isinstance(self.extracted_values, dict) and self.extracted_values:
                    # Build normalized lookup and enable fuzzy fallback like SmartWizard
                    import re as _re
                    from difflib import SequenceMatcher as _SM
                    def _norm_key(s: str) -> str:
                        t = str(s).strip().lower()
                        if t.startswith('[') and t.endswith(']'):
                            t = t[1:-1].strip()
                        t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
                        t = _re.sub(r"\s+", " ", t).strip()
                        return t

                    norm_to_value = {}
                    for src_key, src_val in self.extracted_values.items():
                        if src_val is None:
                            continue
                        sv = str(src_val).strip()
                        if sv == "":
                            continue
                        nk = _norm_key(src_key)
                        # first write wins; preserves the first occurrence
                        norm_to_value.setdefault(nk, sv)

                    def _best_match(nkey: str):
                        best_key = None
                        best_score = 0.0
                        for k in norm_to_value.keys():
                            score = _SM(None, nkey, k).ratio()
                            if score > best_score:
                                best_score = score
                                best_key = k
                        return best_key, best_score

                    for k in pack['keys']:
                        nk = _norm_key(k)
                        if nk in norm_to_value:
                            generated_answers[k] = norm_to_value[nk]
                        else:
                            cand, score = _best_match(nk)
                            if cand and score >= 0.90:
                                generated_answers[k] = norm_to_value[cand]
                            else:
                                generated_answers[k] = ""
                else:
                    for k in pack['keys']:
                        generated_answers[k] = ""
                with open(answers_path, 'w', encoding='utf-8') as f:
                    json.dump({"answers": generated_answers}, f, indent=2)
            except Exception:
                answers_path = None

            with zipfile.ZipFile(bundle_zip, 'w', zipfile.ZIP_DEFLATED) as z:
                z.write(ctx_path, arcname='wizard_context_pack.json')
                z.write(form_json_path, arcname='wizard_form.json')
                z.write(form_csv_path, arcname='wizard_form.csv')
                z.write(readme_path, arcname='README_PROMPT.txt')
                if answers_path and os.path.exists(answers_path):
                    z.write(answers_path, arcname='answers.json')

            self.logmsg(f"📦 Context pack created: {ctx_path}")
            self.logmsg(f"📑 Form files: {form_json_path}, {form_csv_path}")
            self.logmsg(f"🧰 Bundle: {bundle_zip}")
            if not hasattr(self, '_state'):
                self._state = {}
            self._state['last_pack_created'] = bundle_zip
            created_msg = (
                f"Created:\n- {ctx_path}\n- {form_json_path}\n- {form_csv_path}\n- {readme_path}\n"
                + (f"- {answers_path}\n" if (answers_path and os.path.exists(answers_path)) else "")
                + f"- {bundle_zip}{' (includes answers.json)' if (answers_path and os.path.exists(answers_path)) else ''}"
            )
            messagebox.showinfo("Create Answer Pack", created_msg)
            # Refresh badges
            self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Error creating context pack: {e}")
            messagebox.showerror("Create Answer Pack", f"Failed: {e}")

    def run_preflight(self):
        """Run deterministic mapping and produce QA artifacts with a PASS/FAIL gate."""
        try:
            prior = self._filepaths.get('last_final') or self._load_docx("Select Prior Final (DOCX)")
            if not prior:
                return
            model = self._filepaths.get('current_model') or self._filepaths.get('last_model') or self._load_docx("Select Model (DOCX)")
            if not model:
                return
            from tkinter import filedialog
            ctx = filedialog.askopenfilename(title="Select Context Pack (JSON)", filetypes=[("JSON","*.json")])
            if not ctx:
                return
            out_dir = filedialog.askdirectory(title="Select output folder for Preflight results")
            if not out_dir:
                return
            from playbook_runner import run_playbook
            outputs = run_playbook(prior, model, ctx, out_dir, client_rules=self._default_client_rules())
            with open(outputs['answers_path'], 'r', encoding='utf-8') as f:
                ans = json.load(f).get('answers', {})
            with open(outputs['review_list_path'], 'r', encoding='utf-8') as f:
                review = json.load(f)
            with open(outputs['qa_summary_path'], 'r', encoding='utf-8') as f:
                qa = json.load(f)
            required_total = len(ans) + len([r for r in review if r.get('reason') in ('missing','schema_error')])
            answered_total = len(ans)
            schema_issues = sum(1 for r in review if r.get('reason') == 'schema_error')
            needs_review = len(review)
            ok = (answered_total == required_total) and schema_issues == 0 and needs_review == 0
            msg = (
                f"Coverage: {answered_total}/{required_total}\n"
                f"Schema issues: {schema_issues}\n"
                f"Needs review: {needs_review}\n\n"
                f"Artifacts:\n- {outputs['answers_path']}\n- {outputs['review_list_path']}\n- {outputs['qa_summary_path']}"
            )
            if ok:
                messagebox.showinfo("Preflight PASS", msg)
            else:
                messagebox.showwarning("Preflight FAIL", msg)
        except Exception as e:
            self.logmsg(f"❌ Preflight error: {e}")
            messagebox.showerror("Preflight", f"Failed: {e}")

    def _default_client_rules(self) -> dict:
        """Client rules and constants per playbook."""
        return {
            'constants_by_type': {
                'plan_name': 'Medicare Plus Blue Group PPO',
                'organization': 'Blue Cross Blue Shield of Michigan',
                'phone_number': '1-855-669-8040',
                'tty_number': '711',
                'business_hours': '8 a.m. to 5:30 p.m. Eastern time, Monday through Friday. From October 1 through March 31, hours are from 8 a.m. to 8 p.m. Eastern time, seven days a week.'
            },
            'constants': {
                # Name-specific constants can be extended here if needed
            },
            'url_preferences': ['umichmaplans', 'bcbsm.com/umichmaplans', 'medicare/help/formsdocuments/appointment-representative'],
            'enforce_dba_empty': True,
            'employer_billed_premium_blank': True
        }

    def _build_ui(self):
        """Build the dashboard UI."""
        # --- Menu bar ---
        self.menubar = tk.Menu(self)
        # File
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Open Last Year Model...", command=self.load_last_model)
        file_menu.add_command(label="Open Last Year Final...", command=self.load_last_final)
        file_menu.add_separator()
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        self.menubar.add_cascade(label="File", menu=file_menu)
        # Options
        options_menu = tk.Menu(self.menubar, tearoff=0)
        options_menu.add_command(label="Settings...", command=lambda: messagebox.showinfo("Options", "Settings coming soon."))
        self.menubar.add_cascade(label="Options", menu=options_menu)
        # About
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About",
            "CMS Model Updater\nSmart Wizard with knowledge base and year-over-year updates."
        ))
        self.menubar.add_cascade(label="About", menu=help_menu)
        self.config(menu=self.menubar)
        # Build initial recent menu
        self._rebuild_recent_menu()

        pad = {'padx': 12, 'pady': 6}
        UIUtils.create_label(self, "CMS Wizard Dashboard", font=Config.FONT_BOLD).pack(pady=(18, 4))
        # Current state banner
        self.state_label = UIUtils.create_label(self, "", font=Config.FONT_SMALL)
        self.state_label.pack()
        # Backward-compatible alias for legacy setters
        self.status_label = self.state_label

        # Main container with two columns (left: Inputs + Workflows, right: Tools)
        sections = tk.Frame(self, bg=Config.BG_COLOR)
        sections.pack(pady=(10, 12), fill='both', expand=True)
        left_col = tk.Frame(sections, bg=Config.BG_COLOR)
        right_col = tk.Frame(sections, bg=Config.BG_COLOR)
        left_col.pack(side='left', fill='both', expand=True, padx=(12, 6))
        right_col.pack(side='right', fill='both', expand=True, padx=(6, 12))

        # Badges helper dict
        self.badges = {}
        def make_badge(parent):
            lbl = tk.Label(parent, text="○ Missing", bg=Config.BG_COLOR, fg="#888", font=Config.FONT_SMALL)
            return lbl
        def add_row(frame, text, cmd_key, cmd_func):
            row = tk.Frame(frame, bg=Config.BG_COLOR)
            row.pack(fill='x', pady=2)
            btn = UIUtils.create_button(row, text, cmd_func, width=30)
            btn.pack(side='left')
            badge = make_badge(row)
            badge.pack(side='left', padx=8)
            self.btns[cmd_key] = btn
            self.badges[cmd_key] = badge

        # Initialize buttons dict
        self.btns = {}

        # Section 1: Load Inputs (left column, stacked)
        sec1 = tk.LabelFrame(left_col, text="1) Load Inputs", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, padx=10, pady=6)
        sec1.pack(fill='x', pady=(4, 8))
        add_row(sec1, "Load Last Year Final (DOCX)", 'doc2025', self.load_last_final)
        add_row(sec1, "Load Current Year Model (DOCX)", 'doc2026', self.load_current_model)
        add_row(sec1, "Load Context Pack (JSON)", 'load_pack', self.load_context_pack)

        # Section 2: Workflows (left column, stacked below Inputs)
        workflows = tk.LabelFrame(left_col, text="2) Workflows", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, padx=10, pady=6)
        workflows.pack(fill='both', expand=True, pady=(4, 8))
        add_row(workflows, "Build Wizard Tree", 'tree', self.build_wizard)
        add_row(workflows, "Run Wizard", 'run', self.run_wizard)
        add_row(workflows, "Quick Year Update (Apply Answers)", 'quick_update_apply', self.quick_year_update_apply)

        # Tools (right column, split Basic / Advanced)
        tools_basic = tk.LabelFrame(right_col, text="Tools", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, padx=10, pady=6)
        tools_basic.pack(fill='both', expand=False, pady=(4, 8))
        add_row(tools_basic, "Initialize & Build All (One‑Click)", 'oneclick_build', self.initialize_and_build_all)
        add_row(tools_basic, "Import Answer Pack", 'import_pack', self.import_answer_pack)
        add_row(tools_basic, "Export ChatGPT Bundle (.zip)", 'export_chatgpt', self.export_chatgpt_bundle)
        add_row(tools_basic, "Paste ChatGPT Output", 'paste_chatgpt', self.paste_chatgpt_output)
        add_row(tools_basic, "Instructions (Step‑by‑Step)", 'instructions', self.show_instructions)

        advanced = tk.LabelFrame(right_col, text="Advanced", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, padx=10, pady=6)
        advanced.pack(fill='both', expand=True, pady=(4, 8))
        add_row(advanced, "Create Answer Pack (Deterministic)", 'create_pack_det', self.create_answer_pack_deterministic)
        add_row(advanced, "Run High-Precision Auto-Fill (Playbook)", 'playbook', self.run_playbook_flow)
        add_row(advanced, "Build MBC Answers (updates)", 'build_mbc_answers', self.build_mbc_answers_from_updates)
        add_row(advanced, "Apply Updates Answer Packs", 'apply_updates_packs', self.apply_updates_answer_packs)
        add_row(advanced, "Export CSV + Prompt JSON", 'export_csv_prompt', self.export_csv_prompt)
        add_row(advanced, "Import Filled CSV", 'import_filled_csv', self.import_filled_csv_form)
        add_row(advanced, "Train AI (Curate Few‑shots)", 'train_ai', self.train_ai_from_files)
        add_row(advanced, "Generate Context Pack", 'generate_pack', self._on_generate_pack)
        add_row(advanced, "What is a Context Pack?", 'pack_help', self._on_context_help)
        add_row(advanced, "Updates Status", 'updates_status', self.show_updates_status)
        add_row(advanced, "Preflight (Deterministic QA)", 'preflight', self.run_preflight if hasattr(self, 'run_preflight') else (lambda: None))
        add_row(advanced, "Validate Model Mapping", 'validate_mapping', self.validate_model_mapping)

        # LM fallback toggle
        self.use_llm_var = tk.BooleanVar(value=False)
        # Place the LM toggle under Advanced for clarity
        llm_row = tk.Frame(advanced, bg=Config.BG_COLOR)
        llm_row.pack(fill='x', pady=2)
        cb = tk.Checkbutton(llm_row, text="Use LM fallback when deterministic misses", variable=self.use_llm_var, bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, command=self._on_toggle_llm)
        cb.pack(side='left')

        # Section 3: QA & Reports quick links (full width below columns)
        sec3 = tk.LabelFrame(self, text="3) QA & Reports", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, padx=10, pady=6)
        sec3.pack(fill='x', padx=16, pady=(0, 8))
        add_row(sec3, "Open QA Report", 'qa_report', lambda: self._open_artifact('qa_report.md'))
        add_row(sec3, "Open Coverage Summary", 'coverage_summary', lambda: self._open_artifact('coverage_summary.json'))
        add_row(sec3, "Open Schema Issues", 'schema_issues', lambda: self._open_artifact('schema_issues.csv'))
        add_row(sec3, "Open Review Queue", 'review_queue', lambda: self._open_artifact('review_queue.json'))
        add_row(sec3, "Open MBC Left Fingerprints", 'mbc_left', lambda: self._open_artifact('mbc_left_fingerprints.json'))

        # Legacy single buttons removed in favor of grouped sections above

        # Preflight (Deterministic QA)
        self.btns["preflight"] = tk.Button(
            self, text="✅ Preflight (Deterministic QA)", 
            command=self.run_preflight,
            bg=Config.ACCENT_COLOR, fg="white", font=Config.FONT,
            relief="flat", padx=20, pady=5
        )
        self.btns["preflight"].pack(pady=(5, 0))

        # Main progress bar
        self.progress = ttk.Progressbar(
            self, length=600, mode='determinate', style="Custom.Horizontal.TProgressbar"
        )
        self.progress.pack(pady=(15, 5), fill='x')

        # Step-specific progress bar
        self.step_progress_frame = tk.Frame(self, bg=Config.BG_COLOR)
        self.step_progress_frame.pack(pady=(5, 5))
        
        self.step_progress_label = UIUtils.create_label(
            self.step_progress_frame, "", font=Config.FONT_SMALL
        )
        self.step_progress_label.pack()
        
        self.step_progress = ttk.Progressbar(
            self.step_progress_frame, length=600, mode='determinate'
        )
        self.step_progress.pack()

        # Status text
        self.status_text = tk.Text(
            self, height=8, width=80, font=Config.FONT_SMALL,
            bg=Config.BG_COLOR, fg=Config.TEXT_COLOR, relief="flat"
        )
        self.status_text.pack(pady=(5, 10), fill='both', expand=True)

        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.status_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.status_text.configure(yscrollcommand=scrollbar.set)

        self.update_button_states()

        self.log = tk.Text(self, height=10, bg="#e0e8f0", fg=Config.ACCENT_COLOR,
                          font=Config.FONT_SMALL, wrap="word", borderwidth=0)
        self.log.pack(padx=24, fill="both", expand=True)
        self.logmsg("🚀 CMS Model Updater - Step 1: Load last year's model and final documents...")
        self.log.config(state="disabled")

    def logmsg(self, msg: str, newline: bool = True):
        """Log a message to the UI and logger."""
        self.log.config(state="normal")
        self.log.insert("end", msg + ("\n" if newline else ""))
        self.log.see("end")
        self.log.config(state="disabled")
        logger.info(msg)

    def set_status(self, msg: str):
        """Update the status label."""
        self.status_label.config(text=msg)

    def set_progress(self, val: float, maxval: float = 100):
        """Update the main progress bar."""
        self.progress["value"] = val
        self.progress["maximum"] = maxval
        percentage = int((val / maxval) * 100) if maxval > 0 else 0
        self.logmsg(f"Progress: {percentage}% ({val:.1f}/{maxval:.1f})")
        self.update_idletasks()

    def set_step_progress(self, step_name: str, val: float, maxval: float = 100):
        """Update the step-specific progress bar."""
        self.step_progress_label.config(text=f"Current Step: {step_name}")
        self.step_progress["value"] = val
        self.step_progress["maximum"] = maxval
        percentage = int((val / maxval) * 100) if maxval > 0 else 0
        self.logmsg(f"{step_name}: {percentage}% ({val:.1f}/{maxval:.1f})")
        self.update_idletasks()

    def update_button_states(self):
        """Update button states based on workflow sequence and color completed steps."""
        DARK_GREEN = "#1a7f3c"  # Progress bar green
        # Safely get buttons
        def set_btn(key, state="normal", done=False):
            btn = self.btns.get(key)
            if btn:
                btn.config(state=state, bg=DARK_GREEN if done else Config.ACCENT_COLOR)
        # Badge helper
        def set_badge(key: str, present: bool, done_label: str = "● Ready", missing_label: str = "○ Missing"):
            badge = self.badges.get(key)
            if badge:
                if present:
                    badge.config(text=done_label, fg=DARK_GREEN)
                else:
                    badge.config(text=missing_label, fg="#888")
        # Inputs
        set_badge("doc2025", bool(self.state.doc2025), done_label="● Ready")
        set_badge("doc2026", bool(self.state.doc2026), done_label="● Ready")
        set_badge("load_pack", bool(self.state.pack), done_label="● Ready")
        # Workflows
        set_btn("tree", "normal" if bool(self.state.doc2026) else "disabled", bool(self.state.pack))
        set_badge("tree", bool(self.state.pack), done_label="● Ready")
        set_btn("run", "normal" if bool(self.state.doc2026 and self.state.pack) else "disabled", done=False)
        # Tools
        can_create_pack = bool(self.state.doc2025 and self.state.doc2026)
        set_btn("create_pack_det", "normal" if can_create_pack else "disabled", done=bool(self.state.answers))
        set_btn("oneclick_build", "normal")
        set_badge("create_pack_det", bool(self.state.answers), done_label="● Ready")
        set_btn("import_pack", "normal", done=bool(self.state.answers))
        set_badge("import_pack", bool(self.state.answers), done_label="● Ready")
        set_btn("playbook", "normal" if can_create_pack else "disabled")
        set_btn("preflight", "normal" if can_create_pack else "disabled")
        set_btn("generate_pack", "normal" if bool(self.state.doc2026) else "disabled", done=bool(self.state.pack))
        set_badge("generate_pack", bool(self.state.pack), done_label="● Ready")
        set_btn("pack_help", "normal")
        set_btn("apply_updates_packs", "normal")
        set_btn("build_mbc_answers", "normal")
        set_btn("train_ai", "normal")
        set_btn("updates_status", "normal")
        set_btn("instructions", "normal")
        set_btn("export_csv_prompt", "normal")
        set_btn("import_filled_csv", "normal")
        # Quick Year Update requires doc2026 and answers
        set_btn("quick_update_apply", "normal" if bool(self.state.doc2026 and self.state.answers) else "disabled")

    def _load_docx(self, title: str) -> Optional[str]:
        """Load a DOCX file with validation."""
        fp = filedialog.askopenfilename(
            title=title, filetypes=[("Word DOCX files", "*.docx")]
        )
        if fp and os.path.exists(fp):
            try:
                Document(fp)
                return fp
            except Exception as e:
                self.logmsg(f"Invalid DOCX file: {e}")
                messagebox.showerror("Error", f"Invalid DOCX file: {e}")
        return None

    # --- Recent files helpers ---
    def _load_recent_files(self):
        try:
            os.makedirs('database', exist_ok=True)
            if os.path.exists(self.recent_files_path):
                with open(self.recent_files_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except Exception:
            pass
        return []

    def _save_recent_files(self):
        try:
            with open(self.recent_files_path, 'w', encoding='utf-8') as f:
                json.dump(self.recent_files[:10], f, indent=2)
        except Exception:
            pass

    def _add_recent_file(self, path: str):
        try:
            path = os.path.abspath(path)
            if path in self.recent_files:
                self.recent_files.remove(path)
            self.recent_files.insert(0, path)
            self.recent_files = self.recent_files[:10]
            self._save_recent_files()
            self._rebuild_recent_menu()
        except Exception:
            pass

    def _rebuild_recent_menu(self):
        # Clear and rebuild recent submenu
        self.recent_menu.delete(0, 'end')
        if not self.recent_files:
            self.recent_menu.add_command(label="(No recent files)", state='disabled')
            return
        for idx, path in enumerate(self.recent_files[:10], start=1):
            display = f"{idx}. {os.path.basename(path)}"
            self.recent_menu.add_command(label=display, command=lambda p=path: self._open_recent(p))

    def _open_recent(self, path: str):
        try:
            if not os.path.exists(path):
                messagebox.showwarning("Recent File", f"File not found:\n{path}")
                return
            # Heuristic: if 'model' in filename use as last_model, otherwise last_final
            if 'model' in os.path.basename(path).lower():
                self._filepaths['last_model'] = path
                self.logmsg(f"✅ Recent MODEL loaded: {os.path.basename(path)}")
                self.set_status("Step 2: Load last year's FINAL document.")
            else:
                self._filepaths['last_final'] = path
                self.logmsg(f"✅ Recent FINAL loaded: {os.path.basename(path)}")
                if self._filepaths['last_model']:
                    self.set_status("Step 3: Map final to model to extract values.")
            self._add_recent_file(path)
            self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Error opening recent file: {e}")

    def load_last_model(self):
        """Load the last year's model DOCX."""
        try:
            fp = self._load_docx("Select Last Year MODEL DOCX")
            if fp:
                self._filepaths["last_model"] = fp
                self.logmsg(f"✅ Last year MODEL loaded: {os.path.basename(fp)}")
                self.set_status("Step 2: Load last year's FINAL document.")
                self.set_progress(14, 100)  # 1/7 steps = ~14%
                self.update_button_states()
                self._add_recent_file(fp)
        except Exception as e:
            self.logmsg(f"❌ Error loading last model: {e}")
            messagebox.showerror("Error", f"Failed to load last model: {e}")

    def load_last_final(self):
        """Load the last year's final DOCX."""
        try:
            fp = self._load_docx("Select Last Year FINAL DOCX")
            if fp:
                self._filepaths["last_final"] = fp
                self.state.doc2025 = fp
                self.logmsg(f"✅ Last year FINAL loaded: {os.path.basename(fp)}")
                self.set_status("Step 3: Map final to model to extract values.")
                self.set_progress(28, 100)  # 2/7 steps = ~28%
                self.update_button_states()
                self._add_recent_file(fp)
        except Exception as e:
            self.logmsg(f"❌ Error loading last final: {e}")
            messagebox.showerror("Error", f"Failed to load last final: {e}")

    def map_final_to_model(self):
        """Map final document to model to extract values."""
        self.set_status("Step 3: Mapping final to model...")
        self.logmsg("🔄 Starting final to model mapping...")
        threading.Thread(target=self._map_final_thread, daemon=True).start()

    def _map_final_thread(self):
        """Thread for mapping final to model using ENHANCED approach with 23-type classification + AI agent."""
        try:
            def progress_callback(progress: float):
                self.set_step_progress("Extracting Variables", int(progress), 100)
            
            def log_callback(message: str):
                self.logmsg(f"📝 {message}")
            
            # Use the ENHANCED mapper with 23-type classification + AI agent
            from logic_mapper_llm import map_final_to_model
            from document_parser import DocumentParser
            
            # Parse model document into blocks
            parser = DocumentParser()
            model_blocks = parser.parse(self._filepaths["last_model"])
            
            # Parse final document into paragraphs (including tables/headers/footers)
            from docx import Document
            from variable_utils import iter_all_paragraphs
            final_doc = Document(self._filepaths["last_final"])
            final_paragraphs = []
            for para in iter_all_paragraphs(final_doc):
                txt = (para.text or "").strip()
                if txt:
                    final_paragraphs.append(txt)
            self.logmsg(f"📋 Final document paragraphs (incl. tables/headers/footers): {len(final_paragraphs)}")
            
            # Use SIMPLE mapping (no AI) - intelligence built into Smart Wizard
            from simple_mapping_engine import create_simple_mapping_engine
            
            # Create simple, fast mapping engine
            simple_engine = create_simple_mapping_engine()
            
            # Process variables with simple extraction (no AI calls)
            # Load existing extracted values from previous sessions (answers.json)
            try:
                with open('database/answers.json', 'r') as f:
                    self.extracted_values = json.load(f)
                self.logmsg(f"📋 Loaded {len(self.extracted_values)} existing values from answers.json")
            except FileNotFoundError:
                self.extracted_values = {}
                self.logmsg("📋 No existing answers.json found, starting fresh")
            
            extraction_logs = []
            
            variable_blocks = [block for block in model_blocks if block.get('type') == 'variable']
            total_variables = len(variable_blocks)
            
            self.logmsg(f"🚀 Simple mapping: Processing {total_variables} variables (no AI calls)")
            
            for i, block in enumerate(variable_blocks):
                var_name = block.get('inner_text', '')
                var_text = f"[{var_name}]"
                context_before = block.get('before_context', '')
                context_after = block.get('after_context', '')
                
                # Update progress
                progress = int((i + 1) / total_variables * 100)
                progress_callback(progress)
                
                # Simple extraction (no AI)
                extracted_value, confidence, reasoning, metadata = simple_engine.extract_variable_simple(
                    var_name, var_text, context_before, context_after, final_paragraphs
                )
                # If not found, run a second pass more tolerant to whitespace/formatting
                if (not extracted_value) or extracted_value == "None":
                    try:
                        extracted_value2, conf2, reasoning2, metadata2 = simple_engine.extract_variable_simple(
                            var_name, var_text, context_before.replace(' ', '\\s+'), context_after.replace(' ', '\\s+'), final_paragraphs
                        )
                        if extracted_value2 and extracted_value2 != "None":
                            extracted_value, confidence, reasoning, metadata = extracted_value2, conf2, reasoning2, metadata2
                    except Exception:
                        pass
                
                # Store results
                self.extracted_values[var_name] = extracted_value
                
                # Create log entry for wizard
                log_entry = {
                    'variable': var_name,
                    'type': 'variable',  # Legacy
                    'enhanced_type': metadata['enhanced_type'],
                    'extracted_value': extracted_value,
                    'source': 'simple_extraction',
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'metadata': metadata,
                    'requires_ai_review': True  # All variables need wizard review
                }
                extraction_logs.append(log_entry)
            
            self.logmsg(f"✅ Simple mapping complete: {len(self.extracted_values)} variables extracted")
            
            # Display results
            self.logmsg("📝 ⚡ SIMPLE Mapping Results (no AI - prepared for wizard):")
            for log in extraction_logs:
                var = log.get('variable')
                val = log.get('extracted_value', 'N/A')
                confidence = log.get('confidence', 0) * 100
                enhanced_type = log.get('enhanced_type', 'unknown')
                source = log.get('source', 'unknown')
                reasoning = log.get('reasoning', '')
                
                status = "⚡" if val != "None" else "⏳"
                type_icon = "🔧"  # Simple extraction icon
                
                self.logmsg(
                    f"  {status} {type_icon} [{var}] → '{val}'\n"
                    f"     Type: {enhanced_type} | Simple Extraction | Confidence: {confidence:.0f}%\n"
                    f"     🧙‍♂️ Will be enhanced by Smart Wizard"
                )

            # Final summary
            successful = sum(1 for log in extraction_logs if log.get('extracted_value') != "None")
            total = len(extraction_logs)
            success_rate = (successful / total * 100) if total > 0 else 0
            
            self.logmsg(f"📊 SIMPLE Summary: {successful}/{total} variables processed ({success_rate:.0f}%)")
            self.logmsg(f"⚡ Fast extraction with 23-type classification (no AI calls)")
            self.logmsg(f"🧙‍♂️ All {total} variables ready for Smart Wizard enhancement")
            
            # Simple mapping is meant to be fast, not perfect
            self.logmsg("🚀 FAST: Simple mapping completed in seconds!")
            self.logmsg("🎯 NEXT: Load current model to proceed with mapping")
            
            # Save extracted values
            with open('extracted_values.json', 'w') as f:
                json.dump(self.extracted_values, f, indent=2)
            self.logmsg("💾 Simple extracted values saved to 'extracted_values.json'")

            # Optional: If a context pack is present, run high-precision playbook to refine answers
            try:
                candidate_ctx = None
                candidates = [
                    os.path.join('assets', 'update_pack', 'wizard_context_pack.json'),
                    os.path.join('database', 'wizard_context_pack.json')
                ]
                for c in candidates:
                    if os.path.exists(c):
                        candidate_ctx = c
                        break
                if candidate_ctx:
                    self.logmsg(f"🧩 Context pack detected: {candidate_ctx} — running High-Precision Playbook…")
                    from playbook_runner import run_playbook
                    out_dir = os.path.join('assets', 'processsed', 'playbook_outputs')
                    os.makedirs(out_dir, exist_ok=True)
                    outputs = run_playbook(
                        prior_final_path=self._filepaths["last_final"],
                        current_model_path=self._filepaths["last_model"],
                        context_pack_path=candidate_ctx,
                        out_dir=out_dir,
                        client_rules=self._default_client_rules()
                    )
                    with open(outputs['answers_path'], 'r', encoding='utf-8') as f:
                        ans = json.load(f).get('answers', {})
                    # Merge refined answers (prefer validated playbook values)
                    applied = 0
                    for k, v in ans.items():
                        if v is None:
                            continue
                        sv = str(v).strip()
                        if sv != '':
                            self.extracted_values[k] = sv
                            applied += 1
                    with open('extracted_values.json', 'w', encoding='utf-8') as f:
                        json.dump(self.extracted_values, f, indent=2)
                    self.logmsg(f"✅ Playbook refinement applied: {applied} answers merged")
                    self.logmsg(f"📦 Review list: {outputs['review_list_path']}")
            except Exception as e2:
                self.logmsg(f"⚠️ Playbook refinement skipped: {e2}")
            
            # Store extraction logs for Smart Wizard
            self.mapping_results = extraction_logs
            
            # Update UI - ready for current model loading
            self.set_status("✅ Step 3 Complete - Ready to load current model")
            self.logmsg("🧙‍♂️ Next: Load current year model document")
            self.set_progress(45, 100)
            self.update_button_states()
            
        except Exception as e:
            import traceback
            self.logmsg(f"❌ Error in enhanced mapping: {e}")
            self.logmsg("💡 Fallback: Consider checking source document content and Ollama availability")
            self.logmsg(f"📋 Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Enhanced mapping failed: {e}")



    def load_current_model(self):
        """Load the current year's model DOCX."""
        try:
            fp = self._load_docx("Select Current Year MODEL DOCX")
            if fp:
                self._filepaths["current_model"] = fp
                self.state.doc2026 = fp
                self.logmsg(f"✅ Current year MODEL loaded: {os.path.basename(fp)}")
                self.set_status("Step 5: Map models to each other.")
                self.set_progress(57, 100)  # 4/7 steps = ~57%
                self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Error loading current model: {e}")
            messagebox.showerror("Error", f"Failed to load current model: {e}")

    def map_models_to_each_other(self):
        """Map models to each other with enhanced AI agent feedback."""
        self.set_status("Step 5: Mapping models to each other...")
        self.logmsg("🔄 Starting model-to-model mapping...")
        threading.Thread(target=self._map_models_thread, daemon=True).start()

    def _map_models_thread(self):
        """Thread for mapping models to each other with enhanced progress tracking."""
        try:
            from model_mapper import ModelVariableMapper
            
            # Initialize mapper
            mapper = ModelVariableMapper()
            
            # Set up progress tracking
            def progress_callback(message: str, current: int = None, total: int = None):
                if current is not None and total is not None:
                    percentage = (current / total) * 100
                    self.set_step_progress("Model-to-Model Mapping", current, total)
                    self.logmsg(f"🤖 {message} ({percentage:.1f}%)")
                else:
                    self.logmsg(f"🤖 {message}")
            
            def log_callback(message: str):
                self.logmsg(f"📝 {message}")
            
            # Perform mapping with enhanced AI feedback
            mapping_results = mapper.map_variables_between_models(
                old_model_path=self._filepaths["last_model"],
                new_model_path=self._filepaths["current_model"],
                progress_callback=progress_callback,
                log_callback=log_callback
            )
            
            # Validate mapping quality
            validation_results = mapper.validate_mapping(
                mapping_results,
                self._filepaths["last_model"],
                self._filepaths["current_model"]
            )
            
            # Create wizard suggestions
            wizard_suggestions = mapper.create_wizard_suggestions(
                mapping_results,
                self.extracted_values,
                log_callback
            )
            
            # Store all results
            self.model_mapping_results = {
                'variable_mapping': mapping_results,
                'wizard_suggestions': wizard_suggestions,
                'validation_results': validation_results,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save results
            with open('model_mapping_results.json', 'w') as f:
                json.dump(self.model_mapping_results, f, indent=2)
            
            # Log comprehensive results
            self.logmsg(f"✅ Model mapping completed!")
            self.logmsg(f"📊 Mapped {len(mapping_results)} variables")
            self.logmsg(f"💡 Created {len(wizard_suggestions)} wizard suggestions")
            self.logmsg(f"💾 Results saved to 'model_mapping_results.json'")
            
            # Show validation results
            if validation_results.get('status') == 'good':
                self.logmsg(f"🎯 Validation: {validation_results.get('overall_score', 0):.1f}% - Good quality")
            elif validation_results.get('status') == 'needs_review':
                self.logmsg(f"⚠️ Validation: {validation_results.get('overall_score', 0):.1f}% - Needs review")
            else:
                self.logmsg(f"❌ Validation: {validation_results.get('overall_score', 0):.1f}% - Poor quality")
            
            # Update UI
            self.set_status("Step 6: Build wizard tree with suggestions.")
            self.set_progress(71, 100)  # 5/7 steps = ~71%
            self.update_button_states()
            
        except Exception as e:
            self.logmsg(f"❌ Error in model mapping: {e}")
            messagebox.showerror("Error", f"Model mapping failed: {e}")

    def build_wizard(self):
        """Build the wizard tree with pre-populated suggestions."""
        try:
            self.set_status("Step 6: Building wizard tree...")
            self.logmsg("🔄 Building wizard tree with suggestions...")
            # Parse current model
            parsed_blocks = self.parser.parse(self._filepaths["current_model"])
            self.logmsg(f"📋 Parsed {len(parsed_blocks)} blocks from current model")
            
            # Create string paragraphs for wizard context display
            self.doc_paragraphs = []
            for block in parsed_blocks:
                text = block.get('text', '')
                if isinstance(text, str) and text.strip():
                    self.doc_paragraphs.append(text.strip())
                else:
                    self.doc_paragraphs.append(f"Block {block.get('id', 'unknown')}: {block.get('type', 'unknown')}")
            
            # Load suggestions from model mapping
            self.suggestions = self.model_mapping_results.get('wizard_suggestions', {})
            self.logmsg(f"📋 Loaded {len(self.suggestions)} pre-populated suggestions from model mapping")
            
            # Build logic tree from parsed blocks
            self.logic_tree = parsed_blocks
            
            # Save the wizard tree
            os.makedirs(os.path.dirname(Config.WIZARD_TREE_PATH), exist_ok=True)
            with open(Config.WIZARD_TREE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.logic_tree, f, indent=2)
            
            self.logmsg(f"🎯 Wizard tree built and saved as database\\wizard.json ({len(self.logic_tree)} steps).")

            # Also generate a minimal context pack JSON as per spec if missing
            try:
                ctx_items = []
                for b in parsed_blocks:
                    if b.get('type') == 'variable':
                        ctx_items.append({
                            'name': b.get('inner_text') or b.get('variable_text', '').strip('[]'),
                            'type': 'general',
                            'occurrences': 1,
                            'full_context': b.get('text',''),
                            'before_context': b.get('before_context',''),
                            'after_context': b.get('after_context','')
                        })
                pack_path = os.path.join('database', 'wizard_context_pack.json')
                with open(pack_path, 'w', encoding='utf-8') as pf:
                    json.dump({'items': ctx_items}, pf, indent=2)
                self.state.pack = pack_path
            except Exception:
                pass
            
            # Update UI
            self.set_status("Step 7: Run wizard with pre-populated suggestions.")
            self.set_progress(85, 100)  # 6/7 steps = ~85%
            self.update_button_states()
            
        except Exception as e:
            self.logmsg(f"❌ Error building wizard: {e}")
            messagebox.showerror("Error", f"Wizard building failed: {e}")

    def run_wizard(self):
        """Launch the smart wizard for variable input."""
        try:
            # Validate that we have everything needed
            if not self.state.doc2026:
                messagebox.showerror("Error", "No current model loaded. Please load current year model first.")
                return
            # Load suggestions from imported/created answers if available
            prefill_answers = {}
            if self.state.answers and os.path.exists(self.state.answers):
                try:
                    with open(self.state.answers, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        prefill_answers = data.get('answers', data) if isinstance(data, dict) else {}
                except Exception:
                    prefill_answers = {}
            
            self.logmsg("🧙‍♂️ Launching Smart Wizard...")
            if prefill_answers:
                self.logmsg(f"📊 Found {len(prefill_answers)} prefill answers from answer pack")
            
            # Launch the smart wizard
            from smart_wizard import SmartWizard
            wizard = SmartWizard(
                parent=self,
                extracted_values=prefill_answers or self.extracted_values or {},
                model_docx_path=self._filepaths['current_model']
            )
            
            # Update progress to 100%
            self.set_progress(100, 100)
            self.set_status("Wizard completed successfully!")
            
        except Exception as e:
            import traceback
            self.logmsg(f"❌ Error launching smart wizard: {e}")
            self.logmsg(f"📋 Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to launch wizard: {e}")

    def show_learning_stats(self):
        """Show learning statistics."""
        try:
            stats = self.learning_persistence.get_learning_stats()
            
            stats_window = tk.Toplevel(self)
            stats_window.title("Learning Statistics")
            stats_window.geometry("500x400")
            stats_window.configure(bg=Config.BG_COLOR)
            
            # Create text widget for stats
            stats_text = tk.Text(stats_window, bg=Config.BG_COLOR, fg=Config.TEXT_COLOR,
                               font=Config.FONT_SMALL, wrap="word")
            stats_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Format and display stats
            stats_content = f"""
🧠 AI Agent Learning Statistics

📊 Patterns Learned: {stats.get('total_patterns', 0)}
📝 Examples Stored: {stats.get('total_examples', 0)}
🔄 Extraction History: {stats.get('total_extractions', 0)}
📈 Average Confidence: {stats.get('avg_confidence', 0):.2f}%

📋 Variable Types:
{chr(10).join(f"• {var_type}: {count} examples" for var_type, count in stats.get('variable_types', {}).items())}

🕒 Last Updated: {stats.get('last_updated', 'Never')}
            """
            
            stats_text.insert("1.0", stats_content)
            stats_text.config(state="disabled")
            
        except Exception as e:
            self.logmsg(f"❌ Error showing learning stats: {e}")
            messagebox.showerror("Error", f"Failed to show learning stats: {e}")

    def validate_model_mapping(self):
        """Validate the current model mapping."""
        try:
            if not self.model_mapping_results:
                messagebox.showinfo("Info", "No model mapping results to validate.")
                return
            
            validation = self.model_mapping_results.get('validation_results', {})
            
            # Create validation window
            val_window = tk.Toplevel(self)
            val_window.title("Model Mapping Validation")
            val_window.geometry("600x500")
            val_window.configure(bg=Config.BG_COLOR)
            
            # Create text widget for validation results
            val_text = tk.Text(val_window, bg=Config.BG_COLOR, fg=Config.TEXT_COLOR,
                             font=Config.FONT_SMALL, wrap="word")
            val_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Format validation results
            val_content = f"""
🔍 Model Mapping Validation Results

📊 Coverage Rate: {validation.get('coverage_rate', 0):.1f}%
🎯 Quality Score: {validation.get('quality_score', 0):.1f}%
⭐ Overall Score: {validation.get('overall_score', 0):.1f}%
📈 Status: {validation.get('status', 'Unknown')}

📋 Recommendations:
{chr(10).join(f"• {rec}" for rec in validation.get('recommendations', []))}

📊 Detailed Statistics:
• Year-based mappings: {validation.get('year_mappings', 0)}
• Static mappings: {validation.get('static_mappings', 0)}
• Known relationship mappings: {validation.get('known_mappings', 0)}
• Fuzzy/AI mappings: {validation.get('fuzzy_mappings', 0)}
            """
            
            val_text.insert("1.0", val_content)
            val_text.config(state="disabled")
            
        except Exception as e:
            self.logmsg(f"❌ Error validating model mapping: {e}")
            messagebox.showerror("Error", f"Validation failed: {e}")

    # New helpers from spec
    def _on_toggle_llm(self):
        self.state.use_llm_fallback = bool(self.use_llm_var.get())

    def load_context_pack(self):
        try:
            path = filedialog.askopenfilename(title="Select Context Pack (wizard_context_pack.json)", filetypes=[("JSON","*.json")])
            if not path:
                return
            self.state.pack = path
            self.logmsg(f"✅ Context pack loaded: {os.path.basename(path)}")
            self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Error loading context pack: {e}")
            messagebox.showerror("Error", f"Failed to load context pack: {e}")

    def _choose_outdir(self) -> bool:
        out = filedialog.askdirectory(title="Select output folder")
        if not out:
            return False
        self.state.outdir = out
        return True

    def _on_generate_pack(self):
        if not self.state.doc2026:
            messagebox.showwarning("Generate Context Pack", "Load the 2026 model first.")
            return
        if not self.state.outdir and not self._choose_outdir():
            return
        try:
            # Minimal unique-items builder using existing parser flow
            parsed_blocks = self.parser.parse(self.state.doc2026)
            items = []
            for b in parsed_blocks:
                if b.get('type') == 'variable':
                    items.append({
                        'name': b.get('inner_text') or b.get('variable_text','').strip('[]'),
                        'type': 'general',
                        'occurrences': 1,
                        'full_context': b.get('text',''),
                        'before_context': b.get('before_context',''),
                        'after_context': b.get('after_context','')
                    })
            pack_path = os.path.join(self.state.outdir, "wizard_context_pack.json")
            os.makedirs(self.state.outdir, exist_ok=True)
            with open(pack_path, "w", encoding="utf-8") as f:
                json.dump({"items": items}, f, indent=2)
            self.state.pack = pack_path
            self.logmsg(f"✅ Generated context pack → {pack_path}")
            self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Generate context pack failed: {e}")
            messagebox.showerror("Generate Context Pack", str(e))

    def _on_context_help(self):
        message = (
            "What is a context pack?\n\n"
            "It’s auto-generated from your 2026 model. The app scans the document "
            "for bracketed placeholders and stores each one with nearby text and table info.\n\n"
            "This helps the deterministic mapper find the right values from last year’s final.\n\n"
            "File: wizard_context_pack.json"
        )
        messagebox.showinfo("Context Pack", message)

    def initialize_and_build_all(self):
        """One‑Click workflow (decluttered):
        1) Map SOURCE Final → Prior Model (2025)
        2) Align Prior Model ↔ Current Model (2025→2026) and transfer answers
        3) Build Current Model context pack and convert to Wizard keys
        4) Offer CTAs (import to Wizard; Quick Year Update for MBC)
        """
        try:
            from tkinter import filedialog
            from document_parser import parse_unique_items
            from playbook_runner import run_playbook
            from convert_answers_for_wizard import convert_answers_for_wizard
            from model_mapper import ModelVariableMapper

            # 1) Resolve inputs (explicitly require prior model)
            current_model = self.state.doc2026 or self._filepaths.get('current_model') or self._load_docx("Select Current Model (DOCX)")
            if not current_model:
                return
            prior_final = self.state.doc2025 or self._filepaths.get('last_final') or self._load_docx("Select Prior Final (DOCX)")
            if not prior_final:
                return
            prior_model = self._filepaths.get('last_model') or self._load_docx("Select Prior Year Model (DOCX)")
            if not prior_model:
                return
            outdir = self.state.outdir or filedialog.askdirectory(title="Select output folder")
            if not outdir:
                return
            os.makedirs(outdir, exist_ok=True)

            # 2) Build context pack for prior model and run playbook (SOURCE → prior MODEL)
            pack_prior = os.path.join(outdir, 'wizard_context_pack_prior.json')
            with open(pack_prior, 'w', encoding='utf-8') as f:
                json.dump({'items': parse_unique_items(prior_model)}, f, indent=2)
            self.logmsg(f"📦 Built prior-model context pack: {pack_prior}")
            outputs_prior = run_playbook(prior_final, prior_model, pack_prior, outdir, client_rules=self._default_client_rules())
            answers_prior_path = outputs_prior['answers_path']
            self.logmsg(f"✅ SOURCE→prior MODEL answers: {answers_prior_path}")

            # 3) Align models and transfer answers to current model variable names
            mapper = ModelVariableMapper()
            mapping = mapper.map_variables_between_models(old_model_path=prior_model, new_model_path=current_model,
                                                          progress_callback=lambda *_: None, log_callback=self.logmsg)
            with open(answers_prior_path, 'r', encoding='utf-8') as f:
                prior_answers = json.load(f).get('answers', {})
            transferred: Dict[str, str] = {}
            for old_var, value in prior_answers.items():
                if not isinstance(value, str):
                    value = '' if value is None else str(value)
                new_var = mapping.get(old_var)
                if new_var and value.strip():
                    transferred[new_var] = mapper._update_value_for_year(value, old_var, new_var)
            answers_transferred_path = os.path.join(outdir, 'answers_transferred_to_current.json')
            with open(answers_transferred_path, 'w', encoding='utf-8') as f:
                json.dump({'answers': transferred}, f, indent=2)
            self.logmsg(f"🔁 Transferred answers to current model keys: {answers_transferred_path}")

            # 4) Build current model context pack and convert to wizard keys
            pack_current = os.path.join(outdir, 'wizard_context_pack.json')
            with open(pack_current, 'w', encoding='utf-8') as f:
                json.dump({'items': parse_unique_items(current_model)}, f, indent=2)
            answers_wizard = os.path.join(outdir, 'answers_for_wizard.json')
            convert_answers_for_wizard(pack_current, answers_transferred_path, answers_wizard, include_mbc=False)

            # 5) Optional: scaffold MBC for usability (best-effort)
            try:
                from scaffold_mbc import scaffold_mbc
                scaffold_out = os.path.join(outdir, '2026_model_scaffolded.docx')
                scaffold_mbc(current_model, pack_current, pack_current, scaffold_out)
            except Exception:
                pass

            # 6) Present CTAs and update state
            self.state.pack = pack_current
            self.state.answers = answers_transferred_path
            self.state.outdir = outdir
            self.update_button_states()
            msg = (
                f"Prior pack: {pack_prior}\n"
                f"SOURCE→prior answers: {answers_prior_path}\n"
                f"Current pack: {pack_current}\n"
                f"Transferred answers: {answers_transferred_path}\n"
                f"Wizard keys: {answers_wizard}\n\n"
                "Next: Import non‑MBC answers to the Wizard, then Quick Year Update for MBC."
            )
            if messagebox.askyesno("Initialize & Build All", msg + "\n\nImport non‑MBC answers to the Wizard now?"):
                if not self._filepaths.get('current_model'):
                    self._filepaths['current_model'] = current_model
                from smart_wizard import SmartWizard
                wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
                with open(answers_wizard, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                wiz.apply_answers_map(data.get('answers', {}), strict=True)
                self.logmsg("✅ Non‑MBC wizard answers imported.")
            else:
                self.logmsg("ℹ️ Skipped Wizard import.")

            # Optional Quick Year Update CTA (MBC deterministic)
            if messagebox.askyesno("Quick Year Update", "Apply MBC fills to a copy of the model now (deterministic)?"):
                from year_update_utility import YearUpdateUtility
                u = YearUpdateUtility()
                filled_path = os.path.join(outdir, 'CY2026_FILLED.docx')
                res = u.apply_answers_to_docx_with_pack(current_model, filled_path, pack_current, answers_transferred_path)
                if res.get('success'):
                    self.logmsg(f"✅ MBC applied: {res.get('applied',0)} rows → {filled_path}")
                    messagebox.showinfo("Quick Year Update", f"Applied: {res.get('applied',0)} rows\nSaved: {filled_path}")
                else:
                    self.logmsg(f"❌ Quick Year Update failed: {res.get('error')}")
                    messagebox.showerror("Quick Year Update", f"Failed: {res.get('error')}")
        except Exception as e:
            self.logmsg(f"❌ One‑Click error: {e}")
            messagebox.showerror("Initialize & Build All", f"Failed: {e}")

    def show_instructions(self):
        """Show a concise step-by-step guide for first-time and repeated runs."""
        try:
            text = (
                "Step-by-Step Guide\n\n"
                "1) Load Inputs\n"
                "   - Load Last Year Final (DOCX)\n"
                "   - Load Current Year Model (DOCX)\n\n"
                "2) Build Core Outputs (Deterministic)\n"
                "   - Generate Context Pack (or Create Answer Pack which runs the playbook)\n"
                "   - Run High-Precision Auto-Fill (Playbook): writes answers.json, review_list.json, qa_summary.json under core_files/out\n\n"
                "3) MBC (Medical Benefits Chart)\n"
                "   - Build MBC Answers (updates) if you have updates/ data, or rely on playbook carry-forward\n"
                "   - Apply MBC values using Quick Year Update (Apply Answers) with the context pack + answers.json\n\n"
                "4) Wizard (Non-MBC)\n"
                "   - Convert to wizard keys automatically when importing or by answers_for_wizard.json\n"
                "   - Import Answer Pack (non-MBC) into the Wizard and review\n\n"
                "5) Updates & Training (Optional)\n"
                "   - Apply Updates Answer Packs to merge curated values from updates/\n"
                "   - Train AI (Curate Few‑shots) to improve local autofill from accepted answers\n\n"
                "Tips\n"
                "- Always rebuild the context pack when models change.\n"
                "- Keep MBC through deterministic fill; use Wizard for non‑MBC.\n"
                "- Strict mode ensures only exact wizard keys are applied; use fuzzy for safe near matches.\n"
            )
            messagebox.showinfo("Instructions", text)
        except Exception as e:
            self.logmsg(f"❌ Instructions error: {e}")
            messagebox.showerror("Instructions", f"Failed: {e}")

    def export_csv_prompt(self):
        try:
            from tkinter import filedialog
            if not self.state.pack:
                if not self.state.doc2026:
                    messagebox.showwarning("Export CSV", "Load the 2026 model or a context pack first.")
                    return
                # Auto-generate minimal pack
                self._on_generate_pack()
            outdir = self.state.outdir or filedialog.askdirectory(title="Select export folder")
            if not outdir:
                return
            seed = self.state.answers  # optional
            from csv_form_io import export_csv_and_prompt_json
            res = export_csv_and_prompt_json(self.state.pack, outdir, seed)
            self.logmsg(f"✅ Exported CSV and prompt JSON: {res['csv_path']}, {res['prompt_json_path']}")
            messagebox.showinfo("Export CSV", f"CSV: {res['csv_path']}\nPrompt JSON: {res['prompt_json_path']}\nRows: {res['count']}")
        except Exception as e:
            self.logmsg(f"❌ Export CSV error: {e}")
            messagebox.showerror("Export CSV", f"Failed: {e}")

    def export_chatgpt_bundle(self):
        """Create a zip containing wizard_context_pack.json and a strict prompt + schema for ChatGPT."""
        try:
            from tkinter import filedialog
            import zipfile
            # Ensure a context pack is available
            if not self.state.pack:
                if not self.state.doc2026:
                    messagebox.showwarning("Export ChatGPT Bundle", "Load the 2026 model or a context pack first.")
                    return
                self._on_generate_pack()
                if not self.state.pack:
                    return
            out_zip = filedialog.asksaveasfilename(title="Save ChatGPT bundle as", defaultextension=".zip", filetypes=[("ZIP","*.zip")], initialfile="wizard_chatgpt_bundle.zip")
            if not out_zip:
                return
            # Prompt template with strict instructions
            prompt_txt = (
                "You are filling CMS Evidence of Coverage variables.\n"
                "You are given wizard_context_pack.json which lists variables with exact keys.\n\n"
                "Rules:\n"
                "- Return ONLY JSON with this shape: {\"answers\": { <key>: <value>, ... }}.\n"
                "- Use the 'canonical_key' from each item. If absent, use the 'name' exactly.\n"
                "- Include a value for every key. If truly unknown, use an empty string (\"\").\n"
                "- Do not add explanations or comments.\n"
            )
            schema_json = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["answers"],
                "properties": {
                    "answers": {
                        "type": "object",
                        "additionalProperties": {"type": ["string","number","boolean"]}
                    }
                }
            }
            with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
                z.write(self.state.pack, arcname='wizard_context_pack.json')
                z.writestr('README_PROMPT.txt', prompt_txt)
                z.writestr('answers.schema.json', json.dumps(schema_json, indent=2))
            self.logmsg(f"✅ ChatGPT bundle exported: {out_zip}")
            messagebox.showinfo("Export ChatGPT Bundle", f"Saved: {out_zip}")
        except Exception as e:
            self.logmsg(f"❌ Export ChatGPT Bundle error: {e}")
            messagebox.showerror("Export ChatGPT Bundle", f"Failed: {e}")

    def paste_chatgpt_output(self):
        """Quick dialog to paste ChatGPT's JSON output and import directly into the wizard."""
        try:
            if not self._filepaths.get('current_model'):
                messagebox.showwarning("Paste ChatGPT Output", "Load the current year model first.")
                return
            win = tk.Toplevel(self)
            win.title("Paste ChatGPT JSON")
            win.geometry("700x500")
            txt = tk.Text(win, wrap='word')
            txt.pack(fill='both', expand=True)
            def _apply():
                try:
                    raw = txt.get('1.0','end').strip()
                    # Permit code fences
                    if raw.startswith('```'):
                        raw = raw.strip('`')
                        # remove possible language tag
                        first_nl = raw.find('\n')
                        raw = raw[first_nl+1:] if first_nl != -1 else raw
                    data = json.loads(raw)
                    answers = data.get('answers', data)
                    from smart_wizard import SmartWizard
                    wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
                    wiz.apply_answers_map(answers, strict=False)
                    self.logmsg("✅ ChatGPT output applied to Wizard.")
                    win.destroy()
                except Exception as e2:
                    messagebox.showerror("Paste ChatGPT Output", f"Invalid JSON: {e2}")
            tk.Button(win, text="Apply to Wizard", command=_apply).pack(pady=6)
        except Exception as e:
            self.logmsg(f"❌ Paste ChatGPT error: {e}")
            messagebox.showerror("Paste ChatGPT Output", f"Failed: {e}")

    def import_filled_csv_form(self):
        try:
            from tkinter import filedialog
            if not self.state.pack:
                messagebox.showwarning("Import CSV", "Load a context pack first.")
                return
            path = filedialog.askopenfilename(title="Select filled CSV", filetypes=[("CSV","*.csv")])
            if not path:
                return
            outdir = self.state.outdir or os.path.dirname(path) or 'core_files/out'
            os.makedirs(outdir, exist_ok=True)
            out_json = os.path.join(outdir, 'answers_for_wizard_from_csv.json')
            from csv_form_io import import_filled_csv
            res = import_filled_csv(path, self.state.pack, out_json, strict=True)
            self.state.answers = out_json
            self.logmsg(f"✅ Imported filled CSV → {out_json} (accepted: {res['accepted']}, review: {res['review']})")
            # Offer to import into wizard immediately
            if messagebox.askyesno("Import to Wizard", "Load these answers into the Wizard now?"):
                if not self._filepaths.get('current_model'):
                    messagebox.showwarning("Wizard", "Load the current year model first.")
                    return
                with open(out_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                answers = data.get('answers', {})
                from smart_wizard import SmartWizard
                wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
                wiz.apply_answers_map(answers, strict=True)
                self.logmsg("✅ CSV answers applied to Wizard.")
        except Exception as e:
            self.logmsg(f"❌ Import CSV error: {e}")
            messagebox.showerror("Import CSV", f"Failed: {e}")

    def apply_updates_answer_packs(self):
        """Scan updates/ for answer packs and apply them via the Wizard import pathway."""
        try:
            base = os.path.join(os.getcwd(), 'updates')
            if not os.path.isdir(base):
                messagebox.showwarning("Updates", f"Folder not found:\n{base}")
                return
            candidates = []
            for fn in os.listdir(base):
                if not fn.lower().endswith('.json'):
                    continue
                p = os.path.join(base, fn)
                try:
                    with open(p, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, dict) and 'answers' in data:
                        candidates.append((p, data))
                except Exception:
                    continue
            if not candidates:
                messagebox.showinfo("Updates", "No answer packs with an 'answers' key found in updates/.")
                return
            # Confirm and merge
            if not messagebox.askyesno("Apply Updates", f"Found {len(candidates)} packs. Apply all to the Wizard?\n(You can still choose strict/fuzzy per existing import flow.)"):
                return
            from smart_wizard import SmartWizard
            if not self._filepaths.get('current_model'):
                messagebox.showwarning("Apply Updates", "Please load the current year model before applying packs.")
                return
            wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
            overwrite = messagebox.askyesno("Merge Policy", "Overwrite existing non-empty values if conflicts?\nYes = overwrite, No = fill only empty targets.")
            strict = messagebox.askyesno("Strict 1:1 Import?", "Require EXACT key matches (no fuzzy)? \nChoose No to allow safe fuzzy matching (>= 0.90).")
            merged: Dict[str, str] = {}
            per_pack_stats = []
            for path, data in candidates:
                try:
                    # Coerce using wizard helper for consistency
                    ans = wiz._coerce_answer_pack_to_dict(data)
                    ans = wiz._expand_answers_with_context_pack_if_available(ans)
                    considered = sum(1 for _ in ans.items())
                    applied = 0
                    overwritten_ct = 0
                    for k, v in ans.items():
                        sv = str(v or '').strip()
                        if not sv:
                            continue
                        if overwrite or k not in merged or not str(merged.get(k) or '').strip():
                            if k in merged and str(merged.get(k) or '').strip():
                                overwritten_ct += 1
                            merged[k] = sv
                            applied += 1
                except Exception as ie:
                    self.logmsg(f"⚠️ Skipping pack due to error: {path}: {ie}")
                    continue
                else:
                    per_pack_stats.append({
                        'path': path,
                        'applied': applied,
                        'overwritten': overwritten_ct,
                        'considered': considered,
                        'timestamp': datetime.now().isoformat(timespec='seconds')
                    })
            if not merged:
                messagebox.showinfo("Apply Updates", "No applicable entries found after merge.")
                return
            wiz.apply_answers_map(merged, strict=strict)
            # Persist merged answers as current state answers.json for Quick Update convenience
            try:
                os.makedirs('core_files/out', exist_ok=True)
                merged_path = os.path.join('core_files','out','answers_from_updates.json')
                with open(merged_path, 'w', encoding='utf-8') as f:
                    json.dump({'answers': merged}, f, indent=2)
                self.state.answers = merged_path
            except Exception:
                pass
            self.logmsg(f"✅ Applied {len(merged)} merged answers from updates/ packs to the Wizard")
            # Record summary for status panel
            self.updates_applied.extend(per_pack_stats)
        except Exception as e:
            self.logmsg(f"❌ Apply Updates error: {e}")
            messagebox.showerror("Apply Updates", f"Failed: {e}")

    def build_mbc_answers_from_updates(self):
        """Run the helper in updates/ to build an answers pack from MBC rows, then apply it."""
        try:
            base = os.path.join(os.getcwd(), 'updates')
            wizard_pack = self.state.pack or os.path.join('core_files','out','wizard_context_pack.json')
            mbc_path = os.path.join(base, 'mbc_2025_extracted.json')
            schema_path = os.path.join(base, 'mbc_mapping_schema.json')
            if not os.path.exists(wizard_pack):
                messagebox.showwarning("MBC Builder", "Context pack not found. Build or load it first.")
                return
            if not (os.path.exists(mbc_path) and os.path.exists(schema_path)):
                messagebox.showwarning("MBC Builder", "Required files missing in updates/:\n- mbc_2025_extracted.json\n- mbc_mapping_schema.json")
                return
            # Execute helper logic inline to avoid subprocess complexity
            try:
                with open(os.path.join(base, 'wizard_context_pack.json'), 'w', encoding='utf-8') as wf:
                    with open(wizard_pack, 'r', encoding='utf-8') as rf:
                        wf.write(rf.read())
                from updates.apply_mbc_mapping import apply_mapping
            except Exception:
                # Fallback: dynamic import from file path
                import importlib.util
                spec = importlib.util.spec_from_file_location('apply_mbc_mapping', os.path.join(base, 'apply_mbc_mapping.py'))
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(mod)  # type: ignore
                apply_mapping = getattr(mod, 'apply_mapping')
            result = apply_mapping(os.path.join(base,'wizard_context_pack.json'), mbc_path, schema_path, 2026)
            out_path = os.path.join(base, 'answers_from_helper.json')
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            self.logmsg(f"✅ Built MBC answers → {out_path}")
            if not messagebox.askyesno("Apply Now?", "Apply the generated MBC answers to the Wizard now?"):
                return
            # Apply through wizard, using coercion and context expansion
            from smart_wizard import SmartWizard
            if not self._filepaths.get('current_model'):
                messagebox.showwarning("Apply MBC Answers", "Please load the current year model before applying.")
                return
            wiz = SmartWizard(parent=self, extracted_values=self.extracted_values or {}, model_docx_path=self._filepaths['current_model'])
            ans = wiz._coerce_answer_pack_to_dict(result)
            ans = wiz._expand_answers_with_context_pack_if_available(ans)
            wiz.apply_answers_map(ans, strict=False)
            self.logmsg("✅ MBC answers applied to Wizard.")
            # Record single-pack application
            self.updates_applied.append({
                'path': os.path.join(base, 'answers_from_helper.json'),
                'applied': len([k for k,v in ans.items() if str(v or '').strip()]),
                'overwritten': 0,
                'considered': len(ans),
                'timestamp': datetime.now().isoformat(timespec='seconds')
            })
        except Exception as e:
            self.logmsg(f"❌ MBC Builder error: {e}")
            messagebox.showerror("MBC Builder", f"Failed: {e}")

    def show_updates_status(self):
        """Show a concise status window of applied updates packs and contribution counts."""
        try:
            win = tk.Toplevel(self)
            win.title("Updates Status")
            win.geometry("700x320")
            win.configure(bg=Config.BG_COLOR)
            cols = ("Pack", "Applied", "Overwritten", "Considered", "When")
            tree = ttk.Treeview(win, columns=cols, show='headings', height=10)
            for c, w in zip(cols, (360, 80, 90, 90, 160)):
                tree.heading(c, text=c)
                tree.column(c, width=w, anchor='w')
            tree.pack(fill='both', expand=True, padx=10, pady=10)
            for rec in self.updates_applied:
                tree.insert('', 'end', values=(
                    os.path.basename(rec.get('path','')),
                    rec.get('applied', 0),
                    rec.get('overwritten', 0),
                    rec.get('considered', 0),
                    rec.get('timestamp', '')
                ))
            if not self.updates_applied:
                self.logmsg("ℹ️ No updates packs have been applied yet.")
        except Exception as e:
            self.logmsg(f"❌ Updates Status error: {e}")
            messagebox.showerror("Updates Status", f"Failed: {e}")

    def train_ai_from_files(self):
        """Curate validator-approved few-shots and auto-values for the local autofill agent."""
        try:
            from tkinter import filedialog
            # Resolve pack
            pack = self.state.pack
            if not pack or not os.path.exists(pack):
                if self.state.doc2026:
                    # Auto-generate minimal pack if missing
                    parsed_blocks = self.parser.parse(self.state.doc2026)
                    items = []
                    for b in parsed_blocks:
                        if b.get('type') == 'variable':
                            items.append({
                                'name': b.get('inner_text') or b.get('variable_text','').strip('[]'),
                                'type': 'general',
                                'occurrences': 1,
                                'full_context': b.get('text',''),
                                'before_context': b.get('before_context',''),
                                'after_context': b.get('after_context','')
                            })
                    os.makedirs('core_files/out', exist_ok=True)
                    pack = os.path.join('core_files','out','wizard_context_pack.json')
                    with open(pack, 'w', encoding='utf-8') as f:
                        json.dump({'items': items}, f, indent=2)
                    self.state.pack = pack
                    self.logmsg(f"🧩 Auto-generated context pack for training: {pack}")
                else:
                    pack = filedialog.askopenfilename(title="Select Context Pack (wizard_context_pack.json)", filetypes=[("JSON","*.json")])
                    if not pack:
                        return
            # Resolve answers
            answers = self.state.answers
            if not answers or not os.path.exists(answers):
                answers = filedialog.askopenfilename(title="Select canonical answers (answers.json)", filetypes=[("JSON","*.json")])
                if not answers:
                    return
            # Curate
            from ai_training_curator import curate_from_pack_and_answers
            res = curate_from_pack_and_answers(pack, answers, out_dir='learning_data')
            msg = (
                f"Curated {res['counts']['examples']} examples.\n"
                f"Few-shots by type: {', '.join(f'{k}:{v}' for k,v in res['counts']['types'].items())}\n\n"
                f"Artifacts:\n- {res['paths']['few_shots']}\n- {res['paths']['auto_values']}\n- {res['paths']['training_data']}\n- {res['paths']['confidence_scores']}"
            )
            self.logmsg("✅ AI training data curated.")
            messagebox.showinfo("Train AI", msg)
        except Exception as e:
            self.logmsg(f"❌ Train AI error: {e}")
            messagebox.showerror("Train AI", f"Failed: {e}")

    def create_answer_pack_deterministic(self):
        try:
            if not self.state.doc2025 or not self.state.doc2026:
                messagebox.showwarning("Inputs", "Load 2025 final and 2026 model first.")
                return
            # Ensure context pack
            if not self.state.pack:
                # Build minimal pack automatically using parser
                parsed_blocks = self.parser.parse(self.state.doc2026)
                items = []
                for b in parsed_blocks:
                    if b.get('type') == 'variable':
                        items.append({
                            'name': b.get('inner_text') or b.get('variable_text','').strip('[]'),
                            'type': 'general',
                            'occurrences': 1,
                            'full_context': b.get('text',''),
                            'before_context': b.get('before_context',''),
                            'after_context': b.get('after_context','')
                        })
                os.makedirs('database', exist_ok=True)
                pack_path = os.path.join('database', 'wizard_context_pack.json')
                with open(pack_path, 'w', encoding='utf-8') as f:
                    json.dump({'items': items}, f, indent=2)
                self.state.pack = pack_path
            # Choose outdir
            out_dir = self.state.outdir or filedialog.askdirectory(title="Select output folder for Answer Pack")
            if not out_dir:
                return
            self.state.outdir = out_dir
            from playbook_runner import run_playbook
            outputs = run_playbook(self.state.doc2025, self.state.doc2026, self.state.pack, out_dir, client_rules=self._default_client_rules())
            self.state.answers = outputs['answers_path']
            # Attach QA artifacts to state
            self.state.qa_artifacts.update({
                'qa_summary.json': outputs['qa_summary_path'],
                'review_queue.json': outputs['review_list_path']
            })
            self.logmsg(f"✅ Deterministic answer pack created at: {self.state.answers}")
            messagebox.showinfo("Create Answer Pack", f"Created answer pack at:\n{self.state.answers}")
            self.update_button_states()
        except Exception as e:
            self.logmsg(f"❌ Error creating deterministic pack: {e}")
            messagebox.showerror("Create Answer Pack", f"Failed: {e}")

    def quick_year_update_apply(self):
        try:
            if not self.state.doc2026 or not self.state.answers:
                messagebox.showwarning("Inputs", "Load 2026 model and an answers.json first.")
                return
            with open(self.state.answers, 'r', encoding='utf-8') as f:
                data = json.load(f)
            answers = data.get('answers', data)
            output_doc = os.path.join(self.state.outdir or os.path.dirname(self.state.answers) or '.', 'CY2026_FILLED.docx')
            # Apply answers using same replacement strategy used in import flow
            from docx import Document as _Doc
            from variable_utils import iter_all_paragraphs
            import re
            doc = _Doc(self.state.doc2026)
            replacements = answers
            compiled = []
            for var_name, value in replacements.items():
                sv = str(value or '').strip()
                if sv == '':
                    continue
                esc = re.escape(var_name.strip('[]'))
                esc_flex = re.sub(r"\\\s+", r"\\s+", esc.replace("\\ ", "\\s+"))
                b = re.compile(rf"\[+{esc}\]+", re.IGNORECASE)
                bf = re.compile(rf"\[+{esc_flex}\]+", re.IGNORECASE)
                p = re.compile(rf"\b{esc}\b", re.IGNORECASE)
                pf = re.compile(rf"\b{esc_flex}\b", re.IGNORECASE)
                compiled.append((b,bf,p,pf,sv))
            for para in iter_all_paragraphs(doc):
                runs = getattr(para, 'runs', [])
                any_change=False
                for run in runs:
                    t = run.text or ""
                    new=t
                    for b,bf,p,pf,val in compiled:
                        r=b.sub(val,new)
                        if r==new: r=bf.sub(val,new)
                        if r==new: r=p.sub(val,new)
                        if r==new: r=pf.sub(val,new)
                        if r!=new: new=r
                    if new!=t:
                        run.text=new
                        any_change=True
                if not any_change and runs:
                    combined = ''.join(r.text or '' for r in runs)
                    newc=combined
                    for b,bf,p,pf,val in compiled:
                        r=b.sub(val,newc)
                        if r==newc: r=bf.sub(val,newc)
                        if r==newc: r=p.sub(val,newc)
                        if r==newc: r=pf.sub(val,newc)
                        newc=r
                    if newc!=combined:
                        para.text=newc
            doc.save(output_doc)
            self.logmsg(f"✅ Filled: {output_doc}")
            messagebox.showinfo("Quick Year Update", f"Filled: {output_doc}")
        except Exception as e:
            self.logmsg(f"❌ Quick update apply error: {e}")
            messagebox.showerror("Quick Year Update", f"Failed: {e}")

    def _open_artifact(self, filename: str):
        try:
            if not self.state.outdir:
                messagebox.showinfo("Open Report", "No output directory selected yet.")
                return
            path = os.path.join(self.state.outdir, filename)
            if not os.path.exists(path):
                messagebox.showwarning("Open Report", f"Not found: {path}")
                return
            os.startfile(path) if hasattr(os, 'startfile') else None
        except Exception as e:
            self.logmsg(f"❌ Open artifact error: {e}")
            messagebox.showerror("Open Report", f"Failed: {e}")

    def quick_year_update(self):
        """Quick year-over-year update using learned knowledge."""
        try:
            from year_update_utility import quick_year_update, generate_update_preview
            
            # Get input file
            input_path = filedialog.askopenfilename(
                title="Select Source Document",
                filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
            )
            if not input_path:
                return
            
            # Get output file
            output_path = filedialog.asksaveasfilename(
                title="Save Updated Document",
                defaultextension=".docx",
                filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
            )
            if not output_path:
                return
            
            # Get years from user
            year_dialog = tk.Toplevel(self)
            year_dialog.title("Year Update Settings")
            year_dialog.geometry("300x200")
            year_dialog.configure(bg=Config.BG_COLOR)
            year_dialog.transient(self)
            year_dialog.grab_set()
            
            tk.Label(year_dialog, text="Source Year:", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR).pack(pady=5)
            source_year_entry = tk.Entry(year_dialog)
            source_year_entry.insert(0, "2025")
            source_year_entry.pack(pady=5)
            
            tk.Label(year_dialog, text="Target Year:", bg=Config.BG_COLOR, fg=Config.TEXT_COLOR).pack(pady=5)
            target_year_entry = tk.Entry(year_dialog)
            target_year_entry.insert(0, "2026")
            target_year_entry.pack(pady=5)
            
            def perform_update():
                source_year = source_year_entry.get()
                target_year = target_year_entry.get()
                year_dialog.destroy()
                
                # Generate preview first
                self.logmsg(f"🔍 Generating update preview...")
                preview = generate_update_preview(source_year, target_year, input_path)
                
                if preview.get("error"):
                    messagebox.showerror("Error", f"Preview failed: {preview['error']}")
                    return
                
                # Show preview
                preview_stats = preview["statistics"]
                preview_text = f"""
Update Preview ({source_year} → {target_year}):

📊 Total Variables: {preview_stats['total_variables']}
🎯 Predictable: {preview_stats['predictable']}
🔄 Year-only Updates: {preview_stats['year_only_updates']}
❓ Unpredictable: {preview_stats['unpredictable']}

Auto-fill Rate: {(preview_stats['predictable'] / max(preview_stats['total_variables'], 1) * 100):.1f}%
                """
                
                if not messagebox.askyesno("Update Preview", preview_text + "\n\nProceed with update?"):
                    return
                
                # Perform update
                self.logmsg(f"🚀 Performing quick year update...")
                result = quick_year_update(source_year, target_year, input_path, output_path)
                
                if result["success"]:
                    stats = result["statistics"]
                    success_msg = f"""
✅ Quick Update Completed!

📄 Output: {output_path}
📊 Statistics:
• Total Variables: {stats['total_variables']}
• Auto-filled: {stats['auto_filled']}
• Year Transformed: {stats['year_transformed']}
• Unchanged: {stats['unchanged']}

Efficiency: {(stats['auto_filled'] / max(stats['total_variables'], 1) * 100):.1f}% auto-filled
                    """
                    messagebox.showinfo("Success", success_msg)
                    self.logmsg(f"✅ Quick update completed: {stats['auto_filled']} variables auto-filled")
                else:
                    messagebox.showerror("Error", f"Update failed: {result['error']}")
            
            tk.Button(year_dialog, text="Update", command=perform_update, 
                     bg=Config.ACCENT_COLOR, fg="white").pack(pady=10)
            
        except Exception as e:
            self.logmsg(f"❌ Error in quick year update: {e}")
            messagebox.showerror("Error", f"Quick update failed: {e}")

    def show_knowledge_stats(self):
        """Show knowledge base statistics."""
        try:
            from knowledge_base_manager import get_knowledge_manager
            
            manager = get_knowledge_manager()
            stats = manager.get_statistics()
            
            stats_window = tk.Toplevel(self)
            stats_window.title("Knowledge Base Statistics")
            stats_window.geometry("600x500")
            stats_window.configure(bg=Config.BG_COLOR)
            
            # Create text widget for stats
            stats_text = tk.Text(stats_window, bg=Config.BG_COLOR, fg=Config.TEXT_COLOR,
                               font=Config.FONT_SMALL, wrap="word")
            stats_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Format and display stats
            stats_content = f"""
📚 Knowledge Base Statistics

📊 Total Variables: {stats['total_variables']}
🔄 Year Mappings: {stats['total_year_mappings']}
🎯 Auto Values: {stats['total_auto_values']}
📝 Patterns: {stats['total_patterns']}

📈 Year Coverage:
{chr(10).join(f"• {year}: {count} variables" for year, count in stats['year_coverage'].items())}

🏆 Most Common Variables:
{chr(10).join(f"• {var['name']}: {var['occurrences']} occurrences" for var in stats['most_common_variables'][:5])}

💾 Knowledge Base Size: {len(stats['year_coverage'])} years of data
            """
            
            stats_text.insert("1.0", stats_content)
            stats_text.config(state="disabled")
            
        except Exception as e:
            self.logmsg(f"❌ Error showing knowledge stats: {e}")
            messagebox.showerror("Error", f"Failed to show knowledge stats: {e}")


if __name__ == "__main__":
    app = DashboardUI()
    app.mainloop()
