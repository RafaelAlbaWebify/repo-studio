import hashlib
import unittest
from analysis import analyze_python, export_evidence

class EvidenceCoverageTests(unittest.TestCase):
    def test_cycle_with_both_edges_has_explicit_coverage(self):
        sources = {'src/pkg/a.py':'from . import b\n', 'src/pkg/b.py':'from . import a\n'}
        finding = analyze_python(list(sources), sources.__getitem__, 'a'*40)['cycles'][0]
        result = export_evidence(finding, 'cycle', 'a'*40, sources.__getitem__, 'compact', 'pkg')
        coverage = result['json']['evidenceCoverage']
        self.assertEqual(coverage['reportedEdges'], 2)
        self.assertEqual(coverage['edgesWithCompleteSource'], 2)
        self.assertTrue(coverage['anchorsComplete'])
        self.assertFalse(result['truncated'])
        for snippet in result['json']['snippets']:
            self.assertEqual(snippet['sourceSha256'], hashlib.sha256(sources[snippet['path']].encode()).hexdigest())
        self.assertIn('Evidence coverage',result['markdown'])

    def test_missing_source_is_explicitly_partial(self):
        finding = {'id':'c1','type':'cycle','files':['a.py','b.py'],
                   'edges':[{'from':'a','to':'b'},{'from':'b','to':'a'}]}
        def reader(path):
            if path == 'b.py': raise ValueError('unavailable')
            return 'import b\n'
        result = export_evidence(finding,'cycle','b'*40,reader,'compact','test')
        coverage = result['json']['evidenceCoverage']
        self.assertFalse(coverage['anchorsComplete'])
        self.assertEqual(coverage['reportedEdges'],2)
        self.assertLess(coverage['edgesWithCompleteSource'],2)
        self.assertTrue(result['truncated'])
        self.assertIn('Partial evidence',result['markdown'])

    def test_complexity_source_hash(self):
        text='def work():\n    return 42\n'
        finding={'id':'abc','file':'src/work.py','line':1,'endLine':2}
        result=export_evidence(finding,'complexity','c'*40,lambda _:text)
        self.assertTrue(result['json']['evidenceCoverage']['anchorsComplete'])
        self.assertEqual(result['json']['snippets'][0]['sourceSha256'],hashlib.sha256(text.encode()).hexdigest())

if __name__=='__main__': unittest.main()
