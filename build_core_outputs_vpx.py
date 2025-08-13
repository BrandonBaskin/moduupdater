import os
import sys
import json
from typing import Dict

from document_parser import parse_unique_items
from playbook_runner import run_playbook
from convert_answers_for_wizard import convert_answers_for_wizard


def build(model_2026: str, final_2025: str, outdir: str = os.path.join('core_files', 'out')) -> Dict:
    os.makedirs(outdir, exist_ok=True)

    # 1) Context pack
    items = parse_unique_items(model_2026)
    pack_path = os.path.join(outdir, 'wizard_context_pack.json')
    with open(pack_path, 'w', encoding='utf-8') as f:
        json.dump({'items': items}, f, indent=2)

    # 2) Deterministic playbook
    # 2) Deterministic playbook with UM client rules
    client_rules = {
        'constants_by_type': {
            # Provide preferred constants where applicable
        },
        'constants': {},
        'url_preferences': ['www.bcbsm.com/umichmaplans'],
        'enforce_dba_empty': True,
        'employer_billed_premium_blank': True,
    }
    outputs = run_playbook(final_2025, model_2026, pack_path, outdir, client_rules=client_rules)

    # 3) Convert canonical → wizard keys
    answers_for_wizard_path = os.path.join(outdir, 'answers_for_wizard.json')
    # 3) Convert canonical → wizard keys (exclude MBC by default to avoid collisions)
    convert_answers_for_wizard(pack_path, outputs['answers_path'], answers_for_wizard_path, include_mbc=False)

    # 4) Brief summary
    answers = json.load(open(outputs['answers_path'], 'r', encoding='utf-8')).get('answers', {})
    wizard_answers = json.load(open(answers_for_wizard_path, 'r', encoding='utf-8')).get('answers', {})

    return {
        'context_pack_path': pack_path,
        'answers_path': outputs['answers_path'],
        'review_list_path': outputs['review_list_path'],
        'qa_summary_path': outputs['qa_summary_path'],
        'answers_for_wizard_path': answers_for_wizard_path,
        'counts': {
            'answers': len(answers),
            'wizard_answers': len(wizard_answers),
            'mbc_answers': sum(1 for k in answers if str(k).startswith('mbc_')),
        }
    }


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python build_core_outputs_vpx.py <2026_model.docx> <2025_final.docx>')
        sys.exit(2)
    model_2026 = sys.argv[1]
    final_2025 = sys.argv[2]
    results = build(model_2026, final_2025)
    print('[OK] Built core outputs:')
    for k, v in results.items():
        if isinstance(v, dict):
            print(' ', k, v)
        else:
            print(' ', k, '=>', v)
