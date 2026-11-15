import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

class LauncherConfigTest(unittest.TestCase):
    def test_manager_launch_without_cli_args_uses_external_config(self):
        from launcher import arguments
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            config = home / 'repo-studio' / 'launch.json'
            config.parent.mkdir()
            repo = home / 'example-repo'
            repo.mkdir()
            config.write_text(json.dumps({'repo': str(repo), 'jscpd_bin': '/opt/tools/jscpd'}))
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': str(home), 'PORT': '8765'}, clear=True):
                args = arguments([])
            self.assertEqual(args[:2], ['--repo', str(repo)])
            self.assertIn('--jscpd-bin', args)
            self.assertEqual(args[-2:], ['--port', '8765'])

    def test_missing_config_reports_error_without_modification(self):
        from launcher import arguments
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {'XDG_CONFIG_HOME': temp}, clear=True):
                with self.assertRaises(ValueError):
                    arguments([])
            self.assertFalse((Path(temp) / 'repo-studio').exists())

if __name__ == '__main__':
    unittest.main()
