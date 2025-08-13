from typing import Dict, List, Tuple, Optional
import json
import os
import re
from docx import Document
from variable_utils import iter_all_paragraphs, iter_all_text_nodes
from validators import validate_by_type

# Narrative anchor sets and direct regex
ALT_FORMATS_REGEX = re.compile(
    r"This information is available for free in a different format[^.]*\."
    r"(?:\s+Please call Customer Service[^.]*\.)?",
    re.IGNORECASE
)

ALT_FORMATS_ANCHORS = (
    # broader phrasing coverage
    "alternate format", "alternate formats",
    "different format", "different formats",
    "availability of alternate formats",
    "large print", "braille", "audio", "cd", "compact disc",
    "call customer service", "please call customer service",
    "this information is available for free"
)

import re
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")

# Named scalar patterns
OFFERED_BY = re.compile(r"This plan,\s*(.+?),\s*is offered by\s+([^.,\n]+)", re.IGNORECASE)
MEANS_ORG = re.compile(r"it means\s+([^.\n]+)\.", re.IGNORECASE)

def _best_sentence_by_anchors(full_text: str, anchors: tuple[str, ...],
                              hints: List[str] | None = None) -> Optional[str]:
    """
    Return the sentence (or two) that contains the most anchors.
    If the next sentence contains 'call' and the first is the 'different format' line,
    include both to preserve the full disclaimer.
    """
    if not full_text:
        return None
    sentences = _SENT_SPLIT.split(full_text)
    if not sentences:
        return None

    start_idx = 0
    if hints:
        low = full_text.lower()
        for h in (h for h in hints if h):
            i = low.find(h.lower())
            if i != -1:
                pos = 0
                for si, s in enumerate(sentences):
                    pos += len(s) + 1
                    if pos >= i:
                        start_idx = max(0, si - 3)
                        break
                break

    best_i, best_score = -1, -1
    for i in range(start_idx, len(sentences)):
        s = sentences[i]
        low = s.lower()
        score = sum(1 for a in anchors if a.lower() in low)
        if score > best_score:
            best_i, best_score = i, score

    if best_i == -1 or best_score <= 0:
        return None

    chosen = sentences[best_i].strip()
    if best_i + 1 < len(sentences):
        nxt = sentences[best_i + 1].strip()
        if "call" in nxt.lower() or "customer service" in nxt.lower():
            chosen = (chosen + " " + nxt).strip()
    return chosen

def _looks_imperative_instruction(text: str) -> bool:
    words = (text or "").strip().split()
    if len(words) < 8:
        return False
    low = text.lower()
    return low.startswith("plans must insert") or low.startswith("insert language") or low.startswith("insert ")

def _narrative_trigger(name: str, full_ctx: str, vtype: str = "") -> Optional[str]:
    """Return a trigger key when this variable should use a narrative extractor.
    Strictly anchor-based to avoid false positives (e.g., DBA instructions)."""
    blob = f"{name} {full_ctx}".lower()
    # Guard: avoid org/DBA/MAO variables
    if any(bad in blob for bad in ("dba", "mao", "organization")):
        return None
    anchors = (
        "alternate format", "alternate formats", "different format", "different formats",
        "availability of alternate formats", "large print", "braille", "audio", "cd", "compact disc"
    )
    if any(k in blob for k in anchors):
        return "alt_formats"
    return None

def _clean_sentence(s: str) -> str:
    s2 = re.sub(r"\s+", " ", (s or "").strip())
    if s2 and not s2.endswith(('.', '!', '?')):
        s2 += '.'
    return s2

def extract_narrative_from_2025(name: str, full_ctx: str, hints: List[str],
                                doc2025_text: str, vtype: str = "") -> Tuple[Optional[str], Optional[str]]:
    """Return (value, method) if narrative extraction succeeds, else (None, None)."""
    trig = _narrative_trigger(name, full_ctx, vtype)
    if trig != "alt_formats":
        return None, None

    # Pass 1: direct boilerplate regex
    m = ALT_FORMATS_REGEX.search(doc2025_text)
    if m:
        return _clean_sentence(m.group(0)), "regex"

    # Pass 2: best sentence by anchors (global) - compute anchors purely from DOCX text
    sent = _best_sentence_by_anchors(doc2025_text, ALT_FORMATS_ANCHORS, hints=None)
    if sent and any(a.lower() in sent.lower() for a in ALT_FORMATS_ANCHORS) and '[' not in sent:
        return _clean_sentence(sent), "anchors"

    # Pass 3: search around Customer Service/contact zones (±600 chars)
    blob_low = doc2025_text.lower()
    for kw in ("customer service", "contact", "call"):
        idx = blob_low.find(kw)
        if idx != -1:
            s = max(0, idx - 600); e = min(len(doc2025_text), idx + 600)
            seg = doc2025_text[s:e]
            m2 = ALT_FORMATS_REGEX.search(seg)
            if m2:
                return _clean_sentence(m2.group(0)), "proximity_regex"
            sent2 = _best_sentence_by_anchors(seg, ALT_FORMATS_ANCHORS)
            if sent2 and '[' not in sent2:
                return _clean_sentence(sent2), "proximity_anchors"

    return None, None

