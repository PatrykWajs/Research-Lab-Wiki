# Research Lab Wiki

Independent, fully-cited research, published with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

**Live:** https://patrykwajs.github.io/Research-Lab-Wiki/

- Source lives on `main` (this branch); the built site deploys to the `gh-pages` branch via `mkdocs gh-deploy`.
- Bilingual — **English + Ελληνικά** (greeklish `/el/` slugs); switch with the language selector in the header.
- Unlisted: `noindex` (meta tag + `robots.txt`) — a public link, but not search-indexed.
- Citations are native Markdown footnotes pointing to public DOIs / official sources.

## Build & deploy

```bash
python3 -m mkdocs serve                # local preview at http://127.0.0.1:8000
python3 -m mkdocs build                # build into site/
python3 -m mkdocs gh-deploy --force    # build + push to gh-pages (deploy)
```

## Build scripts

- `OPENAI_API_KEY=… python3 translate_md_to_greek.py` — regenerate the Greek `docs/el/` pages from the English Markdown (gpt-4o). Translates prose only; keeps numbers, citations, DOIs, the references list and the brand verbatim.
- `python3 make_og.py` — rebuild `docs/assets/og-cover.png` (1200×630 social-share card).

## Adding a research

Create `docs/<slug>.md` (English) + `docs/el/<greeklish-slug>.md` (Greek), list both under `nav` in `mkdocs.yml`, then `mkdocs gh-deploy --force`.
