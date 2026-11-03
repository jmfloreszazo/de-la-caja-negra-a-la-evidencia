"""Normalize GitHub-only alert syntax for the printed book, retaining prose."""
import re


def keep_listing_captions(html: str) -> str:
    """Give immediate ES/EN listing captions a keep-with-next print class."""
    pattern=(r'<p>(<strong>(?:Listing|Listado)\s(?:(?!</p>).)*</p>)'
             r'(?=\s*(?:<div\b[^>]*class="sourceCode"[^>]*>\s*)?<pre\b)')
    return re.sub(pattern,r'<p class="listing-caption">\1',html,flags=re.S)


def keep_channel_figures(html: str) -> str:
    """Keep a channel diagram and its immediate printed caption on one page."""
    pattern=(r'<p>(<img\b[^>]*src="figures/(?:en|es)/channels_[^"]+\.png"[^>]*>)</p>'
             r'\s*<p><em>((?:Figure|Figura)\s+C\.\d+\s+·(?:(?!</p>).)*)</em></p>')
    return re.sub(pattern,r'<figure class="channel-figure">\1<figcaption><em>\2</em></figcaption></figure>',
                  html,flags=re.S)


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
