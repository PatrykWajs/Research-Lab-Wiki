#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair pass on docs/el/ilektrolytes-kai-proini-enydatosi.md (2026-11-01): gpt-4o left a leading English
article ("The ...") and a few bare words ("vasopressin", "stick", "Sodium") inside quiz strings and body lines.
Re-translate only the affected strings/lines through the same protect -> translate -> restore pipeline, keep
the quiz `a` indices and option order, and re-run the builder's per-line alignment gate on every body line
touched. Run with the BUSINESS .env sourced."""
import re, json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import translate_md_to_greek as T  # noqa: E402

P = ROOT / "docs/el/ilektrolytes-kai-proini-enydatosi.md"
EN = (ROOT / "docs/electrolytes.md").read_text(encoding="utf-8")
el = P.read_text(encoding="utf-8")
BAD = re.compile(r"(?<![A-Za-z])(The|the|vasopressin|stick|Sodium|sodium|potassium|magnesium|water|and|of|with|in|for)(?![A-Za-z])")
STRICT = re.compile(r"(?<![A-Za-z])(The)(?![A-Za-z])")
NUM = re.compile(r'\d+(?:[.,]\d+)*'); REF = re.compile(r'\[\^S\d+\]')
sig = lambda line: (NUM.findall(REF.sub(" ", line)), REF.findall(line))

# ---- quiz strings ----
qm = re.search(r'(<div class="rlw-quiz"[^>]*>\s*<script type="application/json" class="rlw-quiz-data">\s*)(\{.*?\})(\s*</script>\s*</div>)', el, re.S)
bank = json.loads(qm.group(2))["questions"]
todo = []  # (qi, field, idx)
for qi, q in enumerate(bank):
    if BAD.search(q["q"]): todo.append((qi, "q", None))
    if BAD.search(q["why"]): todo.append((qi, "why", None))
    for oi, o in enumerate(q["options"]):
        if BAD.search(o): todo.append((qi, "options", oi))
print("quiz strings to re-translate:", len(todo))
en_bank = json.loads(re.search(r'class="rlw-quiz-data">\s*(\{.*?\})\s*</script>', EN, re.S).group(1))["questions"]
src = []
for qi, f, oi in todo:
    src.append(en_bank[qi][f] if oi is None else en_bank[qi]["options"][oi])
out = []
for i in range(0, len(src), 24):
    part = src[i:i + 24]; prot, store = [], []
    for s in part:
        p, st = T.protect(s); prot.append(p); store.append(st)
    tr = T.translate_batch(prot); assert len(tr) == len(part)
    out += [T.restore(tr[k], store[k]) for k in range(len(part))]
left = 0
for (qi, f, oi), new in zip(todo, out):
    if STRICT.search(new) or "</" in new:  # accept protected technical terms; only a stray article or markup fails
        left += 1; print("  still bad:", new[:90]); continue
    if oi is None: bank[qi][f] = new
    else: bank[qi]["options"][oi] = new
assert [q["a"] for q in bank] == [q["a"] for q in en_bank]
el = el[:qm.start(2)] + json.dumps({"questions": bank}, ensure_ascii=False, indent=1) + el[qm.end(2):]
print("quiz strings repaired:", len(todo) - left, "| unrepaired:", left)

# ---- body lines (outside the quiz div and footnote defs) ----
en_noquiz = EN.replace(re.search(r'<div class="rlw-quiz".*?</div>', EN, re.S).group(0), "```\n@@QUIZ@@\n```")
quiz_div = re.search(r'<div class="rlw-quiz".*?</div>', el, re.S).group(0)
el_noquiz = el.replace(quiz_div, "```\n@@QUIZ@@\n```")
en_lines, el_lines = en_noquiz.split("\n"), el_noquiz.split("\n")
assert len(en_lines) == len(el_lines), (len(en_lines), len(el_lines))
rows = [i for i, l in enumerate(el_lines) if l.strip() and not re.match(r'^\[\^S\d+\]:', l) and STRICT.search(l) and not l.startswith("|---")]
print("body lines with a stray 'The':", len(rows))
fixed, still = 0, []
for i in rows:
    ok = False
    for attempt in range(4):
        cand = T.translate_md(en_lines[i]).strip("\n")
        if "\n" in cand: cand = " ".join(cand.split("\n"))
        if sig(cand) == sig(en_lines[i]) and not STRICT.search(cand):
            lead = re.match(r'^\s*', en_lines[i]).group(0); el_lines[i] = lead + cand.lstrip(); ok = True; fixed += 1; break
    if not ok: still.append(i)
print("body lines fixed:", fixed, "| still flagged:", [i + 1 for i in still])
el = "\n".join(el_lines).replace("```\n@@QUIZ@@\n```", quiz_div)
el = el.replace("](methodology.md)", "](methodologia.md)")

# ---- gates (same as the builder) ----
en_ft, el_ft = len(REF.findall(en_noquiz)), len(REF.findall(el))
tofu = el.count("�"); leftover = el.count("⟦") + el.count("⟧")
body_only = "\n".join(l for l in el.split("\n") if not re.match(r'^\[\^S\d+\]:', l))
glued = re.findall(r'[A-Za-z]{3,}[.,;:)]?\[\^', body_only)
print(f"footnote-tokens EN={en_ft} EL={el_ft} tofu={tofu} leftover={leftover} glued={len(glued)} quiz={len(bank)}")
status = en_ft == el_ft and tofu == 0 and leftover == 0 and not still and left == 0 and len(bank) == 45
print("STATUS", "OK" if status else "CHECK")
if status:
    P.write_text(el, encoding="utf-8"); print("wrote", P)
else:
    sys.exit(1)
