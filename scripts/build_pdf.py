#!/usr/bin/env python3
"""Build illustrated, searchable, paginated PDF editions (does not publish a release)."""
from __future__ import annotations
import argparse
import html
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse, unquote
from pypdf import PdfReader
from weasyprint import HTML, default_url_fetcher

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/"book"
OUT=ROOT/"dist"
EDITIONS={
  "es":("De la caja negra a la evidencia","de-la-caja-negra-a-la-evidencia-es.pdf","Índice","Capítulo 37"),
  "en":("From Black Box to Evidence","from-black-box-to-evidence-en.pdf","Contents","Chapter 37"),
}
CSS=r"""
@page {size:A4;margin:18mm 17mm 20mm;
 @top-right {content:"JMFLORESZAZO · ARCHITECTING WHAT'S NEXT";font:8pt "DejaVu Sans";color:#777;}
 @bottom-right {content:counter(page) " / " counter(pages);font:8pt "DejaVu Sans";color:#777;}}
@page cover {size:A4;margin:0;@top-right{content:none;}@bottom-right{content:none;}}
html{font-family:"DejaVu Sans",sans-serif;font-size:9.3pt;line-height:1.48;color:#18191B}
body{margin:0}
.cover{page:cover;width:210mm;height:297mm;break-after:page}
.cover img{display:block;width:210mm;height:297mm;object-fit:contain}
#TOC{break-after:page}
#TOC::before{content:"CONTENTS / ÍNDICE";display:block;font-weight:700;font-size:17pt;margin:0 0 13mm}
#TOC ul{list-style:none;margin:0;padding:0 0 0 1.3em}
#TOC>ul{padding:0}
#TOC li{margin:3pt 0;line-height:1.33}
#TOC a{color:#333;text-decoration:none}
#TOC a::after{content:leader(".") target-counter(attr(href),page);color:#888;font-size:8pt}
h1,h2,h3,h4{font-family:"DejaVu Sans";color:#151719;line-height:1.22;break-after:avoid}
h1{font-size:26pt;margin:0 0 6mm}
h2{font-size:18pt;margin:12mm 0 5mm}
h3{font-size:13.8pt;margin:8mm 0 4mm}
h4{font-size:11pt;margin:6mm 0 3mm}
p,li{orphans:3;widows:3}
blockquote{border-left:3px solid #D9232E;margin:5mm 0;padding:2mm 4mm;background:#F7F7F5}
pre,code{font-family:"DejaVu Sans Mono",monospace;font-size:7.4pt}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#F4F4F3;padding:3mm;border:1px solid #E5E5E3}
code{overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;font-size:8pt;margin:4mm 0}
th{color:#17191B;background:#EEEFF0}
th,td{border:1px solid #CCCFD2;padding:2mm;vertical-align:top;overflow-wrap:anywhere}
tr{break-inside:avoid}
figure{margin:5mm 0;text-align:center;break-inside:avoid}
img{display:block;max-width:100%;height:auto;margin:3mm auto}
figcaption{font-size:8pt;color:#666}
a{color:#A71720;text-decoration:none;overflow-wrap:anywhere}
hr{border:0;border-top:1px solid #E0E1E2;margin:5mm 0}
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
    if len(headings)!=37:
        raise ValueError(f"{lang}: expected 37 chapters; found {len(headings)}")
    images=re.findall(rf"!\[[^]]*\]\((figures/{lang}/[^)]+\.png)\)",original)
    if len(images)!=41:
        raise ValueError(f"{lang}: expected 41 diagrams; found {len(images)}")
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
    html_doc=subprocess.run(
        ["pandoc","--from=gfm+raw_html","--to=html5","--standalone","--toc",
         "--toc-depth=3","--wrap=none"],
        input=md,text=True,capture_output=True,check=True).stdout
    body=re.search(r"<body[^>]*>(.*?)</body>",html_doc,re.S)
    if not body:raise ValueError("Pandoc produced no HTML body")
    markup=("<!doctype html><html lang='"+lang+"'><head><meta charset='utf-8'><title>"
            +html.escape(title)+"</title><style>"+CSS+"</style></head><body>"
            +"<section class='cover'><img src='../assets/cover-"+lang+".png' alt='"
            +html.escape(title)+"'></section>"+body.group(1)+"</body></html>")
    markup=markup.replace('content:"CONTENTS / ÍNDICE"','content:"'+toc.upper()+'"')
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/filename
    HTML(string=markup,base_url=str(BOOK),url_fetcher=offline_fetcher).write_pdf(str(target))
    reader=PdfReader(str(target))
    if len(reader.pages)<60:
        raise ValueError(f"{lang}: suspiciously short PDF: {len(reader.pages)} pages")
    all_text=" ".join(p.extract_text() or "" for p in reader.pages[1:])
    if final_chapter not in all_text:
        raise ValueError(f"{lang}: final chapter not present in extracted text")
    if target.stat().st_size<200000:
        raise ValueError(f"{lang}: PDF is unexpectedly small")
    print(f"{lang}: {len(reader.pages)} pages, {target.stat().st_size//1024} KiB → {target}")
    return target

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--lang",choices=["es","en","all"],default="all")
    args=p.parse_args()
    for lang in (EDITIONS if args.lang=="all" else [args.lang]):build(lang)

if __name__=="__main__":main()
