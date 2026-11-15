"""Static guards for frontend lifecycle wiring; not a substitute for real Chromium QA."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'static'


class WorkspaceUIIntegration(unittest.TestCase):
    def test_history_refreshes_after_repository_load(self):
        app = (ROOT / 'app.js').read_text()
        self.assertIn("if(typeof wsLoadHistory==='function')void wsLoadHistory();", app)
        self.assertIn("if(typeof wsRefresh==='function')void wsRefresh();", app)

    def test_programmatic_finding_changes_refresh_review(self):
        insights = (ROOT / 'insights.js').read_text()
        self.assertIn("insightSelection=cycleSelect.value;\n if(typeof wsRefresh==='function')void wsRefresh();", insights)
        self.assertIn("$('#insightsCycle').onchange=()=>", insights)
        self.assertIn("if(typeof wsRefresh==='function')void wsRefresh();", insights)

    def test_late_responses_cannot_replace_a_newer_selection(self):
        workspace = (ROOT / 'workspace.js').read_text()
        self.assertIn('serial!==wsRefreshSerial', workspace)
        self.assertIn('JSON.stringify(identity)!==JSON.stringify(wsIdentity())', workspace)
        self.assertIn('serial!==wsHistorySerial', workspace)


if __name__ == '__main__':
    unittest.main()
