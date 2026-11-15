"""UI contracts for filtering and progressive rendering of code-health findings."""
import pathlib, unittest
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Parser(HTMLParser):
    def __init__(self): super().__init__(); self.ids=set()
    def handle_starttag(self,tag,attrs): self.ids.update(val for key,val in attrs if key=='id')
class TriageContract(unittest.TestCase):
    def test_controls_and_progressive_rendering(self):
        html=(ROOT/'static/index.html').read_text(); js=(ROOT/'static/analysis.js').read_text()
        p=Parser();p.feed(html)
        self.assertTrue({'analysisQuery','analysisType','analysisSort','analysisMore','analysisCount'} <= p.ids)
        for token in ('items.slice(0,healthVisible)', 'healthVisible+=60', "$('#analysisQuery').oninput", "$('#analysisSort').onchange"):
            self.assertIn(token,js)
        self.assertNotIn('items.slice(0,120)',js)
    def test_repository_switch_invalidates_displayed_findings(self):
        self.assertIn('resetHealthForRepoChange()', (ROOT/'static/app.js').read_text())
        self.assertIn('healthFindings=null', (ROOT/'static/analysis.js').read_text())
    def test_evidence_coverage_visible_in_ui(self):
        js=(ROOT/'static/analysis.js').read_text()
        self.assertIn('coverage.completeAnchors',js)
        self.assertIn('PARTIAL EVIDENCE',js)
if __name__=='__main__':unittest.main()
