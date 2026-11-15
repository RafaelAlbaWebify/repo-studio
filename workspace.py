"""Local investigation ledger. Exact commit-scoped identities; no speculative cross-commit merge."""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone

PROGRESS = ('pending', 'reviewing', 'reviewed')
DECISIONS = ('undecided', 'keep', 'investigate', 'propose_change')

class Workspace:
    def __init__(self, data):
        self.path = pathlib.Path(data).resolve() / 'investigation-workspace.sqlite3'
        self.lock = threading.RLock()
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS investigations (
                key TEXT PRIMARY KEY, repo TEXT NOT NULL, commit_sha TEXT NOT NULL,
                finding_type TEXT NOT NULL, finding_id TEXT NOT NULL,
                progress TEXT NOT NULL DEFAULT 'pending',
                decision TEXT NOT NULL DEFAULT 'undecided',
                notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL)""")
            columns={r[1] for r in db.execute('PRAGMA table_info(investigations)')}
            if 'source_paths' not in columns:
                db.execute("ALTER TABLE investigations ADD COLUMN source_paths TEXT")
            db.execute("""CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT, investigation_key TEXT NOT NULL,
                created_at TEXT NOT NULL, level TEXT NOT NULL, method TEXT NOT NULL,
                content_sha256 TEXT NOT NULL, FOREIGN KEY(investigation_key) REFERENCES investigations(key))""")
    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('PRAGMA busy_timeout=10000')
            with db:
                yield db
        finally:
            db.close()
    @staticmethod
    def key(repo, commit, kind, fid):
        return hashlib.sha256(json.dumps([str(pathlib.Path(repo).resolve()),commit,kind,fid],separators=(',',':')).encode()).hexdigest()
    def _ensure(self, db, repo, commit, kind, fid):
        if not isinstance(kind,str) or not isinstance(fid,str) or not kind or not fid or len(kind)>80 or len(fid)>256:
            raise ValueError('Identidad de hallazgo inválida')
        key=self.key(repo,commit,kind,fid)
        db.execute('INSERT OR IGNORE INTO investigations(key,repo,commit_sha,finding_type,finding_id,updated_at) VALUES(?,?,?,?,?,?)',
                   (key,str(pathlib.Path(repo).resolve()),commit,kind,fid,self.now()))
        return key
    @staticmethod
    def now(): return datetime.now(timezone.utc).isoformat()
    def update(self, repo, commit, kind, fid, progress, decision, notes, source_paths=None):
        if progress not in PROGRESS or decision not in DECISIONS or not isinstance(notes,str) or len(notes)>4000:
            raise ValueError('Estado o notas inválidos')
        if source_paths is not None:
            if (not isinstance(source_paths, list) or len(source_paths)>40 or not source_paths
                or any(not isinstance(x,str) or not x or len(x)>512 or x.startswith('/')
                       or '..' in pathlib.PurePosixPath(x).parts or '\\' in x for x in source_paths)):
                raise ValueError('Rutas de evidencia inválidas')
            source_paths=sorted(set(source_paths))
        with self.lock, self._connect() as db:
            key=self._ensure(db,repo,commit,kind,fid)
            db.execute('UPDATE investigations SET progress=?,decision=?,notes=?,updated_at=?,source_paths=COALESCE(?,source_paths) WHERE key=?',
                       (progress,decision,notes,self.now(),json.dumps(source_paths) if source_paths else None,key))
            return self._one(db,key)
    def _one(self,db,key):
        db.row_factory=sqlite3.Row
        r=db.execute('SELECT * FROM investigations WHERE key=?',(key,)).fetchone()
        return dict(r)
    def list(self,repo,commit):
        with self.lock, self._connect() as db:
            db.row_factory=sqlite3.Row
            rows=[dict(r) for r in db.execute('SELECT * FROM investigations WHERE repo=? AND commit_sha=? ORDER BY updated_at DESC',(str(pathlib.Path(repo).resolve()),commit))]
            for r in rows:
                r['exports']=[dict(x) for x in db.execute('SELECT created_at,level,method,content_sha256 FROM exports WHERE investigation_key=? ORDER BY id DESC',(r['key'],))]
            return rows
    def history(self, repo, limit=200):
        # Bounded per-repository history; no cross-commit presence inference.
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValueError('Límite de historial inválido')
        canonical = str(pathlib.Path(repo).resolve())
        with self.lock, self._connect() as db:
            db.row_factory = sqlite3.Row
            total = db.execute('SELECT COUNT(*) FROM investigations WHERE repo=?', (canonical,)).fetchone()[0]
            rows = [dict(r) for r in db.execute("""
                SELECT i.key, i.commit_sha, i.finding_type, i.finding_id,
                       i.progress, i.decision, i.notes, i.updated_at, i.source_paths,
                       COUNT(e.id) AS export_count, MAX(e.created_at) AS last_export_at
                FROM investigations i
                LEFT JOIN exports e ON e.investigation_key=i.key
                WHERE i.repo=?
                GROUP BY i.key
                ORDER BY i.updated_at DESC, i.key
                LIMIT ?""", (canonical,limit))]
            return {'items': rows, 'total': total, 'truncated': total > limit}

    @staticmethod
    def revalidation(rows, repo, current_commit):
        """Classify evidence-file changes; never transfer human decisions or infer finding presence."""
        if not re.fullmatch(r'[0-9a-f]{40}', current_commit):
            return rows
        by_commit={}
        for row in rows:
            old=row['commit_sha']
            if old == current_commit:
                row['revalidation']='current_snapshot'
                continue
            try:
                paths=json.loads(row.get('source_paths') or 'null')
            except (TypeError, ValueError):
                paths=None
            if not isinstance(paths,list) or not paths:
                row['revalidation']='unknown_legacy'
                continue
            if not re.fullmatch(r'[0-9a-f]{40}',old):
                row['revalidation']='unknown_commit'
                continue
            if old not in by_commit:
                try:
                    result=subprocess.run(['git','-C',str(repo),'diff','--no-ext-diff','--no-textconv',
                                           '--no-renames','--name-only','-z',old,current_commit,'--'],
                                          capture_output=True,timeout=8,check=False)
                    if result.returncode or len(result.stdout)>2_000_000:
                        by_commit[old]=None
                    else:
                        by_commit[old]=set(os.fsdecode(x) for x in result.stdout.split(b'\0') if x)
                except (OSError, subprocess.TimeoutExpired):
                    by_commit[old]=None
            changed=by_commit[old]
            if changed is None:
                row['revalidation']='unknown_commit'
            elif any(path in changed for path in paths):
                row['revalidation']='source_changed'
            else:
                row['revalidation']='source_unchanged'
        return rows

    def exported(self,repo,commit,kind,fid,level,method,digest):
        if level not in ('compact','balanced','extended') or method not in ('copy','download') or not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Registro de exportación inválido')
        with self.lock, self._connect() as db:
            key=self._ensure(db,repo,commit,kind,fid)
            db.execute('INSERT INTO exports(investigation_key,created_at,level,method,content_sha256) VALUES(?,?,?,?,?)',(key,self.now(),level,method,digest))
            return {'recorded':True}
