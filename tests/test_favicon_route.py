import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class FaviconRouteContract(unittest.TestCase):
    def test_favicon_declared_and_served(self):
        html = (ROOT / "static/index.html").read_text()
        server = (ROOT / "studio.py").read_text()
        icon = ROOT / "static/favicon.svg"
        self.assertIn('rel="icon" type="image/svg+xml" href="/favicon.svg"', html)
        self.assertIn("if p.path=='/favicon.svg':return self.static('favicon.svg','image/svg+xml; charset=utf-8')", server)
        self.assertTrue(icon.is_file())
        self.assertIn('<svg ', icon.read_text())

if __name__ == '__main__':
    unittest.main()
