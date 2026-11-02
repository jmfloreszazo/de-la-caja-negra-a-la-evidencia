"""Normalize GitHub-only alert syntax for the printed book, retaining prose."""
import re


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
