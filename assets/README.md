# Brand assets

The visual identity of *From Black Box to Evidence* (*De la caja negra a la evidencia*), in the visual language of [jmfloreszazo.com](https://jmfloreszazo.com): networks of nodes and relations, and one single red accent that carries the meaning.

**Concept.** A black box made of a mesh of nodes is the legacy system. One red trace runs through it, leaves the box through its border and ends in a red seal with a check mark: the Oracle Gate. A rule extracted from the black box and verified with evidence.

| File | Use |
|---|---|
| `mark.svg` · `mark-512.png` | Symbol: avatar, favicon, small spaces |
| `logo-en-light.svg` · `logo-es-light.svg` | Logo on light backgrounds |
| `logo-en-dark.svg` · `logo-es-dark.svg` | Logo on dark backgrounds |
| `cover-en.png` · `cover-es.png` (and `.svg`) | Book cover, 1600 × 2400 |
| `social-preview.png` (and `.svg`) | GitHub social preview, 1280 × 640, bilingual |

| Colour | Hex | Role |
|---|---|---|
| Ink | `#0B0D10` | Background, the black box |
| Paper | `#F4F2EE` | Text on dark |
| Red | `#E0262B` | The only accent: the trace and the gate |
| Grey | `#9AA0A6` | Secondary text |
| Node / edge | `#59606B` · `#2B3038` | The mesh |

Typography: Noto Sans (Black, Bold, Regular, Light). All text in the SVG files is converted to paths, so they render the same everywhere without fonts.

## Regenerate

```bash
pip install fonttools playwright && playwright install chromium
python3 assets/src/make_brand.py   # writes the SVG files (needs the Noto Sans CJK fonts)
python3 assets/src/render.py       # exports the PNG files with Chromium
```

`render.py` uses a local Chromium path; change `executable_path` or remove it to use the one installed by Playwright.
