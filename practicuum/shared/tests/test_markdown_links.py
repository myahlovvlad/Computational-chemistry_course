from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
from validate_course import markdown_references


class MarkdownLinkTests(unittest.TestCase):
    def test_smarts_in_code_is_not_a_link_but_real_link_survives(self):
        text='[source](data.json)\n\n```python\nrule="[C:1](=[O:2])[O:3]"\n```\n\n[broken](missing.json)\n'
        self.assertEqual(markdown_references(text),['data.json','missing.json'])

    def test_inline_smarts_is_not_link(self):
        self.assertEqual(markdown_references('`[C](=[O])` and [source](real.md)'),['real.md'])
