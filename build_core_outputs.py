import os
import sys
import json
from typing import Optional, Tuple


def find_docx_under(root: str) -> Tuple[Optional[str], Optional[str]]:
    """Heuristically find 2025 final and 2026 model DOCX under root.
    Returns (doc2025, doc2026)."""
    candidates = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith('.docx'):
                candidates.append(os.path.join(dirpath, f))

    if not candidates:
        return None, None

    # Exact placeholders, if present
    p2025 = os.path.join(root, 'PATH_TO_2025_FINAL.docx')
    p2026 = os.path.join(root, 'PATH_TO_2026_MODEL.docx')
    doc2025 = p2025 if os.path.exists(p2025) else None
    doc2026 = p2026 if os.path.exists(p2026) else None

    # Heuristics
    if doc2025 is None:
        pref = [c for c in candidates if ('2025' in os.path.basename(c)) or ('final' in os.path.basename(c).lower())]
        doc2025 = pref[0] if pref else candidates[0]
    if doc2026 is None:
        pref = [c for c in candidates if ('2026' in os.path.basename(c)) or ('model' in os.path.basename(c).lower())]
        doc2026 = pref[0] if pref else (candidates[1] if len(candidates) > 1 else candidates[0])

    return doc2025, doc2026


def main():
    root = os.path.join(os.getcwd(), 'core_files')
    outdir = os.path.join(root, 'out')
    os.makedirs(outdir, exist_ok=True)

    # Resolve inputs
    doc2025 = None
    doc2026 = None
    if len(sys.argv) >= 3:
        doc2025 = sys.argv[1]
        doc2026 = sys.argv[2]
    else:
        doc2025, doc2026 = find_docx_under(root)

    if not (doc2025 and os.path.exists(doc2025)):
        print('[ERROR] Could not locate 2025 final DOCX under:', root)
        sys.exit(2)
    if not (doc2026 and os.path.exists(doc2026)):
        print('[ERROR] Could not locate 2026 model DOCX under:', root)
        sys.exit(2)

    print('[INFO] 2025 final:', doc2025)
    print('[INFO] 2026 model:', doc2026)

    # 1) Generate context pack
    from document_parser import parse_unique_items
    items = parse_unique_items(doc2026)
    pack_path = os.path.join(outdir, 'wizard_context_pack.json')
    with open(pack_path, 'w', encoding='utf-8') as f:
        json.dump({'items': items}, f, indent=2)
    print('[OK] Context pack:', pack_path, 'items:', len(items))

    # 2) Run playbook (deterministic answers)
    from playbook_runner import run_playbook
    # Supply default client rules consistent with VPX spec
    client_rules = {
        'constants_by_type': {},
        'constants': {},
        'url_preferences': ['www.bcbsm.com/umichmaplans'],
        'enforce_dba_empty': True,
        'employer_billed_premium_blank': True,
    }
    outputs = run_playbook(doc2025, doc2026, pack_path, outdir, client_rules=client_rules)
    print('[OK] Playbook outputs:', outputs)

    # 3) Convert to wizard-friendly keys
    from convert_answers_for_wizard import convert_answers_for_wizard
    converted = os.path.join(outdir, 'answers_for_wizard.json')
    convert_answers_for_wizard(pack_path, outputs['answers_path'], converted, include_mbc=False)
    print('[OK] Wizard answers:', converted)

    # 4) Quick summary
    ans = json.load(open(outputs['answers_path'], 'r', encoding='utf-8')).get('answers', {})
    wiz = json.load(open(converted, 'r', encoding='utf-8')).get('answers', {})
    mbc_ans = sum(1 for k in ans if str(k).startswith('mbc_'))
    print('[SUMMARY] raw answers:', len(ans), 'mbc answers:', mbc_ans, 'wizard-keys:', len(wiz))


if __name__ == '__main__':
    main()


