#!/usr/bin/env python3
"""
AI Training Curator

Curates validator-approved examples and few-shots for the local autofill agent.
Inputs:
 - wizard_context_pack.json (pack)
 - answers.json (canonical keys)
 - optional: prior_final.docx for future extensions (not required to curate)

Outputs (under learning_data/):
 - training_data.json      (all accepted examples)
 - few_shots.json          (top K by type)
 - auto_values.json        (safe scalar defaults by name)
 - confidence_scores.json  (counts by type)
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple
from validators import validate_by_type


ALLOWED_TYPES = {
    'phone_number', 'tty_number', 'url', 'address', 'business_hours',
    'financial', 'general', 'plan_name', 'organization'
}


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _apply_client_rules(name: str, vtype: str, value: str) -> str:
    lname = (name or '').lower()
    v = '' if value is None else str(value)
    # DBA empty
    if 'dba' in lname:
        return ''
    # Premium blank unless contains $digit
    if 'premium' in lname and vtype in ('financial', 'general'):
        import re
        if not re.search(r"\$\d", v):
            return ''
    return v


def curate_from_pack_and_answers(pack_path: str, answers_path: str, out_dir: str = 'learning_data', per_type_max: int = 6) -> Dict:
    _ensure_dir(out_dir)
    with open(pack_path, 'r', encoding='utf-8') as f:
        pack = json.load(f)
    with open(answers_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    answers: Dict[str, str] = data.get('answers', data)

    training: List[Dict] = []
    few_shots_by_type: Dict[str, List[Dict]] = {}
    auto_values: Dict[str, str] = {}
    counters: Dict[str, Dict[str, int]] = {}

    items = pack.get('items', []) if isinstance(pack, dict) else []
    for it in items:
        key = it.get('canonical_key') or it.get('name')
        if not key or str(key).startswith('mbc_'):
            continue
        vtype = (it.get('type') or '').lower()
        if vtype not in ALLOWED_TYPES:
            continue
        if key not in answers:
            # try by raw name fallback
            nm = it.get('name')
            if nm not in answers:
                counters.setdefault(vtype, {}).setdefault('missing', 0)
                counters[vtype]['missing'] += 1
                continue
        value = answers.get(key, answers.get(it.get('name')))
        if value is None:
            counters.setdefault(vtype, {}).setdefault('empty', 0)
            counters[vtype]['empty'] += 1
            continue
        value = _apply_client_rules(it.get('name') or key, vtype, str(value))
        if value.strip() == '':
            counters.setdefault(vtype, {}).setdefault('ruled_out', 0)
            counters[vtype]['ruled_out'] += 1
            continue
        ok, reason = validate_by_type(vtype, value)
        if not ok:
            counters.setdefault(vtype, {}).setdefault('invalid', 0)
            counters[vtype]['invalid'] += 1
            continue
        # Accepted example
        rec = {
            'name': it.get('name'),
            'canonical_key': key,
            'type': vtype,
            'vpx_kind': it.get('vpx_kind', ''),
            'full_context': it.get('full_context', ''),
            'before_context': it.get('before_context', ''),
            'after_context': it.get('after_context', ''),
            'value': str(value)
        }
        training.append(rec)
        lst = few_shots_by_type.setdefault(vtype, [])
        if len(lst) < per_type_max:
            lst.append(rec)
        # Seed auto values for clear scalars
        lname = (it.get('name') or '').strip()
        if lname and vtype in {'phone_number','tty_number','url','business_hours','plan_name','organization'}:
            auto_values.setdefault(lname, str(value))
        counters.setdefault(vtype, {}).setdefault('accepted', 0)
        counters[vtype]['accepted'] += 1

    # Write artifacts
    paths = {}
    paths['training_data'] = os.path.join(out_dir, 'training_data.json')
    with open(paths['training_data'], 'w', encoding='utf-8') as f:
        json.dump({'examples': training}, f, indent=2)

    paths['few_shots'] = os.path.join(out_dir, 'few_shots.json')
    with open(paths['few_shots'], 'w', encoding='utf-8') as f:
        json.dump({'by_type': few_shots_by_type}, f, indent=2)

    paths['auto_values'] = os.path.join(out_dir, 'auto_values.json')
    with open(paths['auto_values'], 'w', encoding='utf-8') as f:
        json.dump(auto_values, f, indent=2)

    paths['confidence_scores'] = os.path.join(out_dir, 'confidence_scores.json')
    with open(paths['confidence_scores'], 'w', encoding='utf-8') as f:
        json.dump({'counters': counters}, f, indent=2)

    return {
        'counts': {
            'examples': len(training),
            'types': {k: v.get('accepted', 0) for k, v in counters.items()}
        },
        'paths': paths
    }


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python ai_training_curator.py <pack.json> <answers.json> [out_dir]')
        sys.exit(2)
    pack = sys.argv[1]
    answers = sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) >= 4 else 'learning_data'
    res = curate_from_pack_and_answers(pack, answers, outdir)
    print('[OK]', json.dumps(res, indent=2))