def _doc_text(doc: Document) -> str:
    """Return a single text blob of the DOCX including paragraphs and shape/text-box nodes.

    This is used by deterministic extractors (named scalars, narrative disclaimers) and for
    quick tests. Order is paragraphs in document order followed by any extra text nodes.
    """
    try:
        paras = [p.text for p in iter_all_paragraphs(doc) if p.text and p.text.strip()]
    except Exception:
        paras = []
    try:
        extras = []
        for t in iter_all_text_nodes(doc):
            if t.text and t.text.strip():
                extras.append(t.text)
    except Exception:
        extras = []
    return "\n".join(paras + extras)

def extract_named_scalar(name: str, ctx: str, doc2025_text: str) -> Optional[str]:
    """High-precision named scalar extraction (MAO/org and Plan name)."""
    lname = (name or "").lower()
    text = doc2025_text or ""

    # MAO / Organization name
    if ("mao" in lname) or ("organization" in lname) or ("org" in lname):
        m = OFFERED_BY.search(text)
        if m:
            org = m.group(2).strip().strip(",.; ")
            return org
        m = MEANS_ORG.search(text)
        if m:
            return m.group(1).strip().strip(",.; ")
        return None

    # Plan name
    if "plan name" in lname or "2026 plan name" in lname:
        m = OFFERED_BY.search(text)
        if m:
            plan = m.group(1).strip().strip(",.; ")
            return plan
        return None

    return None


