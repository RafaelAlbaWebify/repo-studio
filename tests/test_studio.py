import json, pathlib, subprocess, tempfile, unittest, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import studio

def git(*args,cwd):return subprocess.run(['git',*args],cwd=cwd,check=True,capture_output=True,text=True).stdout.strip()

class StudioTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.base=pathlib.Path(self.tmp.name);self.repo=self.base/'repo';self.repo.mkdir()
  git('init','-q',cwd=self.repo);git('config','user.email','test@example.org',cwd=self.repo);git('config','user.name','Tester',cwd=self.repo)
  (self.repo/'main.py').write_text('def hello():\n    return "ok"\n')
  (self.repo/'link').symlink_to('/etc/passwd')
  git('add','.',cwd=self.repo);git('commit','-qm','initial',cwd=self.repo)
 def test_git_and_sources(self):
  self.assertEqual(studio.git_root(self.repo),self.repo)
  self.assertIn('main.py',studio.entries(self.repo))
  self.assertIn('return "ok"',studio.file_at(self.repo,'main.py'))
  with self.assertRaises(ValueError):studio.file_at(self.repo,'../etc/passwd')
  with self.assertRaises(ValueError):studio.file_at(self.repo,'/etc/passwd')
 def test_snapshot_ignores_symlinks(self):
  dest=self.base/'snapshot';studio.snapshot_archive(self.repo,dest)
  self.assertTrue((dest/'main.py').exists());self.assertFalse((dest/'link').exists());self.assertFalse((dest/'.git').exists())
 def test_sources_unchanged(self):
  orig=git('status','--porcelain',cwd=self.repo)
  s=studio.State(self.repo,self.base/'results')
  self.assertEqual(orig,git('status','--porcelain',cwd=self.repo))
  self.assertEqual(s.commit,studio.sha(self.repo))
  with self.assertRaises(ValueError):studio.State(self.repo,self.repo/'results')
 def test_jscpd_parse(self):
  doc={'statistics':{'total':{'percentage':4.3}},'duplicates':[{'firstFile':{'name':'src/a.py','start':1},'secondFile':{'name':'src/b.py','start':4},'lines':8,'format':'python','fragment':'pass'}]}
  p=self.base/'j.json';p.write_text(json.dumps(doc));d=studio.duplicates_doc(p)
  self.assertEqual(d['groups']['production'],1)
  self.assertEqual(d['stats']['percentage'],4.3)
 def test_uncommitted_ignored(self):
  (self.repo/'main.py').write_text('modified')
  self.assertIn('hello',studio.file_at(self.repo,'main.py'))
  self.assertIn('modified',(self.repo/'main.py').read_text())

if __name__=='__main__':unittest.main()
