#!/usr/bin/env python3
"""
Wizard binding diagnostic: simulate import mapping and report applied/type-blocked/missed.

Outputs:
  core_files/out/wizard_binding_report.json
  core_files/out/wizard_binding_preview.csv
"""

from __future__ import annotations

import json
import os
import re
import csv
from typing import Dict, List, Tuple

from validators import validate_by_type


def load_json(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def norm_key(s: str) -> str:
    t = str(s or '').strip().lower()
    if t.startswith('[') and t.endswith(']'):
        t = t[1:-1].strip()
    t = ''.join(ch if ch.isalnum() or ch.isspace() else ' ' for ch in t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def expand_canonical_to_wizard(pack: Dict, answers_path: str, include_mbc: bool = False) -> Dict[str, str]:
    data = load_json(answers_path)
    answers = data.get('answers', data)
    items = pack.get('items', []) if isinstance(pack, dict) else []
    out: Dict[str, str] = {}
    for it in items:
        raw = it.get('name')
        key = it.get('canonical_key') or raw
        if not include_mbc and str(key or '').startswith('mbc_'):
            continue
        if key in answers and answers[key] not in (None, ""):
            val = str(answers[key])
            if raw:
                out[raw] = val
            occs = it.get('occurrences')
            if isinstance(occs, list):
                for occ in occs:
                    ph = (occ or {}).get('placeholder')
                    if ph:
                        out[ph.strip('[]')] = val
    # also carry through wizard-like keys that may already be present
    for k, v in answers.items():
        if v not in (None, ""):
            if not include_mbc and str(k).startswith('mbc_'):
                continue
            out[str(k)] = str(v)
    return out


def classify_variable_type(variable_name: str, default_type: str = 'general') -> str:
    """Heuristic type classifier aligned with SmartWizard._classify_variable_type."""
    try:
        var_lower = (variable_name or '').lower()
        if 'plan name' in var_lower:
            return 'plan_name'
        if 'mao name' in var_lower or 'organization' in var_lower:
            return 'organization'
        if ('phone' in var_lower or 'customer service' in var_lower or
            'customer services' in var_lower or 'contact' in var_lower):
            return 'phone_number'
        if 'tty' in var_lower:
            return 'tty_number'
        if (('hours' in var_lower and 'operation' in var_lower) or
            ('days' in var_lower and 'hours' in var_lower)):
            return 'business_hours'
        if 'address' in var_lower:
            return 'address'
        if ('date' in var_lower or 'day' in var_lower or 'month' in var_lower):
            return 'date_time'
        if ('premium' in var_lower or 'cost' in var_lower or 'amount' in var_lower):
            return 'financial'
        if 'url' in var_lower or 'website' in var_lower:
            return 'url'
        return default_type or 'general'
    except Exception:
        return default_type or 'general'


def diagnose(pack_path: str, answers_path: str, out_dir: str) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    pack = load_json(pack_path)
    items = pack.get('items', []) if isinstance(pack, dict) else []
    # Build wizard-side variables (non-MBC) and type map
    variables: List[str] = []
    name_to_type: Dict[str, str] = {}
    for it in items:
        key = it.get('canonical_key') or it.get('name')
        if str(key or '').startswith('mbc_'):
            continue
        nm = it.get('name')
        if nm:
            variables.append(nm)
            it_type = (it.get('type') or 'general').lower()
            # Upgrade type using classifier when general/missing
            name_to_type[nm] = classify_variable_type(nm, it_type)
        # include occurrence placeholders as names sometimes used in packs
        occs = it.get('occurrences')
        if isinstance(occs, list):
            for occ in occs:
                ph = (occ or {}).get('placeholder')
                if ph:
                    nm2 = ph.strip('[]')
                    variables.append(nm2)
                    name_to_type.setdefault(nm2, classify_variable_type(nm2, (it.get('type') or 'general').lower()))
    # normalize unique
    seen = set(); vars_unique = []
    for v in variables:
        if v not in seen:
            seen.add(v)
            vars_unique.append(v)

    # Build normalized map wizard variables → originals
    norm_to_originals: Dict[str, List[str]] = {}
    for v in vars_unique:
        n = norm_key(v)
        norm_to_originals.setdefault(n, []).append(v)
        bracketed = norm_key(f"[{v}]")
        norm_to_originals.setdefault(bracketed, []).append(v)

    # Expand answers
    answers_wiz = expand_canonical_to_wizard(pack, answers_path, include_mbc=False)

    applied = 0
    type_blocked = 0
    missed: List[str] = []
    rows = []
    for k, v in answers_wiz.items():
        nk = norm_key(k)
        if nk in norm_to_originals:
            # validate for all originals this maps to
            for original in norm_to_originals[nk]:
                vtype = name_to_type.get(original, 'general')
                ok, reason = validate_by_type(vtype, v)
                if ok:
                    applied += 1
                    rows.append([original, vtype, v, 'applied', ''])
                else:
                    type_blocked += 1
                    rows.append([original, vtype, v, 'type_blocked', reason])
        else:
            missed.append(k)
            rows.append([k, '', v, 'missed', 'no_match'])

    # write CSV
    csv_path = os.path.join(out_dir, 'wizard_binding_preview.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['wizard_key','type','value','decision','reason'])
        for r in rows:
            w.writerow(r)

    report = {
        'applied': applied,
        'type_blocked': type_blocked,
        'missed': len(missed),
        'answers_considered': len(answers_wiz),
        'csv_path': csv_path
    }
    with open(os.path.join(out_dir, 'wizard_binding_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    return report


if __name__ == '__main__':
    out = os.path.join('core_files','out')
    pack_candidates = [
        os.path.join(out, 'wizard_context_pack.json'),
        os.path.join('database','wizard_context_pack.json')
    ]
    pack = next((p for p in pack_candidates if os.path.exists(p)), None)
    if not pack:
        print('Pack not found.')
        raise SystemExit(2)
    # prefer wizard answers
    ans_candidates = [
        os.path.join(out,'answers_for_wizard.json'),
        os.path.join(out,'answers.json'),
        os.path.join('database','answers.json'),
        os.path.join('database','responses.json'),
        os.path.join('assets','processsed','playbook_outputs','answers.json'),
        os.path.join('assets','processsed','wizard_answer_pack','answers.json')
    ]
    ans = next((p for p in ans_candidates if os.path.exists(p)), None)
    if not ans:
        print('Answers not found.')
        raise SystemExit(2)
    rep = diagnose(pack, ans, out)
    print('[OK]', json.dumps(rep, indent=2))


