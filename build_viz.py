import json, collections, re, sys
import sys
BASE = sys.argv[1] if len(sys.argv) > 1 else 'data/net_final'
OUTP = sys.argv[2] if len(sys.argv) > 2 else 'data/viz.json'
net = json.load(open(BASE + '.json')); pd = json.load(open(BASE + '_perdiss.json')); nm = json.load(open(BASE + '_names.json'))
meta = json.load(open('data/meta_v.json'))
G = {'A': 'ant', 'N': 'ant', 'B': 'late', 'C': 'late', 'D': 'med', 'E': 'med'}
DISPLAY = {'james|liz': 'Liz James', 'powell|a': 'Anton Powell', 'gardner|jane': 'Jane F. Gardner', 'avila|maria': 'María Luisa Ávila', 'gleason|maud': 'Maud W. Gleason', 'cohen|shaye': 'Shaye J. D. Cohen', 'munoz|jose': 'José Esteban Muñoz'}
def fix(k, n):
    n = DISPLAY.get(k, n)
    return ' '.join(t + '.' if re.fullmatch(r'([A-Z]\.)*[A-Z]', t) else t for t in n.split())
import os
AP = 'data/attrs_final.json' if os.path.exists('data/attrs_final.json') else 'data/attrs_draft.json'
ATTR = {r['id']: r for r in json.load(open(AP))}
dis = net['dissertations']
for n in net['nodes']:
    c = collections.Counter(G[dis[s]['subfield']] for s in n['cited_by'])
    top, v = c.most_common(1)[0]
    n['group'] = top if v / n['count'] >= 2 / 3 else 'cross'
    n['by'] = dict(c); n['name'] = fix(n['id'], n['name'])
    a = ATTR.get(n['id'], {})
    n['gen'] = a.get('gender', 'u'); n['life'] = a.get('status', 'u'); n['death'] = a.get('death')
links = [l for l in net['links'] if l['strength'] >= 0.35]
per = {}
for g in ['ant', 'late', 'med']:
    ds = [s for s in pd if G[meta[s]['subfield']] == g]
    c = collections.Counter(k for s in ds for k in pd[s])
    per[g] = {'n': len(ds), 'top': [[fix(k, nm[k]), v] for k, v in sorted(c.items(), key=lambda x: (-x[1], nm[x[0]]))[:25] if v >= 2]}
out = {'n': net['n_dissertations'],
       'nodes': [{k: n[k] for k in ('id', 'name', 'count', 'group', 'by', 'cited_by', 'gen', 'life', 'death')} for n in net['nodes']],
       'links': [[l['source'], l['target'], l['cocites'], l['strength']] for l in links],
       'diss': {s: {'a': d['author'], 't': d['title'], 'y': d['year'], 'i': d['institution'], 'g': G[d['subfield']], 'src': d['source'], 'ns': d['n_scholars'], 'ma': s.endswith(('MA', 'BA'))} for s, d in dis.items()},
       'per': per}
json.dump(out, open(OUTP, 'w'), ensure_ascii=False, separators=(',', ':'))
print(out['n'], len(out['nodes']), len(out['links']), collections.Counter(n['group'] for n in out['nodes']), {g: per[g]['n'] for g in per})
print('harvard', sum(1 for d in out['diss'].values() if 'Harvard' in d['i']))
for g in per: print(g, per[g]['top'][:14])
