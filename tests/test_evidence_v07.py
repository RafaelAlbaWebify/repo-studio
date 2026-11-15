import unittest
from analysis import analyze_python, export_evidence, _export_stem


class EvidenceV07Tests(unittest.TestCase):
    def setUp(self):
        # Second import is deliberately far away from file start: previously
        # even Extended exported only the header and missed this reverse edge.
        self.sources = {
            'src/sampleproject/assisted_browser_provider.py':
                'from __future__ import annotations\n'
                'from .assisted_discovery import Discovery\n'
                + '\n'.join('# filler' for _ in range(120)) + '\n',
            'src/sampleproject/assisted_discovery.py':
                'from __future__ import annotations\n'
                + '\n'.join('# filler' for _ in range(140)) + '\n'
                'def deferred():\n'
                '    from . import assisted_browser_provider\n'
                '    return assisted_browser_provider\n',
        }
        self.commit='e'*40
        cycles=analyze_python(self.sources,self.sources.__getitem__,self.commit)['cycles']
        self.assertEqual(len(cycles),1)
        self.finding=cycles[0]

    def test_compact_includes_exact_imports_on_both_sides(self):
        for level in ('compact','balanced','extended'):
            with self.subTest(level=level):
                export=export_evidence(self.finding,'cycle',self.commit,
                                       self.sources.__getitem__,level,'SampleProject')
                snippets=export['json']['snippets']
                self.assertEqual(len(export['json']['edgeLocations']),2)
                self.assertEqual(len(snippets),2)
                self.assertTrue(all(s['targetFullyIncluded'] for s in snippets))
                source='\n'.join(s['snippet'] for s in snippets)
                self.assertIn('from .assisted_discovery import Discovery',source)
                self.assertIn('from . import assisted_browser_provider',source)
                self.assertIn('143',source)
                self.assertIn('Static',export['markdown'])
                self.assertEqual(export['fileStem'],
                    f'repo-studio-sampleproject-import-cycle-{self.finding["id"]}-{level}')

    def test_duplication_anchors_on_matching_ranges(self):
        first='\n'.join(['header']*100+['special evidence A']+['tail']*100)
        second='\n'.join(['header']*100+['special evidence B']+['tail']*100)
        finding={'id':'abc','first':'a.py','second':'b.py',
                 'matches':[{'firstLine':101,'secondLine':101,'lines':1}]}
        item=export_evidence(finding,'duplication',self.commit,
                             {'a.py':first,'b.py':second}.__getitem__,'compact','Test Repo')
        self.assertIn('special evidence A',item['markdown'])
        self.assertIn('special evidence B',item['markdown'])
        self.assertEqual(item['fileStem'],'repo-studio-test-repo-duplication-abc-compact')

    def test_complexity_targets_function_not_file_header(self):
        source='\n'.join(['# header']*200+['def important():','    return 7'])
        finding={'id':'abc','file':'x.py','line':201,'endLine':202}
        item=export_evidence(finding,'complexity',self.commit,lambda _:source,'compact')
        self.assertIn('def important():',item['markdown'])
        self.assertIn('return 7',item['markdown'])

    def test_safe_filename_and_json(self):
        self.assertEqual(_export_stem('../../My Project','cycle','ab:cd/ef','balanced'),
                         'repo-studio-my-project-import-cycle-ab-cd-ef-balanced')
        finding={'id':'abc','file':'file.py','line':1,'endLine':1}
        evidence=export_evidence(finding,'complexity',self.commit,lambda _: 'pass', 'compact','Thing')
        self.assertEqual(evidence['json']['schemaVersion'],2)
        self.assertEqual(evidence['json']['repoName'],'Thing')
        self.assertFalse(evidence['json']['contextIsComplete'])

if __name__=='__main__':unittest.main()
