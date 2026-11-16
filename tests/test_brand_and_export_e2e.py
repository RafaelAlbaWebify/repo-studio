import pathlib, unittest
from unittest.mock import Mock
ROOT=pathlib.Path(__file__).resolve().parents[1]
class BrandAndExportTests(unittest.TestCase):
 def test_icon_files_and_ui(self):
  html=(ROOT/'static/index.html').read_text()
  self.assertIn('repo-studio-icon.svg',html)
  self.assertIn('BETA 0.9.10',html)
  for f in ('favicon.svg','repo-studio-icon.svg','repo-studio-icon.png','repo-studio-logo.svg'):
   self.assertTrue((ROOT/'static'/f).is_file())
 def test_static_icon_route(self):
  import sys
  sys.path.insert(0,str(ROOT))
  from studio import Handler
  h=Handler.__new__(Handler);h.path='/repo-studio-icon.svg';h.headers={'Host':'127.0.0.1:8765'}
  h.server=type('Server',(),{'server_port':8765,'state':object()})();h.static=Mock();h.do_GET()
  h.static.assert_called_once_with('repo-studio-icon.svg','image/svg+xml; charset=utf-8')
 def test_context_e2e_covers_all_levels_and_commit(self):
  src=(ROOT/'e2e/run.py').read_text()
  self.assertIn("('compact','balanced','extended')",src)
  self.assertIn('EXCLUDED BY USER',src)
  self.assertIn('Original exporter reported complete anchors:',src)
  self.assertIn('to_be_disabled()',src)
