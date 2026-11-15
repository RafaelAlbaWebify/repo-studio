"""Deterministic F1.4 case grouping and UI integration contract."""
import importlib.util
import pathlib
import unittest
from html.parser import HTMLParser

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('studio',ROOT/'studio.py')
studio=importlib.util.module_from_spec(spec);spec.loader.exec_module(studio)

class Ids(HTMLParser):
    def __init__(self): super().__init__();self.ids=set()
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k=='id':self.ids.add(v)

class FindingsTests(unittest.TestCase):
    def setUp(self):
        self.data={'items':[
            {'id':0,'first':'src/a.py','second':'src/b.py','firstLine':10,'secondLine':20,'lines':10,'group':'production','language':'python'},
            {'id':1,'first':'src/b.py','second':'src/a.py','firstLine':27,'secondLine':17,'lines':10,'group':'production','language':'python'},
            {'id':2,'first':'src/x.py','second':'src/y.py','firstLine':1,'secondLine':1,'lines':5,'group':'production','language':'python'},
            {'id':3,'first':'src/tenant_invitations.py','second':'src/existing_user_invitations.py','firstLine':4,'secondLine':7,'lines':10,'group':'production','language':'python'},
        ]}
    def test_overlaps_dont_double_count(self):
        result=studio.finding_cases(self.data,'a'*40)
        c=next(c for c in result['cases'] if c['first']=='src/a.py')
        self.assertEqual(c['count'],2)
        self.assertEqual((c['coveredLinesA'],c['coveredLinesB']),(17,17))
        self.assertEqual(result['matchCount'],4)
    def test_ids_stable_and_commit_scoped(self):
        a=studio.finding_cases(self.data,'a'*40)
        b=studio.finding_cases(self.data,'a'*40)
        c=studio.finding_cases(self.data,'b'*40)
        self.assertEqual(a['cases'][0]['id'],b['cases'][0]['id'])
        self.assertNotEqual(a['cases'][0]['id'],c['cases'][0]['id'])
    def test_review_not_safety_claim(self):
        results=studio.finding_cases(self.data,'a'*40)
        self.assertTrue(all(c['reviewStatus']=='unreviewed' and c['decision']=='No change proposed' for c in results['cases']))
        sensitive=next(c for c in results['cases'] if 'invitations' in c['first'])
        self.assertIn('Security',sensitive['reviewTopics'][0])
    def test_invalid_inputs_discarded(self):
        self.data['items'].append({'id':4,'first':'src/a','second':'src/b','firstLine':-1,'secondLine':4,'lines':7})
        self.assertEqual(studio.finding_cases(self.data,'x')['matchCount'],4)
    def test_browser_wiring(self):
        html=(ROOT/'static/index.html').read_text()
        js=(ROOT/'static/app.js').read_text()
        parser=Ids();parser.feed(html)
        self.assertTrue({'findings','findingFilter','findingGroup','findingList','findingCount','findingMore'}<=parser.ids)
        self.assertIn("'/api/findings'",js)
        self.assertIn('renderFindings()',js)
        self.assertIn('compareSources({first:c.first',js)
        self.assertIn("p.path=='/api/findings'",(ROOT/'studio.py').read_text())

if __name__=='__main__':unittest.main()
