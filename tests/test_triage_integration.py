import json
import pathlib
import subprocess
import tempfile
import unittest
from studio import State
from triage_engine import public_summary

COMMIT_NAME='p0b-test'

class TriageIntegrationTests(unittest.TestCase):
    def test_optional_report_pinned_to_commit_and_local(self):
        with tempfile.TemporaryDirectory() as td:
            base=pathlib.Path(td);repo=base/'repo';repo.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'main.py').write_text('x=1\n')
            subprocess.run(['git','-C',str(repo),'add','.'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=t','-c','user.email=t@t','commit','-qm',COMMIT_NAME],check=True)
            sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
            path=base/'triage.json';path.write_text(json.dumps({'repositoryCommit':sha,'findings':[],'counts':{'raw':0},'schemaVersion':1,'ruleCounts':[],'limitations':[]}))
            state=State(repo,base/'data',triage_report=path)
            self.assertEqual(public_summary(state.triage())['counts']['raw'],0)
            no_report=State(repo,base/'other')
            with self.assertRaises(ValueError):no_report.triage()
            path2=base/'wrong.json';path2.write_text(json.dumps({'repositoryCommit':'0'*40,'findings':[]}))
            wrong=State(repo,base/'wrong_data',triage_report=path2)
            with self.assertRaises(ValueError):wrong.triage()

if __name__=='__main__':unittest.main()
