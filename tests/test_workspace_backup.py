import sqlite3
import tempfile
import unittest
from pathlib import Path
from workspace import Workspace
from workspace_backup import backup_workspace

class WorkspaceBackupTests(unittest.TestCase):
    def test_snapshot_preserves_records_and_foreign_keys(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); repo=root/'repo'; repo.mkdir()
            data=root/'data';data.mkdir()
            w=Workspace(data)
            w.update(repo,'a'*40,'cycle','edge','reviewed','keep','Keep as is')
            w.exported(repo,'a'*40,'cycle','edge','balanced','copy','f'*64)
            dest=root/'backup.sqlite3'
            backup_workspace(data,dest)
            with sqlite3.connect(dest) as db:
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
                self.assertEqual(db.execute('SELECT COUNT(*) FROM investigations').fetchone()[0],1)
                self.assertEqual(db.execute('SELECT COUNT(*) FROM exports').fetchone()[0],1)
            # A backup is a snapshot, not a linked database.
            w.update(repo,'a'*40,'cycle','edge','reviewing','investigate','Later')
            with sqlite3.connect(dest) as db:
                self.assertEqual(db.execute('SELECT notes FROM investigations').fetchone()[0],'Keep as is')
            with self.assertRaises(FileExistsError): backup_workspace(data,dest)
    def test_missing_source_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);data=root/'data';data.mkdir()
            with self.assertRaises(FileNotFoundError):backup_workspace(data,root/'backup.sqlite3')
            self.assertEqual(list(data.iterdir()),[])
