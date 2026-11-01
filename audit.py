"""List initials-only matches and ambiguity drops for the scholars on the map, with entry text, for manual review."""
import sys, json, collections, re, runpy
bibp, metap = sys.argv[1], sys.argv[2]
sys.argv = ["network.py", bibp, metap, "/tmp/audit_net.json", "90"]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("scripts/network.py")
key, parts, clean_sur, count, fulls = g["key"], g["parts"], g["clean_sur"], g["count"], g["fulls"]
bib = json.load(open(bibp))
onmap = {k for k, c in count.items() if c >= 3}
surs = {k.split("|")[0] for k in onmap}
for slug, r in sorted(bib.items()):
    for sur, given, text in r.get("entries", []):
        sk = clean_sur(sur)
        if sk not in surs:
            continue
        f, i = parts(given)
        if f:
            continue  # full first name given: unambiguous
        k = key(sur, given)
        k = g["OVERRIDE"].get((slug, k), k) if k else k
        if k in onmap or (k is None and any(x.startswith(sk + "|") for x in onmap)):
            names = sorted(fn for fn in fulls[sk])
            print(f"{slug:18s} {sur}, {given:8s} -> {k or 'DROPPED (ambiguous: ' + '/'.join(names) + ')'} | {text[:110]}")
