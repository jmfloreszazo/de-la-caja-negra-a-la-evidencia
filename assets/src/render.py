import pathlib, re, sys
from playwright.sync_api import sync_playwright
A = pathlib.Path(__file__).resolve().parents[1]
jobs = [('mark.svg', 'mark-512.png', 1, '#00000000'), ('cover-es.svg', 'cover-es.png', 1, None), ('cover-en.svg', 'cover-en.png', 1, None),
        ('social-preview.svg', 'social-preview.png', 1, None)] + \
       [(f'logo-{l}-{t}.svg', f'logo-{l}-{t}.png', 1, None) for l in ('es', 'en') for t in ('light', 'dark')]
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args=['--no-sandbox'])
    for src, dst, scale, _ in jobs:
        svg = (A / src).read_text()
        w, h = map(int, re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups())
        pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=scale)
        bg = '#0B0D10' if 'dark' in src else 'transparent'
        pg.set_content(f'<html><body style="margin:0;background:{bg}">{svg}</body></html>')
        pg.screenshot(path=str(A / dst), omit_background=(bg == 'transparent'), clip={'x': 0, 'y': 0, 'width': w, 'height': h})
        pg.close()
    b.close()
print('rendered')
