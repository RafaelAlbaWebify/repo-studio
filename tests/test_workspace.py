import tempfile
import unittest
from workspace import Workspace

class WorkspaceTest(unittest.TestCase):
 def test_persistence_and_isolation(self):
  with tempfile.TemporaryDirectory() as d:
   w=Workspace(d)
   w.update(d,'a'*40,'cycle','x','reviewed','keep','human note')
   self.assertEqual(Workspace(d).list(d,'a'*40)[0]['notes'],'human note')
   self.assertEqual(Workspace(d).list(d,'b'*40),[])
   w.exported(d,'a'*40,'cycle','x','balanced','copy','a'*64)
   self.assertEqual(len(Workspace(d).list(d,'a'*40)[0]['exports']),1)
   self.assertNotEqual(w.key(d,'a'*40,'cycle','x'),w.key(d,'b'*40,'cycle','x'))
 def test_reject_invalid(self):
  with tempfile.TemporaryDirectory() as d:
   w=Workspace(d)
   with self.assertRaises(ValueError):w.update(d,'a','cycle','x','closed','keep','')
   with self.assertRaises(ValueError):w.exported(d,'a','cycle','x','balanced','copy','bad')
