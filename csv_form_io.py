#!/usr/bin/env python3
"""
CSV Form Export/Import for Wizard (non-MBC)

Exports a deterministic CSV form keyed by exact wizard variable name, and a
compact prompt JSON that can be used with external LLMs (e.g., ChatGPT).
Also imports a filled CSV back into answers_for_wizard.json with validation.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Dict, List, Tuple
from validators import validate_by_type


NON_MBC_TYPES = {
    'phone_number','tty_number','url','address','business_hours',
    'financial','general','plan_name','organization'
}


def load_pack_items(pack_path: str) -> List[Dict]:
    with open(pack_path, 'r', encoding='utf-8') as f:
        pack = json.load(f)
    return pack.get('items', []) if isinstance(pack, dict) else []


def export_csv_and_prompt_json(pack_path: str, out_dir: str, seed_answers_path: str | None = None) -> Dict:
    os.makedirs(out_dir, exist_ok=True)
    items = load_pack_items(pack_path)

    seeds: Dict[str, str] = {}
    if seed_answers_path and os.path.exists(seed_answers_path):
        with open(seed_answers_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        seeds = data.get('answers', data) if isinstance(data, dict) else {}

    rows: List[List[str]] = []
    keys: List[str] = []
    for it in items:
        name = it.get('name')
        key = it.get('canonical_key') or name
        vtype = (it.get('type') or '').lower()
        if not name or key.startswith('mbc_'):
            continue
        if vtype not in NON_MBC_TYPES:
            vtype = 'general'
        before = it.get('before_context', '')
        after = it.get('after_context', '')
        full = it.get('full_context', '')
        # Simple suggestions (lightweight)
        suggestions = ''
        if vtype == 'tty_number':
            suggestions = '711'
        value = seeds.get(name) or seeds.get(key) or ''
        rows.append([name, vtype, before, after, full, suggestions, value, '', ''])
        keys.append(name)

    csv_path = os.path.join(out_dir, 'wizard_form_llm.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['key','type','before_context','after_context','full_context','suggestions','value','confidence','rationale'])
        for r in rows:
            w.writerow(r)

    rules = {
        'validation': {
            'phone_number': 'Format 1-###-###-####',
            'tty_number': 'Return 711 (preferred) else phone format',
            'url': 'Must start with http(s) or www. Prefer domain bcbsm.com/umichmaplans',
            'business_hours': 'Must include a.m. or p.m.',
            'financial': 'Must include $, or copay/coinsurance, or "covered at 100%"/"no ..."',
            'general': 'Non-empty text if present in context'
        },
        'client_rules': [
            'If key contains "dba" return empty',
            'If key contains "premium" and no $digits present, return empty'
        ],
        'output': 'Return the same CSV with only the value, confidence (0..1), and rationale columns changed; do not add or remove rows.'
    }
    prompt_path = os.path.join(out_dir, 'wizard_form_prompt.json')
    with open(prompt_path, 'w', encoding='utf-8') as f:
        json.dump({'keys': keys, 'rules': rules}, f, indent=2)

    return {'csv_path': csv_path, 'prompt_json_path': prompt_path, 'count': len(rows)}


def import_filled_csv(csv_path: str, pack_path: str, out_path: str, strict: bool = True) -> Dict:
    items = load_pack_items(pack_path)
    allowed = {it.get('name'): (it.get('type') or '').lower() for it in items if not str(it.get('canonical_key') or '').startswith('mbc_')}

    answers: Dict[str, str] = {}
    review: List[Dict] = []
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            name = (row.get('key') or '').strip()
            if strict and name not in allowed:
                continue
            vtype = allowed.get(name, (row.get('type') or 'general').lower())
            value = (row.get('value') or '').strip()
            if not value:
                continue
            ok, reason = validate_by_type(vtype, value)
            if ok:
                answers[name] = value
            else:
                review.append({'name': name, 'reason': 'schema_error', 'suggested_value': value, 'confidence': float(row.get('confidence') or 0)})

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'answers': answers}, f, indent=2)

    return {'answers_for_wizard_path': out_path, 'accepted': len(answers), 'review': len(review)}


