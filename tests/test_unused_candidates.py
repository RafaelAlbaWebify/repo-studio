import unittest
from analysis import analyze_python, export_evidence

COMMIT = 'c' * 40

class UnusedCandidatesTests(unittest.TestCase):
    def test_private_unreferenced_candidate_and_evidence(self):
        files = {'src/pkg/work.py': 'def _possibly_orphaned():\n    return 7\n\ndef public():\n    return 2\n'}
        result = analyze_python(files, files.__getitem__, COMMIT)
        self.assertTrue(result['unusedScanEligible'])
        self.assertEqual(result['counts']['unused'], 1)
        item = result['unused'][0]
        self.assertEqual(item['title'], '_possibly_orphaned')
        evidence = export_evidence(item, 'unused', COMMIT, files.__getitem__, 'compact', 'demo')
        self.assertIn('def _possibly_orphaned()', evidence['markdown'])
        self.assertEqual(evidence['json']['findingType'], 'unused')
        self.assertFalse(evidence['json']['contextIsComplete'])
        self.assertIn('unused-candidate', evidence['fileStem'])

    def test_references_and_decorators_exclude(self):
        files = {'src/pkg/a.py': '@register\ndef _hook():\n    pass\n\ndef _used():\n    return 1\n',
                 'src/pkg/b.py': 'from pkg.a import _used\n'}
        result = analyze_python(files, files.__getitem__, COMMIT)
        self.assertEqual(result['unused'], [])

    def test_dynamic_introspection_disables_candidates(self):
        files = {'x.py': 'def _missing():\n    return 1\ngetattr(object(), "anything")\n'}
        result = analyze_python(files, files.__getitem__, COMMIT)
        self.assertFalse(result['unusedScanEligible'])
        self.assertEqual(result['counts']['unused'], 0)

    def test_partial_scan_disables_candidates(self):
        files = {'a.py':'def _private():\n    pass\n', 'b.py':'def z():\n    pass\n'}
        result = analyze_python(files, files.__getitem__, COMMIT, max_files=1)
        self.assertFalse(result['unusedScanEligible'])
        self.assertTrue(result['truncated'])

    def test_syntax_error_disables_candidates(self):
        files = {'a.py':'def _private():\n    pass\n', 'b.py':'def broken(:\n'}
        result = analyze_python(files, files.__getitem__, COMMIT)
        self.assertFalse(result['unusedScanEligible'])
        self.assertEqual(result['unused'], [])

if __name__ == '__main__':
    unittest.main()
