# Who dissertations cite: gender and sexuality in the ancient and medieval Mediterranean

A co-citation network of the modern scholars cited in **28 PhD dissertations (2010–2026)** on gender and sexuality in the ancient and medieval Mediterranean. It is built from the dissertations' own bibliographies, parsed from full text and audited by hand. An optional view adds 6 master's and BA theses (34 works in all).

Snapshot: November 2026.

## What's in this package

| File | Contents |
|---|---|
| `index.html` | The interactive map. It is self-contained and only loads d3 (cdnjs) and Google Fonts. Open it in a browser or host it anywhere (GitHub Pages, an institutional site, Zenodo/OSF). |
| `data/works.csv` | The 28 dissertations and 6 theses: author, year, title, institution, degree, field group, scholars counted and record URL. It also lists the works checked and excluded, with the reason for each. |
| `data/scholars.csv` | All 261 scholars on the map, in either view. Gives citation counts (overall and per field), gender, living/deceased status (as of November 2026), death year and the evidence for each status. |
| `data/citations.csv` | Every resolved work → scholar citation, one row per pair (7,419 rows). It includes scholars below the map's 3-citation threshold. |
| `data/cocitation_links_phd.csv` | Co-citation links among scholars on the PhD map: the number of dissertations citing both, and cosine-normalised strength. |
| `data/corrections.csv` | Audit log: initials-only citations resolved by checking the cited title, same-name splits, merged spelling variants, removed parsing artefacts, excluded reference works, and the living/deceased verification with sources. |
| `data/intermediate/` | Parsed bibliographies (author name plus the opening of each entry; no dissertation text), work metadata and scholar attributes. These are the inputs needed to rerun the analysis. |
| `scripts/` | The pipeline (Python 3, standard library only). |

## Method in brief

1. **Sample.**
   - 9 dissertations come from Harvard's open repository (DASH), found by keyword search and screened by hand.
   - 19 more were chosen to spread across universities and subfields: 10 antiquity, 10 late antiquity and early Byzantium, and 8 medieval Latin, Jewish and Islamic.
   - Each one's author, title, year, institution and doctoral status was checked against the document and a repository, catalogue or ProQuest record.
2. **Extraction** (`parse_bib.py`).
   - Each PDF → text (`pdftotext -layout`). The bibliography is located, and labelled primary-source sections are skipped.
   - Entries are split, and authors, co-authors and editors are extracted.
   - Lexica and encyclopedias are excluded.
3. **Counting** (`network.py`).
   - A scholar counts once per work, matched by surname plus first name.
   - Initials-only citations are assigned automatically only when exactly one known scholar fits. Otherwise they are resolved by hand from the cited title (see `corrections.csv`) or dropped.
4. **Audit** (`audit.py`). For every scholar on the map, every initials-only citation was checked against the title it cites. This fixed conflations such as:
   - P. G. McC. Brown vs. Peter Brown
   - Charles M. vs. Catharine Edwards
   - Erich vs. Eliezer Segal
   - Alan vs. Averil Cameron
   - Jane F. vs. Julian Gardner
5. **Links.** Co-citation strength = co-citing works / √(count A × count B). The map shows pairs co-cited at least twice.
6. **Gender** follows each scholar's public self-identification (Judith Butler: nonbinary).
7. **Living/deceased** status was checked in three rounds of web searches:
   - every death, against an obituary or institutional notice
   - every scholar born before about 1950
   - every uncertain case

   This corrected 25 scholars first assumed to be living. Younger scholars were not searched individually, so "living" means no death notice was found.

## Limits

- **Sample size.** 28 dissertations show broad patterns, not a census. A one-citation difference is noise.
- **Selection.** The non-Harvard dissertations were chosen for spread, not at random. Only open-access or downloadable texts could be included.
- **Institution effect.** 9 of the 28 are from Harvard, mostly early Christianity.
- **Bibliography only.** Only bibliographies are read, not footnotes. A citation shows that a scholar was used, not how much or how approvingly.
- **Gender skew.** The gender view measures who is cited, not the gender balance of authors in the field.

## Rerunning

```bash
# Counts and network from the parsed bibliographies (PhD-only view)
python3 scripts/network.py data/intermediate/bibliographies_parsed_phd.json data/intermediate/works_meta.json out/net.json 90

# With master's/BA theses
python3 scripts/network.py data/intermediate/bibliographies_parsed.json data/intermediate/works_meta.json out/net_ma.json 90

# Audit initials-only matches for manual review
python3 scripts/audit.py data/intermediate/bibliographies_parsed_phd.json data/intermediate/works_meta.json
```

To add a dissertation:
1. Run `pdftotext -layout file.pdf texts/Name_Year.txt`.
2. Run `python3 scripts/parse_bib.py texts/ parsed.json`.
3. Add an entry to `works_meta.json` with the field code: A/N antiquity; B/C late antiquity and early Byzantium; D/E medieval and Islamic.
4. Rerun `network.py` and `audit.py`, then review the audit output.

`build_viz.py` and `scripts/template.html` rebuild `index.html` from the network output.

The dissertations themselves are not included. They remain the copyright of their authors and are available from the record URLs in `works.csv`.

## Suggested citation

[Your name], *Who Dissertations Cite: Gender and Sexuality in the Ancient and Medieval Mediterranean, 2010–2026* (co-citation map and dataset), November 2026. [URL or DOI]
