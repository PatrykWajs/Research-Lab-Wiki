#!/usr/bin/env python3
"""Assemble the public-page "extras" for a Research-Lab-Wiki page and splice them into
the English Markdown page:

  1. a "## Start here" learning layer  (Bottom line + Myths-vs-reality + What you learn + What this means for you)
  2. a "## The full findings — all N" collapsible section (grouped by evidence tier)
  3. a "## Test yourself" wildcard quiz  (rlw-quiz engine, inline JSON, one question per finding)

Inputs (all local, nothing invented here — the layer + quiz are produced upstream by agents):
  - findings.md  : the vault findings file  Wiki/wiki/Research/<slug>/findings.md
  - layer draft  : a markdown file with sections  ## THE ONE THING / ## MYTHS VS REALITY /
                   ## WHAT YOU ACTUALLY LEARN / ## WHAT THIS MEANS FOR YOU
  - quiz JSON    : {"questions":[{tier,q,options[4],a,why}, ...]}  (one per finding)

Greek is produced separately by translating these same three blocks with
translate_md_to_greek.T.translate_md + the quiz-string protect/restore, then splicing
into el/<greeklish>.md at the same anchors (see build_research_extras_el()).

Usage:
  python3 scripts/build_research_extras.py <slug> --findings F.md --layer L.md --quiz Q.json
Anchors (must exist in docs/<slug>.md): the first '!!! abstract' admonition (layer goes
before it) and the first '[^S#]:' footnote definition (findings+quiz go before it).
"""
import re, json, argparse, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

EN_QUIZ_INTRO = ("Twelve questions drawn at random from the findings above. Pick an answer, "
                 "see why, and learn. Replayable, and your best score is remembered on this device.")


def clean_finding(text):
    text = re.sub(r'\s*Feeds:.*$', '', text.strip())      # drop Feeds: trailer
    text = re.sub(r'\s*\[\^?S\d+\]', '', text)            # drop [S#] / [^S#] source tags
    text = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', text)  # unwrap [[wikilinks]]
    text = re.sub(r'\s+([;:,.])', r'\1', text)
    return re.sub(r'[ \t]{2,}', ' ', text).strip()


def build_findings_section(findings_md):
    src = findings_md.split("## Wiki Links", 1)[0]
    tiers, cur, pend = [], None, None
    for ln in src.split("\n"):
        h = re.match(r'^##\s+(.*)$', ln)
        if h:
            lab = h.group(1).strip()
            if lab.lower().startswith("practical"):
                lab = "Practical — what to actually do"
            cur = {"label": lab, "items": []}; tiers.append(cur); pend = None; continue
        t = re.match(r'^\*\*(\d+)\.\s+(.*?)\*\*\s*$', ln)
        if t and cur is not None:
            cur["items"].append([int(t.group(1)), t.group(2).strip(), ""]); pend = True; continue
        if pend and cur and ln.strip():
            cur["items"][-1][2] += (" " if cur["items"][-1][2] else "") + ln.strip()
    total = sum(len(t["items"]) for t in tiers)
    out = [f"## The full findings — all {total}\n",
           "Every conclusion this review reached, grouped by how strongly the evidence backs it. "
           "Each finding is distilled from the fully-cited evidence above.\n"]
    for t in tiers:
        out.append(f'??? note "{t["label"]} ({len(t["items"])} findings)"\n')
        for num, title, txt in t["items"]:
            out.append(f"    **{num}. {clean_finding(title)}**\n")
            out.append(f"    {clean_finding(txt)}\n")
        out.append("")
    sec = "\n".join(out).rstrip() + "\n"
    assert not re.search(r'\[S\d+\]|Feeds:|\[\[', sec), "leftover vault tags in findings section"
    return sec, total


def _section(draft, name):
    m = re.search(r'^##\s+' + re.escape(name) + r'\s*$(.*?)(?=^##\s+|\Z)', draft, re.M | re.S)
    return m.group(1).strip() if m else ""


def build_layer(layer_draft):
    one = re.sub(r'\s+', ' ', _section(layer_draft, "THE ONE THING")).strip()
    myths = _section(layer_draft, "MYTHS VS REALITY")
    learn = _section(layer_draft, "WHAT YOU ACTUALLY LEARN")
    means = _section(layer_draft, "WHAT THIS MEANS FOR YOU")
    assert one and "|" in myths and learn.startswith("-") and means.strip().startswith("-"), "layer parse failed"
    means_indented = "\n".join(("    " + l if l.strip() else "") for l in means.split("\n"))
    return ("## Start here\n\n"
            f'!!! quote "Bottom line"\n    **{one}**\n\n'
            "**Myths vs. reality**\n\n"
            f"{myths}\n\n"
            "**What you actually learn**\n\n"
            f"{learn}\n\n"
            '!!! tip "What this means for you"\n'
            f"{means_indented}\n")


def build_quiz(slug, quiz_json, lang="en", intro=EN_QUIZ_INTRO):
    head = "## Test yourself" if lang == "en" else "## Δοκίμασε τον εαυτό σου"
    dataid = slug if lang == "en" else f"{slug}-el"
    return (f"{head}\n\n{intro}\n\n"
            f'<div class="rlw-quiz" data-count="12" data-lang="{lang}" data-id="{dataid}" markdown="0">\n'
            '<script type="application/json" class="rlw-quiz-data">\n'
            + quiz_json.strip() + '\n</script>\n</div>\n')


def splice_en(slug, layer, findings, quiz):
    p = DOCS / f"{slug}.md"
    md = p.read_text(encoding="utf-8")
    assert md.count('!!! abstract') >= 1, "no abstract admonition anchor"
    md = re.sub(r'(?m)^!!! abstract', layer + "\n\n!!! abstract", md, count=1)
    m = re.search(r'^\[\^S\d+\]:', md, re.M); assert m, "no footnote-definition anchor"
    md = md[:m.start()] + findings + "\n\n" + quiz + "\n" + md[m.start():]
    p.write_text(md, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--findings", required=True)
    ap.add_argument("--layer", required=True)
    ap.add_argument("--quiz", required=True)
    a = ap.parse_args()
    findings_md = pathlib.Path(a.findings).read_text(encoding="utf-8")
    layer_draft = pathlib.Path(a.layer).read_text(encoding="utf-8")
    quiz_json = pathlib.Path(a.quiz).read_text(encoding="utf-8")
    layer = build_layer(layer_draft)
    findings, n = build_findings_section(findings_md)
    quiz = build_quiz(a.slug, quiz_json, "en")
    splice_en(a.slug, layer, findings, quiz)
    print(f"{a.slug}: spliced Start-here layer + {n} findings + quiz into docs/{a.slug}.md")


if __name__ == "__main__":
    main()
