#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build docs/el/tzinzer-ginger.md — Greek mirror of the ginger page incl. the interactive layer.
Body + Start-here + findings translated via translate_md with the rlw-quiz div fenced off;
the quiz strings translated separately in explicit chunks (lab lesson 11), `a` indices and
option order preserved; data-lang=el, data-id=tzinzer-ginger-el.
Run with the BUSINESS .env sourced in the same shell (OpenAI key)."""
import re, json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import translate_md_to_greek as T  # noqa: E402

DOCS = ROOT / "docs"
EN = (DOCS / "ginger.md").read_text(encoding="utf-8")
N = 46
TIER_EL = {"Tier 1": "Επίπεδο 1", "Tier 2": "Επίπεδο 2", "Tier 3": "Επίπεδο 3", "Tier 4": "Επίπεδο 4", "Practical": "Πρακτικά"}

m = re.search(r'<div class="rlw-quiz".*?</div>', EN, re.S)
assert m, "no rlw-quiz div found"
quiz_div_en = m.group(0)
jm = re.search(r'<script type="application/json" class="rlw-quiz-data">\s*(\{.*?\})\s*</script>', quiz_div_en, re.S)
bank = json.loads(jm.group(1))["questions"]
assert len(bank) == N, len(bank)

en_noquiz = EN.replace(quiz_div_en, "```\n@@QUIZ@@\n```")
assert en_noquiz.count("@@QUIZ@@") == 1
print("Translating body markdown...")
el_body = T.translate_md(en_noquiz)

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

el_json = json.dumps({"questions": el_bank}, ensure_ascii=False, indent=1)
el_quiz_div = ('<div class="rlw-quiz" data-count="12" data-lang="el" data-id="tzinzer-ginger-el" markdown="0">\n'
               '<script type="application/json" class="rlw-quiz-data">\n' + el_json + '\n</script>\n</div>')
el = el_body.replace("```\n@@QUIZ@@\n```", el_quiz_div)
el = el.replace("](methodology.md)", "](methodologia.md)")

out = DOCS / "el" / "tzinzer-ginger.md"
out.write_text(el, encoding="utf-8")

# QA (lab lessons 5 and the placeholder note): both delimiters in either orientation, token counts
en_ft = len(re.findall(r"\[\^S\d+\]", en_noquiz)); el_ft = len(re.findall(r"\[\^S\d+\]", el))
tofu = el.count("�")
leftover = len(re.findall(r"[⟦⟧]\s*\d+\s*[⟦⟧]", el)) + el.count("⟦") + el.count("⟧")
a_ok = [q["a"] for q in bank] == [q["a"] for q in el_bank]
opt_ok = all(len(q["options"]) == 4 for q in el_bank)
greek = len(re.findall(r"[Ͱ-Ͽ]", el)); latin = len(re.findall(r"[A-Za-z]", el))
nq = el.count("@@QUIZ@@")
print(f"el/tzinzer-ginger.md written: {len(el)} chars")
print(f"footnote-tokens EN={en_ft} EL={el_ft} {'OK' if en_ft == el_ft else 'CHECK'}")
print(f"tofu={tofu} leftover_placeholders={leftover} sentinel_left={nq} a_ok={a_ok} opt_ok={opt_ok} el_bank={len(el_bank)} greek_density={greek / (greek + latin):.1%}")
status = "OK" if en_ft == el_ft and tofu == 0 and leftover == 0 and nq == 0 and a_ok and opt_ok and len(el_bank) == N else "CHECK"
print("STATUS", status)
if status != "OK":
    # name the missing refs (alpha-gpc lesson 5)
    from collections import Counter
    ce, cl = Counter(re.findall(r"\[\^S\d+\]", en_noquiz)), Counter(re.findall(r"\[\^S\d+\]", el))
    print("EN-only:", {k: v - cl.get(k, 0) for k, v in ce.items() if v != cl.get(k, 0)})
    sys.exit(1)
