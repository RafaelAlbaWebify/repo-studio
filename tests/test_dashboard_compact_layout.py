import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'static'

class DashboardCompactLayout(unittest.TestCase):
    def test_compact_overview_controls_present(self):
        html = (ROOT / 'index.html').read_text()
        for ident in ('lastAnalysis', 'toolchainSummary', 'dashboardScan'):
            self.assertIn(f'id="{ident}"', html)
        self.assertIn('Repository details and toolchain', html)
        self.assertIn('overview-command-bar', html)

if __name__ == '__main__':
    unittest.main()
