"""Safe, offline-compatible backup of a Repo Studio Workspace database."""
import argparse
from contextlib import closing
import pathlib
import sqlite3
import sys

def backup_workspace(data_dir, destination):
    source = pathlib.Path(data_dir).expanduser().resolve() / 'investigation-workspace.sqlite3'
    target = pathlib.Path(destination).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f'Workspace database not found: {source}')
    if target.exists():
        raise FileExistsError(f'Refusing to overwrite existing backup: {target}')
    if not target.parent.is_dir():
        raise FileNotFoundError(f'Backup directory not found: {target.parent}')
    if target.parent == source.parent and target.name == source.name:
        raise ValueError('Backup destination must differ from source')
    try:
        with closing(sqlite3.connect(f'file:{source}?mode=ro', uri=True, timeout=10)) as live:
            with closing(sqlite3.connect(target, timeout=10)) as snapshot:
                with snapshot:
                    live.backup(snapshot)
                    check = snapshot.execute('PRAGMA integrity_check').fetchone()[0]
                    if check != 'ok':
                        raise RuntimeError(f'Backup integrity check failed: {check}')
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', required=True, help='Workspace state directory, NOT repository path')
    p.add_argument('--output', required=True, help='New .sqlite3 backup file; never overwritten')
    args = p.parse_args()
    try:
        print('Workspace backup:', backup_workspace(args.data,args.output))
    except (OSError,ValueError,sqlite3.Error,RuntimeError) as exc:
        print('BACKUP FAILED:',exc,file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
