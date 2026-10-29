#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build docs/el/elaiolado-kai-elaiokanthali.md — Greek mirror of the olive-oil page incl. the interactive
layer (project #19, 2026-10-25; adapted from build_el_tzinzer.py).

Body + Start-here + findings translated via translate_md with the rlw-quiz div fenced off; quiz strings
translated separately in explicit 24-string chunks (lab lesson 11), `a` indices and option order preserved;
data-lang=el, data-id=elaiolado-kai-elaiokanthali-el.

New since ginger (its candidate lab lesson 22): a per-line alignment gate. EN and EL are split on the same
lines; for every line the sequence of digit tokens and of [^S#] refs must match. A flagged line is
re-translated on its own (up to 4 attempts) and spliced back; anything still misaligned fails the build.
Run with the BUSINESS .env sourced in the same shell (OpenAI key)."""
import re, json, sys, pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import translate_md_to_greek as T  # noqa: E402

DOCS = ROOT / "docs"
SLUG_EL = "elaiolado-kai-elaiokanthali"
EN = (DOCS / "olive-oil-oleocanthal.md").read_text(encoding="utf-8")
N = 45
TIER_EL = {"Tier 1": "Επίπεδο 1", "Tier 2": "Επίπεδο 2", "Tier 3": "Επίπεδο 3", "Tier 4": "Επίπεδο 4", "Practical": "Πρακτικά"}
CACHE = ROOT / "build" / "elaiolado-el-body.cache.md"

m = re.search(r'<div class="rlw-quiz".*?</div>', EN, re.S)
assert m, "no rlw-quiz div found"
quiz_div_en = m.group(0)
jm = re.search(r'<script type="application/json" class="rlw-quiz-data">\s*(\{.*?\})\s*</script>', quiz_div_en, re.S)
bank = json.loads(jm.group(1))["questions"]
assert len(bank) == N, len(bank)

en_noquiz = EN.replace(quiz_div_en, "```\n@@QUIZ@@\n```")
assert en_noquiz.count("@@QUIZ@@") == 1

if CACHE.exists() and "--fresh" not in sys.argv:
    print("Using cached body translation", CACHE)
    el_body = CACHE.read_text(encoding="utf-8")
else:
    print("Translating body markdown...")
    el_body = T.translate_md(en_noquiz)
    CACHE.write_text(el_body, encoding="utf-8")

NUM = re.compile(r'\d+(?:[.,]\d+)*')
REF = re.compile(r'\[\^S\d+\]')


def sig(line):
    s = REF.sub(" ", line)
    return (NUM.findall(s), REF.findall(line))


def is_def(line):
    return bool(re.match(r'^\[\^S\d+\]:', line))


en_lines = en_noquiz.split("\n")
el_lines = el_body.split("\n")
print(f"lines EN={len(en_lines)} EL={len(el_lines)}")
assert len(en_lines) == len(el_lines), "line count drift: cannot align"

flag = [i for i, (a, b) in enumerate(zip(en_lines, el_lines)) if a.strip() and not is_def(a) and sig(a) != sig(b)]
print(f"alignment: {len(flag)} misaligned lines of {len(en_lines)}")
fixed, left = 0, []
for i in flag:
    ok = False
    for attempt in range(4):
        cand = T.translate_md(en_lines[i]).strip("\n")
        if "\n" in cand:
            cand = " ".join(cand.split("\n"))
        if sig(cand) == sig(en_lines[i]):
            # keep the original line's leading indentation
            lead = re.match(r'^\s*', en_lines[i]).group(0)
            el_lines[i] = lead + cand.lstrip()
            ok = True
            fixed += 1
            break
    if not ok:
        left.append(i)
print(f"re-translated and fixed: {fixed}; still misaligned: {len(left)}")
for i in left:
    print("  LINE", i + 1)
    print("   EN:", en_lines[i][:300])
    print("   EL:", el_lines[i][:300])
    print("   EN sig:", sig(en_lines[i]))
    print("   EL sig:", sig(el_lines[i]))
el_body = "\n".join(el_lines)
CACHE.write_text(el_body, encoding="utf-8")

print("Translating quiz strings in chunks...")


def tq(strings, chunk=24):
    out = []
    for i in range(0, len(strings), chunk):
        part = strings[i:i + chunk]
        prot, store = [], []
        for s in part:
            p, st = T.protect(s); prot.append(p); store.append(st)
        tr = T.translate_batch(prot)
        assert len(tr) == len(part), (i, len(tr), len(part))
        out += [T.restore(tr[k], store[k]) for k in range(len(part))]
        print(f"  quiz strings {i + 1}-{i + len(part)} done")
    return out


flat, spans = [], []
for q in bank:
    items = [q["q"]] + list(q["options"]) + [q["why"]]
    spans.append((len(flat), len(items))); flat += items
tr = tq(flat)
assert len(tr) == len(flat)
el_bank = []
for q, (off, n) in zip(bank, spans):
    c = tr[off:off + n]
    el_bank.append({"tier": TIER_EL.get(q["tier"], q["tier"]), "q": c[0], "options": c[1:5], "a": q["a"], "why": c[5]})
for q in el_bank:
    for s in [q["q"], q["why"]] + q["options"]:
        assert "</" not in s, s

el_json = json.dumps({"questions": el_bank}, ensure_ascii=False, indent=1)
el_quiz_div = (f'<div class="rlw-quiz" data-count="12" data-lang="el" data-id="{SLUG_EL}-el" markdown="0">\n'
               '<script type="application/json" class="rlw-quiz-data">\n' + el_json + '\n</script>\n</div>')
el = el_body.replace("```\n@@QUIZ@@\n```", el_quiz_div)
el = el.replace("](methodology.md)", "](methodologia.md)")

out = DOCS / "el" / f"{SLUG_EL}.md"
out.write_text(el, encoding="utf-8")

en_ft = len(REF.findall(en_noquiz)); el_ft = len(REF.findall(el))
tofu = el.count("�")
leftover = len(re.findall(r"[⟦⟧]\s*\d+\s*[⟦⟧]", el)) + el.count("⟦") + el.count("⟧")
a_ok = [q["a"] for q in bank] == [q["a"] for q in el_bank]
opt_ok = all(len(q["options"]) == 4 for q in el_bank)
greek = len(re.findall(r"[Ͱ-Ͽ]", el)); latin = len(re.findall(r"[A-Za-z]", el))
nq = el.count("@@QUIZ@@")
body_only = "\n".join(l for l in el.split("\n") if not is_def(l))
glued = re.findall(r'[A-Za-z]{3,}[.,;:)]?\[\^', body_only)
print(f"el/{SLUG_EL}.md written: {len(el)} chars")
print(f"footnote-tokens EN={en_ft} EL={el_ft} {'OK' if en_ft == el_ft else 'CHECK'}")
print(f"tofu={tofu} leftover_placeholders={leftover} sentinel_left={nq} a_ok={a_ok} opt_ok={opt_ok} "
      f"el_bank={len(el_bank)} greek_density={greek / (greek + latin):.1%} misaligned_left={len(left)} "
      f"latin_glued_to_ref={len(glued)} {Counter(glued).most_common(8)}")
status = ("OK" if en_ft == el_ft and tofu == 0 and leftover == 0 and nq == 0 and a_ok and opt_ok
          and len(el_bank) == N and not left else "CHECK")
print("STATUS", status)
if status != "OK":
    ce, cl = Counter(REF.findall(en_noquiz)), Counter(REF.findall(el))
    print("EN-only:", {k: v - cl.get(k, 0) for k, v in ce.items() if v != cl.get(k, 0)})
    sys.exit(1)
