"""Regression checks for the F1.3 UI wiring and read-only evidence view."""
import pathlib, unittest
from html.parser import HTMLParser

ROOT=pathlib.Path(__file__).resolve().parents[1]

class Ids(HTMLParser):
    def __init__(self):super().__init__();self.ids=set()
    def handle_starttag(self, tag, attrs):
        for key,val in attrs:
            if key=='id':self.ids.add(val)

class CompareContract(unittest.TestCase):
    def test_comparison_controls_connected(self):
        html=(ROOT/'static/index.html').read_text()
        js=(ROOT/'static/compare.js').read_text()
        parser=Ids();parser.feed(html)
        needed={'compareWrap','compareWide','reviewImpact','impactResult','compareGrid','compareSync','compareScrollA','compareScrollB','compareLinesA','compareLinesB'}
        self.assertTrue(needed <= parser.ids,needed-parser.ids)
        for name in needed-{'compareLinesA','compareLinesB','compareScrollA','compareScrollB'}:
            self.assertIn(name,js)
        self.assertIn("'compareLines'+which",js)
        self.assertIn("'compareScroll'+suffix",js)
        self.assertIn('compare.js',html)
    def test_impact_report_is_read_only(self):
        js=(ROOT/'static/compare.js').read_text()
        self.assertNotIn("post('/api/",js)
        self.assertIn('No relationships returned',js)
        self.assertIn('manual review required',js)
        self.assertIn('contextDetails',js)

if __name__=='__main__': unittest.main()
