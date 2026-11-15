"""Full local HTTP journey against a disposable Git repository and SQLite database."""
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from studio import Handler, State
from workspace import Workspace


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def request(url, path, state, payload=None):
    headers = {'Content-Type': 'application/json', 'Origin': url, 'X-Repo-Studio-Token': state.token}
    data = json.dumps(payload).encode() if payload is not None else None
    with urllib.request.urlopen(urllib.request.Request(url+path, data=data, headers=headers if data else {}, method='POST' if data else 'GET'), timeout=15) as response:
        return json.load(response)


with tempfile.TemporaryDirectory() as td:
    base = pathlib.Path(td)
    repo = base/'repo';repo.mkdir()
    git(repo, 'init', '-q');git(repo, 'config', 'user.name', 'QA');git(repo, 'config', 'user.email', 'qa@example.invalid')
    (repo/'a.py').write_text('import b\n\ndef alpha():\n    return b.beta()\n')
    (repo/'b.py').write_text('import a\n\ndef beta():\n    return 1\n')
    git(repo, 'add', '.');git(repo, 'commit', '-qm', 'first')
    old = git(repo, 'rev-parse', 'HEAD')
    state = State(repo, base/'data')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler);server.state = state
    thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        analysis = request(url, '/api/analysis', state)
        cycle = analysis['cycles'][0]['id']
        review = request(url, '/api/workspace/update', state, {
            'kind':'cycle','id':cycle,'progress':'reviewed','decision':'investigate','notes':'Verify consumers and imports'
        })
        assert set(json.loads(review['source_paths'])) == {'a.py', 'b.py'}
        request(url, '/api/workspace/export', state, {
            'kind':'cycle','id':cycle,'level':'balanced','method':'copy','sha256':'a'*64
        })
        result = request(url, '/api/workspace/history', state)
        assert result['total'] == 1 and result['items'][0]['export_count'] == 1
        assert result['items'][0]['revalidation'] == 'current_snapshot'
        assert result['items'][0]['decision'] == 'investigate'
        assert git(repo, 'status', '--porcelain') == ''
    finally:
        server.shutdown();server.server_close();thread.join(timeout=3)
    # Restart the application state, rather than relying on an in-memory cache.
    new_state = State(repo, base/'data')
    assert new_state.workspace.list(repo,old)[0]['notes'] == 'Verify consumers and imports'
    assert len(new_state.workspace.list(repo,old)[0]['exports']) == 1
    (repo/'a.py').write_text('import b\n\ndef alpha():\n    return b.beta()+1\n')
    git(repo, 'add', '.');git(repo, 'commit', '-qm', 'second')
    new = git(repo, 'rev-parse', 'HEAD')
    assert new_state.workspace.list(repo,new) == []
    historical = Workspace.revalidation(new_state.workspace.history(repo)['items'],repo,new)
    assert historical[0]['revalidation'] == 'source_changed'
    assert historical[0]['decision'] == 'investigate'
    assert git(repo, 'status', '--porcelain') == ''
    print('INTEGRATION_JOURNEY_PASS: analysis -> save -> export -> restart -> commit change -> historical revalidation')
