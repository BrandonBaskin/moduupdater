# document_parser.py

from typing import List, Dict, Optional
import re
from config import Config
from logging_config import logger
try:
    from docx import Document
except ImportError:
    Document = None
from variable_utils import extract_all_variables

# Document Parsing
class DocumentParser:
    """Parses DOCX files to extract nested logic blocks."""
    def __init__(self):
        if not Document:
            raise ImportError("python-docx is required. Run: pip install python-docx")

    @staticmethod
    def _is_option(text: str) -> bool:
        return " or " in text.lower() or "and/or" in text.lower()

    @staticmethod
    def _is_conditional(text: str) -> bool:
        return "insert if applicable" in text.lower() or "if applicable" in text.lower()

    @staticmethod
    def _is_optional(text: str) -> bool:
        return "optional:" in text.lower()

    @staticmethod
    def _is_delete(text: str) -> bool:
        return "delete" in text.lower()

    @staticmethod
    def _is_variable(text: str) -> bool:
        # More precise variable detection
        text_lower = text.lower()
        # Check for insert patterns
        if "insert" in text_lower:
            return True
        # Check for replace patterns  
        if "replace" in text_lower:
            return True
        # Check for specific variable patterns like [variable name]
        if re.search(r'\[.*\]', text):
            return True
        return False

    def _get_block_type(self, text: str) -> str:
        """Determine block type based on content."""
        if self._is_option(text):
            return "option"
        if self._is_conditional(text):
            return "conditional"
        if self._is_optional(text):
            return "optional"
        if self._is_delete(text):
            return "delete"
        return "variable"

    def _extract_options(self, text: str) -> List[str]:
        """Extract options from text containing 'or' or 'and/or'."""
        if self._is_option(text):
            splits = re.split(r'\bOR\b|\bAND/OR\b', text, flags=re.IGNORECASE)
            options = [re.sub(r'^.*?:', '', s.strip(" :[]")).strip() for s in splits]
            return [opt for opt in options if opt]
        return []

    def _parse_nested_brackets(self, text: str, parent_id: Optional[int] = None,
                             para_idx: Optional[int] = None, block_id_gen: List[int] = None) -> List[Dict]:
        """Parse nested bracket structures in text, creating individual blocks for each variable."""
        if block_id_gen is None:
            block_id_gen = [1]
        blocks = []
        
        # First, find all variables in the text
        all_variables = list(extract_all_variables(text))
        
        if not all_variables:
            return blocks
            
        # Create individual blocks for each variable
        for var_name, var_start, var_end, full_match in all_variables:
            inner_text = var_name.strip()
            block_type = self._get_block_type(inner_text)
            block_id = block_id_gen[0]
            block_id_gen[0] += 1
            
            # Capture focused context around this specific variable
            context_start = max(0, var_start - 80)  # 80 characters before
            context_end = min(len(text), var_end + 80)  # 80 characters after
            full_context = text[context_start:context_end].strip()
            
            # Clean up context - remove extra whitespace but preserve structure
            full_context = ' '.join(full_context.split())
            
            # Extract before and after context for better AI processing
            before_context = text[context_start:var_start].strip()
            after_context = text[var_end:context_end].strip()
            
            block = {
                'id': block_id,
                'type': block_type,
                'text': full_context,  # Full context for display
                'inner_text': inner_text,  # The variable name
                'variable_text': full_match,  # The [variable] with brackets
                'before_context': before_context,  # Text before the variable
                'after_context': after_context,  # Text after the variable
                'parent_id': parent_id,
                'para_idx': para_idx,
                'options': self._extract_options(inner_text) if block_type == "option" else None,
                'children': [],
                'variables': [var_name]  # This block has exactly one variable
            }
            
            # Only process nested if it's not a simple variable
            if block_type != "variable":
                block['children'] = self._parse_nested_brackets(
                    inner_text, block_id, para_idx, block_id_gen)
            
            blocks.append(block)
        
        return blocks

    def parse(self, file_path: str) -> List[Dict]:
        """Parse a DOCX file into logic blocks."""
        try:
            doc = Document(file_path)
            all_blocks = []
            block_id_gen = [1]
            para_idx = 0
            from variable_utils import iter_paragraphs  # late import to avoid circular
            for para in iter_paragraphs(doc):
                if para.text.strip():
                    all_blocks.extend(
                        self._parse_nested_brackets(para.text, para_idx=para_idx, block_id_gen=block_id_gen)
                    )
                para_idx += 1
            logger.info(f"Parsed {len(all_blocks)} blocks from {file_path}")
            return all_blocks
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            raise

    @staticmethod
    def flatten_tree(blocks: List[Dict]) -> List[Dict]:
        """Flatten a block tree into a list."""
        out = []
        def traverse(block: Dict):
            out.append(block)
            for child in block.get('children', []):
                traverse(child)
        for block in blocks:
            traverse(block)
        return out


