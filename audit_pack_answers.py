import json
import sys


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main(pack_path: str, answers_path: str):
    pack = load(pack_path)
    data = load(answers_path)
    answers = data.get('answers', data)

    items = pack.get('items', []) if isinstance(pack, dict) else []
    total_pack = len(items)
    mbc_pack = sum(1 for it in items if str(it.get('canonical_key','')).startswith('mbc_'))

    total_answers = len(answers)
    mbc_answers = sum(1 for k in answers.keys() if str(k).startswith('mbc_'))

    # overlap by canonical key
    overlap = 0
    missing = []
    for it in items:
        key = it.get('canonical_key') or it.get('name')
        if key in answers and answers[key] not in (None, ""):
            overlap += 1
        else:
            missing.append(key)

    print(f"Pack items: {total_pack} (MBC: {mbc_pack})")
    print(f"Answers entries: {total_answers} (MBC: {mbc_answers})")
    print(f"Overlap (by canonical/name): {overlap}")
    if missing:
        print("First 20 missing keys:")
        for k in missing[:20]:
            print(" -", k)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python audit_pack_answers.py <context_pack.json> <answers.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])


