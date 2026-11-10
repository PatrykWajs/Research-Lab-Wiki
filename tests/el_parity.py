# -*- coding: utf-8 -*-
"""EN -> EL parity checks for the Research-Lab-Wiki pages.

Every check here is a past Sunday-run failure turned into a permanent gate
(Health/Research/CLAUDE.md, lab lessons 5, 19, 22, 24, 26):

  refs        the EL page cites the same [^S#] set, with the same counts      (lesson 5)
  defs        the EL page defines the same [^S#]: footnotes, each one time
  numbers     the protected numbers (doses, %, PMIDs, years) are the same      (lesson 22)
  tables      the table row count is the same                                 (lesson 19)
  wikilinks   no "[[" in a published page (bracketed PubMed titles)           (lesson 24)
  latin       no English article at the start of a Greek sentence             (lesson 26)
  residue     no tofu (U+FFFD) and no placeholder residue (U+27E6 / U+27E7)
  hub         every EN hub card has an EL card that links to an existing page

No dependencies. Run:  python3 tests/el_parity.py            (report, exit 1 on a failure)
                       python3 tests/el_parity.py ginger      (one page, by EN slug)
                       python3 -m unittest tests.test_el_parity
"""
import collections
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EL = DOCS / "el"

REF = re.compile(r"\[\^S\d+\](?!:)")
DEF = re.compile(r"^\[\^S\d+\]:", re.M)
NUM = re.compile(r"\d+(?:[.,]\d+)*")
QUIZ = re.compile(r'<div class="rlw-quiz".*?</div>\s*$', re.S | re.M)
# An English article or demonstrative that starts a sentence, followed by a word.
LATIN_START = re.compile(
    r"(?:^|[.;!?·]\s+|^\s*[-*]\s+|\|\s*|\*\*|\"\s*)(The|These|This|Those|An)\s+[A-Za-zΑ-Ωα-ωάέήίόύώ]"
)


def page_map():
    """EN slug -> EL file name, read from the hub rewrite dict in translate_md_to_greek.py."""
    src = (ROOT / "translate_md_to_greek.py").read_text(encoding="utf-8")
    pairs = dict(re.findall(r'"\]\(([\w-]+\.md)\)":\s*"\]\(([\w-]+\.md)\)"', src))
    out = {}
    for en, el in pairs.items():
        if (DOCS / en).exists():
            out[en[:-3]] = el
    return out


def body(text):
    """Text without the quiz block: the quiz is translated by a separate pass."""
    return QUIZ.sub("", text)


def prose_lines(text):
    """Lines that carry translated prose: no footnote definitions, no code fences."""
    out, fence = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence or DEF.match(line):
            continue
        out.append(line)
    return out


def norm_nums(text):
    s = REF.sub(" ", DEF.sub(" ", text))
    return collections.Counter(n.replace(",", ".") for n in NUM.findall(s))


def counter_diff(a, b, limit=8):
    miss = list((a - b).elements())[:limit]
    extra = list((b - a).elements())[:limit]
    return miss, extra


def check_pair(slug, el_name):
    """Return a list of (check, message) failures for one EN/EL page pair."""
    en = (DOCS / f"{slug}.md").read_text(encoding="utf-8")
    el = (EL / el_name).read_text(encoding="utf-8")
    fails = []

    a, b = collections.Counter(REF.findall(en)), collections.Counter(REF.findall(el))
    if a != b:
        m, x = counter_diff(a, b)
        fails.append(("refs", f"EN={sum(a.values())} EL={sum(b.values())} missing={m} extra={x}"))

    da, db = collections.Counter(DEF.findall(en)), collections.Counter(DEF.findall(el))
    dup = [k for k, v in db.items() if v > 1]
    if da != db or dup:
        m, x = counter_diff(da, db)
        fails.append(("defs", f"EN={sum(da.values())} EL={sum(db.values())} missing={m} extra={x} dup={dup[:5]}"))

    na, nb = norm_nums(body(en)), norm_nums(body(el))
    if na != nb:
        m, x = counter_diff(na, nb)
        fails.append(("numbers", f"missing in EL={m} extra in EL={x}"))

    ta = sum(1 for l in en.split("\n") if l.lstrip().startswith("|"))
    tb = sum(1 for l in el.split("\n") if l.lstrip().startswith("|"))
    if ta != tb:
        fails.append(("tables", f"table rows EN={ta} EL={tb}"))

    for name, text in (("EN", en), ("EL", el)):
        n = text.count("[[")
        if n:
            fails.append(("wikilinks", f"{name} page has {n} '[[' "))

    hits = []
    for i, line in enumerate(prose_lines(el), 1):
        for m in LATIN_START.finditer(line):
            hits.append(f"L{i}:{m.group(1)}")
    if hits:
        fails.append(("latin", f"{len(hits)} English sentence starts, first: {hits[:6]}"))

    for ch, label in (("�", "tofu"), ("⟦", "placeholder"), ("⟧", "placeholder")):
        if ch in el:
            fails.append(("residue", f"{el.count(ch)} x {label}"))
    return fails


def check_hub():
    """Every EN hub card has an EL card, and every EL card link resolves."""
    fails = []
    en = (DOCS / "index.md").read_text(encoding="utf-8")
    el = (EL / "index.md").read_text(encoding="utf-8")
    en_links = re.findall(r"\]\(([\w-]+\.md)\)", en)
    el_links = re.findall(r"\]\(([\w-]+\.md)\)", el)
    mp = page_map()
    for link in en_links:
        slug = link[:-3]
        if slug in mp and mp[slug] not in el_links:
            fails.append(("hub", f"EL hub has no card for {link} -> {mp[slug]}"))
    for link in el_links:
        if not (EL / link).exists():
            fails.append(("hub", f"EL hub links to a missing page {link}"))
    if len(en_links) != len(el_links):
        fails.append(("hub", f"page links EN={len(en_links)} EL={len(el_links)}"))
    return fails


def main(argv):
    mp = page_map()
    slugs = argv or sorted(mp)
    bad = 0
    for slug in slugs:
        if slug not in mp:
            print(f"?? {slug}: not in the page map")
            bad += 1
            continue
        fails = check_pair(slug, mp[slug])
        print(f"{'OK  ' if not fails else 'FAIL'} {slug} -> el/{mp[slug]}")
        for check, msg in fails:
            print(f"       {check}: {msg}")
        bad += bool(fails)
    if not argv:
        hub = check_hub()
        print(f"{'OK  ' if not hub else 'FAIL'} hub (index.md <-> el/index.md)")
        for check, msg in hub:
            print(f"       {check}: {msg}")
        bad += bool(hub)
    total = len(slugs) + (0 if argv else 1)
    print(f"{total - bad}/{total} ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
