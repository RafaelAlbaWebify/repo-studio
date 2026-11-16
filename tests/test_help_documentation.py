"""Keep the shipped 0.9.9 Help index and installation guides in sync."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DocumentationAcceptance(unittest.TestCase):
    def test_installation_guides_and_readme_links(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for guide in ('INSTALL_OMARCHY.md', 'INSTALL_UBUNTU.md', 'WINDOWS_INSTALL.md'):
            self.assertTrue((ROOT / guide).is_file(), guide)
            self.assertIn(f']({guide})', readme)
        self.assertIn('install_windows.ps1', (ROOT / 'WINDOWS_INSTALL.md').read_text(encoding='utf-8'))

    def test_in_app_help_navigation_and_workflows(self):
        page = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
        articles = set(re.findall(r'<article id="(help-[a-z-]+)"', page))
        links = set(re.findall(r'<a href="#(help-[a-z-]+)"', page))
        self.assertEqual(links, articles, 'Every Help article must have an index anchor')
        for anchor in ('help-professional', 'help-workspace', 'help-coverage', 'help-install'):
            self.assertIn(anchor, articles)
        for term in ('Professional findings', 'Export history', 'Source revalidation',
                     'INSTALL_OMARCHY.md', 'INSTALL_UBUNTU.md', 'WINDOWS_INSTALL.md'):
            self.assertIn(term, page)

    def test_contextual_help_for_new_controls(self):
        script = (ROOT / 'static' / 'support.js').read_text(encoding='utf-8')
        for control in ('workspaceSave', 'workspaceExportFilter', 'workspaceFreshnessFilter',
                        'triageReload', 'triageQueue', 'triageHideNoise'):
            self.assertIn(control + ':', script)


if __name__ == '__main__':
    unittest.main()
