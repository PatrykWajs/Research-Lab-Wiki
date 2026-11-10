#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Greek punctuation pass (2026-11-10): an English semicolon became ';' in the Greek pages, but in Greek ';' is the
QUESTION MARK, so every such sentence read as a question. The Greek semicolon is the ano teleia '·'.

The English line says which is which. For each Greek line (and each quiz string), the script lists the marks in order:
EN marks from {';', '?'}, EL marks from {';', '·'}, skipping HTML entities (&nbsp;), URLs, link targets, inline code,
LaTeX and HTML tags. If the two sequences have the same length, an EL ';' whose EN mark is ';' becomes '·' and an EL ';'
whose EN mark is '?' stays. A line whose sequences differ in length is left alone and reported. Footnote definitions
(English citation titles) and code fences are never touched.

python3 build/fix_greek_semicolons.py            dry run, per-page counts
python3 build/fix_greek_semicolons.py --apply    write, then tests/el_parity.py must still pass (else the page is restored)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import el_parity as P  # noqa: E402

QUIZ = re.compile(r'<div class="rlw-quiz".*?</div>', re.S)
QDATA = re.compile(r'(class="rlw-quiz-data">\s*)(\{.*?\})(\s*</script>)', re.S)
SENT = "```\n@@QUIZ@@\n```"
SKIP = re.compile(r"&#?\w+;|https?://\S+|\]\([^)]*\)|`[^`]*`|\$[^$]*\$|<[^>]+>")


def marks(s, chars):
    blocked = [False] * len(s)
    for m in SKIP.finditer(s):
        for k in range(m.start(), m.end()):
            blocked[k] = True
    return [(i, c) for i, c in enumerate(s) if c in chars and not blocked[i]]


def fix_string(en, el):
    """Return (new_el, changed, mismatch)."""
    a, b = marks(en, ";?"), marks(el, ";·")
    if not b or not any(c == ";" for _, c in b):
        return el, 0, False
    if len(a) != len(b):
        return el, 0, True
    s, n = list(el), 0
    for (_, ce), (pos, cg) in zip(a, b):
        if ce == ";" and cg == ";":
            s[pos] = "·"
            n += 1
    return "".join(s), n, False


def main():
    apply = "--apply" in sys.argv
    tot = mism_tot = 0
    for slug, el_name in sorted(P.page_map().items()):
        en_path, el_path = P.DOCS / f"{slug}.md", P.EL / el_name
        en, el = en_path.read_text(encoding="utf-8"), el_path.read_text(encoding="utf-8")
        eq, lq = QUIZ.search(en), QUIZ.search(el)
        en_lines = (en.replace(eq.group(0), SENT) if eq else en).split("\n")
        el_lines = (el.replace(lq.group(0), SENT) if lq else el).split("\n")
        if len(en_lines) != len(el_lines):
            print(f"{slug:24} SKIPPED: lines do not align ({len(en_lines)} vs {len(el_lines)})")
            continue
        fence, n_body, mism = False, 0, []
        for i, (a, b) in enumerate(zip(en_lines, el_lines)):
            if b.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence or P.DEF.match(b):
                continue
            new, n, bad = fix_string(a, b)
            if bad:
                mism.append(i + 1)
            el_lines[i], n_body = new, n_body + n
        n_quiz = 0
        div = lq.group(0) if lq else None
        if eq and lq:
            em, lm = QDATA.search(eq.group(0)), QDATA.search(lq.group(0))
            ebank, lbank = json.loads(em.group(2))["questions"], json.loads(lm.group(2))["questions"]
            if len(ebank) == len(lbank):
                for qe, ql in zip(ebank, lbank):
                    for f in ("q", "why"):
                        new, n, bad = fix_string(qe.get(f, ""), ql.get(f, ""))
                        ql[f], n_quiz = new, n_quiz + n
                        mism_tot += bad
                    for k in range(min(len(qe["options"]), len(ql["options"]))):
                        new, n, bad = fix_string(qe["options"][k], ql["options"][k])
                        ql["options"][k], n_quiz = new, n_quiz + n
                        mism_tot += bad
                raw = lm.group(2)
                dumped = json.dumps({"questions": lbank}, ensure_ascii=False, indent=1 if "\n" in raw else None)
                div = div[:lm.start(2)] + dumped + div[lm.end(2):]
        new_el = "\n".join(el_lines)
        if div:
            new_el = new_el.replace(SENT, div, 1)
        left = sum(1 for _, c in marks("\n".join(l for l in new_el.split("\n") if not P.DEF.match(l)), ";"))
        print(f"{slug:24} body {n_body:4} quiz {n_quiz:3} | lines with a mismatch {len(mism):3} | ';' left {left:4}")
        tot += n_body + n_quiz
        mism_tot += len(mism)
        if apply and new_el != el:
            el_path.write_text(new_el, encoding="utf-8")
            fails = P.check_pair(slug, el_name)
            if fails:
                el_path.write_text(el, encoding="utf-8")
                print(f"   ROLLED BACK: {fails}")
    print(f"total ';' -> '·': {tot} | mismatched lines/strings left alone: {mism_tot}")


if __name__ == "__main__":
    main()
