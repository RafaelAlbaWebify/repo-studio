"""Commit pinning regression for repository browsing."""
import pathlib, subprocess, sys, tempfile, unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from studio import State

def git(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()

class CommitConsistencyTests(unittest.TestCase):
    def test_changed_head_requires_reselection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp); repo=root/'fixture'; repo.mkdir()
            git(repo,'init','-q'); git(repo,'config','user.name','Fixture'); git(repo,'config','user.email','fixture@example.test')
            (repo/'sample.py').write_text('a=1\n');git(repo,'add','.');git(repo,'commit','-qm','first')
            state=State(str(repo),root/'results')
            state.require_selected_commit()
            (repo/'sample.py').write_text('a=2\n'); git(repo,'add','.');git(repo,'commit','-qm','second')
            with self.assertRaisesRegex(ValueError,'HEAD changed'):
                state.require_selected_commit()
    def test_api_file_and_listing_pin_commit(self):
        source=(pathlib.Path(__file__).resolve().parents[1]/'studio.py').read_text()
        self.assertIn("entries(s.repo,s.commit)",source)
        self.assertIn("file_at(s.repo,q.get('path',[''])[0],s.commit)",source)
        self.assertIn("if p.path=='/api/file':s.require_selected_commit()",source)
        self.assertIn("if p.path=='/api/files':s.require_selected_commit()",source)
