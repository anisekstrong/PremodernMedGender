"""Count scholars once per dissertation and build a co-citation network.

Usage: python3 network.py BIB_JSON META_JSON OUT_JSON [TOP_N]
META_JSON: {slug: {"title","author","year","institution","subfield"}}
"""
import collections, itertools, json, math, re, sys, unicodedata

bib = json.load(open(sys.argv[1]))
meta = json.load(open(sys.argv[2]))
OUT = sys.argv[3]
TOP_N = int(sys.argv[4]) if len(sys.argv) > 4 else 60

# Manual merges for known variant spellings, filled in after inspection: key -> canonical key
ALIASES = {}
# Name keys that are parsing artefacts or not scholars (checked by hand)
DROP = {"lifestyles|christian", "renunciation|sexual"}  # book-title fragments


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


STOP = set("""culture essays theory women woman life christianity society men ancient commentary ideology aspects
leadership garments history islands antiquity intermarriage love creativity medieval capital analysis sexuality
studies gender religion literature world introduction empire rome art greek roman early late modern social
political family marriage law economy studies body bodies identity texts essays reading practice praxis
status slaves children martyrdom order power representations representation images""".split())
# Reference works (lexica, encyclopedias), not scholarship
REFWORK = {"liddell|henry", "scott|robert", "lewis|charlton", "short|charles", "wissowa|georg", "pauly|august", "glare|p"}
OVERRIDE = {("Woodacre_2011", "elliott|john"): "elliott|john huxtable"}  # checked by hand
# Initials-only citations resolved by reading the cited title (audit, Nov 2026). (slug, surname, given as printed) -> key
MANUAL = {
 ("Heffron_2020", "cameron", "A"): "cameron|averil",          # Christianity and the Rhetoric of Empire; Parastaseis
 ("Valtadorou_2020", "cameron", "A"): "cameron|averil",       # Images of Women in Antiquity (ed. with Kuhrt)
 ("Sapsford_2017", "cameron", "A"): "cameron|alan",           # Callimachus and his Critics
 ("Hollaender_2021", "james", "S.L"): "james|sharon",         # Companion to Women in the Ancient World
 ("Grozdanoski_2019", "martin", "T"): "martin|therese",       # women as makers of medieval art
 ("Valtadorou_2020", "davies", "M"): "davies|malcolm",        # PMGF, Trachiniae, Stesichorus
 ("Hollaender_2021", "brown", "P.G"): "brown|peter g. mcc.",  # Menander -- not Peter Brown
 ("Hollaender_2021", "brown", "P.G.M"): "brown|peter g. mcc.",
 ("Hollaender_2021", "moore", "S"): "moore|suzanne",          # 'Here's Looking at You, Kid!' -- not Stephen D. Moore
 ("Valtadorou_2020", "edwards", "C"): "edwards|charles m.",   # 'Aphrodite on a Ladder', Hesperia
 ("Sapsford_2017", "segal", "E"): "segal|erich",              # Roman Laughter
 ("Valtadorou_2020", "segal", "E"): "segal|erich",            # Oxford Readings in Greek Tragedy
 ("Valtadorou_2020", "hughes", "D"): "hughes|d. (papyrologist)",  # P.Oxy. XLVII -- not Diane Owen Hughes
 ("Hollaender_2021", "humphreys", "S.C"): "humphreys|sally",
 ("Valtadorou_2020", "humphreys", "S"): "humphreys|sally",
 ("Heffron_2020", "kelly", "J"): "kelly|j. n. d.",            # Golden Mouth
 ("McAvoy_2017", "wilkinson", "L"): "wilkinson|l. p.",
 ("Sapsford_2017", "wilkinson", "L"): "wilkinson|l. p.",
 ("Grozdanoski_2019", "jones", "A"): "jones|alan",
 ("Wise_2017", "james", "S.L"): "james|sharon",
 ("Wise_2017", "henderson", "J"): "henderson|john",     # In Ovid with Bed -- John Henderson, not Jeffrey
 ("Stewart_2012", "evans", "J"): "evans|j. a. s.",        # Procopius
 ("Heffron_2020", "evans", "J"): "evans|j. a. s.",        # The Empress Theodora
 ("Hollaender_2021", "gardner", "J.F"): "gardner|jane",   # Sexing a Roman -- not Julian Gardner
 ("Wise_2017", "gardner", "J"): "gardner|jane",           # Women in Roman Law and Society
 ("Valtadorou_2020", "phillips", "K"): "phillips|kyle",   # Perseus and Andromeda, AJA 1968 -- not Kim M. Phillips
 ("Wise_2017", "james", "S"): "james|sharon",            # Romance kharjas
 ("Heffron_2020", "jones", "A"): "jones|a. h. m.",
 ("Stewart_2012", "jones", "A"): "jones|a. h. m.",
}
ALIAS_FULL = {"gleason|maude": "gleason|maud", "kuefler|mathew": "kuefler|matthew", "kuefler|manly": "kuefler|matthew", "osiek|carolyn": "osiek|caroline", "wissowa|georgi": "wissowa|georg", "certeau|michel": "certeau|michel"}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def clean_sur(sur):
    sur = fold(sur).strip().replace("\u2019", "'")
    return re.sub(r"^(de|da|del|della|di|van|von|der|den|le|la|du)\s+", "", sur)


