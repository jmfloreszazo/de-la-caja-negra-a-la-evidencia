#!/usr/bin/env python3
"""Regenerate the whole book on one page per language: book/es.md and book/en.md.

The chapters in book/es/ and book/en/ are the source of truth. Never edit book/es.md or book/en.md by hand:
change the chapters and run `python3 scripts/build.py`. `python3 scripts/check.py` fails if they are stale.
"""
import os, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOK = ROOT / 'book'
EDITIONS = {
    'es': dict(index='Índice', name='Español', other='English',
               title='De la caja negra a la evidencia',
               subtitle='Modernizar COBOL más allá de la traducción: agentes de IA, patrones de arquitectura, transacciones y oráculos verificables',
               note='Este fichero es el libro completo en una sola página. Se genera a partir de los capítulos de [`book/es/`](es/README.md) con `python3 scripts/build.py`: para proponer cambios, edita los capítulos, no este fichero.',
               lists=('## En esta parte', '## Contenido')),
    'en': dict(index='Contents', name='English', other='Español',
               title='From Black Box to Evidence',
               subtitle='Modernizing COBOL beyond translation: AI agents, architecture patterns, transactions and verifiable oracles',
               note='This file is the whole book on a single page. It is generated from the chapters in [`book/en/`](en/README.md) with `python3 scripts/build.py`: to propose changes, edit the chapters, not this file.',
               lists=('## In this part', '## Contents')),
}
LINK = re.compile(r'(!?)\[([^\]]*)\]\(([^)\s]+)\)')
HEADING = re.compile(r'^(#{1,6}) (.*)$')


def order(lang):
    readme = (BOOK / lang / 'README.md').read_text(encoding='utf-8')
    section = readme.split(f'## {EDITIONS[lang]["index"]}', 1)[1]
    return [(BOOK / lang / m).resolve() for m in re.findall(r'\]\(([^)]+\.md)\)', section)]


def unit_level(path, lang):
    rel = path.relative_to((BOOK / lang).resolve())
    return 2 if len(rel.parts) == 1 or rel.name == 'README.md' else 3


def gh_slug(text, seen):
    """GitHub heading anchor: lowercase, keep letters, digits, '_', '-' and spaces; spaces become '-'."""
    s = re.sub(r'[`*]', '', text).strip().lower()
    s = re.sub(r'[^\w\- ]', '', s).replace(' ', '-')
    n = seen.get(s, 0)
    seen[s] = n + 1
    return s if n == 0 else f'{s}-{n}'


def render(lang):
    """Return (output path, Markdown text) of the single-page edition for one language."""
    cfg, out_path = EDITIONS[lang], BOOK / f'{lang}.md'

    def relink(m, src):
        bang, text, target = m.groups()
        if re.match(r'^[a-z]+:', target) or target.startswith('#'):
            return m.group(0)
        path_part, _, frag = target.partition('#')
        resolved = (src.parent / path_part).resolve()
        if resolved.suffix == '.md' and (BOOK / lang).resolve() in resolved.parents:
            return f'{bang}[{text}](@@ANCHOR:{resolved}@@)'
        rel = os.path.relpath(resolved, out_path.parent).replace(os.sep, '/')
        return f'{bang}[{text}]({rel}{"#" + frag if frag else ""})'

    files, titles, body = order(lang), {}, []
    for f in files:
        level, out, code, skip = unit_level(f, lang), [], False, False
        for i, line in enumerate(f.read_text(encoding='utf-8').splitlines()):
            if line.startswith('```'):
                code = not code
            if not code:
                if i < 2 and line.startswith(('**Español**', '**English**', '[Español]')):
                    continue
                if line.startswith(('[← ', '[Índice]', '[Contents]')):
                    continue
                if line.strip() in cfg['lists']:
                    skip = True
                if skip:
                    continue
                h = HEADING.match(line)
                if h:
                    if len(h.group(1)) == 1:
                        titles[f] = h.group(2).strip()
                    line = '#' * (len(h.group(1)) + level - 1) + ' ' + h.group(2)
                line = LINK.sub(lambda mm: relink(mm, f), line)
            out.append(line)
        body.append(re.sub(r'\n---\s*$', '', '\n'.join(out).strip()).strip())
    other = 'en' if lang == 'es' else 'es'
    toc = [f'{"" if unit_level(f, lang) == 2 else "  "}- [{titles[f]}](@@ANCHOR:{f}@@)' for f in files]
    cover = f'<p align="center"><img src="../assets/cover-{lang}.png" alt="{cfg["title"]}" width="360"></p>'
    doc = '\n'.join([cover, '', f'# {cfg["title"]}', '', f'**{cfg["subtitle"]}**', '',
                     f'José María Flores Zazo · v2026.10.29 · **{cfg["name"]}** · [{cfg["other"]}]({other}.md)', '',
                     '> [!NOTE]', '> ' + cfg['note'], '', f'## {cfg["index"]}', '', *toc, '']) + '\n' + '\n\n'.join(body) + '\n'
    by_title, seen, anchors, code = {t: f for f, t in titles.items()}, {}, {}, False
    for line in doc.splitlines():
        if line.startswith('```'):
            code = not code
            continue
        h = None if code else HEADING.match(line)
        if h:
            slug = gh_slug(h.group(2), seen)
            f = by_title.get(h.group(2).strip())
            if f is not None and f not in anchors and len(h.group(1)) == unit_level(f, lang):
                anchors[f] = slug
    doc = re.sub(r'@@ANCHOR:([^@]+)@@', lambda m: '#' + anchors[pathlib.Path(m.group(1))], doc)
    return out_path, re.sub(r'\n{3,}', '\n\n', doc)


if __name__ == '__main__':
    for lang in EDITIONS:
        path, text = render(lang)
        path.write_text(text, encoding='utf-8')
        print(f'{path.relative_to(ROOT)}: {len(text.split())} words')
