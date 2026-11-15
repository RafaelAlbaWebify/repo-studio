#!/usr/bin/env python3
"""Cross-platform offline clean-profile test of portable launcher, no user writes."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

SOURCE = Path(__file__).resolve().parents[1]


def git(repo, *arguments):
    return subprocess.run(['git', '-C', str(repo), *arguments], check=True,
                          text=True, capture_output=True, timeout=15).stdout.strip()


def hash_tree(repo):
    return {p.relative_to(repo).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in repo.rglob('*') if p.is_file() and '.git' not in p.parts}


def get_json(url):
    with urllib.request.urlopen(url, timeout=2) as response:
        return json.load(response)


def main():
    with tempfile.TemporaryDirectory(prefix='rs098-clean-linux-') as temp:
        root = Path(temp)
        app = root / 'fresh-install' / 'repo-studio'
        shutil.copytree(SOURCE, app, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.venv', '*.sqlite3', '*.zip'))
        home = root / 'empty-home'; home.mkdir()
        xdg = home / '.config'; cfg = xdg / 'repo-studio'; cfg.mkdir(parents=True)
        repo = root / 'fixture'; repo.mkdir()
        git(repo, 'init', '-q')
        (repo / 'alpha.py').write_text('import beta\n\ndef alpha():\n    return beta.beta()\n', encoding='utf-8')
        (repo / 'beta.py').write_text('import alpha\n\ndef beta():\n    return 1\n', encoding='utf-8')
        git(repo, 'add', '.'); git(repo, '-c', 'user.name=Smoke', '-c', 'user.email=smoke@example.invalid', 'commit', '-qm', 'fixture')
        before = hash_tree(repo)
        (cfg / 'launch.json').write_text(json.dumps({'repo': str(repo)}), encoding='utf-8')
        env = {**os.environ, 'HOME': str(home), 'XDG_CONFIG_HOME': str(xdg), 'PYTHONDONTWRITEBYTECODE': '1'}
        # A clean XDG profile must also isolate STATE. Otherwise the inherited
        # XDG_STATE_HOME can point to the real user's persistent Workspace.
        if os.name != 'nt':
            state_home = home / '.local' / 'state'
            state_home.mkdir(parents=True)
            env['XDG_STATE_HOME'] = str(state_home)
        if os.name == 'nt':
            env['APPDATA'] = str(xdg)
            env['LOCALAPPDATA'] = str(home / 'AppData' / 'Local')
            Path(env['LOCALAPPDATA']).mkdir(parents=True, exist_ok=True)
        for key in ('JSCPD_BIN','REPOWISE_BIN','JSCPD_REPORT','REPOWISE_INDEX','REPO_STUDIO_DATA','REPO_STUDIO_REPO'):
            env.pop(key, None)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        env['PORT'] = str(port)
        url = f'http://127.0.0.1:{port}'
        log = root / 'server.log'
        def start():
            handle = log.open('a', encoding='utf-8')
            proc = subprocess.Popen([sys.executable, '-B', str(app / 'launcher.py')],
                                    cwd=app, env=env, stdin=subprocess.DEVNULL,
                                    stdout=handle, stderr=subprocess.STDOUT)
            handle.close()
            for _ in range(80):
                if proc.poll() is not None:
                    raise RuntimeError('Clean launch failed: ' + log.read_text()[-1500:])
                try:
                    return proc, get_json(url + '/api/status')
                except Exception:
                    time.sleep(.1)
            proc.terminate(); proc.wait(timeout=5)
            raise RuntimeError('Timed out launching clean installation: ' + log.read_text()[-1500:])
        def stop(proc):
            if os.name == 'nt':
                # launcher.py delegates to studio.py on Windows: stop both.
                subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                               capture_output=True, timeout=10, check=False)
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(timeout=5)
            else:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(timeout=5)
        proc = None
        try:
            proc, status = start()
            assert os.path.samefile(status['repository'], repo), status
            assert status['jscpdAvailable'] is False and status['repowiseAvailable'] is False
            assert Path(status['dataPath']).resolve().is_relative_to(home.resolve()), status
            assert 'Repo Studio' in urllib.request.urlopen(url, timeout=2).read().decode()
            assert get_json(url + '/api/workspace/history')['total'] == 0
            state = Path(status['dataPath'])
            assert state.is_dir(), 'No XDG-independent state directory created'
            stop(proc); proc = None
            assert hash_tree(repo) == before, 'Fixture source modified by application'
            assert git(repo, 'status', '--porcelain') == '', 'Fixture git status changed'
            proc, status2 = start()
            assert os.path.samefile(status2['repository'], repo)
            assert get_json(url + '/api/workspace/history')['total'] == 0
            assert hash_tree(repo) == before
            print('CLEAN_PORTABLE_INSTALL_PASS', os.name)
            print('Fresh HOME, launch.json, fresh committed Git fixture, localhost UI/API, persistent state path and restart PASS')
        finally:
            if proc is not None and proc.poll() is None:
                stop(proc)


if __name__ == '__main__':
    main()