def parts(given):
    toks = [t for t in re.split(r"[\s.\-]+", fold(given)) if t]
    first = toks[0] if toks and len(toks[0]) > 1 else None
    inits = "".join(t[0] for t in toks)
    return first, inits


# pass 1: collect full first names per surname, with their initials
fulls = collections.defaultdict(dict)   # sur -> {first: inits}
for slug, r in bib.items():
    if not r:
        continue
    for sur, given in r["authors"]:
        f, i = parts(given)
        if f:
            sk = clean_sur(sur)
            f = ALIAS_FULL.get(f"{sk}|{f}", f"{sk}|{f}").split("|", 1)[1]
            if len(i) > len(fulls[sk].get(f, "")):
                fulls[sk][f] = i
            else:
                fulls[sk].setdefault(f, i)

unresolved = collections.Counter()


def key(sur, given):
    sk = clean_sur(sur)
    if not sk or sk in STOP or ":" in given or fold(given).strip() in STOP:
        return None
    f, i = parts(given)
    if f:
        k = f"{sk}|{f}"
    else:
        cands = [fn for fn, fi in fulls[sk].items() if fi.startswith(i) or i.startswith(fi)]
        if len(cands) == 1:
            k = f"{sk}|{cands[0]}"
        elif not cands:
            k = f"{sk}|{i or '?'}"
        else:
            unresolved[sk] += 1
            return None
    k = ALIAS_FULL.get(k, k)
    if k in REFWORK or k in DROP:
        return None
    return ALIASES.get(k, k)


display = collections.defaultdict(collections.Counter)
per_diss = {}
for slug, r in bib.items():
    if not r or slug not in meta:
        continue
    s = set()
    for sur, given in r["authors"]:
        if len(sur) < 2 or not re.search(r"[a-z]", sur):
            continue
        mk = (slug, clean_sur(sur), given.strip())
        k = MANUAL[mk] if mk in MANUAL else key(sur, given)
        if not k:
            continue
        k = OVERRIDE.get((slug, k), k)
        s.add(k)
        display[k][f"{given} {sur}".strip()] += 1
    per_diss[slug] = s

N = len(per_diss)
count = collections.Counter(k for s in per_diss.values() for k in s)
# subfield spread for each scholar
spread = collections.defaultdict(set)
for slug, s in per_diss.items():
    for k in s:
        spread[k].add(meta[slug].get("subfield", "?"))


def best_name(k):
    # prefer the longest commonly used form (full given name over initials)
    c = display[k]
    return max(c, key=lambda n: (c[n] > 0, len(n.split()[0]) if n.split() else 0, c[n]))


ranked = sorted(count, key=lambda k: (-count[k], k))
cut = count[ranked[TOP_N - 1]] if len(ranked) >= TOP_N else 1
top = [k for k in ranked if count[k] >= 3]  # fixed threshold so variants are comparable
topset = set(top)
pair = collections.Counter()
for s in per_diss.values():
    for a, b in itertools.combinations(sorted(s & topset), 2):
        pair[(a, b)] += 1

nodes = [{"id": k, "name": best_name(k), "count": count[k], "share": round(count[k] / N, 3),
          "subfields": sorted(spread[k]),
          "cited_by": sorted(slug for slug, s in per_diss.items() if k in s)} for k in top]
links = []
for (a, b), c in pair.items():
    strength = c / math.sqrt(count[a] * count[b])
    if c >= 2:
        links.append({"source": a, "target": b, "cocites": c, "strength": round(strength, 3)})

json.dump({"n_dissertations": N, "nodes": nodes, "links": links,
           "dissertations": {s: meta[s] | {"n_scholars": len(per_diss[s])} for s in per_diss}},
          open(OUT, "w"), indent=1, ensure_ascii=False)
print(f"dissertations={N} nodes={len(nodes)} (min count 3) links={len(links)}")
for n in nodes:
    print(f"{n['count']:3d}  {n['name']:35s} {','.join(n['subfields'])}")

# per-dissertation scholar sets, for per-field rankings
json.dump({s: sorted(v) for s, v in per_diss.items()}, open(OUT.replace(".json", "_perdiss.json"), "w"))
json.dump({k: best_name(k) for k in count}, open(OUT.replace(".json", "_names.json"), "w"), ensure_ascii=False)
