#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic repair pass for one Greek page that fails tests/el_parity.py (2026-11-10).

Generalises build/repair_el_ilektrolytes.py. It re-translates ONLY the flagged parts, keeps everything else
byte-identical, and writes the page only if the full el_parity check of that page passes afterwards.

Flagged body lines (EN and EL are aligned line by line once the quiz div is replaced by a sentinel):
  * a line whose protected numbers (normalised 1,5 -> 1.5) or [^S#] sequence differ from its EN line;
  * a line with an English article at a sentence start (lesson 26), using el_parity.LATIN_START.
Flagged quiz strings: q / why / options that match LATIN_START. The `a` indices and option order are kept.
A candidate is accepted only if its numbers and refs equal the EN line's and it has no English sentence start
(up to 4 attempts per line). Footnote definition lines are never touched.

Run with the BUSINESS .env sourced in the SAME shell call (translate_md_to_greek builds its client on import):
  set -a; source "/Users/patrykwajs/Documents/BUSINESS/AGENTIC AI/.env"; set +a
  python3 build/repair_el_page.py <en-slug> [--dry-run]
Exit 0 = written and el_parity passes; 1 = nothing written.
"""
import collections
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import el_parity as P  # noqa: E402
import translate_md_to_greek as T  # noqa: E402

QUIZ = re.compile(r'<div class="rlw-quiz".*?</div>', re.S)
QDATA = re.compile(r'(class="rlw-quiz-data">\s*)(\{.*?\})(\s*</script>)', re.S)
SENT = "```\n@@QUIZ@@\n```"


def nums(line):
    s = P.REF.sub(" ", line)
    return collections.Counter(n.replace(",", ".") for n in P.NUM.findall(s))


def refs(line):
    return P.REF.findall(line)


def latin(text):
    return bool(P.LATIN_START.search(text))


def good(cand, en_line):
    return nums(cand) == nums(en_line) and refs(cand) == refs(en_line) and not latin(cand) and "�" not in cand \
        and "⟦" not in cand and "⟧" not in cand


def main():
    slug = sys.argv[1]
    dry = "--dry-run" in sys.argv
    mp = P.page_map()
    en_path, el_path = P.DOCS / f"{slug}.md", P.EL / mp[slug]
    en, el = en_path.read_text(encoding="utf-8"), el_path.read_text(encoding="utf-8")
    links = {f"]({k}.md)": f"]({v})" for k, v in mp.items()}

    # ---- body lines ----
    en_q, el_q = QUIZ.search(en), QUIZ.search(el)
    en_lines = en.replace(en_q.group(0), SENT).split("\n")
    el_lines = el.replace(el_q.group(0), SENT).split("\n")
    assert len(en_lines) == len(el_lines), (len(en_lines), len(el_lines))
    fence, flagged = False, []
    for i, (a, b) in enumerate(zip(en_lines, el_lines)):
        if b.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence or not b.strip() or P.DEF.match(b) or b.startswith("|---"):
            continue
        if nums(a) != nums(b) or refs(a) != refs(b) or latin(b):
            flagged.append(i)
    print(f"{slug}: body lines flagged {len(flagged)}")
    fixed, still = 0, []
    for i in flagged:
        ok = False
        for _ in range(4):
            cand = T.translate_md(en_lines[i]).strip("\n")
            cand = " ".join(cand.split("\n"))
            for k, v in links.items():
                cand = cand.replace(k, v)
            if good(cand, en_lines[i]):
                lead = re.match(r"^\s*", en_lines[i]).group(0)
                el_lines[i] = lead + cand.lstrip()
                ok, fixed = True, fixed + 1
                break
        if not ok:
            still.append(i + 1)
    print(f"  body fixed {fixed} | still flagged (EL line numbers in the quiz-free text) {still}")

    # ---- quiz strings ----
    qm = QDATA.search(el_q.group(0))
    bank = json.loads(qm.group(2))["questions"]
    en_bank = json.loads(QDATA.search(en_q.group(0)).group(2))["questions"]
    assert len(bank) == len(en_bank)
    todo = []
    for qi, q in enumerate(bank):
        for f in ("q", "why"):
            if latin(q[f]):
                todo.append((qi, f, None))
        for oi, o in enumerate(q["options"]):
            if latin(o):
                todo.append((qi, "options", oi))
    src = [en_bank[qi][f] if oi is None else en_bank[qi]["options"][oi] for qi, f, oi in todo]
    out = []
    for j in range(0, len(src), 24):
        part = src[j:j + 24]
        prot, store = [], []
        for s in part:
            p, st = T.protect(s)
            prot.append(p)
            store.append(st)
        tr = T.translate_batch(prot)
        assert len(tr) == len(part)
        out += [T.restore(tr[k], store[k]) for k in range(len(part))]
    qleft = 0
    for (qi, f, oi), new in zip(todo, out):
        if latin(new) or "</" in new:
            qleft += 1
            continue
        if oi is None:
            bank[qi][f] = new
        else:
            bank[qi]["options"][oi] = new
    assert [q["a"] for q in bank] == [q["a"] for q in en_bank]
    print(f"  quiz strings flagged {len(todo)} | fixed {len(todo) - qleft} | left {qleft}")
    div = el_q.group(0)
    div = div[:qm.start(2)] + json.dumps({"questions": bank}, ensure_ascii=False, indent=1) + div[qm.end(2):]
    new_el = "\n".join(el_lines).replace(SENT, div, 1)

    # ---- gate: write, run the full el_parity check, roll back on any failure ----
    if dry:
        print("  dry run: nothing written")
        return 1
    bak = ROOT / "build" / f"{el_path.stem}.pre-repair-{time.strftime('%Y%m%d-%H%M%S')}.md"
    shutil.copy2(el_path, bak)
    el_path.write_text(new_el, encoding="utf-8")
    fails = P.check_pair(slug, mp[slug])
    if fails:
        shutil.copy2(bak, el_path)
        print("  GATE FAIL, rolled back:", fails)
        return 1
    print(f"  GATE OK, wrote {el_path.name} (backup {bak.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
