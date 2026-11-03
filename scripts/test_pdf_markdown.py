"""Protect book prose and executable examples while hiding print-only noise."""
import unittest

from pdf_markdown import normalize_alerts, keep_listing_captions


class PdfMarkdownTests(unittest.TestCase):
    def test_immediate_listing_caption_stays_with_unchanged_code(self):
        for label in ('Listing','Listado'):
            source='<p><strong>'+label+' 12.2 · Math.Round</strong> — <em>Illustrative</em></p>\n<pre><code>x &lt; 2;</code></pre>'
            expected=source.replace('<p>','<p class="listing-caption">',1)
            self.assertEqual(keep_listing_captions(source),expected)

    def test_unrelated_or_separated_paragraph_is_not_reclassified(self):
        for source in (
            '<p><strong>Note</strong></p>\n<pre><code>x</code></pre>',
            '<p><strong>Listing 1</strong></p><p>Context</p><pre><code>x</code></pre>',
            '<p>Listing 1 is discussed here.</p><pre><code>x</code></pre>',
        ):
            self.assertEqual(keep_listing_captions(source),source)

    def test_pandoc_highlight_wrapper_is_kept_with_its_caption(self):
        source='<p><strong>Listing 1</strong> — <em>Illustrative</em></p>\n<div class="sourceCode" id="cb1"><pre\nclass="sourceCode csharp"><code>x</code></pre></div>'
        self.assertEqual(keep_listing_captions(source),
                         source.replace('<p>','<p class="listing-caption">',1))

    def test_alert_control_is_hidden_but_thesis_and_blockquote_remain(self):
        source = "> [!IMPORTANT]\n> **Chapter thesis.** Preserve this argument.\n"
        self.assertEqual(normalize_alerts(source),
                         ">\n> **Chapter thesis.** Preserve this argument.\n")

    def test_marker_in_fenced_code_or_inline_prose_is_preserved(self):
        for fence in ("```text", "~~~~text"):
            source = fence + "\n> [!WARNING]\n" + fence.rstrip("text") + "\n"
            self.assertEqual(normalize_alerts(source), source)
        source = "The literal token `[!NOTE]` belongs to this explanation.\n"
        self.assertEqual(normalize_alerts(source), source)

    def test_all_book_alert_types_and_line_endings(self):
        for kind in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"):
            self.assertEqual(normalize_alerts("> [!" + kind + "]\r\n> Text\r\n"),
                             ">\r\n> Text\r\n")


if __name__ == "__main__":
    unittest.main()
