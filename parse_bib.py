"""Extract cited modern authors from a dissertation's bibliography (pdftotext -layout output).

Usage: python3 parse_bib.py TXT_DIR OUT_JSON
Output: {slug: {"start_line":..,"n_entries":..,"authors":[[surname, given], ...], "sample":[...]} }
"""
import json, os, re, sys, unicodedata

HEAD = re.compile(r"^\s*(select(ed)?\s+)?(bibliography|works\s+cited|references|literature\s+cited|sources\s+cited|references\s+cited|bibliography\s+used|works\s+consulted)(\s*[:\-–]\s*(primary|secondary)?\s*(sources|literature)?)?\s*:?\s*$", re.I)
SEC = re.compile(r"^\s*([ivx]+\.\s*)?(bibliography\s*[-–:]\s*)?(cited\s+)?(secondary\s+(sources|literature|works|scholarship|texts)(\s+and\s+\w+)?|modern\s+(works|scholarship|studies|literature|sources))\s*:?\s*$", re.I)
PRIM = re.compile(r"^\s*([ivx]+\.\s*)?(bibliography\s*[-–:]\s*)?(cited\s+)?((arabic|greek|latin|syriac|hebrew|coptic|aramaic|persian|ancient|medieval)\s+(sources|texts)|primary\s+(sources|literature|texts|works)|ancient\s+(sources|texts|authors)|editions\s+and\s+translations|texts\s+and\s+translations|manuscripts|archival\s+sources)\b.*$", re.I)
UP = r"A-ZÀ-ÖØ-ÞĀ-Žʿʾ"
PART = r"(?:de|da|del|della|di|van|von|der|den|le|la|las|los|du|al-|el-|ten|ter|y|e)"
NAME = rf"(?:{PART}\s+)*[{UP}][^\s,.;:“”\"()]*(?:[\s\-](?:{PART}[\s\-]+)*[{UP}][^\s,.;:“”\"()]*)*"
ENTRY = re.compile(rf"^\s*(?P<sur>{NAME}),\s+(?P<given>[{UP}][^,;:“”\"()]{{0,40}}?)(?:,|\.(?:\s|$)|\s+(?:and|&)\s|\s*\(|\s+\d{{4}})")
INIT = re.compile(rf"^\s*(?P<given>[{UP}]\.(?:\s?-?[{UP}]\.)*)\s+(?P<sur>{NAME})\s*[,(–]")
DASH = re.compile(r"^\s*(—{2,}|–{2,}|-{3,}|_{3,}|‒{2,}|―{1,}|-\s{2,})")
COAUTH = re.compile(rf"(?:,|\s)\s*(?:and|&)\s+([{UP}][^\s,.]*(?:\s+[{UP}]\.?)*(?:\s+[{UP}][^\s,.]*)*)\s+({NAME})")
END = re.compile(r"^\s{0,3}(appendix|appendices|index(\s+of\s+\w+)?|general\s+index|catalogue|catalog|list\s+of\s+(figures|plates|illustrations)|figures|plates|illustrations|curriculum\s+vitae|vita)\b[^\d]{0,40}$", re.I)
PAGE = re.compile(r"^\s*([ivxlc]+|\d{1,4})\s*$", re.I)


def norm_ws(s):
    return re.sub(r"[ \t ]+", " ", s.rstrip())


def find_start(lines):
    n = len(lines)
    heads = [i for i, l in enumerate(lines) if HEAD.match(norm_ws(l)) and i > n * 0.5]
    if not heads:
        return None
    start = heads[-1]
    # If the last heading is followed by very few entries, it may be a running header; prefer the earliest
    # heading in the back half that is followed by entry-like lines.
    for h in heads:
        window = lines[h + 1:h + 80]
        if sum(bool(ENTRY.match(norm_ws(x))) for x in window) >= 5:
            start = h
            break
    return start


def parse(text):
    lines = text.split("\n")
    s = find_start(lines)
    if s is None:
        return None
    body = lines[s + 1:]
    # skip primary-source sections when explicitly labeled
    out_lines, in_primary = [], bool(re.search(r"primary", lines[s], re.I))
    for l in body:
        t = norm_ws(l)
        if END.match(t):
            break
        if PRIM.match(t) and len(t) < 60:
            in_primary = True; continue
        if SEC.match(t):
            in_primary = False; continue
        if not in_primary:
            out_lines.append(l)
    # group into entries
    entries, cur, prev_blank = [], None, True
    for l in out_lines:
        t = norm_ws(l)
        if not t.strip() or PAGE.match(t):
            prev_blank = True; continue
        indented = bool(re.match(r"^\s{2,}", l.replace("\t", "    ")))
        m = (ENTRY.match(t) or INIT.match(t)) if (not indented or prev_blank) else None
        d = (DASH.match(t) or (prev_blank and re.match(r"^\s+\.\s", l))) if (not indented or prev_blank) else None
        if m or d:
            if cur: entries.append(cur)
            cur = t.strip()
        elif cur is not None:
            cur += " " + t.strip()
        prev_blank = False
    if cur: entries.append(cur)
    authors_all, last, sample, ent = [], None, [], []
    for e in entries:
        if DASH.match(e) or e.startswith(". "):
            names = last or []
        else:
            m = ENTRY.match(e) or INIT.match(e)
            if not m:
                continue
            given = m.group("given").strip().rstrip(".")
            names = [(m.group("sur").strip(), given)]
            head = e[:m.end() + 120]
            cut = re.search(r"[“\"]|\.\s+[{}][a-z]".format(UP), head[m.end() - 1:])
            seg = head[: m.end() - 1 + cut.start()] if cut else head[:m.end() + 60]
            for g, sname in COAUTH.findall(seg):
                if len(sname) > 1 and sname.lower() not in ("eds", "ed", "trans"):
                    names.append((sname.strip(), g.strip()))
            last = names
        authors_all.extend(names)
        ent.extend([[a, b, e[:160]] for a, b in names])
        if len(sample) < 6:
            sample.append(e[:140])
    return {"start_line": s + 1, "n_entries": len(entries), "authors": authors_all, "sample": sample, "entries": ent}


if __name__ == "__main__":
    d, outp = sys.argv[1], sys.argv[2]
    res = {}
    for f in sorted(os.listdir(d)):
        if f.endswith(".txt"):
            r = parse(open(os.path.join(d, f), encoding="utf-8", errors="ignore", newline="").read().replace("\r\n", "\n").replace("\r", " "))
            res[f[:-4]] = r
            print(f, "NO BIBLIOGRAPHY FOUND" if not r else f"line {r['start_line']} entries={r['n_entries']} authors={len(r['authors'])}")
    json.dump(res, open(outp, "w"), indent=1, ensure_ascii=False)
