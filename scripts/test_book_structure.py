"""Check that new book units cannot disappear from the generated reading order."""
import unittest

import build


class BookStructureTests(unittest.TestCase):
    def test_index_covers_every_source_unit_once(self):
        for language in build.EDITIONS:
            root = build.BOOK / language
            source = {p.resolve() for p in root.rglob('*.md')
                      if not (p.parent == root and p.name in {'README.md', 'diagrams.md', 'diagramas.md'})}
            ordered = build.order(language)
            with self.subTest(language=language):
                self.assertEqual(len(ordered), len(set(ordered)))
                self.assertEqual(set(ordered), source)

    def test_tooling_chapter_follows_method_and_final_annex_is_last(self):
        for language in build.EDITIONS:
            names = [path.name for path in build.order(language)]
            method = next(i for i, name in enumerate(names) if name.startswith('10-'))
            self.assertTrue(names[method + 1].startswith('10a-'))
            self.assertTrue(names[method + 2].startswith('11-'))
            self.assertTrue(names[-1].startswith('annex-h-' if language == 'en' else 'anexo-h-'))


if __name__ == '__main__':
    unittest.main()
