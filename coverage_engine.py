"""Evidence-based audit coverage for a committed Git tree (read-only)."""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import subprocess
import time

DYNAMIC_NAMES = frozenset({'getattr', 'globals', 'locals', 'eval', 'exec'})
MAX_SOURCE_BYTES = 300_000


def _git(repo, *args, timeout=120):
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          capture_output=True, timeout=timeout).stdout


def _inventory(repo, commit):
    # `ls-tree --long` includes size and type. -z preserves arbitrary Git filenames.
    out = _git(repo, 'ls-tree', '-r', '-l', '-z', commit)
    result = []
    for raw in out.split(b'\x00'):
        if not raw:
            continue
        header, path = raw.split(b'\t', 1)
        parts = header.decode('ascii').split()
        if len(parts) != 4:
            raise ValueError('Unsupported Git tree listing')
        mode, kind, object_id, size = parts
        result.append({'path': path.decode('utf-8', 'surrogateescape'),
                       'mode': mode, 'objectType': kind,
                       'objectId': object_id, 'sizeBytes': int(size) if size.isdecimal() else None})
    return sorted(result, key=lambda row: row['path'])


def _dynamic_calls(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in DYNAMIC_NAMES:
            names.add(node.func.id)
    return sorted(names)


def coverage_report(repo, commit=None, max_analyzer_files=2500, max_bytes=MAX_SOURCE_BYTES):
    repo = str(repo)
    head = _git(repo, 'rev-parse', 'HEAD').decode('ascii').strip()
    selected = commit or head
    # Exactly one SHA is used for inventory and blob reads. Refuse a moving HEAD.
    try:
        selected = _git(repo, 'rev-parse', '--verify', f'{selected}^{{commit}}').decode('ascii').strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError('Selected commit does not exist') from exc
    if head != selected:
        raise ValueError('Repository HEAD differs from selected commit; reselect the repository')
    start = time.monotonic()
    inventory = _inventory(repo, selected)
    rows = []
    python_count = 0
    eligible_count = 0
    dynamic_files = []
    errors = []
    for entry in inventory:
        path, mode, kind, size = (entry[x] for x in ('path', 'mode', 'objectType', 'sizeBytes'))
        row = dict(entry)
        row.update({'pythonAstStatus': 'not_applicable', 'reason': None, 'dynamicCalls': []})
        if not (path.endswith('.py') and mode in ('100644', '100755') and kind == 'blob'):
            row['reason'] = ('non_python' if not path.endswith('.py') else 'non_regular_git_entry')
            rows.append(row)
            continue
        python_count += 1
        if python_count > max_analyzer_files:
            row.update(pythonAstStatus='not_run', reason='analyzer_file_limit')
        elif size is not None and size > max_bytes:
            row.update(pythonAstStatus='skipped', reason='source_size_limit')
        else:
            try:
                # Fetch blob by OID; avoids path ambiguity, encoding substitution and moving revisions.
                raw = _git(repo, 'cat-file', 'blob', entry['objectId'], timeout=30)
                if len(raw) > max_bytes:
                    row.update(pythonAstStatus='skipped', reason='source_size_limit')
                elif b'\x00' in raw:
                    row.update(pythonAstStatus='skipped', reason='binary_source')
                else:
                    source = raw.decode('utf-8', 'strict')
                    tree = ast.parse(source, filename=path)
                    row['pythonAstStatus'] = 'examined'
                    row['dynamicCalls'] = _dynamic_calls(tree)
                    eligible_count += 1
                    if row['dynamicCalls']:
                        dynamic_files.append(path)
            except (UnicodeError, SyntaxError, ValueError) as exc:
                row.update(pythonAstStatus='failed', reason=type(exc).__name__)
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                row.update(pythonAstStatus='failed', reason=type(exc).__name__)
        if row['pythonAstStatus'] in ('failed', 'skipped', 'not_run'):
            errors.append({'path':path, 'state':row['pythonAstStatus'], 'reason':row['reason']})
        rows.append(row)
    statuses = dict(sorted(Counter(r['pythonAstStatus'] for r in rows if r['path'].endswith('.py')).items()))
    all_python_accounted = (sum(statuses.values()) == python_count)
    # Mimic 0.9.8 global gate; do not interpret this as safe to remove unused functions.
    unused_eligible = all_python_accounted and statuses == {'examined': python_count} and not dynamic_files
    manifest_hash = hashlib.sha256(json.dumps(rows, ensure_ascii=True, sort_keys=True,
                                             separators=(',', ':')).encode()).hexdigest()
    result = {'schemaVersion': 1, 'repositoryCommit': selected, 'inventoryCount':len(rows),
              'pythonFileCount':python_count, 'pythonAstStates': statuses,
              'pythonAstExamined':eligible_count, 'dynamicIntrospectionFiles':dynamic_files,
              'currentUnusedGlobalGateEligible':unused_eligible,
              'pythonInventoryReconciled':all_python_accounted,
              'manifestSha256':manifest_hash,
              'elapsedSeconds':round(time.monotonic()-start, 3),
              'limits':{'maxPythonFiles':max_analyzer_files,'maxPythonSourceBytes':max_bytes},
              'engineStates':{'python_ast':'completed' if all_python_accounted and not errors else 'partial',
                              'jscpd':'not_run', 'repowise':'not_run', 'ruff':'not_integrated',
                              'pyright':'not_integrated', 'vulture':'not_integrated',
                              'bandit':'not_integrated', 'runtime_profiling':'not_integrated'},
              'limitations':['AST parsing is not a defect or runtime-performance audit',
                             'No claim of complete dynamic call graph or safe dead-code removal',
                             'Other analyzers are not executed by this report'],
              'files':rows}
    if not all_python_accounted:
        raise AssertionError('Python inventory does not reconcile')
    return result