def load_context_pack(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_answers(prior_final_path: str, context_pack: Dict, client_rules: Dict = None) -> Tuple[Dict[str, str], List[Dict], Dict]:
    """High-precision extractor per playbook.

    Implements:
    - Constants and client policy rules
    - MBC table-exact and raw-match fallback
    - Type-based schema validation
    - Review list + QA summary
    """
    client_rules = client_rules or {}
    answers: Dict[str, str] = {}
    review: List[Dict] = []

    # Load prior final
    try:
        prior_doc = Document(prior_final_path)
        prior_paragraphs = [p.text for p in iter_all_paragraphs(prior_doc) if p.text and p.text.strip()]
        # Also include text from shapes/text boxes
        try:
            prior_extra_texts = []
            for t in iter_all_text_nodes(prior_doc):
                if t.text and t.text.strip():
                    prior_extra_texts.append(t.text)
            # Merge while keeping order (paragraphs first)
            prior_paragraphs.extend(prior_extra_texts)
        except Exception:
            pass
    except Exception:
        prior_doc = None
        prior_paragraphs = []

    # Rules and helpers
    constants_by_name: Dict[str, str] = client_rules.get('constants', {})
    constants_by_type: Dict[str, str] = client_rules.get('constants_by_type', {})
    url_preferences: List[str] = client_rules.get('url_preferences', [])
    enforce_dba_empty: bool = client_rules.get('enforce_dba_empty', True)
    employer_billed_premium_blank: bool = client_rules.get('employer_billed_premium_blank', True)

    def _norm(s: str) -> str:
        t = s.strip().lower()
        t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
        return re.sub(r"\s+", " ", t).strip()

    def _pick_preferred_url(candidates: List[str]) -> Optional[str]:
        if not candidates:
            return None
        # Prefer URLs containing any preferred substrings
        for pref in url_preferences:
            for u in candidates:
                if pref.lower() in u.lower():
                    return u
        # Otherwise first
        return candidates[0]

    # --- MBC helpers ---
    def _normalize_service_label(text: str) -> str:
        text = re.sub(r"\[[^\]]*\]", " ", text)  # remove placeholders in brackets
        text = re.split(r"coverage|covered", text, flags=re.IGNORECASE)[0]
        text = ' '.join(text.split())
        return _norm(' '.join(text.split()[:16]))  # first ~16 words normalized

    def _slugify(text: str) -> str:
        t = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
        t = re.sub(r"_+", "_", t).strip('_')
        return t[:60]

    def _extract_mbc_rows(doc: Document) -> Dict[str, str]:
        service_to_pay: Dict[str, str] = {}
        for tbl in doc.tables:
            try:
                # Heuristic: 2+ columns and at least 3 rows
                if not tbl.rows or len(tbl.rows) < 3:
                    continue
                num_cols = max(len(r.cells) for r in tbl.rows)
                if num_cols < 2:
                    continue
                # Attempt to find header row hinting "What you pay"
                header = ' '.join(c.text.strip() for c in tbl.rows[0].cells if c.text).lower()
                looks_like_mbc = ('what you pay' in header) or ('service' in header)
                # If not obvious header, still consider as candidate and try to parse
                if not looks_like_mbc and num_cols >= 2:
                    looks_like_mbc = True
                if not looks_like_mbc:
                    continue
                for r in tbl.rows[1:]:
                    cells = r.cells
                    if len(cells) < 2:
                        continue
                    left = (cells[0].text or '').strip()
                    right = (cells[1].text or '').strip()
                    if not left or not right:
                        continue
                    norm_left = _normalize_service_label(left)
                    if not norm_left:
                        continue
                    # Keep first occurrence (assume primary)
                    service_to_pay.setdefault(norm_left, right)
            except Exception:
                continue
        return service_to_pay

    mbc_rows: Dict[str, str] = _extract_mbc_rows(prior_doc) if prior_doc else {}

    # Jaccard similarity for left-label matching (Pass 1 exact table)
    def _tokenize(text: str) -> set:
        return set((text or '').lower().split())

    def _jaccard(a: str, b: str) -> float:
        sa = _tokenize(a); sb = _tokenize(b)
        if not sa or not sb:
            return 0.0
        inter = sa & sb
        union = sa | sb
        return len(inter) / max(1, len(union))

    def _raw_match_financial_for_service(service_hint: str) -> Optional[str]:
        if not prior_paragraphs:
            return None
        norm_hint = _norm(service_hint)
        best: Optional[str] = None
        # Scan paragraphs near mentions of the service
        for para in prior_paragraphs:
            if norm_hint and norm_hint.split(' ')[0] not in _norm(para):
                continue
            if re.search(r"\b(copay|coinsurance|covered at 100%|no coinsurance|no copayment|no deductible)\b", para, re.I):
                best = para.strip()
                # Prefer the first strong match
                break
        return best

    # Narrative helpers
    def _extract_first(pattern: str) -> Optional[str]:
        for para in prior_paragraphs:
            m = re.search(pattern, para, re.I)
            if m:
                return m.group(0)
        return None

    def _extract_urls() -> List[str]:
        urls: List[str] = []
        for para in prior_paragraphs:
            for m in re.finditer(r"(?i)(https?://|www\.)\S+", para):
                urls.append(m.group(0))
        # De-dup preserve order
        seen = set()
        uniq = []
        for u in urls:
            if u not in seen:
                uniq.append(u)
                seen.add(u)
        return uniq

    # Process items
    items = context_pack.get('items', [])
    mbc_table_exact = 0
    mbc_raw_match = 0
    audit_logs: List[Dict] = []

    for it in items:
        name = it.get('name', '')
        key = it.get('canonical_key') or name
        vtype = (it.get('type', '') or '').lower()
        vpx_kind = (it.get('vpx_kind', '') or '').lower()
        before_ctx = it.get('before_context', '') or ''
        after_ctx = it.get('after_context', '') or ''
        full_ctx = it.get('full_context', '') or ''
        mbc_effective = it.get('mbc_effective_label') or before_ctx or ''
        mbc_generic = bool(it.get('mbc_generic_left'))

        # Apply name-based constants first (exact)
        const_val = constants_by_name.get(name) or constants_by_name.get(key)
        if const_val:
            ok, reason = validate_by_type(vtype, const_val)
            if ok:
                answers[key] = const_val
                continue
            else:
                review.append({'name': key, 'reason': 'schema_error', 'suggested_value': const_val, 'source_hint': 'constant', 'confidence': 1.0})
                continue

        # MBC variables
        if key.startswith('mbc_') and key.endswith('_cost_share'):
            # Resolve effective service label
            service_hint = mbc_effective or before_ctx or full_ctx
            norm_hint = _normalize_service_label(service_hint)
            # Pass 1: Jaccard against 2025 MBC left labels
            best_key = None
            best_score = 0.0
            for left_norm, pay_text in mbc_rows.items():
                score = _jaccard(norm_hint, left_norm)
                if score > best_score:
                    best_score = score
                    best_key = left_norm
            # Thresholds
            thresh = 0.70 if not mbc_generic else 0.58
            if best_key is not None and best_score >= thresh:
                value = mbc_rows.get(best_key)
                if value:
                    ok, reason = validate_by_type('financial', value)
                    if ok:
                        answers[key] = value
                        mbc_table_exact += 1
                        audit_logs.append({'var': key, 'pass': 'mbc.table_exact', 'validator': 'ok', 'score': round(best_score, 3), 'left': best_key, 'snippet': (value or '')[:120]})
                        continue
                    else:
                        review.append({'name': key, 'reason': 'schema_error', 'suggested_value': value, 'source_hint': 'table_exact', 'confidence': 1.0})
                        audit_logs.append({'var': key, 'pass': 'mbc.table_exact', 'validator': reason or 'invalid', 'score': round(best_score, 3)})
                        continue
            # Pass 2: Raw-text fallback (cost sentence)
            raw = _raw_match_financial_for_service(service_hint=service_hint or '')
            if raw:
                cand = raw
                ok, reason = validate_by_type('financial', cand)
                if ok:
                    answers[key] = cand
                    mbc_raw_match += 1
                    audit_logs.append({'var': key, 'pass': 'mbc.raw_match', 'validator': 'ok', 'snippet': (cand or '')[:120]})
                    continue
                else:
                    review.append({'name': key, 'reason': 'schema_error', 'suggested_value': cand, 'source_hint': 'raw_match', 'confidence': 0.9})
                    audit_logs.append({'var': key, 'pass': 'mbc.raw_match', 'validator': reason or 'invalid'})
                    continue
            # No match → review
            review.append({'name': key, 'reason': 'missing', 'suggested_value': '', 'source_hint': service_hint or 'unknown', 'confidence': 0.0})
            continue

        # Non-MBC variables in the allowed set (insert*/Insert*)
        if not (name.lower().startswith('insert') or key.lower().startswith('mbc_')):
            # Skip non-required per playbook
            continue

        # Narrative disclaimers first: e.g., alternate formats (high-context VPX)
        hints = [full_ctx, before_ctx, after_ctx]
        doc2025_text = "\n".join(prior_paragraphs)
        nval, nmethod = extract_narrative_from_2025(name, full_ctx, hints, doc2025_text, vtype)
        if nval and vpx_kind == 'narrative_disclaimer':
            answers[key] = nval
            audit_logs.append({'var': key, 'pass': f'narrative.alt_formats', 'method': nmethod or 'unknown', 'validator': 'ok', 'snippet': (nval or '')[:120]})
            continue

        # Named scalars (MAO/org, Plan name) before generic scalar heuristics
        nscalar = extract_named_scalar(name, full_ctx, doc2025_text)
        if nscalar:
            answers[key] = nscalar
            audit_logs.append({'var': key, 'pass': 'named.scalar', 'validator': 'ok', 'snippet': (nscalar or '')[:120]})
            continue

        # Type-based constants
        t_const = constants_by_type.get(vtype)
        if t_const:
            ok, reason = validate_by_type(vtype, t_const)
            if ok:
                answers[name] = t_const
                continue
            else:
                review.append({'name': name, 'reason': 'schema_error', 'suggested_value': t_const, 'source_hint': 'constant(type)', 'confidence': 1.0})
                continue

        # Apply client policy special cases
        lname = name.lower()
        if enforce_dba_empty and 'dba' in lname:
            answers[name] = ''
            continue
        if employer_billed_premium_blank and 'premium' in lname and vtype in ('financial', 'general'):
            # Leave blank unless we positively find a $-amount
            val = _extract_first(r"\$\d[\d,]*(?:\.\d{2})?")
            if val:
                answers[name] = val
            else:
                answers[name] = ''
            continue

        # Heuristic extraction by type from narrative (direct insertion & scalars)
        extracted: Optional[str] = None
        if vpx_kind == 'direct_insertion_hours' or vtype == 'business_hours':
            # Tight extractor: only return hours/day range, not entire sentence
            # Search near hour anchors
            import re as _rh
            window = full_ctx or before_ctx
            seg = window if window else ' '.join(prior_paragraphs[:5])
            # common forms: 8 a.m. to 5:30 p.m., Monday through Friday
            # Use a simplified dash set to avoid encoding issues in some environments
            HOURS_RE = _rh.compile(r"([0-9]{1,2}(?::[0-5]\d)?\s*(?:a\.m\.|p\.m\.)\s*(?:to|-)\s*[0-9]{1,2}(?::[0-5]\d)?\s*(?:a\.m\.|p\.m\.)?)", _rh.IGNORECASE)
            mhrs = HOURS_RE.search(seg)
            if mhrs:
                extracted = mhrs.group(1).strip()
        elif vtype == 'phone_number' or 'customer service' in lname:
            extracted = _extract_first(r"1-\d{3}-\d{3}-\d{4}")
        elif vtype == 'tty_number' or 'tty' in lname:
            # Prefer literal 711
            extracted = '711'
        elif vtype == 'url' or 'url' in lname or 'website' in lname or 'directory' in lname:
            urls = _extract_urls()
            extracted = _pick_preferred_url(urls)
        elif vtype == 'address' or 'address' in lname:
            # Use presence of state + zip
            for para in prior_paragraphs:
                if re.search(r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b", para):
                    extracted = para.strip()
                    break
        elif vtype == 'business_hours' or 'hours' in lname:
            for para in prior_paragraphs:
                if ('a.m.' in para.lower()) or ('p.m.' in para.lower()):
                    extracted = para.strip()
                    break
        elif vtype == 'organization' and ('mao' in lname or 'organization' in lname):
            # Prefer client org constant if provided
            extracted = constants_by_type.get('organization') or constants_by_name.get(name)
        elif vtype == 'plan_name' or 'plan name' in lname:
            extracted = constants_by_type.get('plan_name') or constants_by_name.get(name)
        elif vtype == 'financial' or any(k in lname for k in ['copay', 'coinsurance', 'deductible']):
            # Try to find a line with financial phrase nearby
            # Use before/after context keywords if available
            key = before_ctx.strip() or full_ctx.strip()
            extracted = _raw_match_financial_for_service(key or name)

        # Special-case: SHIP information blocks
        if not extracted and ('ship' in lname or 'state health insurance assistance program' in full_ctx.lower()):
            for para in prior_paragraphs:
                if re.search(r"state health insurance assistance program|\bSHIP\b", para, re.I):
                    # Prefer paragraph containing SHIP; include full paragraph
                    extracted = para.strip()
                    break

        if extracted:
            ok, reason = validate_by_type(vtype, extracted)
            if ok:
                answers[key] = extracted
                audit_logs.append({'var': key, 'pass': 'scalar.heuristic', 'type': vtype, 'validator': 'ok', 'snippet': (extracted or '')[:120]})
                continue
            else:
                review.append({'name': key, 'reason': 'schema_error', 'suggested_value': extracted, 'source_hint': 'narrative', 'confidence': 0.7})
                audit_logs.append({'var': key, 'pass': 'scalar.heuristic', 'type': vtype, 'validator': reason or 'invalid', 'snippet': (extracted or '')[:120]})
                continue

        # Not found
        review.append({'name': key, 'reason': 'missing', 'suggested_value': '', 'source_hint': 'unknown', 'confidence': 0.0})
        audit_logs.append({'var': key, 'pass': 'missing', 'validator': 'n/a'})

    qa = {
        'table_exact': mbc_table_exact,
        'raw_match': mbc_raw_match,
        'needs_review': len(review)
    }
    # Attach audit logs to QA for debugging (optional artifact)
    qa['audit'] = audit_logs
    return answers, review, qa


def run_playbook(prior_final_path: str, current_model_path: str, context_pack_path: str, out_dir: str, client_rules: Dict = None) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    ctx = load_context_pack(context_pack_path)
    answers, review, qa = extract_answers(prior_final_path, ctx, client_rules)

    outputs = {
        'answers_path': os.path.join(out_dir, 'answers.json'),
        'review_list_path': os.path.join(out_dir, 'review_list.json'),
        'qa_summary_path': os.path.join(out_dir, 'qa_summary.json')
    }
    with open(outputs['answers_path'], 'w', encoding='utf-8') as f:
        json.dump({'answers': answers}, f, indent=2)
    with open(outputs['review_list_path'], 'w', encoding='utf-8') as f:
        json.dump(review, f, indent=2)
    with open(outputs['qa_summary_path'], 'w', encoding='utf-8') as f:
        json.dump(qa, f, indent=2)
    return outputs


