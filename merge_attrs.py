import json, os, unicodedata, re
rows = json.load(open('data/attrs_draft.json'))
def norm(s): return re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower())
by = {norm(r['name']): r for r in rows}
ALIAS = {norm('Carolyn Osiek'): norm('Caroline Osiek'), norm('Ross Shepard Kraemer'): norm('Ross Kraemer'), norm('Judith P. Hallett'): norm('Judith Hallett'),
         norm('Diana E. E. Kleiner'): norm('D.E.E. Kleiner'), norm('Natalie Boymel Kampen'): norm('Natalie Kampen'), norm('Guy G. Stroumsa'): norm('Guy Stroumsa'),
         norm('Dennis R. MacDonald'): norm('Dennis Ronald MacDonald')}
log = []
for f in ['data/verified_1.json', 'data/verified_2.json', 'data/verified_3.json']:
    if not os.path.exists(f): continue
    for v in json.load(open(f)):
        k = norm(v['name']); k = ALIAS.get(k, k)
        if k not in by:
            cand = [x for x in by if x.endswith(norm(v['name'].split()[-1]))]
            k = cand[0] if len(cand) == 1 else None
        if not k: log.append(('UNMATCHED', v['name'])); continue
        r = by[k]; st = v['status'].split()[0]
        if 'low confidence' in v.get('evidence', '').lower(): st, v['death'] = 'u', None
        if st != r['status'] or v.get('death') != r['death'] or v.get('gender', r['gender']) != r['gender']:
            log.append((r['name'], f"{r['status']} {r['death'] or ''} -> {st} {v.get('death') or ''}"))
        r['status'] = st; r['death'] = v.get('death') if st == 'deceased' else None
        if v.get('gender') in ('m', 'w', 'nb'): r['gender'] = v['gender']
        r['evidence'] = v.get('evidence', '')
json.dump(rows, open('data/attrs_final.json', 'w'), ensure_ascii=False, indent=0)
for l in log: print(l)
import collections; print(collections.Counter(r['status'] for r in rows))
