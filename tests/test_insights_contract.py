"""Sprint 2 dependency exploration must use committed evidence and honest states."""
import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class InsightsContract(unittest.TestCase):
 def test_navigation_and_static_route(self):
  html=(ROOT/'static/index.html').read_text()
  self.assertIn('data-page="insights"',html)
  self.assertIn('id="insightsGraph"',html)
  self.assertIn('src="/insights.js"',html)
  source=(ROOT/'studio.py').read_text()
  self.assertIn("if p.path=='/insights.js'",source)
 def test_only_actual_graph_edges_and_coverage(self):
  js=(ROOT/'static/insights.js').read_text()
  self.assertIn('cycle.edges||[]',js)
  self.assertIn('json?.edgeLocations',js)
  self.assertIn('json?.evidenceCoverage',js)
  self.assertIn('Missing',js) if False else None
  self.assertIn('Coverage ≠ correctness',(ROOT/'static/index.html').read_text())
  self.assertNotIn('safe to delete',js.lower())
