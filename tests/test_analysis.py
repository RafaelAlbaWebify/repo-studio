import tempfile, unittest, pathlib, subprocess
from analysis import analyze_python, export_evidence
from studio import State


class AnalysisTests(unittest.TestCase):
    def test_import_cycle_and_complexity(self):
        files={
            'src/demo/a.py':'from . import b\n\ndef helper():\n    return b.value\n',
            'src/demo/b.py':'from .a import helper\nvalue = 2\n',
            'src/demo/large.py':'def conditional(x):\n'+''.join(f'    if x == {i}: return {i}\n' for i in range(13))+'    return -1\n',
        }
        result=analyze_python(files,files.__getitem__,'a'*40)
        self.assertEqual(len(result['cycles']),1)
        self.assertEqual(set(result['cycles'][0]['modules']),{'demo.a','demo.b'})
        self.assertEqual(result['counts']['complexity'],1)
        self.assertEqual(result['complexity'][0]['cyclomaticApprox'],14)
        self.assertEqual(result['counts']['cycles'],1)
        self.assertEqual(analyze_python(files,files.__getitem__,'a'*40)['cycles'],result['cycles'])

    def test_evidence_does_not_mutate_source_and_has_commit(self):
        source='def f():\n    return 1\n'
        finding={'id':'aabb','type':'complexity','file':'a.py','line':1,'endLine':2,
                 'limitations':['not proof']}
        item=export_evidence(finding,'complexity','f'*40,lambda path:source,'compact')
        self.assertIn('f'*40,item['markdown'])
        self.assertIn('return 1',item['markdown'])
        self.assertIn('Do not modify',item['markdown'])
        self.assertEqual(item['json']['snippets'][0]['path'],'a.py')
        self.assertFalse(item['json']['contextIsComplete'])
        self.assertEqual(source,'def f():\n    return 1\n')

    def test_oversize_context_is_bounded(self):
        source='\n'.join('secretless content '+('x'*200) for _ in range(200))
        finding={'id':'t','file':'a.py','line':1,'endLine':200}
        result=export_evidence(finding,'complexity','f'*40,lambda path:source,'compact')
        self.assertLess(len(result['markdown']),9000)

    def test_repo_remains_clean_and_api_analysis(self):
        with tempfile.TemporaryDirectory() as td:
            base=pathlib.Path(td);repo=base/'repo';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'a.py').write_text('def simple():\n    return 1\n')
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=t','-c','user.email=t@t','commit','-qm','test'],check=True)
            state=State(repo,base/'data')
            self.assertEqual(state.analysis()['pythonFilesScanned'],1)
            self.assertFalse(state.analysis()['cycles'])
            self.assertEqual(subprocess.run(['git','-C',str(repo),'status','--porcelain'],capture_output=True,text=True,check=True).stdout,'')

if __name__=='__main__':unittest.main()
