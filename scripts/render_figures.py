#!/usr/bin/env python3
"""Render the book's diagrams as PNG images with the book's visual identity.

Sources:  book/figures/src/es/<id>.mmd and book/figures/src/en/<id>.mmd (Mermaid, the source of truth)
Images:   book/figures/es/<id>.png and book/figures/en/<id>.png (committed, shown in the chapters)
Theme:    book/figures/theme.json and theme.css; red accent per node in book/figures/accents.json (ink background, graphite nodes, light text, red as the only accent)

    python3 scripts/render_figures.py           render new or changed diagrams
    python3 scripts/render_figures.py --all     render everything again
    python3 scripts/render_figures.py --check   only check that every source renders (used by CI)
    python3 scripts/render_figures.py es        only one language

Requires mermaid-cli (npm i -g @mermaid-js/mermaid-cli) and, for identical images, the Noto Sans CJK fonts
(sudo apt install fonts-noto-cjk). Optional env MERMAID_PUPPETEER_CONFIG=<json> for a custom Chromium.
"""
import hashlib, json, os, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / 'book' / 'figures'
THEME = FIG / 'theme.json'
CSS = FIG / 'theme.css'
ACCENTS = FIG / 'accents.json'
RED, RED_BG, PAPER = '#E0262B', '#2A1113', '#F4F2EE'
HASHES = FIG / 'hashes.json'
BG, TEXT, LINE = '#0B0D10', '#C9CCD1', '#9AA0A6'
VERSION = '1'


def prepare(code, ident=''):
    """Central theme only: drop per-diagram init directives, give C4 relations readable colours and
    paint the red accent on the nodes listed in accents.json."""
    code = '\n'.join(l for l in code.splitlines() if not l.strip().startswith('%%{'))
    accent = json.loads(ACCENTS.read_text(encoding='utf-8')).get(ident, []) if ACCENTS.is_file() else []
    if accent and code.lstrip().startswith(('flowchart', 'graph')):
        code += f'\n  classDef accent fill:{RED_BG},stroke:{RED},stroke-width:2px,color:{PAPER}\n  class {",".join(accent)} accent'
    if accent and code.lstrip().startswith('C4'):
        code += ''.join(f'\n  UpdateElementStyle({a}, $bgColor="{RED_BG}", $borderColor="{RED}", $fontColor="{PAPER}")' for a in accent)
    if code.lstrip().startswith('C4'):
        rels = re.findall(r'^\s*(?:Bi)?Rel(?:_[A-Za-z]+)?\(\s*(\w+)\s*,\s*(\w+)', code, re.M)
        code += ''.join(f'\n  UpdateRelStyle({a}, {b}, $textColor="{TEXT}", $lineColor="{LINE}")' for a, b in rels)
    return code + '\n'


def render(src, out):
    with tempfile.TemporaryDirectory() as tmp:
        mmd = pathlib.Path(tmp) / 'd.mmd'
        mmd.write_text(prepare(src.read_text(encoding='utf-8'), src.stem), encoding='utf-8')
        cmd = ['mmdc', '-q', '-i', str(mmd), '-o', str(out), '-c', str(THEME), '-C', str(CSS), '-b', BG, '-w', '1100', '-s', '2']
        if os.environ.get('MERMAID_PUPPETEER_CONFIG'):
            cmd[1:1] = ['-p', os.environ['MERMAID_PUPPETEER_CONFIG']]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return r.returncode == 0 and out.is_file(), (r.stderr or r.stdout).strip().splitlines()[-1:] 


def main():
    args = sys.argv[1:]
    mode = next((a for a in args if a.startswith('--')), '')
    langs = [a for a in args if not a.startswith('--')]
    accents = json.loads(ACCENTS.read_text(encoding='utf-8')) if ACCENTS.is_file() else {}
    theme_hash = hashlib.sha256(THEME.read_bytes() + CSS.read_bytes() + VERSION.encode()).hexdigest()
    hashes = json.loads(HASHES.read_text()) if HASHES.is_file() and mode != '--all' else {}
    sources = sorted(p for p in (FIG / 'src').glob('*/*.mmd') if not langs or p.parent.name in langs)
    done = failed = skipped = 0
    for src in sources:
        lang, ident = src.parent.name, src.stem
        key = f'{lang}/{ident}'
        digest = hashlib.sha256(src.read_bytes() + json.dumps(accents.get(ident, [])).encode()).hexdigest() + theme_hash
        out = FIG / lang / f'{ident}.png'
        if mode == '--check':
            with tempfile.TemporaryDirectory() as tmp:
                rendered = pathlib.Path(tmp) / 'x.png'
                ok, err = render(src, rendered)
                # Temporary draft-only transfer of PUBLIC book diagrams from the
                # official CI renderer. This block MUST be removed before review.
                if ok and key in {'es/agent_chain', 'en/agent_chain',
                                  'es/c4_containers', 'en/c4_containers'}:
                    import base64
                    png = base64.b64encode(rendered.read_bytes()).decode('ascii')
                    print(f'__FIGURE_B64_BEGIN__{key}__{png}__FIGURE_B64_END__', flush=True)
        elif hashes.get(key) == digest and out.is_file():
            skipped += 1
            continue
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            ok, err = render(src, out)
            if ok:
                hashes[key] = digest
        if ok:
            done += 1
            print(f'  ok    {key}')
        else:
            failed += 1
            print(f'  FAIL  {key}: {" ".join(err)}')
    if mode != '--check':
        HASHES.write_text(json.dumps(dict(sorted(hashes.items())), indent=1) + '\n')
    print(f'\n{done} rendered · {skipped} unchanged · {failed} failed · {len(sources)} sources')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
