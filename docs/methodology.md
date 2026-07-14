---
description: How Research Lab Wiki grades evidence, states confidence, and verifies every citation.
---

# Methodology

Every research here follows the same rules: cite each claim to a primary source, grade the strength of that source, state confidence honestly, and report facts and uncertainty rather than a tidy verdict. Findings are then **presented ranked by how strongly the evidence backs them** — settled, multi-study consensus first; single-study or contested claims last — so the reader can see at a glance how much weight each point deserves. This page is the shared key those reports point back to.

## Confidence levels

Each report states a confidence per question — and often a different confidence for different parts of the same question (exposure can be certain while disease causation is not).

| Level | What it means |
|---|---|
| **High** | Multiple independent studies agree, ideally with a controlled or quantified design (e.g. a glove-controlled exposure trial). Unlikely to reverse with new data. |
| **Moderate** | A real, consistent signal, but the evidence is mostly observational / cross-sectional, heterogeneous, or genuinely contested between experts. Direction is clearer than magnitude. |
| **Low–Moderate** | Plausible and mechanism-consistent, but not directly demonstrated for the specific claim — inferred from adjacent evidence. Treat as a hypothesis, not a fact. |

## Evidence grades

Every source in a bibliography carries one of these grades, so a reader can see at a glance how much weight a claim deserves.

| Grade | Source type | Weight |
|---|---|---|
| **Agency** | Official risk assessment or regulation (EFSA, US FDA, ECHA, NTP, EU law). | Highest for policy / exposure limits; agencies can still disagree — when they do, the report says so. |
| **Systematic review / meta-analysis** | Pooled, pre-registered synthesis across many primary studies. | Highest primary-evidence tier for an effect. |
| **Primary human** | Biomonitoring or controlled human-exposure study. | Strong for exposure; for disease, weaker if cross-sectional than if prospective. |
| **Secondary** | Narrative review, expert commentary, or expert testimony. | Context and corroboration, not a standalone fact. |
| **News** | Journalism. | Orientation only — never the sole support for a claim. |

## How each citation is verified

Automated "deep research" tools are useful for *finding* sources but can misfire when they try to self-verify. The flow used here treats their output as leads and checks every one by hand:

1. **Harvest leads.** Gather candidate claims and sources from searches — treat them as unverified.
2. **Verify against the primary source.** Open each study's DOI / PMID / agency page and confirm the exact number or quote before it is published. If it can't be confirmed, it is omitted — never guessed.
3. **Gap-fill.** Any thin part of the question gets fresh searches and primary reading, each new source cited.
4. **Grade and write.** Only then is the report written, with each claim tied to a graded source.

## The re-verification pass

Citations are not verified once and trusted forever. Every published report is periodically **re-read from its primary sources**, and this pass has its own hard rules — because automated tools and even careful notes make two specific, recurring mistakes.

1. **Every identifier is title-matched against the source database.** For each cited PMID, the live PubMed record is pulled and its title/author checked against what the report claims — because a study identifier can silently point to the *wrong paper* (a different study entirely). This has caught real errors: on one re-verification, two citations turned out to carry the ID of an unrelated paper, and were corrected.
2. **Every cited study is read from its own abstract**, not just the load-bearing few — so a number, a direction of effect, or a funding tie can be corrected against what the study actually reports.
3. **Corrections are shown, not hidden.** When re-verification changes something, the report carries a short **"What changed"** note listing every fix (a wrong identifier, a reversed finding, an author name), so the reader can see the correction rather than a silently-edited page.

The goal is that a claim's evidence is exactly as strong as it looks — and that when it isn't, the page says so.

!!! note "Standing rules"
    - **Never invent** a study, author, DOI, or number. Missing or unverifiable → it is left out, not filled in.
    - **Cite everything.** Every claim traces to a numbered source.
    - **Facts, not verdicts.** Contested points get the evidence on both sides and an explicit flag of what's genuinely uncertain — industry-funded and null results are weighed, not ignored, and an agency's press position never outranks the primary evidence.
    - **Literature-current date.** Each report stamps when its evidence was last checked; science moves, and old reports are re-verified before being relied on again.
