import pathlib
import subprocess
import tempfile
import unittest
from coverage_engine import coverage_report


def git(repo,*args):
    return subprocess.run(['git','-C',str(repo),*args], check=True, capture_output=True)


class CoverageEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo=pathlib.Path(self.tmp.name)/'repo'
        self.repo.mkdir()
        git(self.repo,'init','-q')

    def commit(self):
        git(self.repo,'add','.')
        git(self.repo,'-c','user.name=CI','-c','user.email=ci@example.test','commit','-qm','fixture')

    def test_inventory_and_limits(self):
        (self.repo/'a.py').write_text('def a():\n    return 1\n')
        (self.repo/'b.py').write_text('def b(x):\n    return getattr(x,"a")\n')
        (self.repo/'doc.txt').write_text('hello')
        self.commit()
        r=coverage_report(self.repo)
        self.assertEqual(r['inventoryCount'],3)
        self.assertEqual(r['pythonAstStates'],{'examined':2})
        self.assertEqual(r['dynamicIntrospectionFiles'],['b.py'])
        self.assertFalse(r['currentUnusedGlobalGateEligible'])
        self.assertTrue(r['pythonInventoryReconciled'])
        self.assertEqual(r['manifestSha256'],coverage_report(self.repo)['manifestSha256'])
        limited=coverage_report(self.repo,max_analyzer_files=1)
        self.assertEqual(limited['pythonAstStates'],{'examined':1,'not_run':1})

    def test_failures_and_nonpython(self):
        (self.repo/'ok.py').write_text('value = 1\n')
        (self.repo/'bad.py').write_text('def broken(:\n')
        (self.repo/'latin.py').write_bytes(b'\xff')
        (self.repo/'oversized.py').write_text('a=1\n'*300)
        (self.repo/'script.ps1').write_text('Write-Output ok')
        self.commit()
        r=coverage_report(self.repo,max_bytes=100)
        self.assertEqual(r['inventoryCount'],5)
        self.assertEqual(r['pythonAstStates'],{'examined':1,'failed':2,'skipped':1})
        self.assertEqual(r['engineStates']['python_ast'],'partial')
        self.assertEqual([x['pythonAstStatus'] for x in r['files'] if x['path']=='script.ps1'],['not_applicable'])

    def test_no_mutation_and_commit_guard(self):
        (self.repo/'a.py').write_text('a=1\n')
        self.commit()
        head=git(self.repo,'rev-parse','HEAD').stdout.decode().strip()
        status_before=git(self.repo,'status','--porcelain').stdout
        coverage_report(self.repo,head)
        self.assertEqual(status_before,git(self.repo,'status','--porcelain').stdout)
        with self.assertRaises(ValueError):
            coverage_report(self.repo,'0'*40)

if __name__=='__main__':unittest.main()
