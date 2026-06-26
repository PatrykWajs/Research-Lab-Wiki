# Research Lab Wiki

Independent, fully-cited research — investigations traced to peer-reviewed studies and official sources, weighed honestly, and closed with an evidence-graded verdict.

**Live:** https://patrykwajs.github.io/Research-Lab-Wiki/

- Static HTML, served by GitHub Pages (no build step).
- Each research lives in its own folder (`<slug>/index.html`) → a clean, extensionless URL.
- Unlisted: `noindex` (meta tag + `robots.txt`) — a public link, but not search-indexed.
- Citations point only to public, independently verifiable sources (DOIs / official agencies).

## Research

- **BPA in Thermal Receipts & Human Health** — `bpa-thermal-receipts/` — 25 cited studies; exposure route, health endpoints, BPS/BPF substitutes, EFSA-vs-FDA regulatory split, mitigation, evidence-graded verdict.
- **Methodology** — `methodology/` — the shared evidence-grade + confidence + verification key every research points back to.

## Adding a research

Create `<slug>/index.html` (copy an existing one), use **relative** asset paths (`../styles.css`, `../favicon.svg`), and add a card to the hub `index.html`.
