import tempfile,pathlib,subprocess,unittest
from studio import State

class SourceRangeTest(unittest.TestCase):
    def test_bounded_and_pinned_source(self):
        with tempfile.TemporaryDirectory() as t:
            root=pathlib.Path(t);repo=root/'repo';repo.mkdir()
            (repo/'a.py').write_text('one\ntwo\nthree\n')
            subprocess.run(['git','init','-q',str(repo)],check=True)
            subprocess.run(['git','-C',str(repo),'add','a.py'],check=True)
            subprocess.run(['git','-C',str(repo),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','test'],check=True)
            s=State(repo,root/'state')
            got=s.source_range('a.py',2,3)
            self.assertEqual((got['firstLine'],got['lastLine']),(2,3))
            self.assertIn('two',got['snippet'])
            with self.assertRaises(ValueError):s.source_range('../a.py',1,2)
            with self.assertRaises(ValueError):s.source_range('a.py',1,121)
            with self.assertRaises(ValueError):s.source_range('a.py',1,9)
            (repo/'a.py').write_text('changed\n')
            self.assertIn('two',s.source_range('a.py',2,2)['snippet'])
