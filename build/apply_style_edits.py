#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply reviewed Greek style edits to docs/el pages, transactionally (2026-11-10 style pass).

Input: one or more JSON edit lists, each item {"page": "el/<file>.md", "line": N, "old": "...", "new": "...", "why": "..."}.
An edit is applied only if ALL hold for its line after the change:
  * `old` occurs exactly once in the current line;
  * the protected numbers (normalised 1,5 -> 1.5), the `[^S#]` sequence, the link targets `](...)`, and the counts of
    `**`, `|`, `$`, `<` and `>` are unchanged;
  * no English-article residue (el_parity.LATIN_START) and no new English possessive appears.
Then, per page: the quiz JSON must still parse with the same question count and `a` indices, and the full
el_parity check must pass; otherwise the whole page is left untouched. Pages are written only with --apply.

python3 build/apply_style_edits.py <edits.json> [...] [--apply] [--log <applied.json>]
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import el_parity as P  # noqa: E402
import el_style as ST  # noqa: E402

LINK = re.compile(r"\]\([^)]*\)")
QDATA = re.compile(r'class="rlw-quiz-data">\s*(\{.*?\})\s*</script>', re.S)


def nums(s):
    return collections.Counter(n.replace(",", ".") for n in P.NUM.findall(P.REF.sub(" ", s)))


def sig(s):
    return (nums(s), P.REF.findall(s), LINK.findall(s), s.count("**"), s.count("|"), s.count("$"), s.count("<"), s.count(">"))


def quiz(text):
    m = QDATA.search(text)
    if not m:
        return None
    q = json.loads(m.group(1))["questions"]
    return [x["a"] for x in q]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    log_path = sys.argv[sys.argv.index("--log") + 1] if "--log" in sys.argv else None
    if log_path in args:
        args.remove(log_path)
    edits = []
    for f in args:
        edits += json.loads(Path(f).read_text(encoding="utf-8"))
    by_page = collections.defaultdict(list)
    for e in edits:
        by_page[e["page"]].append(e)
    rev = {v: k for k, v in P.page_map().items()}
    applied_log, totals = [], collections.Counter()
    for page, es in sorted(by_page.items()):
        path = ROOT / "docs" / page
        old_text = path.read_text(encoding="utf-8")
        lines = old_text.split("\n")
        q_before = quiz(old_text)
        ok, rej = [], collections.Counter()
        for e in sorted(es, key=lambda x: x["line"]):
            i = e["line"] - 1
            if not (0 <= i < len(lines)):
                rej["bad line"] += 1
                continue
            cur = lines[i]
            if cur.count(e["old"]) != 1:
                rej["old not unique/found"] += 1
                continue
            new = cur.replace(e["old"], e["new"], 1)
            if sig(new) != sig(cur):
                rej["numbers/refs/links/markup changed"] += 1
                continue
            if P.LATIN_START.search(new) and not P.LATIN_START.search(cur):
                rej["English article residue"] += 1
                continue
            if len(ST.POSS.findall(ST.STRIP.sub(" ", new))) > len(ST.POSS.findall(ST.STRIP.sub(" ", cur))):
                rej["new possessive"] += 1
                continue
            lines[i] = new
            ok.append(e)
        new_text = "\n".join(lines)
        page_ok, reason = True, ""
        try:
            if quiz(new_text) != q_before:
                page_ok, reason = False, "quiz JSON changed shape"
        except (ValueError, KeyError) as exc:
            page_ok, reason = False, f"quiz JSON broken: {exc}"
        if page_ok and ok:
            path.write_text(new_text, encoding="utf-8")
            fails = P.check_pair(rev[page.split("/", 1)[1]], page.split("/", 1)[1])
            if fails or not apply:
                path.write_text(old_text, encoding="utf-8")
                if fails:
                    page_ok, reason = False, f"el_parity: {fails}"
        status = ("APPLIED" if apply else "OK (dry run)") if page_ok else f"PAGE REJECTED ({reason})"
        print(f"{page:44} edits {len(es):4} | pass {len(ok):4} | rejected {sum(rej.values()):3} {dict(rej)} | {status}")
        if page_ok:
            totals["applied" if apply else "would apply"] += len(ok)
            applied_log += ok
        totals["rejected"] += sum(rej.values())
    print(dict(totals))
    if log_path and apply:
        Path(log_path).write_text(json.dumps(applied_log, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
