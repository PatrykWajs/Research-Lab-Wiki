# -*- coding: utf-8 -*-
"""Calque candidates in the visible Greek text (2026-11-10 style pass). Read-only.

Three patterns that an independent Greek reader flagged on the live pages:
  possessive  an English possessive inside Greek prose          ("το EFSA's ~20,000×", "IOM's 20 ng/mL")
  bare_year   an article + a bare year + a noun/adjective        ("μια 1999 μελέτη", "η 2015 προσωρινή TDI")
  latin_word  a lower-case Latin-script common word in Greek text ("corn-oil", "lycopene")
Footnote definitions (English citation titles), code fences, URLs, link targets, LaTeX ($...$) and HTML tags are skipped.
`bare_year` and `latin_word` are CANDIDATES: a reader decides; `possessive` is always a defect.

python3 tests/el_style.py              -> per-page counts
python3 tests/el_style.py --json out   -> candidates as JSON (page, line, kinds, EN line, EL line) for a review pass
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import el_parity as P  # noqa: E402

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
POSS = re.compile(r"\b[A-Z][A-Za-z0-9.\-]*'s\b")
ARTS = r"(?:μια|μία|ένα|ένας|μιας|ενός|η|ο|το|τη|την|τον|του|της|τα|οι|των|στο|στη|στην|στον|στα|Η|Ο|Το|Τα|Οι|Μια|Μία|Ένα)"
BARE_YEAR = re.compile(rf"(?<![\wͰ-Ͽ]){ARTS}\s+\**((?:19|20)\d\d)\**\s+(?![\-–]|και\b|έως\b|με\b|τη\b|την\b|το\b|τον\b|στο\b|στη\b|στην\b)(?=[\wͰ-Ͽ])")
LATIN = re.compile(r"(?<![\w/.\-@#])[a-z]{4,}(?:-[a-z]{3,})*(?![\w/.\-@])")
STRIP = re.compile(r"\$[^$]*\$|`[^`]*`|\]\([^)]*\)|https?://\S+|<[^>]+>|\"[A-Za-z_]+\":|^\s*(?:!!!|\?\?\?\+?)\s+[a-z]+|\bin (?:vivo|vitro|situ)\b|\bet al\b|&[a-z]+;")
# False friends: Greek words a machine translation picked for an English research term (2026-11-10 reviews).
FALSE_FRIENDS = {"πισίν": "pool (pooled analysis) -> συγκεντρωτική ανάλυση", "οθόνη": "screen (research) -> διαλογή",
                 "μονόγραμμα": "monograph -> μονογραφία", "διαρθρικ": "transrectal -> διορθικό", "με πλύση": "wash-in -> φάση εισαγωγής",
                 "ανταπτογόν": "adaptogen -> προσαρμογόνο", "γλυκανισμέν": "sweetened -> γλυκασμένη"}
# Possessives that belong to a proper name and stay (trial and study names, statistics), checked 2026-11-10.
NAME_POSS = {"Men's", "Women's", "Physicians'", "Cohen's"}
UNITS = {"mmol", "nmol", "pmol", "kcal", "days", "week", "weeks"}  # units and the like that stay Latin


def candidates():
    out = []
    for slug, el_name in sorted(P.page_map().items()):
        en = (P.DOCS / f"{slug}.md").read_text(encoding="utf-8").split("\n")
        el = (P.EL / el_name).read_text(encoding="utf-8").split("\n")
        aligned = len(en) == len(el)
        fence = False
        for i, line in enumerate(el, 1):
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence or P.DEF.match(line) or not GREEK.search(line):
                continue
            text = STRIP.sub(" ", line)  # JSON keys, admonition keywords, Latin phrases, entities out
            kinds = {}
            poss = [w for w in POSS.findall(text) if w not in NAME_POSS]
            if poss:
                kinds["possessive"] = poss
            if BARE_YEAR.search(text):
                kinds["bare_year"] = [m.group(0) for m in BARE_YEAR.finditer(text)]
            ff = [k for k in FALSE_FRIENDS if k in text]
            if ff:
                kinds["false_friend"] = ff
            lat = [w for w in LATIN.findall(text) if w not in UNITS]
            if lat:
                kinds["latin_word"] = sorted(set(lat))
            if kinds:
                out.append({"page": f"el/{el_name}", "slug": slug, "line": i, "kinds": kinds,
                            "en": en[i - 1] if aligned else None, "el": line})
    return out


def main():
    c = candidates()
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    by = {}
    for x in c:
        d = by.setdefault(x["slug"], {"lines": 0, "possessive": 0, "bare_year": 0, "latin_word": 0, "false_friend": 0})
        d["lines"] += 1
        for k in x["kinds"]:
            d[k] += 1
    for s, d in sorted(by.items()):
        print(f"{s:28} lines {d['lines']:4}  possessive {d['possessive']:3}  bare_year {d['bare_year']:3}  latin_word {d['latin_word']:4}")
    print("total lines", len(c), "| possessive lines", sum(1 for x in c if "possessive" in x["kinds"]))
    print("false-friend lines", sum(1 for x in c if "false_friend" in x["kinds"]))
    return 1 if any(k in x["kinds"] for x in c for k in ("possessive", "false_friend")) else 0


if __name__ == "__main__":
    sys.exit(main())
