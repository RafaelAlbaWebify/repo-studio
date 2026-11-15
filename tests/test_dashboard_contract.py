"""Dashboard contracts: no fictional metrics, valid drilldowns and safe states."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'static'

class DashboardContract(unittest.TestCase):
    def test_overview_dashboard_and_scripts(self):
        html=(ROOT/'index.html').read_text()
        for name in ('intelligenceDashboard','dashPython','dashUnused','dashToolStates','dashDistribution','dashHotspots','dashboardScan'):
            self.assertIn(f'id="{name}"',html)
        self.assertIn('src="/dashboard.js"',html)
    def test_dashboard_js_route_is_served(self):
        # Unit-level HTTP routing regression: this route was omitted in the first RC.
        import sys
        from unittest.mock import Mock
        sys.path.insert(0,str(ROOT.parent))
        from studio import Handler
        h=Handler.__new__(Handler)
        h.headers={'Host':'127.0.0.1:8765'}
        h.server=type('Server',(),{'server_port':8765,'state':object()})()
        h.path='/dashboard.js'
        h.static=Mock()
        h.do_GET()
        h.static.assert_called_once_with('dashboard.js','text/javascript; charset=utf-8')
        self.assertTrue((ROOT/'dashboard.js').is_file())
    def test_missing_audits_are_not_zero(self):
        app=(ROOT/'app.js').read_text()
        self.assertIn("state.reportReady?dupItems.length.toLocaleString():'Not analyzed'",app)
        dash=(ROOT/'dashboard.js').read_text()
        self.assertIn("'Not configured'",dash)
        self.assertIn("'Not eligible · no conclusion'",dash)
        self.assertIn("dashGo('complexity',x.file)",dash)

if __name__=='__main__':unittest.main()
