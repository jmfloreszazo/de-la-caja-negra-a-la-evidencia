# Visual identity · JMFLORESZAZO v5

This project uses the approved **dimensional black box → evidence trace → verification gate** as its primary artwork. Its **variant B** is the compact icon used immediately below the heading in both root READMEs, in avatars and in small spaces. The project's icon must never be mistaken for the author's personal trademark.

The primary mark, compact icons and horizontal lockups retain the [Version 5.0 design principles](https://jmfloreszazo.com/version-5-0-architecting-whats-next/): paper white (`#F7F7F5`), charcoal (`#121315`), neutral grey and a red accent (`#D9232E`).

The book covers and interior diagrams use a lighter editorial treatment: warm paper (`#FBF8F3`), navy text (`#20354B`), teal (`#287F7A`), pale blue/green surfaces and coral (`#C35B46`) for the evidence trace. The dimensional box/gate motif, author and edition identifier are preserved. This cover treatment does not replace the author's primary mark or the README's compact icons.

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

Typography uses the browser's Arial/Helvetica fallback, rather than a machine-specific font path. The source contains no proprietary font files.

The read-only CI check runs for all pull requests and for pushes affecting brand assets. It never writes a commit or modifies the target branch.
