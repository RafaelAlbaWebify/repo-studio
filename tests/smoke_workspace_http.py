import json, pathlib, subprocess, tempfile, threading, urllib.request, socket, sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from studio import State,Handler
from http.server import ThreadingHTTPServer
with tempfile.TemporaryDirectory() as td:
 base=pathlib.Path(td);repo=base/'repo';repo.mkdir()
 def git(*args):subprocess.run(['git',*args],cwd=repo,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 git('init');git('config','user.email','x@example.org');git('config','user.name','x')
 (repo/'main.py').write_text('def hello():\n    return 1\n');git('add','.');git('commit','-m','init')
 state=State(repo,base/'data')
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.state=state
 threading.Thread(target=server.serve_forever,daemon=True).start()
 url=f'http://127.0.0.1:{server.server_port}'
 def get(path):return json.load(urllib.request.urlopen(url+path))
 assert get('/api/workspace/history')['total']==0
 headers={'Content-Type':'application/json','Origin':url,'X-Repo-Studio-Token':state.token}
 payload={'kind':'cycle','id':'x','progress':'reviewing','decision':'investigate','notes':'test'}
 req=urllib.request.Request(url+'/api/workspace/update',data=json.dumps(payload).encode(),headers=headers,method='POST')
 assert json.load(urllib.request.urlopen(req))['progress']=='reviewing'
 assert get('/api/workspace/history')['total']==1
 assert get('/api/workspace')['items'][0]['notes']=='test'
 assert b'workspaceLedger' in urllib.request.urlopen(url).read()
 assert 'function wsLoadHistory' in urllib.request.urlopen(url+'/workspace.js').read().decode()
 server.shutdown();server.server_close()
 assert State(repo,base/'data').workspace.history(repo)['total']==1
 assert subprocess.run(['git','status','--porcelain'],cwd=repo,capture_output=True,text=True).stdout==''
 print('HTTP/API/SQLite persistence/read-only smoke PASS')
