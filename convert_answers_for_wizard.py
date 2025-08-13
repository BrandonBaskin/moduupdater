import json
import os
from typing import Dict


def load_json(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_answers_for_wizard(context_pack_path: str, answers_path: str, out_path: str, include_mbc: bool = False) -> str:
    """
    Convert canonical-keyed answers (e.g., mbc_*) into Wizard-friendly keys using the context pack.

    - For each item in the pack, if its canonical_key is present in answers, emit mappings for:
      * raw name (inner text)
      * each occurrence.placeholder (without brackets)
    - Also carry through any non-canonical keys already present in answers.
    """
    pack = load_json(context_pack_path)
    data = load_json(answers_path)
    answers = data.get('answers', data)

    expanded: Dict[str, str] = {}
    items = pack.get('items', []) if isinstance(pack, dict) else []

    for it in items:
        raw_name = it.get('name')
        key = it.get('canonical_key') or raw_name
        if key in answers and answers[key] not in (None, ""):
            # Skip MBC keys unless explicitly requested
            if not include_mbc and isinstance(key, str) and key.startswith('mbc_') and key.endswith('_cost_share'):
                continue
            val = str(answers[key])
            if raw_name:
                expanded[raw_name] = val
            for occ in it.get('occurrences', []) or []:
                ph = occ.get('placeholder')
                if ph:
                    expanded[ph.strip('[]')] = val

    for k, v in answers.items():
        if v not in (None, ""):
            # Also suppress MBC canonical spillover unless include_mbc=True
            if not include_mbc and isinstance(k, str) and k.startswith('mbc_') and k.endswith('_cost_share'):
                continue
            expanded[k] = str(v)

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'answers': expanded}, f, indent=2)
    return out_path


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        print("Usage: python convert_answers_for_wizard.py <context_pack.json> <answers.json> <out.json>")
        sys.exit(1)
    print(convert_answers_for_wizard(sys.argv[1], sys.argv[2], sys.argv[3]))


