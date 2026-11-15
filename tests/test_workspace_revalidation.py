"""Regression: commit changes do not silently carry human decisions."""
import pathlib
import sqlite3
from contextlib import closing
import subprocess
import tempfile
import unittest
from workspace import Workspace
from studio import State


def git(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args],capture_output=True,text=True,check=True).stdout.strip()

class WorkspaceRevalidationTests(unittest.TestCase):
    def test_source_change_unchanged_unavailable_and_repo_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);repo=root/'repo';repo.mkdir()
            git(repo,'init','-q');git(repo,'config','user.name','QA');git(repo,'config','user.email','qa@example.test')
            (repo/'a.py').write_text('x=1\n');(repo/'b.py').write_text('y=1\n')
            git(repo,'add','.');git(repo,'commit','-qm','first');old=git(repo,'rev-parse','HEAD')
            (root/'data').mkdir();db=Workspace(root/'data')
            db.update(repo,old,'complexity','a','reviewed','keep','keep A',['a.py'])
            db.update(repo,old,'complexity','b','reviewed','keep','keep B',['b.py'])
            db.update(repo,old,'cycle','legacy','reviewing','investigate','legacy')
            db.exported(repo,old,'complexity','a','balanced','copy','0'*64)
            (repo/'a.py').write_text('x=2\n');git(repo,'add','.');git(repo,'commit','-qm','second')
            new=git(repo,'rev-parse','HEAD')
            records=db.revalidation(db.history(repo)['items'],repo,new)
            by_id={x['finding_id']:x for x in records}
            self.assertEqual(by_id['a']['revalidation'],'source_changed')
            self.assertEqual(by_id['b']['revalidation'],'source_unchanged')
            self.assertEqual(by_id['legacy']['revalidation'],'unknown_legacy')
            self.assertEqual(by_id['a']['decision'],'keep')
            self.assertEqual(by_id['a']['export_count'],1)
            self.assertEqual(db.list(repo,new),[])
            self.assertEqual(git(repo,'status','--porcelain'),'')
            db.update(repo,new,'complexity','a','pending','undecided','new review',['a.py'])
            current=db.revalidation(db.history(repo)['items'],repo,new)
            self.assertEqual(next(x for x in current if x['commit_sha']==new)['revalidation'],'current_snapshot')
            self.assertEqual(next(x for x in db.list(repo,old) if x['finding_id']=='a')['notes'],'keep A')

    def test_missing_commit_and_path_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);repo=root/'repo';repo.mkdir()
            git(repo,'init','-q');git(repo,'config','user.name','QA');git(repo,'config','user.email','qa@example.test')
            (repo/'a.py').write_text('x=1\n');git(repo,'add','.');git(repo,'commit','-qm','first')
            current=git(repo,'rev-parse','HEAD');(root/'data').mkdir();db=Workspace(root/'data')
            db.update(repo,'f'*40,'cycle','old','reviewing','investigate','old',['a.py'])
            item=db.revalidation(db.history(repo)['items'],repo,current)[0]
            self.assertEqual(item['revalidation'],'unknown_commit')
            for bad in [['../escape'],['/etc/passwd'],['a\\b'],[],['a']*41]:
                with self.assertRaises(ValueError):db.update(repo,current,'cycle','x','pending','undecided','',bad)

    def test_legacy_database_migrated_without_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            data=pathlib.Path(temp);path=data/'investigation-workspace.sqlite3'
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('''CREATE TABLE investigations (key TEXT PRIMARY KEY,repo TEXT NOT NULL,commit_sha TEXT NOT NULL,finding_type TEXT NOT NULL,finding_id TEXT NOT NULL,progress TEXT NOT NULL,decision TEXT NOT NULL,notes TEXT NOT NULL,updated_at TEXT NOT NULL)''')
                db.execute("INSERT INTO investigations VALUES ('k','/r','c','cycle','i','reviewed','keep','legacy note','now')")
            ws=Workspace(data)
            with closing(sqlite3.connect(path)) as db:
                row=db.execute("SELECT notes,source_paths FROM investigations WHERE key='k'").fetchone()
                self.assertEqual(row,('legacy note',None))

    def test_detected_cycle_provides_real_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);repo=root/'repo';repo.mkdir()
            git(repo,'init','-q');git(repo,'config','user.name','QA');git(repo,'config','user.email','qa@example.test')
            (repo/'a.py').write_text('import b\n');(repo/'b.py').write_text('import a\n')
            git(repo,'add','.');git(repo,'commit','-qm','first')
            state=State(repo,root/'data');cycle=state.analysis()['cycles'][0]
            self.assertEqual(set(state.finding_source_paths('cycle',cycle['id'])),{'a.py','b.py'})
            self.assertIsNone(state.finding_source_paths('cycle','not-a-finding'))

if __name__=='__main__':unittest.main()
