"""Brand assets for 'De la caja negra a la evidencia / From Black Box to Evidence'.

Visual language taken from jmfloreszazo.com: networks of nodes and delegation relations, one single red accent
that carries the meaning, bilingual pieces and the uppercase JMFLORESZAZO wordmark.
Concept: a black box made of a mesh of nodes (the legacy system) and one red path that leaves it and breaks
its border as a check mark (a rule extracted and verified: from black box to evidence).
All text is converted to vector paths so the SVG files render identically everywhere.
"""
import pathlib, random
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = pathlib.Path(__file__).resolve().parents[1]
OUT.mkdir(exist_ok=True)
INK, PAPER, RED, GREY, NODE, EDGE, MUTED = '#0B0D10', '#F4F2EE', '#E0262B', '#9AA0A6', '#59606B', '#2B3038', '#C9CCD1'
N = '/usr/share/fonts/opentype/noto/'


class Font:
    def __init__(self, path):
        self.f = TTFont(path, fontNumber=0, lazy=True)
        self.gs, self.cmap = self.f.getGlyphSet(), self.f.getBestCmap()
        self.upm, self.hmtx = self.f['head'].unitsPerEm, self.f['hmtx']

    def width(self, text, size, track=0):
        return sum(self.hmtx[self.cmap[ord(c)]][0] * size / self.upm + track for c in text) - (track if text else 0)

    def path(self, text, size, x, y, track=0, anchor='start'):
        x -= {'start': 0, 'middle': self.width(text, size, track) / 2, 'end': self.width(text, size, track)}[anchor]
        s, out = size / self.upm, []
        for c in text:
            g = self.cmap[ord(c)]
            pen = SVGPathPen(self.gs)
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
            out.append(pen.getCommands())
            x += self.hmtx[g][0] * s + track
        return ' '.join(out)


BLACK, BOLD, REG, LIGHT = (Font(N + f'NotoSansCJK-{w}.ttc') for w in ('Black', 'Bold', 'Regular', 'Light'))


def txt(font, text, size, x, y, fill, track=0, anchor='start'):
    return f'<path d="{font.path(text, size, x, y, track, anchor)}" fill="{fill}"/>'


def mesh(x0, y0, size, n, seed, node_r, edge_w, node_col, edge_col, red_cells, red_col, red_w, exit_to):
    """A square mesh of jittered nodes; red_cells is the path (list of (i, j)) that ends leaving the box."""
    rnd, step = random.Random(seed), size / (n - 1)
    pts = {(i, j): (x0 + i * step + (rnd.uniform(-.18, .18) * step if 0 < i < n - 1 else 0),
                    y0 + j * step + (rnd.uniform(-.18, .18) * step if 0 < j < n - 1 else 0))
           for i in range(n) for j in range(n)}
    edges = []
    for (i, j), (x, y) in pts.items():
        for di, dj, p in ((1, 0, .62), (0, 1, .62), (1, 1, .22), (1, -1, .14)):
            q = (i + di, j + dj)
            if q in pts and rnd.random() < p:
                edges.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{pts[q][0]:.1f}" y2="{pts[q][1]:.1f}"/>')
    svg = [f'<g stroke="{edge_col}" stroke-width="{edge_w}" stroke-linecap="round">{"".join(edges)}</g>',
           f'<g fill="{node_col}">' + ''.join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{node_r}"/>' for x, y in pts.values()) + '</g>']
    route = [pts[c] for c in red_cells] + exit_to
    d = 'M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in route)
    svg.append(f'<path d="{d}" fill="none" stroke="{red_col}" stroke-width="{red_w}" stroke-linecap="round" stroke-linejoin="round"/>')
    svg.append(f'<g fill="{red_col}">' + ''.join(f'<circle cx="{pts[c][0]:.1f}" cy="{pts[c][1]:.1f}" r="{node_r * 1.9}"/>' for c in red_cells) + '</g>')
    return ''.join(svg)


def badge(cx, cy, r, ring=None):
    """The Oracle Gate: a red seal with a check mark."""
    ring_svg = f'<circle cx="{cx}" cy="{cy}" r="{r * 1.18}" fill="{ring}"/>' if ring else ''
    w = r * .2
    d = f'M{cx - r * .45:.1f} {cy + r * .02:.1f} L{cx - r * .12:.1f} {cy + r * .36:.1f} L{cx + r * .5:.1f} {cy - r * .34:.1f}'
    return ring_svg + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{RED}"/><path d="{d}" fill="none" stroke="{PAPER}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'


def mark(x, y, s, dark_bg=False, ring=None):
    """The symbol in a box of side s at (x, y): black box, node mesh, red path breaking out as a check mark."""
    box = INK if not dark_bg else '#14171C'
    border = '' if not dark_bg else f' stroke="{EDGE}" stroke-width="{s * .012}"'
    inner = s * .62
    ix, iy = x + s * .12, y + s * .19
    bx, by, br = x + s, y + s * .5, s * .2
    return (f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * .12}" fill="{box}"{border}/>' +
            mesh(ix, iy, inner, 5, 7, s * .016, s * .008, NODE, EDGE, [(0, 1), (1, 2), (2, 1), (3, 2), (4, 2)], RED, s * .045,
                 [(bx - br, by)]) +
            badge(bx, by, br, ring or (box if not dark_bg else INK)))


