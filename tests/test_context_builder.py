import pathlib
import unittest
from unittest.mock import Mock

ROOT=pathlib.Path(__file__).resolve().parents[1]

class ContextBuilderContract(unittest.TestCase):
    def test_browser_elements_are_connected(self):
        h=(ROOT/'static/index.html').read_text(); js=(ROOT/'static/context_builder.js').read_text()
        for x in ('contextBuilder','contextBudget','contextLoad','contextFragments','contextSummary','contextCopy','contextDownload'):
            self.assertIn(f'id="{x}"',h)
        self.assertIn('src="/context_builder.js"',h)
        self.assertIn('EXCLUDED BY USER',js)
        self.assertIn('Source SHA-256',js)
        self.assertIn('repoCommit',js)
        self.assertIn('contextBudget',js)
    def test_http_static_route(self):
        import sys
        sys.path.insert(0,str(ROOT))
        from studio import Handler
        h=Handler.__new__(Handler)
        h.headers={'Host':'127.0.0.1:8765'}
        h.server=type('S',(),{'server_port':8765,'state':object()})()
        h.path='/context_builder.js';h.static=Mock();h.do_GET()
        h.static.assert_called_once_with('context_builder.js','text/javascript; charset=utf-8')

class BenchmarkContract(unittest.TestCase):
    def test_empty_template_does_not_claim_savings(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('measure',ROOT/'benchmark/measure.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        report=mod.summarize(mod.read(ROOT/'benchmark/results.csv'))
        self.assertIsNone(report['quality_matched_reduction_pct'])
        self.assertEqual(report['quality_matched_pairs'],0)
    def test_only_quality_matched_measures_aggregate(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('measure',ROOT/'benchmark/measure.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        a={'input_tokens':100,'output_tokens':100,'elapsed_seconds':4.,'quality_pass':True,'followups':0}
        b={'input_tokens':90,'output_tokens':90,'elapsed_seconds':3.,'quality_pass':True,'followups':0}
        c=dict(b,quality_pass=False)
        result=mod.summarize([('a','baseline',a),('a','repo_studio',b),('b','baseline',a),('b','repo_studio',c)])
        self.assertEqual(result['quality_matched_pairs'],1)
        self.assertEqual(result['quality_matched_reduction_pct'],10.0)
