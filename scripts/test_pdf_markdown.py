"""Protect book prose and executable examples while hiding print-only noise."""
import unittest

from pdf_markdown import normalize_alerts


class PdfMarkdownTests(unittest.TestCase):
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
