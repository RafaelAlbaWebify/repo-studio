import pathlib
import tempfile
import unittest
from workspace import Workspace


class WorkspaceHistoryTest(unittest.TestCase):
    def test_cross_commit_history_without_merging(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Workspace(folder)
            repo = pathlib.Path(folder) / 'repo'
            repo.mkdir()
            other = pathlib.Path(folder) / 'other'
            other.mkdir()
            db.update(repo, 'a' * 40, 'cycle', 'id1', 'reviewed', 'keep', 'No change in A')
            db.update(repo, 'b' * 40, 'cycle', 'id1', 'reviewing', 'investigate', 'Check in B')
            db.exported(repo, 'a' * 40, 'cycle', 'id1', 'compact', 'copy', 'a' * 64)
            db.exported(repo, 'a' * 40, 'cycle', 'id1', 'balanced', 'download', 'b' * 64)
            db.update(other, 'a' * 40, 'cycle', 'id1', 'pending', 'undecided', 'other repo')
            history = Workspace(folder).history(repo)
            self.assertEqual(history['total'], 2)
            self.assertFalse(history['truncated'])
            records = {r['commit_sha']: r for r in history['items']}
            self.assertEqual(records['a' * 40]['export_count'], 2)
            self.assertEqual(records['a' * 40]['decision'], 'keep')
            self.assertEqual(records['b' * 40]['decision'], 'investigate')
            self.assertEqual(Workspace(folder).history(other)['total'], 1)

    def test_bounded_and_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Workspace(folder)
            for i in range(4):
                db.update(folder, f'{i:040x}', 'cycle', 'same', 'pending', 'undecided', '')
            history = db.history(folder, 2)
            self.assertEqual(history['total'], 4)
            self.assertEqual(len(history['items']), 2)
            self.assertTrue(history['truncated'])
            for invalid in (0, 501, True, '2'):
                with self.assertRaises(ValueError):
                    db.history(folder, invalid)
