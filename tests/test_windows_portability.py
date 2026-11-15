import os
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest
import launcher
import studio

class WindowsPortability(unittest.TestCase):
    def test_windows_config_uses_appdata(self):
        with tempfile.TemporaryDirectory() as d, patch.object(launcher, 'is_windows', return_value=True):
            with patch.dict(os.environ, {'APPDATA': d, 'XDG_CONFIG_HOME': '/ignored'}, clear=True):
                self.assertEqual(launcher.config_path(), Path(d) / 'repo-studio' / 'launch.json')

    def test_windows_state_uses_localappdata(self):
        with tempfile.TemporaryDirectory() as d, patch.object(studio, 'is_windows', return_value=True):
            with patch.dict(os.environ, {'LOCALAPPDATA': d}, clear=True):
                self.assertEqual(studio.default_data_dir(), Path(d) / 'RepoStudio' / 'data')

    def test_windows_cmd_present(self):
        root = Path(__file__).resolve().parents[1]
        self.assertIn('launcher.py', (root / 'launch_windows.cmd').read_text())
        self.assertTrue((root / 'install_windows.ps1').is_file())

if __name__ == '__main__': unittest.main()
