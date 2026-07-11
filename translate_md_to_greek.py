#!/usr/bin/env python3
"""Translate the English MkDocs Markdown pages to Greek (docs/el/, greeklish slugs).

Markdown-aware: translates only prose (headings, paragraphs, list items, table cells,
admonition bodies + titles, frontmatter description). Keeps verbatim: footnote
DEFINITIONS (the references stay English), fenced code, table separators, HR rules,
and all inline tokens — footnote refs [^S#], markdown links, code spans, emoji
shortcodes, HTML entities, numbers/units, acronyms/chemicals, proper names, brand.
Single-pass placeholder protection (no nesting). Re-runnable.

Run: python3 translate_md_to_greek.py
"""
import os, re, json, pathlib
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
MODEL = "gpt-4o"

# EN file -> EL output (greeklish slug) + per-file link rewrites applied AFTER translation
PAGES = {
    "index.md":               ("el/index.md",                 {"](bpa-thermal-receipts.md)": "](bpa-thermikes-apodeixeis.md)",
                                                                "](methodology.md)": "](methodologia.md)",
                                                                "](collagen.md)": "](kollagono.md)",
                                                                "](testosterone.md)": "](testosteroni.md)"}),
    "testosterone.md":        ("el/testosteroni.md",          {"](bpa-thermal-receipts.md)": "](bpa-thermikes-apodeixeis.md)"}),
}

PROTECT_WORDS = ["Research Lab Wiki","GlyNAC","UC-II","Pro-Hyp","Hyp-Gly","GLP-1","MPS","SMD","BMD",
    "WOMAC","VISA-A","PINP","P1NP","CTX","NAC","DIAAS","PDCAAS","AMSTAR","GRADE","NMDA","CONSIST","ApoE",
    "Rousselot","Gelita","GELITA","TENDOFORTE","Nitta","Nippi","InterHealth","Myung","Park","Konig","König",
    "Liang","Oikawa","Yamadera","Sugaya","Grasset","Reynolds","Ravindran","Yuenyongviwat","Bischof","Sugihara",
    "BPAF","BPA","BPS","BPF","EFSA","FDA","ECHA","NHANES","NTP",
    "REACH","SVHC","TDI","HPG","DNA","CLARITY","SHBG","Pergafast","Biedermann","Tschudin","Grob",
    "Hormann","Ehrlich","Swan","Huberman","Varghese","Hall","Alharbi","Barakat","BfR","DOI","PMID",
    "JEG-Tox","EPIC-Norfolk","Th17","8-OHdG","NaN",
    "GAIT","mTORC1","Clegg","Aussieker","McKendry","Buchanan","Kumar","Hazen","Biswas","Hilser","Jerger","Lee SK",
    "Travison","Mazur","Corona","Leproult","Van Cauter","Pilz","Lerchbaum","Abu-Zaid","Prasad","Koehler","Morgado",
    "Fornalik","Lopresti","Leisegang","Neychev","Melville","Volek","Whittaker","Reed","Santi","Maldonado-Cárceles",
    "Krüger","Exton","Geniole","Hayes","Myerson","Neustadt","Senathirajah","Al-Dujaili","Jiang","Fui","Grossmann",
    "EMAS","MMAS","DEHP","PUFA","SFA","MUFA","DHEA","StAR","Withania","Eurycoma","Tribulus","Arjuna","Natural Ltd",
    "DHT","LH","FSH","OSA","CPAP","DINP","AGD","Caronia","Iranmanesh","Whirledge","Zueger","Friedl","Nattiv","Hackney",
    "van der Merwe","Merwe","Lak","Antonio","D'Andrea","Jorde","Naghii","Abbott","Chauhan","Pandit","Gonzales","Yakubu",
    "Radke","Henrotin","Meeker","Hamed","Levine","Skakkebaek","Skakkebæk","Travison","Bhasin","Nieschlag","Vorona",
    "Lokeshwar","Wittert","Cignarelli","Barrett-Connor","Lepidium","maca","shilajit","fadogia","Fadogia","boron"]
_WORD_ALT = '|'.join(re.escape(w) for w in sorted(PROTECT_WORDS, key=len, reverse=True))
# one left-to-right pass: footnote ref | md link | code span | emoji | entity | acronym | digit-token
COMBINED = re.compile(
    r'(\[\^[A-Za-z0-9]+\]|\[[^\]]*\]\([^)]*\)|`[^`]+`|:[a-z0-9_+-]+:|&[#A-Za-z0-9]+;|'
    + _WORD_ALT + r'|\S*\d\S*)')
L, R = '', ''

SYS = ("You are a professional EN→EL (Greek) translator for a scientific health-research website "
       "written in Markdown. Translate each given snippet into natural, fluent Greek. HARD RULES: "
       "(1) Some snippets contain placeholder tokens — a private-use bracket char, a number, a closing "
       "bracket char. Keep EVERY placeholder EXACTLY as written, in a natural position; never drop, "
       "translate, space-out, merge, or renumber them. (2) PRESERVE all Markdown formatting exactly: "
       "**bold**, *italic*, `code`. Do not add or remove markup. (3) Do NOT translate chemical names, "
       "acronyms, proper names, units, numbers, DOIs or URLs. (4) Keep the brand 'Research Lab Wiki' in "
       "Latin script. (5) Do not add, drop, or merge content. Return JSON {\"t\":[...]} with exactly the "
       "same number of strings, in order.")

