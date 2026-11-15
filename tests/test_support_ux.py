"""Regression contracts for truthful analysis actions and in-app assistance."""
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
class SupportUXTests(unittest.TestCase):
    def test_distinct_analysis_actions_and_help_pages(self):
        html=(ROOT/'static/index.html').read_text()
        for label in ('Scan duplications','Run code analysis','Help & user guide','About Repo Studio','Repository details and toolchain'):
            self.assertIn(label,html)
        for name in ('help','about','taskActivity','hoverHelp'):
            self.assertIn(f'id="{name}"',html)
        self.assertNotIn('>Run duplication audit</button>',html)
        self.assertNotIn('>Analyze Python</button>',html)
    def test_progress_is_pending_not_fake_percentage(self):
        source=(ROOT/'static/analysis.js').read_text()
        self.assertIn('performance.now()',source)
        self.assertIn("showTaskActivity('Analyzing committed Python",source)
        self.assertIn('finally{for(const [b,text,disabled]',source)
        duplication=(ROOT/'static/app.js').read_text()
        self.assertIn('Scanning duplicates…',duplication)
        self.assertIn("post('/api/audit'",duplication)
    def test_help_explains_different_units(self):
        html=(ROOT/'static/index.html').read_text()
        self.assertIn('different units',html)
        self.assertIn('characters ÷ 4',html)
        self.assertIn('does not execute project modules',html)
        self.assertIn('synthetic data',html)
    def test_served_routes(self):
        import sys
        sys.path.insert(0,str(ROOT))
        from studio import Handler
        for route,name,content_type in [('support.js','support.js','text/javascript; charset=utf-8'),('help-dashboard.png','help-dashboard.png','image/png'),('help-context.png','help-context.png','image/png')]:
            handler=Handler.__new__(Handler)
            handler.path='/'+route
            handler.headers={'Host':'127.0.0.1:8765'}
            handler.server=type('Server',(),{'server_port':8765,'state':object()})()
            handler.static=Mock()
            handler.do_GET()
            handler.static.assert_called_once_with(name,content_type)
            self.assertTrue((ROOT/'static'/name).exists())
if __name__=='__main__':unittest.main()
