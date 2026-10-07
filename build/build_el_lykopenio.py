#!/usr/bin/env python3
"""Build docs/el/lykopenio.md — Greek mirror of the lycopene page incl. the interactive layer.
Body + Start-here + findings translated via translate_md; the rlw-quiz JSON translated separately
(strings only; `a` indices + option order preserved; data-lang=el, data-id=lykopenio-el)."""
import re, json, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import translate_md_to_greek as T

DOCS = ROOT / "docs"
EN = (DOCS / "lycopene.md").read_text(encoding="utf-8")
TIER_EL = {
    "Tier 1": "Επίπεδο 1",
    "Tier 2": "Επίπεδο 2",
    "Tier 3": "Επίπεδο 3",
    "Tier 4": "Επίπεδο 4",
    "Practical": "Πρακτικά"
}

# 1. Pull the EN quiz div + its JSON
m = re.search(r'<div class="rlw-quiz".*?</div>', EN, re.S)
assert m, "no rlw-quiz div found"
quiz_div_en = m.group(0)
jm = re.search(r'<script type="application/json" class="rlw-quiz-data">\s*(\{.*?\})\s*</script>', quiz_div_en, re.S)
bank = json.loads(jm.group(1))["questions"]
assert len(bank) == 42, f"expected 42 questions, found {len(bank)}"

# 2. Body translation with the quiz div fenced off
en_noquiz = EN.replace(quiz_div_en, "```\n@@QUIZ@@\n```")
print("Translating body markdown...")
el_body = T.translate_md(en_noquiz)

# 3. Translate the quiz strings (protect numbers/acronyms/citations, keep `a`)
print("Translating quiz questions...")
def tq(strings):
    prot, store = [], []
    for s in strings:
        p, st = T.protect(s)
        prot.append(p)
        store.append(st)
    tr = T.translate_batch(prot)
    return [T.restore(tr[i], store[i]) for i in range(len(prot))]

flat, spans = [], []
for q in bank:
    items = [q["q"]] + list(q["options"]) + [q["why"]]
    spans.append((len(flat), len(items)))
    flat += items

tr = tq(flat)
el_bank = []
for q, (off, n) in zip(bank, spans):
    chunk = tr[off:off+n]
    el_bank.append({
        "tier": TIER_EL.get(q["tier"], q["tier"]),
        "q": chunk[0],
        "options": chunk[1:1+4],
        "a": q["a"],
        "why": chunk[5]
    })

el_json = json.dumps({"questions": el_bank}, ensure_ascii=False, indent=1)
el_quiz_div = (
    '<div class="rlw-quiz" data-count="12" data-lang="el" data-id="lykopenio-el" markdown="0">\n'
    '<script type="application/json" class="rlw-quiz-data">\n' + el_json + '\n</script>\n</div>'
)

# 4. Splice Greek quiz back
el = el_body.replace("```\n@@QUIZ@@\n```", el_quiz_div)

# Rewrite methodology link if any
el = el.replace("](methodology.md)", "](methodologia.md)")

out = DOCS / "el" / "lykopenio.md"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(el, encoding="utf-8")

# 5. QA
en_ft, el_ft = EN.count("[^"), el.count("[^")
tofu = el.count("\ufffd")
leftover = el.count("⟦") + el.count("⟧")
a_ok = [q["a"] for q in bank] == [q["a"] for q in el_bank]
opt_ok = all(len(q["options"]) == 4 for q in el_bank)
greek = len(re.findall(r'[Ͱ-Ͽ]', el))
latin = len(re.findall(r'[A-Za-z]', el))
nq = el.count("@@QUIZ@@")

print(f"el/lykopenio.md written: {len(el)} chars")
print(f"footnote-tokens EN={en_ft} EL={el_ft} {'OK' if en_ft==el_ft else 'CHECK'}")
print(f"tofu={tofu} leftover_placeholders={leftover} sentinel_left={nq} a_ok={a_ok} opt_ok={opt_ok} "
      f"el_bank={len(el_bank)} greek_density={greek/(greek+latin):.1%}")

status = "OK" if en_ft==el_ft and tofu==0 and leftover==0 and nq==0 and a_ok and opt_ok and len(el_bank)==42 else "CHECK"
print("STATUS", status)
if status != "OK":
    sys.exit(1)
