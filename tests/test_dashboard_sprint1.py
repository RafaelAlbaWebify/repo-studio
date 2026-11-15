import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]/'static'
class DashboardSprint1(unittest.TestCase):
 def test_intelligence_elements_present(self):
  html=(ROOT/'index.html').read_text()
  for ident in ('dashDonut','dashPriority','dashDuplicates','dashDupStatus','dashDistribution','dashHotspots'):
   self.assertIn(f'id="{ident}"',html)
 def test_no_unmeasured_combination_or_fake_severity(self):
  js=(ROOT/'dashboard.js').read_text()
  self.assertIn('if(h.unusedScanEligible)',js)
  self.assertIn('if(state.reportReady&&dupItems.length)',js)
  self.assertIn('Duplicate matches are a different unit', (ROOT/'index.html').read_text())
  self.assertNotIn("'High'",js)
 def test_clickable_drilldowns(self):
  js=(ROOT/'dashboard.js').read_text()
  for code in ("dashGo(r.type)","dashGo('complexity',x.file)","openFile(complex.file,complex.line)","dashReviewDup"):
   self.assertIn(code,js)
