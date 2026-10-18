#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build docs/ginger.md for Research-Lab-Wiki (project #18, 2026-10-18).

Footnote definitions are generated from the vault sources.md (itself generated from verified
PubMed records), so author/journal/year/PMID are never retyped. The body is report.md with
[S#] -> [^S#]; the findings section is the collapsible-by-tier block from
scripts/build_research_extras.py; the Start-here layer and the quiz are the agent-free drafts
in build/ (grounded in findings.md). Every [^S#] used is checked against the generated
definition set before writing.
"""
import re, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DOCS = ROOT / "docs"
sys.path.insert(0, str(ROOT / "scripts"))
from build_research_extras import build_findings_section, build_layer  # noqa: E402

VAULT = pathlib.Path("/Users/patrykwajs/orca/workspaces/PERSONAL/PERSONAL/Wiki/wiki/Health/Research/ginger")
REPORT_PATH = VAULT / "report.md"
FINDINGS_PATH = VAULT / "findings.md"
SOURCES_PATH = VAULT / "sources.md"
LAYER_PATH = BUILD / "ginger-layer-EN.md"
QUIZ_PATH = BUILD / "ginger-quiz-EN.json"
N_SOURCES = 228
N_FINDINGS = 46

report_raw = REPORT_PATH.read_text(encoding="utf-8")
findings_raw = FINDINGS_PATH.read_text(encoding="utf-8")
sources_raw = SOURCES_PATH.read_text(encoding="utf-8")
layer_draft = LAYER_PATH.read_text(encoding="utf-8")
quiz_json = QUIZ_PATH.read_text(encoding="utf-8")

# 1. report body: drop frontmatter, H1 and the vault blockquote line
body = re.sub(r"^---.*?---\s*", "", report_raw, flags=re.S)
body = re.sub(r"^#\s+[^\n]+\n+", "", body)
body = re.sub(r"^>\s*Full cited synthesis for.*?\n+", "", body, flags=re.M)
body = re.sub(r"(?<!\^)\[S(\d+)\]", r"[^S\1]", body)
body = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", body)
assert "[[" not in body and "Feeds:" not in body

# 2. findings: collapsible tier blocks
findings_section, n_find = build_findings_section(findings_raw)
assert n_find == N_FINDINGS, n_find

# 3. layer
layer_text = build_layer(layer_draft)

# 4. quiz validation + answer-key balance (lab lesson 14)
bank = json.loads(quiz_json)["questions"]
assert len(bank) == N_FINDINGS, len(bank)
for q in bank:
    assert len(q["options"]) == 4 and q["a"] in (0, 1, 2, 3), q["n"]
    for s in [q["q"], q["why"]] + q["options"]:
        assert "</" not in s and "&" not in s, q["n"]
# rebalance: move the correct option to a target slot cycling 0..3 (same four strings, deterministic)
for i, q in enumerate(bank):
    target = i % 4
    opts = list(q["options"]); correct = opts[q["a"]]
    opts.remove(correct); opts.insert(target, correct)
    q["options"] = opts; q["a"] = target
from collections import Counter
print("answer-key distribution:", dict(sorted(Counter(q["a"] for q in bank).items())))
quiz_json = json.dumps({"questions": bank}, ensure_ascii=False, indent=1)
QUIZ_PATH.write_text(quiz_json + "\n", encoding="utf-8")

# 5. footnote definitions from sources.md
pat = re.compile(r"\*\*\[S(\d+)\]\*\*\s+(.+?)\s+(\d{4}),\s+\*([^*]+)\*\s+-\s+\[(.*?)\]\(https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/\)")
source_dict = {}
for m in pat.finditer(sources_raw):
    num = int(m.group(1)); author = m.group(2).strip(); year = m.group(3); journal = m.group(4).strip()
    title = m.group(5).strip().rstrip("."); pmid = m.group(6)
    source_dict[num] = f"[^S{num}]: {author} {year}, *{journal}*. [PMID {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/). {title}."
assert len(source_dict) == N_SOURCES, f"parsed {len(source_dict)} sources"

temp = layer_text + "\n" + body + "\n" + findings_section
refs = sorted({int(x) for x in re.findall(r"\[\^S(\d+)\]", temp)})
undefined = [r for r in refs if r not in source_dict]
assert not undefined, undefined
print(f"referenced sources: {len(refs)} of {len(source_dict)}")
footnotes = "\n".join(source_dict[i] for i in refs)

header = """---
description: What ginger actually does versus what people think — 228 verified sources on pharmacokinetics, inflammation, nausea and gastric motility, pain and migraine, exercise recovery, cardiometabolic markers, male hormones and safety.
---

# Ginger: What It Actually Does vs What People Think

> A food-dose gut agent with a modest, timing-dependent antiemetic and analgesic record and no demonstrated systemic mechanism: free gingerols are undetectable in blood after 2 g of extract, 100- to 1,000-fold below the enzyme concentrations the "natural ibuprofen" story needs. About 1 g/day eases pregnancy nausea (not vomiting) and pre-loaded chemotherapy vomiting; pain and soreness effects are small; testosterone, fat-loss and blood-thinning claims have no controlled human evidence; heartburn is the one consistent cost.

*Literature reviewed to 18 October 2026. 228 sources, every identifier resolved against PubMed.*
"""

quiz_div = f"""## Test yourself

Twelve questions drawn at random from the findings above. Pick an answer, see why, and learn. Replayable, and your best score is remembered on this device.

<div class="rlw-quiz" data-count="12" data-lang="en" data-id="ginger" markdown="0">
<script type="application/json" class="rlw-quiz-data">
{quiz_json}
</script>
</div>
"""

full = (header.rstrip() + "\n\n" + layer_text.strip() + "\n\n" + body.strip() + "\n\n"
        + findings_section.strip() + "\n\n" + quiz_div.strip() + "\n\n" + footnotes.strip() + "\n")
out = DOCS / "ginger.md"
out.write_text(full, encoding="utf-8")
defs = {int(x) for x in re.findall(r"^\[\^S(\d+)\]:", full, re.M)}
used = {int(x) for x in re.findall(r"\[\^S(\d+)\](?!:)", full)}
print(f"wrote {out} ({len(full)} chars); defs={len(defs)} used={len(used)} undefined={sorted(used-defs)} unused={sorted(defs-used)}")
assert used <= defs and defs <= used
