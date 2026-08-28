"""One-off: lift the customer-stated weight out of the concern text into its own field.

Only weights the customer stated are recorded. Two cases the regex flagged as
ambiguous are resolved by reading, not by picking a number:
  C-61805  "used to be 5'6\" 140 lbs, now 5'3\" 155 lbs"      -> 155 (140 is her past weight)
  C-55386  "138 lbs ... cites an ad showing a 170 lb model"  -> 138 (170 is the ad model)
Everything else with no stated weight is left null.
"""
import json, re

MANUAL = {'C-61805': 155, 'C-55386': 138}

# Strict: needs an explicit unit or a weigh-verb, so ages ("89 years old"),
# bra sizes ("36D"), bust measurements ("47-inch bust") and order numbers
# ("#31839") cannot match.
PATS = [
    re.compile(r'(\d{2,3})\s*(?:lbs\b|lb\b|pounds\b|pound\b)', re.I),
    re.compile(r'(\d{2,3})\s*#(?!\d)'),
    re.compile(r'weigh(?:s|ing|ed)?\s+(?:about\s+|around\s+|currently\s+)?(\d{2,3})\b', re.I),
]

def extract(text):
    vals = set()
    for p in PATS:
        for m in p.finditer(text):
            v = int(m.group(1))
            if 80 <= v <= 400:
                vals.add(v)
    return vals

rows = [json.loads(l) for l in open('records.jsonl')]
stated = 0
for r in rows:
    if r['ticket'] in MANUAL:
        r['weight_lb'] = MANUAL[r['ticket']]
    else:
        vals = extract(r['concern'])
        if len(vals) > 1:
            raise SystemExit(f"unresolved ambiguity in {r['ticket']}: {sorted(vals)}")
        r['weight_lb'] = vals.pop() if vals else None
    if r['weight_lb'] is not None:
        stated += 1

with open('records.jsonl', 'w') as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')

print(f'weight stated: {stated} | not stated: {len(rows)-stated} | total {len(rows)}')
