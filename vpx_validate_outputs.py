#!/usr/bin/env python3
"""
VPX Output Validator

Checks that generated artifacts conform to the VPX spec:
 - Context pack item schema completeness
 - MBC canonical key shape and dedupe by effective label
 - Narrative disclaimer extractability from 2025 final
 - Scalar validations by type (phone, tty, url, hours, financial)
 - Client rules (DBA empty, premium without $ empty)
 - QA summary keys present

Usage:
  python vpx_validate_outputs.py [<pack_json> <answers_json> <qa_json> <doc2025>]

Defaults:
  pack_json:       core_files/out/wizard_context_pack.json
  answers_json:    core_files/out/answers.json
  qa_json:         core_files/out/qa_summary.json
  doc2025:         PATH_TO_2025_FINAL.docx
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Dict, List, Tuple

from validators import (
    is_phone_number,
    is_tty_number,
    is_url,
    is_business_hours,
    is_financial,
)
from docx import Document
from variable_utils import iter_all_paragraphs, iter_all_text_nodes


ALT_FORMATS_REGEX = re.compile(
    r"This information is available for free in a different format[^.]*\.(?:\s+Please call Customer Service[^.]*\.)?",
    re.IGNORECASE,
)


def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def doc_to_text(doc: Document) -> str:
    paras = [p.text for p in iter_all_paragraphs(doc) if p.text and p.text.strip()]
    extras: List[str] = []
    for t in iter_all_text_nodes(doc):
        try:
            if t.text and t.text.strip():
                extras.append(t.text)
        except Exception:
            pass
    return "\n".join(paras + extras)


def validate_context_pack_schema(pack: Dict) -> Tuple[int, int, List[str]]:
    required = {
        "name",
        "type",
        "vpx_kind",
        "canonical_key",
        "full_context",
        "before_context",
        "after_context",
        "in_table",
        "occurrences",
        "para_index",
    }
    items = pack.get("items", [])
    total = len(items)
    missing = 0
    samples: List[str] = []
    for it in items:
        keys = set(it.keys())
        if not required.issubset(keys):
            missing += 1
            if len(samples) < 5:
                absent = ",".join(sorted(required - keys))
                samples.append(f"{it.get('name','?')}: missing [{absent}]")
    return total, missing, samples


def validate_mbc_keys(pack: Dict) -> Tuple[int, int, List[str]]:
    items = pack.get("items", [])
    mbc_items = [it for it in items if str(it.get("vpx_kind","")) == "mbc_cost_share" or (it.get("in_table") and str(it.get("canonical_key","" )).startswith("mbc_"))]
    total = len(mbc_items)
    issues = 0
    samples: List[str] = []
    by_key: Dict[str, set] = {}
    for it in mbc_items:
        key = str(it.get("canonical_key", ""))
        if not (key.startswith("mbc_") and key.endswith("_cost_share")):
            issues += 1
            if len(samples) < 5:
                samples.append(f"bad key: {key}")
        eff = it.get("mbc_effective_label") or (it.get("before_context") or "").strip()
        by_key.setdefault(key, set()).add(eff)
    # duplicates for same canonical must correspond to identical effective label
    for k, labels in by_key.items():
        if len(labels) > 1:
            issues += 1
            if len(samples) < 5:
                samples.append(f"duplicate label mismatch for {k}: {sorted(labels)}")
    return total, issues, samples


def check_narrative_alt_formats(pack: Dict, doc2025_path: str) -> Tuple[bool, str]:
    items = pack.get("items", [])
    cand = next((it for it in items if str(it.get("vpx_kind","")) == "narrative_disclaimer"), None)
    if not cand:
        return False, "no narrative_disclaimer item in pack"
    try:
        doc = Document(doc2025_path)
    except Exception as e:
        return False, f"open 2025 failed: {e}"
    text = doc_to_text(doc)
    m = ALT_FORMATS_REGEX.search(text)
    if not m:
        return False, "regex not found"
    sent = m.group(0).strip()
    ok = sent.lower().startswith("this information is available for free in a different format")
    return ok, (sent if ok else "regex mismatch")


def scalars_validation(pack: Dict, answers: Dict) -> Dict[str, List[str]]:
    items = pack.get("items", [])
    ans = answers.get("answers", answers) if isinstance(answers, dict) else {}
    problems: Dict[str, List[str]] = {"phone":[],"tty":[],"url":[],"hours":[],"financial":[]}
    for it in items:
        key = it.get("canonical_key") or it.get("name")
        vtype = (it.get("type") or "").lower()
        if key not in ans:
            continue
        val = str(ans.get(key) or "")
        if not val:
            continue
        if vtype == "phone_number" and not is_phone_number(val):
            problems["phone"].append(key)
        if vtype == "tty_number" and not is_tty_number(val):
            problems["tty"].append(key)
        if vtype == "url" and not is_url(val):
            problems["url"].append(key)
        if vtype == "business_hours" and not is_business_hours(val):
            problems["hours"].append(key)
        if vtype == "financial" and not is_financial(val):
            problems["financial"].append(key)
    return problems


def client_rules_check(answers: Dict) -> Dict[str, List[str]]:
    ans = answers.get("answers", answers) if isinstance(answers, dict) else {}
    dba_bad: List[str] = []
    prem_bad: List[str] = []
    for k, v in ans.items():
        sk = str(k).lower()
        sv = str(v or "")
        if "dba" in sk and sv.strip() != "":
            dba_bad.append(k)
        if "premium" in sk and ("$" not in sv or not re.search(r"\$\d", sv)) and sv.strip() != "":
            prem_bad.append(k)
    return {"dba_non_empty": dba_bad, "premium_should_be_empty": prem_bad}


def qa_summary_check(qa: Dict) -> Tuple[bool, List[str]]:
    required = {"table_exact","raw_match","needs_review"}
    missing = sorted(list(required - set(qa.keys())))
    return (len(missing) == 0), missing


def main():
    root = os.getcwd()
    pack_path = os.path.join(root, 'core_files', 'out', 'wizard_context_pack.json')
    answers_path = os.path.join(root, 'core_files', 'out', 'answers.json')
    qa_path = os.path.join(root, 'core_files', 'out', 'qa_summary.json')
    doc2025 = os.path.join(root, 'PATH_TO_2025_FINAL.docx')

    if len(sys.argv) >= 5:
        pack_path, answers_path, qa_path, doc2025 = sys.argv[1:5]

    pack = load_json(pack_path)
    answers = load_json(answers_path)
    qa = load_json(qa_path)

    print('[FILES]')
    for p in [pack_path, answers_path, qa_path, doc2025]:
        print(' -', p, 'OK' if os.path.exists(p) else 'MISSING')

    print('\n[SCHEMA] Context pack item fields')
    total, missing, samples = validate_context_pack_schema(pack)
    print(f' - items: {total}, schema-missing: {missing}')
    for s in samples:
        print('   *', s)

    print('\n[MBC] Canonical key shape and dedupe')
    mbc_total, mbc_issues, mbc_samples = validate_mbc_keys(pack)
    print(f' - mbc items: {mbc_total}, issues: {mbc_issues}')
    for s in mbc_samples:
        print('   *', s)

    print('\n[NARRATIVE] Alt formats extraction from 2025 final')
    ok, detail = check_narrative_alt_formats(pack, doc2025)
    print(' - ok:' , ok)
    if detail:
        print('   *', (detail[:220] + '...') if len(detail) > 220 else detail)

    print('\n[SCALARS] Type-based validations')
    probs = scalars_validation(pack, answers)
    for k, v in probs.items():
        print(f' - {k}: {len(v)} bad')
        if v[:5]:
            for s in v[:5]:
                print('   *', s)

    print('\n[CLIENT RULES]')
    cr = client_rules_check(answers)
    for k, v in cr.items():
        print(f' - {k}: {len(v)}')
        if v[:5]:
            for s in v[:5]:
                print('   *', s)

    print('\n[QA SUMMARY]')
    okqa, miss = qa_summary_check(qa)
    print(' - ok:', okqa, ('missing: ' + ','.join(miss) if miss else ''))

    print('\nDONE')


if __name__ == '__main__':
    main()


