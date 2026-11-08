"""Protect book prose and executable examples while hiding print-only noise."""
import unittest

from pdf_markdown import (
    normalize_alerts, keep_listing_captions, keep_channel_figures,
    keep_book_figures, mark_book_openings,
)


class PdfMarkdownTests(unittest.TestCase):
    def test_book_units_start_new_pages_in_both_languages(self):
        titles = [
            (2, "Part I · Before translating", "part-opening"),
            (2, "Parte IV · Patrones", "part-opening"),
            (2, "Annexes", "part-opening"),
            (2, "Anexos", "part-opening"),
            (2, "Prologue", "chapter-opening"),
            (2, "Epílogo", "chapter-opening"),
            (3, "Chapter 25 bis · Infrastructure", "chapter-opening"),
            (3, "Capítulo 25 bis · Infraestructura", "chapter-opening"),
            (3, "Companion chapter · Channels", "chapter-opening"),
            (3, "Capítulo complementario · Canales", "chapter-opening"),
            (3, "Annex G · Sources", "chapter-opening"),
            (3, "Annex H · Beyond COBOL", "chapter-opening"),
            (3, "Anexo H · Más allá de COBOL", "chapter-opening"),
            (3, "Chapter 10 bis · Models and ADRs", "chapter-opening"),
            (3, "Anexo A · Laboratorio", "chapter-opening"),
        ]
        for level, title, kind in titles:
            with self.subTest(title=title):
                source = f'<h{level} id="unit" class="existing">{title}</h{level}>'
                rendered = mark_book_openings(source)
                self.assertIn(f'class="book-opening {kind} existing"', rendered)
                self.assertIn('id="unit"', rendered)
                self.assertIn(title, rendered)
                self.assertEqual(mark_book_openings(rendered), rendered)

    def test_internal_sections_and_printed_heading_examples_stay_unchanged(self):
        source = ('<h3 id="authorship">Authorship and responsibility</h3>'
                  '<h4 id="example">Chapter 1 is an example</h4>'
                  '<pre><code>&lt;h2&gt;Example&lt;/h2&gt;</code></pre>')
        self.assertEqual(mark_book_openings(source), source)

    def test_all_diagram_families_keep_their_captions(self):
        for lang, label in (("en", "Figure"), ("es", "Figura")):
            for name in ("agent_chain", "c4_containers", "channels_cash_happy"):
                image = f'<img src="figures/{lang}/{name}.png" alt="Example" />'
                source = f'<p>{image}</p>\n<p><em>{label} 11.1 · Meaning.</em></p>'
                rendered = keep_book_figures(keep_channel_figures(source))
                self.assertEqual(rendered.count("<figure "), 1)
                self.assertIn(image, rendered)
                self.assertIn(f"<figcaption><em>{label} 11.1 · Meaning.</em></figcaption>", rendered)
                self.assertEqual(keep_book_figures(rendered), rendered)
                separated = source.replace("</p>\n<p>", "</p><p>Context</p><p>", 1)
                self.assertEqual(keep_book_figures(separated), separated)

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

    def test_channel_diagram_caption_is_bound_without_changing_image_or_text(self):
        for lang,label in [('en','Figure'),('es','Figura')]:
            image=f'<img src="figures/{lang}/channels_cash_happy.png" alt="Cash" />'
            caption=label+' C.3 · Cash &amp; ledger.'
            source='<p>'+image+'</p>\n<p><em>'+caption+'</em></p>'
            rendered=keep_channel_figures(source)
            self.assertEqual(rendered.count('<figure class="channel-figure">'),1)
            self.assertIn(image,rendered)
            self.assertIn('<figcaption><em>'+caption+'</em></figcaption>',rendered)
            self.assertEqual(keep_channel_figures(rendered),rendered)
            separated=source.replace('</p>\n<p>','</p>\n<p>Context</p>\n<p>',1)
            self.assertEqual(keep_channel_figures(separated),separated)
            unrelated=source.replace('channels_cash_happy','bank_faults')
            self.assertEqual(keep_channel_figures(unrelated),unrelated)

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
