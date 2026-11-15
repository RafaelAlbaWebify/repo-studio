import unittest
from analysis import export_evidence

class MissingRanges(unittest.TestCase):
    def test_partial_complexity_exposes_exact_uncovered_target(self):
        src='def work():\n'+''.join(f'    x{i} = {i}  # ' + 'test-content-' * 8 + '\n' for i in range(250))
        finding={'id':'r1','type':'complexity','file':'module.py','line':1,'endLine':251}
        result=export_evidence(finding,'complexity','a'*40,lambda _:src,'compact','fixture')
        cov=result['json']['evidenceCoverage']
        self.assertFalse(cov['anchorsComplete'])
        self.assertEqual(cov['missingEvidenceItems'],0)
        self.assertTrue(cov['partialTargetRanges'])
        gap=cov['partialTargetRanges'][0]['ranges'][0]
        self.assertEqual(gap[1],251)
        self.assertIn(f'lines {gap[0]}-{gap[1]}',result['markdown'])
