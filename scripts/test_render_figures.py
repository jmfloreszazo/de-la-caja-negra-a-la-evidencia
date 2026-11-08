"""Protect the light editorial palette and the shared diagram preparation."""
import json
import re
import unittest

import check_figure_provenance
import render_figures


def luminance(colour):
    channels = [int(colour[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
              for value in channels]
    return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


class FigureThemeTests(unittest.TestCase):
    def test_light_palette_has_readable_text_contrast(self):
        palette = json.loads(render_figures.THEME.read_text(encoding="utf-8"))["themeVariables"]
        self.assertFalse(palette["darkMode"])
        self.assertGreater(luminance(palette["background"]), 0.9)
        pairs = [
            ("primaryTextColor", "primaryColor"), ("secondaryTextColor", "secondaryColor"),
            ("tertiaryTextColor", "tertiaryColor"), ("textColor", "background"),
            ("actorTextColor", "actorBkg"), ("noteTextColor", "noteBkgColor"),
            ("labelTextColor", "labelBoxBkgColor"), ("stateLabelColor", "stateBkg"),
        ] + [(f"gitBranchLabel{index}", f"git{index}") for index in range(4)]
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                values = sorted((luminance(palette[foreground]), luminance(palette[background])))
                self.assertGreaterEqual((values[1] + 0.05) / (values[0] + 0.05), 4.5)

    def test_flowchart_accents_come_from_the_shared_palette(self):
        prepared = render_figures.prepare("flowchart TB\nowner --> base\n", "agent_chain")
        self.assertIn(f"fill:{render_figures.ACCENT_BG}", prepared)
        self.assertIn(f"stroke:{render_figures.ACCENT}", prepared)
        self.assertIn(f"color:{render_figures.TEXT}", prepared)
        self.assertNotIn("#0B0D10", prepared)

    def test_c4_nodes_and_relations_use_dark_text_on_light_fills(self):
        source = 'C4Container\nPerson(owner, "Owner")\nContainer(gov, "Baseline", "Policy")\nRel(owner, gov, "Approves")'
        prepared = render_figures.prepare(source, "c4_containers")
        self.assertIn(f'UpdateElementStyle(owner, $fontColor="{render_figures.TEXT}")', prepared)
        self.assertIn(f'UpdateElementStyle(gov, $bgColor="{render_figures.ACCENT_BG}"', prepared)
        self.assertIn(f'$textColor="{render_figures.TEXT}"', prepared)
        self.assertIn(f'$lineColor="{render_figures.LINE}"', prepared)

    def test_fingerprint_revision_matches_the_provenance_guard(self):
        self.assertEqual(render_figures.VERSION.encode(), check_figure_provenance.VERSION)

    def test_architecture_layout_preserves_elements_and_relationships(self):
        elements = {"owner", "policy", "legacy", "disc", "golden", "research", "exp",
                    "gov", "build", "transition", "verify", "release"}
        relationships = {
            ("owner", "disc"), ("policy", "disc"), ("legacy", "golden"),
            ("legacy", "research"), ("disc", "exp"), ("golden", "exp"),
            ("research", "exp"), ("exp", "gov"), ("owner", "gov"),
            ("gov", "build"), ("build", "transition"), ("legacy", "transition"),
            ("transition", "verify"), ("build", "verify"), ("gov", "verify"),
            ("golden", "verify"), ("verify", "release"), ("owner", "release"),
        }
        for language in ("en", "es"):
            with self.subTest(language=language):
                source = (render_figures.FIG / "src" / language / "c4_containers.mmd").read_text(encoding="utf-8")
                self.assertEqual(set(re.findall(r"^\s*(\w+)[(\[]", source, re.M)), elements)
                self.assertEqual(set(re.findall(r'(\w+) -->\|"[^"]+"\| (\w+)', source)), relationships)


if __name__ == "__main__":
    unittest.main()
