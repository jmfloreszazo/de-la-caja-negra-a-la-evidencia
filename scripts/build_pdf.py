#!/usr/bin/env python3
"""Build illustrated, searchable, paginated PDF editions (does not publish a release)."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse, unquote
from pypdf import PdfReader
from weasyprint import HTML, default_url_fetcher
from build import order
from pdf_markdown import (
    normalize_alerts, keep_listing_captions, keep_channel_figures,
    keep_book_figures, mark_book_openings,
)

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/"book"
OUT=ROOT/"dist"
AUTHOR="José María Flores Zazo"
EDITIONS={
  "es":("De la caja negra a la evidencia","de-la-caja-negra-a-la-evidencia-es.pdf","Índice","Capítulo 37"),
  "en":("From Black Box to Evidence","from-black-box-to-evidence-en.pdf","Contents","Chapter 37"),
}
CSS=r"""
@page {size:A4;margin:20mm 20mm 22mm;
 @top-right {content:"JMFLORESZAZO · ARCHITECTING WHAT'S NEXT";font:7pt "DejaVu Sans";color:#607286;}
 @bottom-right {content:counter(page) " / " counter(pages);font:8pt "DejaVu Sans";color:#607286;}}
@page :left {margin-left:18mm;margin-right:22mm}
@page :right {margin-left:22mm;margin-right:18mm}
@page cover {size:A4;margin:0;@top-right{content:none;}@bottom-right{content:none;}}
html{font-family:"DejaVu Serif",serif;font-size:10pt;line-height:1.52;color:#20354B}
body{margin:0}
.cover{page:cover;width:210mm;height:297mm;break-after:page}
.cover img{display:block;width:210mm;height:297mm;object-fit:contain}
#TOC{break-after:page}
#TOC{font-family:"DejaVu Sans",sans-serif}
#TOC::before{content:"CONTENTS / ÍNDICE";display:block;font-weight:700;font-size:20pt;color:#20354B;margin:0 0 10mm}
#TOC ul{list-style:none;margin:0;padding:0 0 0 1.3em}
#TOC>ul{padding:0}
#TOC li{margin:3pt 0;line-height:1.33}
#TOC a{color:#20354B;text-decoration:none}
#TOC a::after{content:leader(".") target-counter(attr(href),page);color:#607286;font-size:8pt}
h1,h2,h3,h4{font-family:"DejaVu Sans";color:#20354B;line-height:1.25;break-after:avoid}
h1{font-size:26pt;margin:0 0 6mm}
h2{font-size:18pt;margin:12mm 0 5mm}
h3{font-size:13.8pt;margin:8mm 0 4mm}
h4{font-size:11pt;margin:6mm 0 3mm}
.book-opening{break-before:page;margin-top:0}
.chapter-opening{font-size:20pt;border-top:3px solid #287F7A;padding-top:7mm;margin-bottom:8mm}
.part-opening{font-size:28pt;border-top:5px solid #C35B46;padding-top:30mm;margin-bottom:14mm;color:#20354B}
p,li{orphans:3;widows:3}
blockquote{font-family:"DejaVu Sans",sans-serif;font-size:9pt;border-left:3px solid #287F7A;margin:5mm 0;padding:3mm 4mm;background:#EAF4F1}
pre,code{font-family:"DejaVu Sans Mono",monospace;font-size:7.4pt}
pre{white-space:pre-wrap;overflow-wrap:anywhere;break-inside:avoid;background:#F3F6F8;padding:3mm;border:1px solid #CAD7DF;border-left:3px solid #287F7A}
.listing-caption{break-after:avoid}
div.sourceCode{break-inside:avoid}
code{overflow-wrap:anywhere}
table{font-family:"DejaVu Sans",sans-serif;border-collapse:collapse;width:100%;font-size:8pt;margin:4mm 0}
th{color:#20354B;background:#E4F2EF}
th,td{border:1px solid #CAD7DF;padding:2mm;vertical-align:top;overflow-wrap:anywhere}
tbody tr:nth-child(even){background:#F8FAFB}
tr{break-inside:avoid}
figure{margin:5mm 0;text-align:center;break-inside:avoid}
img{display:block;max-width:100%;height:auto;margin:3mm auto}
figure img{max-height:210mm;width:auto;object-fit:contain}
figcaption{font-family:"DejaVu Sans",sans-serif;font-size:8pt;line-height:1.4;color:#526577;text-align:left}
a{color:#216A73;text-decoration:none;overflow-wrap:anywhere}
hr{border:0;border-top:1px solid #CAD7DF;margin:5mm 0}
"""

def offline_fetcher(url):
    parsed=urlparse(url)
    if parsed.scheme!="file":
        raise ValueError(f"External PDF asset blocked: {url}")
    file=Path(unquote(parsed.path)).resolve()
    if not file.is_relative_to(ROOT.resolve()) or not file.is_file():
        raise FileNotFoundError(f"Invalid local PDF asset: {file}")
    return default_url_fetcher(url)

def build(lang):
    title,filename,toc,final_chapter=EDITIONS[lang]
    original=(BOOK/f"{lang}.md").read_text(encoding="utf-8")
    headings=re.findall(r"^### (?:Capítulo|Chapter) \d+",original,re.M)
    expected_chapters=sum(bool(re.search(r"^# (?:Capítulo|Chapter) \d+",path.read_text(encoding="utf-8"),re.M))
                          for path in order(lang))
    if not expected_chapters or len(headings)!=expected_chapters:
        raise ValueError(f"{lang}: expected {expected_chapters} indexed chapters; found {len(headings)}")
    images=re.findall(rf"!\[[^]]*\]\((figures/{lang}/[^)]+\.png)\)",original)
    # Every rendered source must be referenced exactly once: the diagram catalog is the inventory.
    expected_images=sorted(p.stem for p in (BOOK/"figures"/"src"/lang).glob("*.mmd"))
    if sorted(Path(p).stem for p in images)!=expected_images:
        raise ValueError(f"{lang}: book references {len(images)} diagrams but {len(expected_images)} sources exist")
    for p in images:
        if not (BOOK/p).is_file():
            raise FileNotFoundError(BOOK/p)
    cover=ROOT/"assets"/f"cover-{lang}.png"
    if not cover.is_file():
        raise FileNotFoundError(cover)
    # Replace the 360px GitHub cover with a full A4 title page.
    md=re.sub(r'^<p align="center"><img src="\.\./assets/cover-[a-z]+\.png"[^>]*></p>\s*',"",original,count=1)
    # Remove GitHub-specific TOC; Pandoc generates navigable links with correct page numbers.
    marker=f"## {toc}"
    start=md.find(marker)
    if start<0:raise ValueError(f"{lang}: source TOC is missing")
    nxt=re.search(r"^## [^\n]+",md[start+len(marker):],flags=re.M)
    if nxt is None:raise ValueError(f"{lang}: first section following TOC missing")
    md=md[:start]+md[start+len(marker)+nxt.start():]
    md=normalize_alerts(md)
    html_doc=subprocess.run(
        ["pandoc","--from=gfm+raw_html","--to=html5","--standalone","--toc",
         "--toc-depth=3","--wrap=none"],
        input=md,text=True,capture_output=True,check=True).stdout
    body=re.search(r"<body[^>]*>(.*?)</body>",html_doc,re.S)
    if not body:raise ValueError("Pandoc produced no HTML body")
    markup=("<!doctype html><html lang='"+lang+"'><head><meta charset='utf-8'><title>"
            +html.escape(title)+"</title><meta name='author' content='"+html.escape(AUTHOR,quote=True)
            +"'><style>"+CSS+"</style></head><body>"
            +"<section class='cover'><img src='../assets/cover-"+lang+".png' alt='"
            +html.escape(title)+"'></section>"+body.group(1)+"</body></html>")
    markup=markup.replace('content:"CONTENTS / ÍNDICE"','content:"'+toc.upper()+'"')
    markup=keep_listing_captions(markup)
    markup=keep_channel_figures(markup)
    markup=keep_book_figures(markup)
    markup=mark_book_openings(markup)
    if markup.count('<figure class="channel-figure">')!=6:
        raise ValueError(f"{lang}: expected six channel diagrams bound to their captions")
    if markup.count('<figure class=')!=len(images):
        raise ValueError(f"{lang}: every diagram must stay with its caption")
    figures=[]
    def mark_figure(match):
        ident=f"pdf-figure-{len(figures)+1}"
        figures.append(ident)
        return (match.group(0).replace("<img ",f'<img id="{ident}" ',1)
                .replace("</figcaption>",f'<span id="{ident}-end"></span></figcaption>',1))
    markup=re.sub(r'<figure class="(?:channel|book)-figure">.*?</figure>',mark_figure,markup,flags=re.S)
    openings=re.findall(r'<h[23]\b(?=[^>]*class="[^"]*\bbook-opening\b)[^>]*\bid="([^"]+)"[^>]*>',markup)
    if len(openings)!=len(order(lang)) or len(set(openings))!=len(openings):
        raise ValueError(f"{lang}: structural opening count does not match the chapter sources")
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/filename
    document=HTML(string=markup,base_url=str(BOOK),url_fetcher=offline_fetcher).render()
    starts=[]
    for number,page in enumerate(document.pages,1):
        for ident in openings:
            if ident in page.anchors:
                y=page.anchors[ident][1]
                if y>20*96/25.4+2:
                    raise ValueError(f"{lang}: {ident} does not start at the top of page {number}: y={y}")
                starts.append(dict(id=ident,page=number,topCssPixels=round(y,3)))
    if len(starts)!=len(openings) or len({item['page'] for item in starts})!=len(openings):
        raise ValueError(f"{lang}: each structural book unit must start on its own page")
    figure_pages=[]
    for ident,source in zip(figures,images,strict=True):
        image_pages=[number for number,page in enumerate(document.pages,1) if ident in page.anchors]
        caption_pages=[number for number,page in enumerate(document.pages,1) if f"{ident}-end" in page.anchors]
        if len(image_pages)!=1 or caption_pages!=image_pages:
            raise ValueError(f"{lang}: diagram and caption split across pages: {source}")
        figure_pages.append(dict(source=source,page=image_pages[0]))
    document.write_pdf(str(target))
    reader=PdfReader(str(target))
    if reader.metadata is None or reader.metadata.author!=AUTHOR:
        raise ValueError(f"{lang}: PDF author metadata is missing or incorrect")
    if len(reader.pages)<60:
        raise ValueError(f"{lang}: suspiciously short PDF: {len(reader.pages)} pages")
    all_text=" ".join(p.extract_text() or "" for p in reader.pages[1:])
    if final_chapter not in all_text:
        raise ValueError(f"{lang}: final chapter not present in extracted text")
    if target.stat().st_size<200000:
        raise ValueError(f"{lang}: PDF is unexpectedly small")
    target.with_suffix(".layout.json").write_text(
        json.dumps(dict(language=lang,pages=len(reader.pages),author=AUTHOR,
                        figuresWithCaptions=len(images),figurePages=figure_pages,unitOpenings=starts),indent=2)+"\n",
        encoding="utf-8",newline="\n")
    print(f"{lang}: {len(reader.pages)} pages, {target.stat().st_size//1024} KiB → {target}")
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--lang",choices=["es","en","all"],default="all")
    args=p.parse_args()
    for lang in (EDITIONS if args.lang=="all" else [args.lang]):build(lang)

if __name__=="__main__":main()
