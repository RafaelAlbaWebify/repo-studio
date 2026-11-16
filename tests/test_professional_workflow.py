import unittest
from professional_workflow import dossier,find_finding

COMMIT='a'*40
ITEM={'id':'b'*20,'path':'src/app.py','line':4,'analyzer':'pyright','rule':'reportPossiblyUnboundVariable','reviewQueue':'review_first','area':'production','inventoryStatus':'in_inventory','duplicateOfSourceIndex':None,'raw':{'message':'variable may be unbound','severity':'error'}}
REPORT={'repositoryCommit':COMMIT,'findings':[ITEM]}
SOURCE='\n'.join(f'value_{i}=1' for i in range(1,15))+'\n'
class ProfessionalWorkflowTests(unittest.TestCase):
 def test_bounded_dossier_contains_line_and_explicit_unknowns(self):
  d=dossier(REPORT,ITEM['id'],COMMIT,lambda p:SOURCE)
  self.assertIn('    4 | value_4=1',d['markdown'])
  self.assertIn('NOT included or verified',d['markdown'])
  self.assertEqual(d['sourceLineCount'],14)
  self.assertEqual(d['verification'],'UNVERIFIED_CANDIDATE')
 def test_rejects_stale_evidence_and_invalid_ids(self):
  with self.assertRaises(ValueError): dossier(REPORT,ITEM['id'],'c'*40,lambda p:SOURCE)
  with self.assertRaises(ValueError): find_finding(REPORT,'bad')
 def test_rejects_unverified_paths_and_out_of_range(self):
  invalid={**ITEM,'inventoryStatus':'not_in_inventory'}
  with self.assertRaises(ValueError):find_finding({'findings':[invalid]},ITEM['id'])
  with self.assertRaises(ValueError):dossier(REPORT,ITEM['id'],COMMIT,lambda p:'x\n')
 def test_rejects_oversized_dossier(self):
  with self.assertRaises(ValueError):dossier(REPORT,ITEM['id'],COMMIT,lambda p:('x'*100000+'\n')*6,level='compact')
if __name__=='__main__':unittest.main()