def svg_doc(w, h, body, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ''
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{rect}{body}</svg>'


def write(name, svg):
    (OUT / name).write_text(svg, encoding='utf-8')
    return name


files = []
# 1. Symbol (square, transparent) -----------------------------------------
files.append(write('mark.svg', svg_doc(512, 512, mark(22, 66, 380))))

# 2. Horizontal lockups, light and dark, both languages --------------------
TITLES = {'es': ('DE LA CAJA NEGRA', 'A LA EVIDENCIA'), 'en': ('FROM BLACK BOX', 'TO EVIDENCE')}
for lang, (l1, l2) in TITLES.items():
    for theme, fg, sub, bg in (('light', INK, '#5F6670', None), ('dark', PAPER, GREY, None)):
        w1 = max(BLACK.width(l1, 92, 1), BLACK.width(l2, 92, 1))
        W = int(372 + w1 + 40)
        body = (mark(24, 30, 250, dark_bg=(theme == 'dark')) +
                txt(BLACK, l1, 92, 362, 132, fg, 1) + txt(BLACK, l2, 92, 362, 232, RED, 1) +
                txt(BOLD, 'by JMFLORESZAZO', 26, 366, 284, sub, 5))
        files.append(write(f'logo-{lang}-{theme}.svg', svg_doc(W, 310, body, bg)))

# 3. Covers (portrait 1600 x 2400), both languages -------------------------
COVER = {
    'es': ('De la caja negra', 'a la evidencia', 'Modernizar COBOL más allá de la traducción',
           ['Agentes de IA · patrones de arquitectura', 'transacciones · oráculos verificables'], 'Edición v2026.10.29'),
    'en': ('From Black Box', 'to Evidence', 'Modernizing COBOL beyond translation',
           ['AI agents · architecture patterns', 'transactions · verifiable oracles'], 'Edition v2026.10.29'),
}
for lang, (t1, t2, subtitle, tags, edition) in COVER.items():
    W, H = 1600, 2400
    trace = [(0, 4), (1, 5), (2, 5), (3, 6), (4, 6), (5, 5), (6, 6), (7, 7), (8, 6), (9, 6), (10, 6), (11, 6), (12, 6)]
    box = mesh(200, 330, 1000, 13, 11, 6.5, 2.4, NODE, EDGE, trace, RED, 15, [(1236, 830), (1300, 830)])
    body = (f'<rect x="150" y="280" width="1100" height="1100" rx="40" fill="none" stroke="{EDGE}" stroke-width="4"/>' +
            f'<rect x="1240" y="800" width="20" height="60" fill="{INK}"/>' + box + badge(1360, 830, 92, INK) +
            txt(BOLD, 'PASS', 30, 1360, 975, RED, 6, 'middle') +
            txt(BOLD, 'JMFLORESZAZO  ·  ARCHITECTING WHAT’S NEXT', 30, 800, 160, GREY, 7, 'middle') +
            txt(BLACK, t1, 136, 150, 1640, PAPER, 0) + txt(BLACK, t2, 136, 150, 1790, RED, 0) +
            txt(LIGHT, subtitle, 54, 154, 1900, MUTED) +
            ''.join(txt(REG, t, 38, 154, 1990 + k * 56, GREY) for k, t in enumerate(tags)) +
            f'<line x1="150" y1="2190" x2="1450" y2="2190" stroke="{EDGE}" stroke-width="3"/>' +
            txt(BOLD, 'JOSÉ MARÍA FLORES ZAZO', 44, 150, 2270, PAPER, 6) +
            txt(REG, edition, 32, 1450, 2270, GREY, 2, 'end'))
    files.append(write(f'cover-{lang}.svg', svg_doc(W, H, body, INK)))

# 4. Social preview for GitHub (1280 x 640), bilingual ----------------------
W, H = 1280, 640
bg_mesh = mesh(780, 70, 520, 9, 21, 4, 1.6, '#3A4048', '#1E2228', [], RED, 0, [])
bg_mesh = bg_mesh.rsplit('<path', 1)[0]  # background mesh without red path
body = (bg_mesh + mark(56, 185, 270, dark_bg=True) +
        txt(BLACK, 'De la caja negra a la evidencia', 50, 440, 268, PAPER) +
        txt(BLACK, 'From Black Box to Evidence', 50, 440, 336, RED) +
        txt(LIGHT, 'Modernizar COBOL más allá de la traducción', 27, 442, 400, MUTED) +
        txt(LIGHT, 'Modernizing COBOL beyond translation', 27, 442, 440, MUTED) +
        txt(BOLD, 'JOSÉ MARÍA FLORES ZAZO  ·  JMFLORESZAZO.COM', 21, 442, 530, GREY, 4) +
        txt(REG, 'Open book ES · EN  —  runnable lab: GnuCOBOL · .NET 10 · Podman', 21, 442, 568, '#6F7680', 1))
files.append(write('social-preview.svg', svg_doc(W, H, body, INK)))
print('\n'.join(files))
