# Visual identity · JMFLORESZAZO v5

This project uses the approved **dimensional black box → evidence trace → verification gate** as its primary artwork. Its **variant B** is the compact icon used immediately below the heading in both root READMEs, in avatars and in small spaces. The project's icon must never be mistaken for the author's personal trademark.

The primary mark, compact icons and horizontal lockups retain the [Version 5.0 design principles](https://jmfloreszazo.com/version-5-0-architecting-whats-next/): paper white (`#F7F7F5`), charcoal (`#121315`), neutral grey and a red accent (`#D9232E`).

The November 2026 book covers reuse the existing minimal variant B: a black silhouette and split gate with the red evidence exit, on paper white (`#F7F7F5`). The title is charcoal/red; there is no dimensional network illustration or coloured panel. Both languages retain José María Flores Zazo's authorship and show a November 2026 edition label. Interior diagrams retain their warm-paper, navy, teal and coral palette. The primary symbol, README icons and historical released covers are unchanged.

| Asset | Usage |
| --- | --- |
| `symbol-primary.svg` | Approved dimensional primary symbol (cube, network, red evidence trace, gate) |
| `mark.svg` / `icon-b-dark.svg` | Compact variant B icon in light / dark README themes |
| `mark-512.png` | Variant B avatar export |
| `cover-es.svg`, `cover-en.svg` and matching PNG | Spanish and English 1600 × 2400 book covers |
| `logo-{es,en}-{light,dark}.svg` and matching PNG | Horizontal book lockups |
| `social-preview.svg` and PNG | 1280 × 640 social media artwork |

## Regenerate without absolute font or browser paths

```bash
node assets/src/make_brand.mjs
python3 -m pip install cairosvg==2.9.1
python3 assets/src/render.py
node assets/src/make_brand.mjs --check
python3 assets/src/render.py --check
python3 assets/src/check_brand.py
```

For a cover-only change, use `python3 assets/src/render.py --only cover-es cover-en` and the matching `--check --only cover-es cover-en`. This avoids rewriting unrelated PNG exports in a different local font environment.

The SVG artwork is generated from a single deterministic file, `assets/src/make_brand.mjs`. PNG exports are derived and should never be edited separately. A browser is not necessary. Use SVG for GitHub previews so dark/light rendering remains crisp and a PNG export cannot inadvertently show an older design.

Typography explicitly uses DejaVu Sans. Install `fonts-dejavu-core` on Ubuntu before rendering, as the artwork workflow does; this avoids host-dependent Arial/Helvetica fallback. The source contains no proprietary font files. Byte-level PNG comparison requires the same CairoSVG, Cairo and font environment; a different renderer environment is not evidence of a design change.

The read-only CI check runs for all pull requests and for pushes affecting brand assets. It never writes a commit or modifies the target branch.
