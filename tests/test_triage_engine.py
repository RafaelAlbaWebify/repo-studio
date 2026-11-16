import json
import tempfile
import unittest
from pathlib import Path
from triage_engine import normalize,load_and_normalize,filter_findings,public_summary

COMMIT='3'*40


def fixtures():
    items=[{'analyzer':'bandit','path':'tests/test_a.py','line':8,'rule':'B101','message':'assert','severity':'LOW'},
           {'analyzer':'pyright','path':'src/demo/a.py','line':9,'rule':'reportMissingImports','message':'missing import'},
           {'analyzer':'bandit','path':'src/demo/a.py','line':15,'rule':'B608','message':'SQL string'},
           {'analyzer':'bandit','path':'src/demo/a.py','line':15,'rule':'B608','message':'SQL string'},
           {'analyzer':'vulture','path':'src/demo/a.py','line':10,'rule':'VULTURE_UNUSED','message':'unused f','confidence':60}]
    summary={'repositoryCommit':COMMIT,'tools':{n:{'status':'completed_with_findings','findingCount':sum(x['analyzer']==n for x in items),'toolVersion':n+' 1'} for n in ('bandit','pyright','ruff','vulture')},'totals':{'rawFindingCount':len(items)}}
    return summary,items

class TriageEngineTests(unittest.TestCase):
    def test_lossless_and_reversible(self):
        summary,items=fixtures(); report=normalize(summary,items,expected_commit=COMMIT,inventory={'src/demo/a.py','tests/test_a.py'})
        self.assertEqual(report['counts']['raw'],5)
        self.assertEqual(report['counts']['uniqueExact'],4)
        self.assertEqual(report['counts']['exactDuplicateEntries'],1)
        self.assertEqual(report['counts']['byArea']['production'],4)
        self.assertEqual(report['counts']['noiseReasons']['assert_usage'],1)
        self.assertEqual(report['counts']['noiseReasons']['unresolved_import_environment'],1)
        self.assertEqual(len(filter_findings(report,hide_noise=True)['items']),2)
        self.assertEqual(filter_findings(report,area='production',queue='review_first')['totalMatching'],1)
        self.assertEqual([x['raw'] for x in report['findings']],items)
        self.assertNotIn('findings',public_summary(report))

    def test_reject_unverified_commit_and_missing_records(self):
        summary,items=fixtures()
        with self.assertRaises(ValueError):normalize(summary,items,expected_commit='a'*40)
        summary['tools']['bandit']['findingCount']=100
        with self.assertRaises(ValueError):normalize(summary,items)

    def test_reject_untrusted_paths_and_invalid_filters(self):
        summary,items=fixtures();items[0]['path']='../../escape.py'
        with self.assertRaises(ValueError):normalize(summary,items)
        items[0]['path']='tests/test_a.py'
        result=normalize(summary,items)
        with self.assertRaises(ValueError):filter_findings(result,limit=999999)
        with self.assertRaises(ValueError):filter_findings(result,analyzer='nope')

    def test_manifest_integrity(self):
        summary,items=fixtures()
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/'summary.json').write_text(json.dumps(summary))
            (p/'findings.json').write_text(json.dumps(items))
            c=p/'coverage.json';c.write_text(json.dumps({'repositoryCommit':COMMIT,'inventoryCount':2,'files':[{'path':'src/demo/a.py'},{'path':'tests/test_a.py'}]}))
            report=load_and_normalize(p,coverage_path=c,expected_commit=COMMIT)
            self.assertEqual(report['counts']['pathsNotInInventory'],0)
            self.assertIn('findings.json',report['provenance']['inputSha256'])
            c.write_text(json.dumps({'repositoryCommit':'f'*40,'inventoryCount':2,'files':[]}))
            with self.assertRaises(ValueError):load_and_normalize(p,coverage_path=c)

if __name__=='__main__':unittest.main()
