"""Prepare book pagination and captions without changing the manuscript."""
from html import unescape
import re


def keep_listing_captions(html: str) -> str:
    """Give immediate ES/EN listing captions a keep-with-next print class."""
    pattern=(r'<p>(<strong>(?:Listing|Listado)\s(?:(?!</p>).)*</p>)'
             r'(?=\s*(?:<div\b[^>]*class="sourceCode"[^>]*>\s*)?<pre\b)')
    return re.sub(pattern,r'<p class="listing-caption">\1',html,flags=re.S)


def keep_channel_figures(html: str) -> str:
    """Keep a channel diagram and its immediate printed caption on one page."""
    return _keep_figures(html, r'channels_[^"]+', "channel-figure")


def keep_book_figures(html: str) -> str:
    """Keep every book diagram with its immediate caption, not only channels."""
    return _keep_figures(html, r'[^"]+', "book-figure")


def _keep_figures(html: str, filename: str, class_name: str) -> str:
    pattern=(rf'<p>(<img\b[^>]*src="figures/(?:en|es)/{filename}\.png"[^>]*>)</p>'
             r'\s*<p><em>((?:Figure|Figura)\s+(?:(?!</p>).)*)</em></p>')
    return re.sub(pattern, rf'<figure class="{class_name}">\1<figcaption><em>\2</em></figcaption></figure>',
                  html, flags=re.S)


def mark_book_openings(html: str) -> str:
    """Mark structural book units, leaving internal section headings alone."""
    def mark(match):
        level, attributes, content = match.groups()
        title = unescape(re.sub(r"<[^>]+>", "", content)).strip()
        chapter = re.match(
            r"^(?:(?:Chapter|Capítulo)\s+\d|Companion chapter\b|Capítulo complementario\b|(?:Annex|Anexo)\s+[A-Z]\b)",
            title,
        )
        if level != "2" and not chapter:
            return match.group(0)
        if re.search(r'\bclass="[^"]*\bbook-opening\b', attributes):
            return match.group(0)
        kind = "part-opening" if re.match(r"^(?:Part|Parte)\s+[IVX]+\b|^(?:Annexes|Anexos)$", title) else "chapter-opening"
        classes = f"book-opening {kind}"
        if re.search(r'\bclass="', attributes):
            attributes = re.sub(r'\bclass="', f'class="{classes} ', attributes, count=1)
        else:
            attributes += f' class="{classes}"'
        return f"<h{level}{attributes}>{content}</h{level}>"
    return re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", mark, html, flags=re.S)


def normalize_alerts(markdown: str) -> str:
    lines = []
    fence = None
    for line in markdown.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            run = marker.group(1)
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence):
                fence = None
            lines.append(line)
            continue
        if fence is None:
            # Keep the blockquote and thesis/warning prose; remove only the
            # standalone GitHub control line Pandoc otherwise prints literally.
            line = re.sub(r"^(>\s*)\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*(\r?\n)?$",
                          lambda m: ">" + (m.group(2) or ""), line)
        lines.append(line)
    return "".join(lines)
