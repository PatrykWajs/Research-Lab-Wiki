# Research Lab Wiki

Independent, fully-cited research — investigations traced to peer-reviewed studies and official sources, weighed honestly, and closed with an evidence-graded verdict.

**Live:** https://patrykwajs.github.io/Research-Lab-Wiki/

- Static HTML, served by GitHub Pages (no build step).
- Each research lives in its own folder (`<slug>/index.html`) → a clean, extensionless URL.
- Unlisted: `noindex` (meta tag + `robots.txt`) — a public link, but not search-indexed.
- Citations point only to public, independently verifiable sources (DOIs / official agencies).
- Bilingual: every page has a Greek twin under `/el/`, with an EN ⟷ ΕΛ toggle in the header.
- Link previews: `og-cover.png` (Open Graph / Twitter card) on every page.

## Research

- **BPA in Thermal Receipts & Human Health** — `bpa-thermal-receipts/` — 25 cited studies; exposure route, health endpoints, BPS/BPF substitutes, EFSA-vs-FDA regulatory split, mitigation, evidence-graded verdict.
- **Methodology** — `methodology/` — the shared evidence-grade + confidence + verification key every research points back to.

## Adding a research

Create `<slug>/index.html` (copy an existing one), use **relative** asset paths (`../styles.css`, `../favicon.svg`), and add a card to the hub `index.html`. Then regenerate the build artifacts below.

## Build scripts

- **Bilingual mirror** — `python3 translate_site_to_greek.py` regenerates the Greek `/el/` mirror from the English pages (gpt-4o; reads `OPENAI_API_KEY` from the root or BUSINESS `.env`). It translates only human-readable text, protects numbers / units / citations / DOIs / acronyms / the brand, leaves the references list in English, fixes relative asset paths, and injects the EN ⟷ ΕΛ toggle. Re-runnable and idempotent on the English side.
- **Social card** — `python3 make_og.py` rebuilds `og-cover.png` (1200×630, clinical white/teal, reuses the flask logo).
