#!/usr/bin/env python3
"""Native Windows CI smoke for per-user installer/update/rollback; isolated env only.

Requires Windows, pwsh, git. Does not touch the actual user profile.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def invoke(script, env, *args, expect_ok=True):
    result = subprocess.run(
        ['pwsh', '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(script), *map(str, args)],
        env=env, cwd=ROOT, capture_output=True, text=True, timeout=60,
    )
    if (result.returncode == 0) != expect_ok:
        raise AssertionError(f'Unexpected exit status {result.returncode}: {result.stdout}\n{result.stderr}')
    return result


def main():
    if os.name != 'nt':
        raise SystemExit('Native Windows installer smoke must run on Windows (not a simulated Linux run).')
    if not shutil.which('pwsh') or not shutil.which('git'):
        raise SystemExit('Requires pwsh and git on PATH.')
    script = ROOT / 'install_windows.ps1'
    with tempfile.TemporaryDirectory(prefix='repo-studio-win-install-') as d:
        root = Path(d)
        env = dict(os.environ)
        env['LOCALAPPDATA'] = str(root / 'local')
        env['APPDATA'] = str(root / 'roaming')
        env['USERPROFILE'] = str(root / 'profile')
        for var in ('REPO_STUDIO_REPO', 'REPO_STUDIO_DATA', 'JSCPD_BIN', 'REPOWISE_BIN'):
            env.pop(var, None)
        for var in ('LOCALAPPDATA', 'APPDATA', 'USERPROFILE'):
            Path(env[var]).mkdir(parents=True, exist_ok=True)
        repo = root / 'fixture'; repo.mkdir()
        subprocess.run(['git', '-C', str(repo), 'init', '-q'], check=True)
        (repo / 'fixture.py').write_text('print(1)\n', encoding='utf-8')
        subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(repo), '-c', 'user.name=QA', '-c', 'user.email=qa@example.invalid',
                        'commit', '-qm', 'fixture'], check=True)
        base = Path(env['LOCALAPPDATA']) / 'Programs' / 'RepoStudio'
        backup = Path(env['LOCALAPPDATA']) / 'RepoStudio' / 'backup' / 'previous-release'
        data = Path(env['LOCALAPPDATA']) / 'RepoStudio' / 'data'
        config = Path(env['APPDATA']) / 'repo-studio' / 'launch.json'
        invoke(script, env, '-Repository', repo)
        assert (base / 'studio.py').is_file()
        assert os.path.samefile(json.loads(config.read_text(encoding='utf-8'))['repo'], repo)
        assert not backup.exists(), 'Fresh install must not create a previous-release backup'
        # Simulate an older installed code release. Updating should back this up.
        (base / 'previous_marker.txt').write_text('original-code', encoding='utf-8')
        data.mkdir(parents=True, exist_ok=True)
        (data / 'user_state.txt').write_text('preserve', encoding='utf-8')
        # Inject a failure after code replacement but before config commit.
        # The old code, config and state must all survive unchanged.
        fault_env = dict(env)
        fault_env['REPO_STUDIO_QA_FAIL_BEFORE_CONFIG_COMMIT'] = '1'
        invoke(script, fault_env, '-Repository', repo, expect_ok=False)
        assert (base / 'previous_marker.txt').read_text(encoding='utf-8') == 'original-code'
        assert not backup.exists(), 'Failed update consumed the rollback slot'
        assert os.path.samefile(json.loads(config.read_text(encoding='utf-8'))['repo'], repo)
        assert (data / 'user_state.txt').read_text(encoding='utf-8') == 'preserve'
        invoke(script, env)  # Upgrade, keeping launch.json.
        assert not (base / 'previous_marker.txt').exists()
        assert (backup / 'previous_marker.txt').read_text(encoding='utf-8') == 'original-code'
        assert (data / 'user_state.txt').read_text(encoding='utf-8') == 'preserve'
        assert os.path.samefile(json.loads(config.read_text(encoding='utf-8'))['repo'], repo)
        invoke(script, env, expect_ok=False)  # Existing rollback backup must block upgrades.
        assert (backup / 'previous_marker.txt').is_file()
        invoke(script, env, '-Rollback')
        assert (base / 'previous_marker.txt').read_text(encoding='utf-8') == 'original-code'
        assert (data / 'user_state.txt').read_text(encoding='utf-8') == 'preserve'
        assert os.path.samefile(json.loads(config.read_text(encoding='utf-8'))['repo'], repo)
        print('WINDOWS_INSTALL_UPDATE_ROLLBACK_PASS (native Windows isolated profile)')


if __name__ == '__main__':
    main()