# --- Context Pack Builder (deterministic) ---
def parse_unique_items(docx_path: str) -> List[Dict]:
    """Build context items from the 2026 model.

    Each item:
      - name: raw variable text inside brackets
      - type: heuristically classified
      - canonical_key: for MBC rows use mbc_<slug>_cost_share, otherwise name
      - full_context/before_context/after_context
      - in_table: bool
      - occurrences: list of occurrence dicts with placeholder text
      - para_index: approximate paragraph index in traversal
    """
    from docx import Document as _Doc
    from variable_utils import iter_all_paragraphs, iter_all_text_nodes

    def _slugify(text: str) -> str:
        t = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
        t = re.sub(r"_+", "_", t).strip('_')
        return t[:120]

    def _classify_type(name: str, ctx: str) -> str:
        blob = f"{name} {ctx}".lower()
        if 'phone' in blob or 'customer service' in blob:
            return 'phone_number'
        if 'tty' in blob:
            return 'tty_number'
        if 'url' in blob or 'website' in blob or 'directory' in blob or 'www.' in blob:
            return 'url'
        if 'address' in blob:
            return 'address'
        if ('hours' in blob and 'operation' in blob) or ('hours' in blob and any(w in blob for w in ['mon', 'monday', 'fri', 'friday'])):
            return 'business_hours'
        if 'copay' in blob or 'coinsurance' in blob or 'deductible' in blob or 'what you pay' in blob:
            return 'financial'
        return 'general'

    def _classify_vpx_kind(name: str, ctx: str, vtype: str, in_table: bool) -> str:
        blob = f"{name} {ctx}".lower()
        if in_table:
            return 'mbc_cost_share'
        # narrative alt-formats trigger (avoid org/DBA/MAO)
        if not any(b in blob for b in ('dba','mao','organization')) and any(t in blob for t in (
            'alternate format','alternate formats','different format','different formats',
            'availability of alternate formats','large print','braille','audio','cd','compact disc'
        )):
            return 'narrative_disclaimer'
        if vtype == 'business_hours':
            return 'direct_insertion_hours'
        if vtype in ('plan_name','organization'):
            return f'scalar_named_{vtype}'
        if vtype in ('phone_number','tty_number','url','address','financial'):
            return f'scalar_generic_{vtype}'
        return 'general'

    doc = _Doc(docx_path)
    items: List[Dict] = []
    seen_keys = set()
    para_idx = 0

    # 1) Paragraph-like nodes (body, headers, footers)
    for para in iter_all_paragraphs(doc):
        text = para.text or ''
        if not text:
            para_idx += 1
            continue
        for var_name, start, end, full_match in extract_all_variables(text):
            inner = var_name.strip()
            before = text[max(0, start-120):start].strip()
            after = text[end:min(len(text), end+120)].strip()
            # Build full_context with a marker at the variable position
            ctx_pre = text[max(0, start-200):start]
            ctx_post = text[end:min(len(text), end+200)]
            ctx = (ctx_pre + " 📍 " + ctx_post).strip()
            vtype = _classify_type(inner, ctx)
            key = inner
            in_table = False
            occ = [{ 'placeholder': full_match }]
            canonical = key
            entry = {
                'name': inner,
                'type': vtype,
                'canonical_key': canonical,
                'full_context': ctx,
                'before_context': before,
                'after_context': after,
                'in_table': in_table,
                'vpx_kind': _classify_vpx_kind(inner, ctx, vtype, in_table),
                'occurrences': occ,
                'para_index': para_idx,
            }
            # Deduplicate by canonical_key+first occurrence placeholder
            sig = (entry['canonical_key'], entry['occurrences'][0]['placeholder'])
            if sig not in seen_keys:
                items.append(entry)
                seen_keys.add(sig)
        para_idx += 1

    # 1b) Shapes/Text boxes: scan all text nodes (w:t) and capture bracket variables.
    # Note: iter_all_text_nodes includes body + headers/footers and shapes/text boxes.
    try:
        for t in iter_all_text_nodes(doc):
            try:
                ttext = t.text or ''
            except Exception:
                ttext = ''
            if not ttext or ('[' not in ttext or ']' not in ttext):
                continue
            for var_name, start, end, full_match in extract_all_variables(ttext):
                inner = var_name.strip()
                # Context window around the occurrence where possible
                before = ttext[max(0, start-120):start].strip()
                after = ttext[end:min(len(ttext), end+120)].strip()
                ctx_pre = ttext[max(0, start-200):start]
                ctx_post = ttext[end:min(len(ttext), end+200)]
                ctx = (ctx_pre + " 📍 " + ctx_post).strip()
                vtype = _classify_type(inner, ctx)
                in_table = False
                canonical = inner
                entry = {
                    'name': inner,
                    'type': vtype,
                    'canonical_key': canonical,
                    'full_context': ctx,
                    'before_context': before,
                    'after_context': after,
                    'in_table': in_table,
                    'vpx_kind': _classify_vpx_kind(inner, ctx, vtype, in_table),
                    'occurrences': [{ 'placeholder': full_match }],
                    # Shapes don't map to a document paragraph index reliably; reuse last para_idx
                    'para_index': para_idx,
                }
                sig = (entry['canonical_key'], entry['occurrences'][0]['placeholder'])
                if sig not in seen_keys:
                    items.append(entry)
                    seen_keys.add(sig)
    except Exception:
        # Best-effort; shapes are optional and may not be accessible in some docs
        pass

    # 2) Tables: detect MBC rows and create canonical keys with effective label resolution
    def _is_generic_label(label: str) -> bool:
        words = (label or '').strip().split()
        low = (label or '').lower()
        if len(words) <= 2:
            return True
        generics = ['insert', 'list', 'as appropriate', 'as applicable', 'cost share']
        return any(g in low for g in generics)

    def _effective_label(current: str, last_meaningful: str) -> tuple[str, bool]:
        if _is_generic_label(current):
            return (last_meaningful or current or ''), True
        return (current or '', False)

    table_index = 0
    for tbl in doc.tables:
        try:
            if not tbl.rows or max(len(r.cells) for r in tbl.rows) < 2:
                continue
            header_text = ' '.join(c.text or '' for c in tbl.rows[0].cells)
            low = header_text.lower()
            looks_mbc = ('what you pay' in low) and any(k in low for k in ['service', 'services', 'benefit', 'benefits', 'coverage'])
            last_meaningful_label = ''
            # Iterate rows (skip header)
            for ri, r in enumerate(tbl.rows[1:], start=1):
                cells = r.cells
                if len(cells) < 2:
                    continue
                left = (cells[0].text or '').strip()
                right = (cells[1].text or '').strip()
                if '[' not in right or ']' not in right:
                    continue
                # extract first placeholder from right
                m = re.search(r"\[([^\]]+)\]", right)
                if not m:
                    continue
                inner = m.group(1).strip()
                before = left
                after = ''
                # Insert a marker to indicate where the bracket occurs in context
                ctx = f"Service: {left} | What you pay: 📍 {right}".strip()
                vtype = 'financial'
                in_table = True
                # Determine effective label (inherit last meaningful if current is generic)
                eff_label, inherited = _effective_label(left, last_meaningful_label)
                if not _is_generic_label(left):
                    last_meaningful_label = left
                # canonical key for mbc only if the table looks like MBC
                canonical = (f"mbc_{_slugify(eff_label)}_cost_share" if looks_mbc and eff_label else inner or '')
                entry = {
                    'name': inner,
                    'type': vtype,
                    'canonical_key': canonical,
                    'full_context': ctx,
                    'before_context': before,
                    'after_context': after,
                    'in_table': in_table,
                    'vpx_kind': ('mbc_cost_share' if looks_mbc else _classify_vpx_kind(inner, ctx, vtype, in_table)),
                    'occurrences': [{ 'placeholder': f"[{inner}]" }],
                    'para_index': para_idx,
                    # VPX assist fields for deterministic playbook
                    'mbc_effective_label': eff_label,
                    'mbc_generic_left': inherited,
                    'mbc_table_header': header_text,
                    'table_index': table_index,
                    'row_index': ri,
                }
                sig = (entry['canonical_key'], entry['occurrences'][0]['placeholder'])
                if sig not in seen_keys:
                    items.append(entry)
                    seen_keys.add(sig)
            table_index += 1
        except Exception:
            continue

    return items