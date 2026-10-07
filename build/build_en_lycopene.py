#!/usr/bin/env python3
"""Build docs/lycopene.md for Research-Lab-Wiki."""
import re, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
DOCS = ROOT / "docs"

# Source paths from Wiki
VAULT_RESEARCH = pathlib.Path("/Users/patrykwajs/Documents/PERSONAL/Wiki/wiki/Health/Research/lycopene")
REPORT_PATH = VAULT_RESEARCH / "report.md"
FINDINGS_PATH = VAULT_RESEARCH / "findings.md"
SOURCES_PATH = VAULT_RESEARCH / "sources.md"
LAYER_PATH = BUILD / "lycopene-layer-EN.md"
QUIZ_PATH = BUILD / "lycopene-quiz-EN.json"

# Read inputs
report_raw = REPORT_PATH.read_text(encoding="utf-8")
findings_raw = FINDINGS_PATH.read_text(encoding="utf-8")
sources_raw = SOURCES_PATH.read_text(encoding="utf-8")
layer_text = LAYER_PATH.read_text(encoding="utf-8")
quiz_json = QUIZ_PATH.read_text(encoding="utf-8")

# 1. Strip YAML frontmatter & top title from report.md
report_body = re.sub(r"^---.*?---\s*", "", report_raw, flags=re.S)
report_body = re.sub(r"^#\s+[^\n]+\n+", "", report_body)

# 2. Strip YAML frontmatter & top title from findings.md
findings_body = re.sub(r"^---.*?---\s*", "", findings_raw, flags=re.S)
findings_body = re.sub(r"^#\s+[^\n]+\n+", "", findings_body)
# Remove wiki Feeds: lines from findings
findings_body = re.sub(r"\nFeeds:\s*\[\[.*?\]\]\n*", "\n\n", findings_body)

# 3. Convert [S#] citations to [^S#] in report and findings
def convert_citations(text):
    # Avoid double conversion if already [^S#]
    return re.sub(r"(?<!\^)\[S(\d+)\]", r"[^S\1]", text)

report_body = convert_citations(report_body)
findings_body = convert_citations(findings_body)

# Clean wikilinks [[lycopene]] -> **lycopene** or standard text
def strip_wikilinks(text):
    return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)

report_body = strip_wikilinks(report_body)
findings_body = strip_wikilinks(findings_body)

# 4. Parse sources.md into clean footnote definitions
# Pattern: **[S#]** Author Year, *Journal* - [Title](https://pubmed.ncbi.nlm.nih.gov/PMID/) (PMID PMID)...
footnote_lines = []
source_pattern = r"\*\*\[S(\d+)\]\*\*\s+([^,\n]+)\s+(\d{4}),\s+\*([^*]+)\*\s+-\s+\[(.*?)\]\(https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/\)"

# Sort by numeric S index
source_dict = {}
for m in re.finditer(source_pattern, sources_raw):
    num = int(m.group(1))
    author = m.group(2).strip()
    year = m.group(3).strip()
    journal = m.group(4).strip()
    title = m.group(5).strip().rstrip(".")
    pmid = m.group(6).strip()
    source_dict[num] = f"[^S{num}]: {author} {year}, *{journal}*. [PMID {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/). {title}."

# Check for S130 if group author
if 130 not in source_dict:
    m130 = re.search(r"\*\*\[S130\]\*\*\s+(.*?)\s+(\d{4}),\s+\*([^*]+)\*\s+-\s+\[(.*?)\]\(https://pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/\)", sources_raw)
    if m130:
        author = m130.group(1).strip()
        year = m130.group(2).strip()
        journal = m130.group(3).strip()
        title = m130.group(4).strip().rstrip(".")
        pmid = m130.group(5).strip()
        source_dict[130] = f"[^S130]: {author} {year}, *{journal}*. [PMID {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/). {title}."

assert len(source_dict) == 133, f"Expected 133 sources, parsed {len(source_dict)}"

# Find all [^S#] referenced in body + layer + report + findings + quiz
temp_body = (
    layer_text.strip() + "\n\n" +
    report_body.strip() + "\n\n" +
    findings_body.strip()
)
referenced_ids = sorted(list(set(int(x) for x in re.findall(r"\[\^S(\d+)\]", temp_body))))
print(f"Referenced sources in lycopene page: {len(referenced_ids)} of {len(source_dict)}")

sorted_footnotes = [source_dict[i] for i in referenced_ids]
footnotes_text = "\n".join(sorted_footnotes)

# 5. Assemble docs/lycopene.md
header = """---
description: What lycopene actually does versus what people think — 133 verified sources on cutaneous photoprotection, pharmacokinetics, prostate oncology, cardiovascular hemodynamics, male andrology, and toxicology.
---

# Lycopene: What It Actually Does vs What People Think

> A potent lipophilic antioxidant and singlet oxygen quencher whose real dermatological win is burn flare mitigation, not sunburn prevention: oral intake produces zero increase in the visual MED threshold ($p > 0.05$), but blunts supra-threshold erythema intensity by 25% to 48% (real SPF ~1.3). It requires a strict 10-to-12-week pre-loading window, dietary fat for absorption, and does not boost testosterone or reverse prostate cancer.

*Literature reviewed to 7 October 2026. 133 sources, every identifier resolved against PubMed.*
"""

quiz_div = f"""## Test yourself

Twelve questions drawn at random from the findings above. Pick an answer, see why, and learn. Replayable, and your best score is remembered on this device.

<div class="rlw-quiz" data-count="12" data-lang="en" data-id="lycopene" markdown="0">
<script type="application/json" class="rlw-quiz-data">
{quiz_json}
</script>
</div>
"""

full_content = (
    header.rstrip() + "\n\n" +
    layer_text.strip() + "\n\n" +
    report_body.strip() + "\n\n" +
    "## Findings: Clinical Evidence & Mechanism Tiers\n\n" +
    findings_body.strip() + "\n\n" +
    quiz_div.strip() + "\n\n" +
    footnotes_text.strip() + "\n"
)

out_file = DOCS / "lycopene.md"
out_file.write_text(full_content, encoding="utf-8")
print(f"Wrote {out_file} ({len(full_content)} chars)")
