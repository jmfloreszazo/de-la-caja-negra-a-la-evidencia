#!/usr/bin/env python3
"""One command to check the repository: links, Spanish/English sync and generated files.

    python3 scripts/check.py

1. Links: every relative Markdown link points to an existing file.
2. Sync: every page in book/es has its counterpart in book/en (through the language link at the top of the page)
   and both have the same sections, tables, listings, code blocks and their languages, figures,
   cited references and linked chapters. Prose is not compared: that is what reviews are for.
3. Generated: book/es.md and book/en.md are exactly what scripts/build.py produces from the chapters.
4. Figures: every diagram source exists in both languages and has its rendered image.
Exit code 0 when everything is in order.
"""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build

ROOT = build.ROOT
problems = []

# 1. Links -------------------------------------------------------------------
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
def prose(text):
    out, code = [], False
    for line in text.splitlines():
        if line.startswith('```'):
            code = not code
            continue
        if not code:
            out.append(line)
    return '\n'.join(out)

checked = 0
for md in sorted(ROOT.rglob('*.md')):
    if 'node_modules' in md.parts:
        continue
    for target in LINK.findall(prose(md.read_text(encoding='utf-8'))):
        if re.match(r'^[a-z]+:', target) or target.startswith('#'):
            continue
        path = (md.parent / target.split('#', 1)[0]).resolve()
        if ROOT not in path.parents and path != ROOT:
            continue  # GitHub UI link such as ../../discussions
        checked += 1
        if not path.exists():
            problems.append(f'broken link: {md.relative_to(ROOT)} -> {target}')
print(f'[1] links ......... {checked} relative links checked')

# 2. Spanish/English sync ----------------------------------------------------
BOOK = ROOT / 'book'
SKIP = {'README.md', 'diagramas.md', 'diagrams.md'}
def pages(lang):
    return sorted(p.resolve() for p in (BOOK / lang).rglob('*.md') if not (p.parent == BOOK / lang and p.name in SKIP))

def counterpart(path):
    m = re.search(r'\]\(([^)]+\.md)\)', path.read_text(encoding='utf-8').splitlines()[0])
    return (path.parent / m.group(1)).resolve() if m else None

def shape(path):
    text = path.read_text(encoding='utf-8')
    plain = prose(text)
    fences = re.findall(r'^```(\S*)', text, re.M)[::2]
    figures = re.findall(r'book/figures/(?:es|en)/([\w-]+)\.png|figures/(?:es|en)/([\w-]+)\.png', plain)
    figures = [a or b for a, b in figures]
    cites = set()
    for group in re.findall(r'\[(\d+(?:\s*[,–-]\s*\d+)*)\](?!\()', plain):
        cites.update(re.findall(r'\d+', group))
    chapters = sorted(set(re.findall(r'\]\([^)]*?/(\d\d)-[^)]*\.md', plain) +
                          re.findall(r'\]\((\d\d)-[^)]*\.md', plain)))
    annexes = sorted(set(re.findall(r'(?:anexo|annex)-([a-g])-', plain)))
    return {
        'sections': len(re.findall(r'^## ', plain, re.M)),
        'subsections': len(re.findall(r'^### ', plain, re.M)),
        'tables': len(re.findall(r'^\|[-| :]+\|$', plain, re.M)),
        'listings': len(re.findall(r'^\*\*(?:Listado|Listing) ', plain, re.M)),
        'code blocks': fences,
        'figures': figures,
        'references': sorted(cites, key=int),
        'linked chapters': chapters,
        'linked annexes': annexes,
    }

es_pages, en_pages = pages('es'), pages('en')
if len(es_pages) != len(en_pages):
    problems.append(f'page count differs: es={len(es_pages)} en={len(en_pages)}')
paired = set()
for es in es_pages:
    en = counterpart(es)
    rel = es.relative_to(ROOT)
    if en is None or not en.is_file():
        problems.append(f'no English counterpart: {rel}')
        continue
    if counterpart(en) != es:
        problems.append(f'language link does not point back: {en.relative_to(ROOT)}')
    paired.add(en)
    a, b = shape(es), shape(en)
    for key in a:
        if a[key] != b[key]:
            problems.append(f'out of sync ({key}): {rel} {a[key]} <-> {en.relative_to(ROOT)} {b[key]}')
for en in en_pages:
    if en not in paired:
        problems.append(f'no Spanish counterpart: {en.relative_to(ROOT)}')
print(f'[2] es/en sync .... {len(paired)} page pairs compared')

# 3. Generated single-page books --------------------------------------------
for lang in build.EDITIONS:
    path, text = build.render(lang)
    if not path.is_file() or path.read_text(encoding='utf-8') != text:
        problems.append(f'stale generated file: {path.relative_to(ROOT)} (run python3 scripts/build.py)')
print('[3] generated ..... book/es.md and book/en.md compared with a fresh build')

# 4. Figures ------------------------------------------------------------------
FIG = BOOK / 'figures'
src = {lang: {p.stem for p in (FIG / 'src' / lang).glob('*.mmd')} for lang in ('es', 'en')}
img = {lang: {p.stem for p in (FIG / lang).glob('*.png')} for lang in ('es', 'en')}
for ident in sorted(src['es'] ^ src['en']):
    problems.append(f'figure source in only one language: {ident}')
for lang in ('es', 'en'):
    for ident in sorted(src[lang] - img[lang]):
        problems.append(f'figure not rendered: book/figures/{lang}/{ident}.png (run python3 scripts/render_figures.py)')
    for ident in sorted(img[lang] - src[lang]):
        problems.append(f'image without source: book/figures/{lang}/{ident}.png')
print(f'[4] figures ....... {len(src["es"])} sources per language, each with its image')

print()
for p in problems:
    print('FAIL', p)
print('CHECK: FAIL' if problems else 'CHECK: PASS')
sys.exit(1 if problems else 0)
