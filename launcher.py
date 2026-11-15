#!/usr/bin/env python3
"""Portable Repo Studio launcher. User configuration is never embedded in release files."""
import json
import os
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parent
OPTIONS = {
    'jscpd_bin': '--jscpd-bin',
    'repowise_bin': '--repowise-bin',
    'jscpd_report': '--jscpd-report',
    'repowise_index': '--repowise-index',
    'data': '--data',
}
OVERRIDES = {
    'repo': 'REPO_STUDIO_REPO',
    'jscpd_bin': 'JSCPD_BIN',
    'repowise_bin': 'REPOWISE_BIN',
    'jscpd_report': 'JSCPD_REPORT',
    'repowise_index': 'REPOWISE_INDEX',
    'data': 'REPO_STUDIO_DATA',
}


def is_windows():
    return os.name == 'nt'

def config_path():
    if is_windows():
        base = Path(os.environ.get('APPDATA') or (Path.home() / 'AppData' / 'Roaming'))
    else:
        base = Path(os.environ.get('XDG_CONFIG_HOME') or (Path.home() / '.config')).expanduser()
    return base / 'repo-studio' / 'launch.json'


def arguments(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) > 1:
        raise ValueError('Expected at most one positional repository path')
    path = config_path()
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError('Repo Studio launch configuration must be a JSON object')
    repo = argv[0] if argv else os.environ.get(OVERRIDES['repo']) or data.get('repo')
    if not isinstance(repo, str) or not Path(repo).expanduser().is_absolute() or not Path(repo).is_dir():
        raise ValueError('Repository not configured. Set REPO_STUDIO_REPO or configure ' + str(path))
    result = ['--repo', str(Path(repo).expanduser().resolve(strict=True))]
    for key, flag in OPTIONS.items():
        val = os.environ.get(OVERRIDES[key]) or data.get(key)
        if isinstance(val, str) and val:
            result += [flag, str(Path(val).expanduser())]
    result += ['--port', os.environ.get('PORT', '8765')]
    return result


def main():
    try:
        args = arguments()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print('Repo Studio launcher: ' + str(exc), file=sys.stderr)
        return 2
    command = [sys.executable, '-B', str(ROOT / 'studio.py'), *args]
    if is_windows():
        # Windows has different process replacement semantics; retain exit status.
        return subprocess.call(command)
    os.execv(sys.executable, command)


if __name__ == '__main__':
    sys.exit(main())
