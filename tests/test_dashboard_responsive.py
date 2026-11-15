import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "static"

class DashboardResponsiveContract(unittest.TestCase):
    def test_minimal_overview_without_duplicate_hero(self):
        html = (ROOT / "index.html").read_text()
        self.assertEqual(html.count('id="intelligenceDashboard"'), 1)
        self.assertEqual(html.count('id="dashboardScan"'), 1)
        self.assertNotIn('overview-hero', html)
        self.assertIn('Repository details and toolchain', html)
        self.assertIn('Local · Read-only', html)
    def test_layout_breakpoints_and_focus(self):
        css = (ROOT / "style.css").read_text()
        self.assertIn('@media (max-width:1080px)', css)
        self.assertIn('@media (max-height:700px)', css)
        self.assertIn(':focus-visible', css)

if __name__ == "__main__":
    unittest.main()
