import os
import sys
import json
from typing import Dict, Tuple


def load_json(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def detect_paths() -> Tuple[str, str, str]:
    """Return (pack_path, answers_path, outdir). Raises if not found."""
    cwd = os.getcwd()
    outdir = os.path.join(cwd, 'core_files', 'out')
    pack_candidates = [
        os.path.join(outdir, 'wizard_context_pack.json'),
        os.path.join(cwd, 'database', 'wizard_context_pack.json'),
    ]
    answers_candidates = [
        os.path.join(outdir, 'answers.json'),
        os.path.join(outdir, 'answers_for_wizard.json'),
    ]
    pack = next((p for p in pack_candidates if os.path.exists(p)), None)
    ans = next((p for p in answers_candidates if os.path.exists(p)), None)
    if not pack:
        raise FileNotFoundError('Could not find wizard_context_pack.json under core_files/out or database/')
    if not ans:
        raise FileNotFoundError('Could not find answers.json or answers_for_wizard.json under core_files/out')
    return pack, ans, outdir


def expand_answers_for_wizard(pack: Dict, answers: Dict) -> Dict[str, str]:
    """Expand canonical-keyed answers into wizard raw names and placeholders."""
    items = pack.get('items', []) if isinstance(pack, dict) else []
    expanded: Dict[str, str] = {}
    for it in items:
        raw_name = it.get('name')
        key = it.get('canonical_key') or raw_name
        if key in answers and answers[key] not in (None, ""):
            val = str(answers[key])
            if raw_name:
                expanded[raw_name] = val
            for occ in it.get('occurrences', []) or []:
                ph = occ.get('placeholder')
                if ph:
                    expanded[ph.strip('[]')] = val
    # Carry through any direct keys
    for k, v in answers.items():
        if v not in (None, ""):
            expanded[k] = str(v)
    return expanded


def main():
    # Arg parsing
    if len(sys.argv) == 3:
        pack_path, answers_path = sys.argv[1], sys.argv[2]
        outdir = os.path.join(os.path.dirname(os.path.dirname(pack_path)), 'out')
        os.makedirs(outdir, exist_ok=True)
    else:
        pack_path, answers_path, outdir = detect_paths()

    print('[INFO] Pack:', pack_path)
    print('[INFO] Answers:', answers_path)

    pack = load_json(pack_path)
    data = load_json(answers_path)
    answers = data.get('answers', data)

    items = pack.get('items', []) if isinstance(pack, dict) else []
    total_items = len(items)
    total_ans = len(answers)
    mbc_items = sum(1 for it in items if str(it.get('canonical_key','')).startswith('mbc_'))
    mbc_ans = sum(1 for k in answers.keys() if str(k).startswith('mbc_'))

    # Overlap by canonical/name
    overlap = 0
    missing_keys = []
    for it in items:
        key = it.get('canonical_key') or it.get('name')
        if key in answers and str(answers[key]).strip() != '':
            overlap += 1
        else:
            missing_keys.append(key)

    print(f'[SUMMARY] Items: {total_items} (MBC: {mbc_items}) | Answers entries: {total_ans} (MBC: {mbc_ans})')
    print(f'[SUMMARY] Overlap by canonical/name: {overlap} / {total_items}')

    # Build wizard-expanded answers preview
    expanded = expand_answers_for_wizard(pack, answers)
    exp_path = os.path.join(outdir, 'answers_expanded_preview.json')
    with open(exp_path, 'w', encoding='utf-8') as f:
        json.dump({'answers': expanded}, f, indent=2)
    print('[OK] Wrote expanded preview (wizard keys) →', exp_path, '| entries:', len(expanded))

    # Report a few missing keys
    if missing_keys:
        print('[NOTE] First 15 missing canonical/name keys:')
        for k in missing_keys[:15]:
            print(' -', k)


if __name__ == '__main__':
    main()