def load_key():
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k
    try:                       # fall back to a local .env (not committed)
        for ln in open(ROOT / ".env"):
            if ln.startswith("OPENAI_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None

client = OpenAI(api_key=load_key())

def protect(text):
    store = []
    def stash(m):
        store.append(m.group(0)); return f'{L}{len(store)-1}{R}'
    return COMBINED.sub(stash, text), store

def restore(text, store):
    for i in range(len(store) - 1, -1, -1):
        text = text.replace(f'{L}{i}{R}', store[i])
    return text

def translate_batch(strings):
    if not strings:
        return []
    def call(items):
        r = client.chat.completions.create(model=MODEL, temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYS},
                      {"role": "user", "content": json.dumps({"strings": items}, ensure_ascii=False)}])
        o = json.loads(r.choices[0].message.content)
        return o.get("t") or o.get("translations") or o.get("strings")
    out = call(strings)
    if not isinstance(out, list) or len(out) != len(strings):
        out = []
        for s in strings:
            t = call([s]); out.append(t[0] if isinstance(t, list) and t else s)
    return out

# A line decomposes into (prefix_kept, translatable, suffix_kept) or None to keep verbatim.
RE_FOOTNOTE_DEF = re.compile(r'^\[\^[^\]]+\]:')
RE_HEADING      = re.compile(r'^(#{1,6}\s+)(.*)$')
RE_ADMON_TITLE  = re.compile(r'^(\s*(?:!!!|\?\?\?)\s+[\w-]+\s+")([^"]*)(".*)$')
RE_LIST         = re.compile(r'^(\s*(?:[-*+]|\d+\.)\s+)(.*)$')
RE_BLOCKQUOTE   = re.compile(r'^(>\s?)(.*)$')
RE_TABLE_SEP    = re.compile(r'^\s*\|[\s:\-|]+\|\s*$')
RE_TABLE_ROW    = re.compile(r'^\s*\|.*\|\s*$')

def translate_md(text):
    lines = text.split('\n')
    in_front = lines and lines[0].strip() == '---'
    front_end = -1
    if in_front:
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                front_end = i; break
    in_code = False
    # collect translatable pieces with a way to rebuild
    pieces = []          # list of dicts describing each line's plan
    to_send = []         # protected cores to translate
    send_map = []        # (piece_index, slot) -> position in to_send

    def add_send(core):
        prot, store = protect(core.strip())
        if not re.search(r'[A-Za-z]', re.sub(rf'{L}\d+{R}', '', prot)):
            return None  # nothing translatable
        lead = core[:len(core) - len(core.lstrip())]
        trail = core[len(core.rstrip()):]
        idx = len(to_send); to_send.append(prot.strip())
        return (idx, store, lead, trail)

    for i, line in enumerate(lines):
        if in_front and i <= front_end:
            m = re.match(r'^(description:\s*)(.+)$', line)
            if m:
                s = add_send(m.group(2))
                pieces.append({'k':'desc','pre':m.group(1),'s':s} if s else {'k':'raw','t':line})
            else:
                pieces.append({'k':'raw','t':line})
            continue
        if line.strip().startswith('```'):
            in_code = not in_code; pieces.append({'k':'raw','t':line}); continue
        if in_code or RE_FOOTNOTE_DEF.match(line) or RE_TABLE_SEP.match(line) \
           or line.strip() == '' or line.strip() == '---':
            pieces.append({'k':'raw','t':line}); continue
        m = RE_ADMON_TITLE.match(line)
        if m:
            s = add_send(m.group(2))
            pieces.append({'k':'wrap','pre':m.group(1),'suf':m.group(3),'s':s} if s else {'k':'raw','t':line}); continue
        m = RE_HEADING.match(line)
        if m:
            s = add_send(m.group(2)); pieces.append({'k':'wrap','pre':m.group(1),'suf':'','s':s} if s else {'k':'raw','t':line}); continue
        if RE_TABLE_ROW.match(line):
            cells = line.split('|')
            cellplan = []
            for c in cells:
                s = add_send(c) if c.strip() else None
                cellplan.append(('s', s) if s else ('raw', c))
            pieces.append({'k':'table','cells':cellplan}); continue
        m = RE_BLOCKQUOTE.match(line)
        if m:
            s = add_send(m.group(2)); pieces.append({'k':'wrap','pre':m.group(1),'suf':'','s':s} if s else {'k':'raw','t':line}); continue
        m = RE_LIST.match(line)
        if m:
            s = add_send(m.group(2)); pieces.append({'k':'wrap','pre':m.group(1),'suf':'','s':s} if s else {'k':'raw','t':line}); continue
        # plain paragraph line (may be indented admonition body)
        s = add_send(line)
        pieces.append({'k':'wrap','pre':'','suf':'','s':s} if s else {'k':'raw','t':line})

    translated = translate_batch(to_send)

    def render(s):
        idx, store, lead, trail = s
        return lead + restore(translated[idx], store) + trail

    out = []
    for p in pieces:
        if p['k'] == 'raw':
            out.append(p['t'])
        elif p['k'] == 'desc':
            out.append(p['pre'] + render(p['s']))
        elif p['k'] == 'wrap':
            out.append(p['pre'] + render(p['s']) + p['suf'])
        elif p['k'] == 'table':
            out.append('|'.join(render(s) if kind == 's' else s for kind, s in p['cells']))
    return '\n'.join(out)

def main():
    for en_rel, (el_rel, link_fixes) in PAGES.items():
        src = (DOCS / en_rel).read_text(encoding='utf-8')
        el = translate_md(src)
        for a, b in link_fixes.items():
            el = el.replace(a, b)
        out = DOCS / el_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(el, encoding='utf-8')
        en_ft = src.count('[^'); el_ft = el.count('[^')
        print(f"{en_rel:28s} -> {el_rel:34s} footnote-tokens EN={en_ft} EL={el_ft} {'OK' if en_ft==el_ft else 'CHECK'}")

if __name__ == "__main__":
    main()
