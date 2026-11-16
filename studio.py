#!/usr/bin/env python3
"""Repo Studio F1: local-only read-only repository audit UI. Python 3.10+ standard library."""
from __future__ import annotations
import argparse, hashlib, http.server, json, os, pathlib, re, secrets, shutil, subprocess, tarfile, tempfile, threading, time, urllib.parse, webbrowser
from collections import Counter
from analysis import analyze_python, export_evidence
from coverage_engine import coverage_report
from triage_engine import public_summary, filter_findings
from professional_workflow import find_finding, dossier as professional_dossier
from workspace import Workspace

ROOT=pathlib.Path(__file__).resolve().parent
MAX_BODY=8192
KEYS=('OPENAI_API_KEY','ANTHROPIC_API_KEY','GOOGLE_API_KEY','GEMINI_API_KEY','OPENROUTER_API_KEY','LITELLM_API_KEY','AWS_ACCESS_KEY_ID','AWS_SECRET_ACCESS_KEY')

def run(cmd,cwd=None,timeout=45):
    env=os.environ.copy()
    for k in KEYS: env.pop(k,None)
    env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',DO_NOT_TRACK='1',REPOWISE_SKIP_EDITOR_SETUP='1')
    p=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,timeout=timeout,stdin=subprocess.DEVNULL,errors='replace')
    if p.returncode: raise RuntimeError((p.stderr or p.stdout or 'Command failed')[-800:])
    return p.stdout

def git_root(repo):
    p=pathlib.Path(repo).expanduser().resolve(strict=True)
    if not p.is_dir(): raise ValueError('La ruta no es un directorio')
    root=pathlib.Path(run(['git','-C',str(p),'rev-parse','--show-toplevel']).strip()).resolve()
    if root!=p: raise ValueError('Selecciona la raíz del repositorio Git')
    return p

def sha(repo): return run(['git','-C',str(repo),'rev-parse','HEAD']).strip()

def safe_rel(s):
    if not isinstance(s,str) or len(s)>500 or not s or '\\' in s or '\x00' in s: raise ValueError('Ruta no válida')
    p=pathlib.PurePosixPath(s)
    if p.is_absolute() or any(x in ('..','.') for x in s.split('/')): raise ValueError('Ruta no válida')
    return s

def entries(repo, commit="HEAD"):
    raw=subprocess.run(['git','-C',str(repo),'ls-tree','-rz','--name-only',commit],capture_output=True,check=True).stdout
    names=[x.decode('utf-8','replace') for x in raw.split(b'\x00') if x]
    return [x for x in names if not x.startswith('.git/')][:12000]

def file_at(repo,path,commit="HEAD"):
    safe_rel(path)
    files=set(entries(repo, commit))
    if path not in files: raise ValueError('Archivo no encontrado en HEAD')
    p=subprocess.run(['git','-C',str(repo),'show',commit+':'+path],capture_output=True,timeout=15)
    if p.returncode: raise ValueError('No es posible leer el archivo')
    if len(p.stdout)>300000 or b'\x00' in p.stdout: raise ValueError('Archivo binario o demasiado grande para previsualizar')
    return p.stdout.decode('utf-8','replace')

def snapshot_archive(repo,dest):
    dest.mkdir(parents=True,exist_ok=True)
    p=subprocess.Popen(['git','-C',str(repo),'archive','--format=tar','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=p.stdout,mode='r|') as tf:
            count=0
            for member in tf:
                count+=1
                if count>100000: raise ValueError('Archivo demasiado grande')
                name=member.name
                if name.startswith('/') or '\\' in name or '..' in pathlib.PurePosixPath(name).parts or not name: raise ValueError('Ruta insegura en Git archive')
                target=(dest/name).resolve()
                if dest.resolve()!=target and dest.resolve() not in target.parents: raise ValueError('Fuera del snapshot')
                if member.isdir(): target.mkdir(parents=True,exist_ok=True)
                elif member.isfile():
                    if member.size>50*1024*1024: continue
                    target.parent.mkdir(parents=True,exist_ok=True)
                    src=tf.extractfile(member)
                    if src:
                        with target.open('wb') as out: shutil.copyfileobj(src,out)
                # Ignore symlinks/hardlinks/devices to prohibit target escape
        err=p.stderr.read().decode('utf-8','replace')
        if p.wait(timeout=10): raise RuntimeError(err[-500:])
    finally:
        if p.poll() is None: p.kill();p.wait()
        if p.stdout: p.stdout.close()
        if p.stderr: p.stderr.close()

def duplicates_doc(report):
    d=json.loads(pathlib.Path(report).read_text())
    if not isinstance(d.get('duplicates'),list): raise ValueError('Formato de jscpd no válido')
    stats=d.get('statistics',{}).get('total',{})
    items=[]
    for idx,x in enumerate(d['duplicates']):
        a=x.get('firstFile',{}); b=x.get('secondFile',{})
        ap=a.get('name','');bp=b.get('name','')
        if not isinstance(ap,str) or not isinstance(bp,str):continue
        group='production' if ap.startswith('src/') and bp.startswith('src/') else ('tests' if ap.startswith('tests/') and bp.startswith('tests/') else 'other')
        items.append({'id':idx,'first':ap,'second':bp,'firstLine':a.get('start'),'secondLine':b.get('start'),'lines':x.get('lines',0),'language':x.get('format',''),'group':group,'fragment':str(x.get('fragment',''))[:1000]})
    items.sort(key=lambda x:(x['group']!='production',-(x['lines'] if isinstance(x['lines'],int) else 0)))
    return {'stats':stats,'items':items,'groups':dict(Counter(x['group'] for x in items))}


def _merged_size(intervals):
    """Count covered lines once even if detector ranges overlap."""
    merged=[]
    for begin,end in sorted(intervals):
        if not merged or begin>merged[-1][1]+1: merged.append([begin,end])
        else: merged[-1][1]=max(merged[-1][1],end)
    return sum(end-begin+1 for begin,end in merged)


def finding_cases(dups,commit):
    """Deterministic, non-prescriptive review cases grouped by source-file pair."""
    grouped={}
    for item in dups.get('items',[]):
        first,second=item.get('first'),item.get('second')
        start_a,start_b=item.get('firstLine'),item.get('secondLine')
        count=item.get('lines')
        if not isinstance(first,str) or not isinstance(second,str): continue
        if not isinstance(start_a,int) or not isinstance(start_b,int) or not isinstance(count,int):continue
        if min(start_a,start_b,count)<1 or count>100000:continue
        # Canonicalize source order so reversed matches form one case.
        a,b=sorted((first,second))
        line_a,line_b=(start_a,start_b) if a==first else (start_b,start_a)
        key=(a,b)
        if key not in grouped:
            identity=hashlib.sha256((commit+'\0'+a+'\0'+b).encode()).hexdigest()[:16]
            grouped[key]={'id':identity,'first':a,'second':b,'group':item['group'],
                          'language':item.get('language',''),'matches':[], 'reviewStatus':'unreviewed',
                          'decision':'No change proposed'}
        grouped[key]['matches'].append({'duplicationId':item['id'],'firstLine':line_a,'secondLine':line_b,'lines':count})
    cases=[]
    for case in grouped.values():
        matches=case['matches']
        case['matches']=sorted(matches,key=lambda m:(-m['lines'],m['firstLine'],m['secondLine']))
        case['count']=len(matches)
        case['coveredLinesA']=_merged_size([(m['firstLine'],m['firstLine']+m['lines']-1) for m in matches])
        case['coveredLinesB']=_merged_size([(m['secondLine'],m['secondLine']+m['lines']-1) for m in matches])
        case['reviewTopics']=['Confirm equivalent behavior and intended differences',
                              'Check consumers, tests and dynamic usage',
                              'Assess whether extraction reduces overall complexity']
        sensitive=('auth','identity','tenant','security','permission','token','invitation','password','session','sqlite','database','migration')
        if any(keyword in (case['first']+' '+case['second']).lower() for keyword in sensitive):
            case['reviewTopics'].insert(0,'Security or persistence-sensitive code: verify boundaries separately')
        case['limitations']=['Similarity does not imply unnecessary code',
                             'No call-site completeness or behavioral equivalence verified',
                             'No tests executed on this proposed change; no refactoring performed']
        cases.append(case)
    cases.sort(key=lambda c:(c['group']!='production',-(c['coveredLinesA']+c['coveredLinesB']),c['first'],c['second']))
    return {'commit':commit,'caseCount':len(cases),'matchCount':sum(c['count'] for c in cases),
            'cases':cases,'method':'jscpd file-pair grouping with merged intervals; not a refactoring recommendation'}

class State:
    def __init__(self,repo,data,jscpd=None,index=None,repowise=None,jscpd_bin=None,triage_report=None):
        self.lock=threading.Lock();self.busy=False;self.error=None;self.latest=None
        self.repo=git_root(repo);self.commit=sha(self.repo)
        self.data=pathlib.Path(data).expanduser().resolve();self.data.mkdir(parents=True,exist_ok=True)
        if self.repo==self.data or self.repo in self.data.parents: raise ValueError('Los informes deben guardarse fuera del repositorio')
        self.jscpd_bin=jscpd_bin or shutil.which('jscpd')
        self.repowise=repowise or shutil.which('repowise')
        self.index=pathlib.Path(index).expanduser().resolve() if index else None
        self.report=pathlib.Path(jscpd).expanduser().resolve() if jscpd else None
        self.token=secrets.token_urlsafe(32)
        self.workspace=Workspace(self.data)
        self._analysis_cache=None
        self.triage_report_path=pathlib.Path(triage_report).expanduser().resolve() if triage_report else None
        self._triage_cache=None
    def status(self):
        return {'repository':str(self.repo),'commit':self.commit,'busy':self.busy,'error':self.error,'reportReady':bool(self.report and self.report.is_file()),'jscpdAvailable':bool(self.jscpd_bin),'repowiseAvailable':bool(self.repowise),'indexReady':bool(self.index and self.index.is_dir()),'dataPath':str(self.data),'token':self.token}
    def select(self,p):
        r=git_root(p);commit=sha(r)
        if r==self.data or r in self.data.parents:raise ValueError('La carpeta de resultados no puede estar dentro del repositorio')
        with self.lock:
            if self.busy:raise ValueError('Hay una auditoría en curso')
            self.repo=r;self.commit=commit;self.report=None;self.index=None;self.error=None;self._analysis_cache=None;self._triage_cache=None
    def start_audit(self):
        with self.lock:
            if self.busy: raise ValueError('Ya hay una auditoría en curso')
            if not self.jscpd_bin: raise ValueError('No se encuentra jscpd; indica --jscpd-bin')
            self.busy=True;self.error=None
        threading.Thread(target=self.audit,daemon=True).start()
    def audit(self):
        try:
            head=sha(self.repo)
            if head!=self.commit:raise ValueError('HEAD ha cambiado. Vuelve a seleccionar el repositorio')
            out=self.data / hashlib.sha256((str(self.repo)+self.commit).encode()).hexdigest()[:16]
            out.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='repo-studio-') as td:
                snap=pathlib.Path(td)/'snapshot';snapshot_archive(self.repo,snap)
                rpt=out/'jscpd';rpt.mkdir(exist_ok=True)
                run([str(self.jscpd_bin),str(snap),'--reporters','json,html','--output',str(rpt),'--min-lines','5','--min-tokens','50'],cwd=td,timeout=180)
            dest=out/'jscpd/jscpd-report.json'
            duplicates_doc(dest)
            self.report=dest;self.latest=time.time()
        except Exception as e:
            self.error=str(e)[:600]
        finally:
            with self.lock:self.busy=False
    def coverage(self):
        self.require_selected_commit()
        return coverage_report(self.repo, self.commit)

    def triage(self):
        self.require_selected_commit()
        if self.triage_report_path is None:
            raise ValueError('No imported professional analysis configured; use --triage-report')
        with self.lock:
            if self._triage_cache is not None:
                return self._triage_cache
        report=json.loads(self.triage_report_path.read_text(encoding='utf-8'))
        if report.get('repositoryCommit') != self.commit or not isinstance(report.get('findings'),list):
            raise ValueError('Imported triage report does not match the selected Git commit')
        with self.lock:
            self._triage_cache=report
        return report

    def analysis(self):
        # Pin to the selected commit; do not silently analyze a different HEAD.
        if sha(self.repo)!=self.commit:
            raise ValueError('HEAD changed. Reselect repository to analyze current commit.')
        with self.lock:
            if self._analysis_cache is not None:
                return self._analysis_cache
        paths=entries(self.repo, self.commit)
        known=set(paths)
        def committed_source(name):
            if name not in known:raise ValueError('Not tracked in HEAD')
            result=subprocess.run(['git','-C',str(self.repo),'show',self.commit+':'+name],
                                  capture_output=True,timeout=15)
            if result.returncode or len(result.stdout)>300_000 or b'\x00' in result.stdout:
                raise ValueError('Source unavailable or too large')
            return result.stdout.decode('utf-8','replace')
        result=analyze_python(paths,committed_source,self.commit)
        with self.lock:
            if self._analysis_cache is None:
                self._analysis_cache=result
            return self._analysis_cache
    def finding_source_paths(self,kind,fid):
        """Only derive source paths from a finding actually detected at this commit."""
        if kind=='professional':
            return [find_finding(self.triage(),fid)['path']]
        if kind=='duplication':
            if not self.report or not self.report.is_file():return None
            candidates=finding_cases(duplicates_doc(self.report),self.commit)['cases']
        elif kind in ('cycle','complexity','unused'):
            candidates=self.analysis()[{'cycle':'cycles','complexity':'complexity','unused':'unused'}[kind]]
        else:
            return None
        finding=next((x for x in candidates if x['id']==fid),None)
        if finding is None:return None
        paths=(finding.get('files') if kind=='cycle' else
               [finding['first'],finding['second']] if kind=='duplication' else
               [finding['file']])
        return paths if paths and len(paths)<=40 else None

    def evidence(self,kind,fid,level):
        if sha(self.repo)!=self.commit:
            raise ValueError('HEAD changed. Reselect repository first.')
        if kind=='duplication':
            doc=duplicates_doc(self.report) if self.report and self.report.is_file() else {'items':[]}
            findings=finding_cases(doc,self.commit)['cases']
        elif kind in ('cycle','complexity','unused'):
            findings=self.analysis()[{'cycle':'cycles','complexity':'complexity','unused':'unused'}[kind]]
        else:
            raise ValueError('Unknown finding category')
        selected=next((f for f in findings if f['id']==fid),None)
        if not selected:raise ValueError('Finding not found for this commit')
        return export_evidence(selected,kind,self.commit,lambda name:file_at(self.repo,name,self.commit),level,self.repo.name)
    def source_range(self,path,first,last):
        """Explicit, bounded source-line retrieval from the pinned Git commit."""
        self.require_selected_commit()
        try:
            first=int(first);last=int(last)
        except (TypeError,ValueError):
            raise ValueError('Invalid source line range')
        if first < 1 or last < first or last-first+1 > 120:
            raise ValueError('Source range must contain 1-120 lines')
        if path not in entries(self.repo,self.commit):
            raise ValueError('File not tracked at selected commit')
        source=file_at(self.repo,path,self.commit)
        lines=source.splitlines()
        if last > len(lines):
            raise ValueError('Requested lines exceed file length')
        return {'path':path,'firstLine':first,'lastLine':last,'commit':self.commit,
                'sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
                'snippet':'\n'.join(f'{n:5d} {lines[n-1]}' for n in range(first,last+1)),
                'reason':'User-requested supplementary committed source',
                'targetLine':first,'targetEndLine':last,'targetFullyIncluded':True,'truncated':False,
                'uncoveredTargetRanges':[]}

    def require_selected_commit(self):
        if sha(self.repo) != self.commit:
            raise ValueError('HEAD changed. Reselect repository first.')

    def search(self,query):
        # RS_INDEX_COMMIT_GUARD_V1: never search stale or wrong-repository index.
        self.require_selected_commit()
        if self.index is not None and self.index.is_dir() and sha(self.index) != self.commit:
            raise ValueError('Repowise index commit does not match selected repository')
        if not self.index or not self.index.is_dir():raise ValueError('Índice Repowise no configurado')
        if not self.repowise:raise ValueError('Repowise no instalado')
        if not query or len(query)>120:raise ValueError('Consulta no válida')
        raw=run([str(self.repowise),'search',query,'--mode','symbol','--limit','20','--format','json'],cwd=self.index,timeout=30)
        return json.loads(raw)
    def context(self,path):
        safe_rel(path)
        self.require_selected_commit()
        if path not in set(entries(self.repo,self.commit)):
            raise ValueError('Archivo no encontrado en HEAD')
        if self.index is not None and self.index.is_dir() and sha(self.index) != self.commit:
            raise ValueError('Repowise index commit does not match selected repository')
        if not self.index or not self.index.is_dir():
            raise ValueError('Índice Repowise no configurado')
        if not self.repowise:
            raise ValueError('Repowise no instalado')
        raw=run([str(self.repowise),'context',path,'--include','callers','--include','callees','--full'],cwd=self.index,timeout=45)
        data=json.loads(raw)
        if len(raw)>2_000_000: raise ValueError('Contexto demasiado grande')
        return data

class Handler(http.server.BaseHTTPRequestHandler):
    server_version='RepoStudio/0.8'
    def log_message(self,fmt,*args):pass
    def local_request(self):
        # Host allowlist prevents a remote DNS-rebinding name from accessing the UI/API.
        host = self.headers.get('Host', '')
        port = self.server.server_port
        return host in (f'127.0.0.1:{port}', f'localhost:{port}')
    def forbidden(self):
        self.respond({'error':'Host no autorizado'},403)
    def respond(self,data,status=200):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def static(self,name,ctype):
        body=(ROOT/'static'/name).read_bytes()
        self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'");self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if not self.local_request(): return self.forbidden()
        try:
            p=urllib.parse.urlparse(self.path);q=urllib.parse.parse_qs(p.query);s=self.server.state
            if p.path=='/':return self.static('index.html','text/html; charset=utf-8')
            if p.path=='/csp_styles.js':return self.static('csp_styles.js','text/javascript; charset=utf-8')
            if p.path=='/app.js':return self.static('app.js','text/javascript; charset=utf-8')
            if p.path=='/triage_ui.js':return self.static('triage_ui.js','text/javascript; charset=utf-8')
            if p.path=='/professional_workflow_ui.js':return self.static('professional_workflow_ui.js','text/javascript; charset=utf-8')
            if p.path=='/compare.js':return self.static('compare.js','text/javascript; charset=utf-8')
            if p.path=='/analysis.js':return self.static('analysis.js','text/javascript; charset=utf-8')
            if p.path=='/dashboard.js':return self.static('dashboard.js','text/javascript; charset=utf-8')
            if p.path=='/insights.js':return self.static('insights.js','text/javascript; charset=utf-8')
            if p.path=='/context_builder.js':return self.static('context_builder.js','text/javascript; charset=utf-8')
            if p.path=='/workspace.js':return self.static('workspace.js','text/javascript; charset=utf-8')
            if p.path=='/style.css':return self.static('style.css','text/css; charset=utf-8')
            if p.path=='/favicon.svg':return self.static('favicon.svg','image/svg+xml; charset=utf-8')
            if p.path=='/repo-studio-icon.svg':return self.static('repo-studio-icon.svg','image/svg+xml; charset=utf-8')
            if p.path=='/repo-studio-icon.png':return self.static('repo-studio-icon.png','image/png')
            if p.path=='/repo-studio-logo.svg':return self.static('repo-studio-logo.svg','image/svg+xml; charset=utf-8')
            if p.path=='/support.js':return self.static('support.js','text/javascript; charset=utf-8')
            if p.path=='/help-dashboard.png':return self.static('help-dashboard.png','image/png')
            if p.path=='/help-context.png':return self.static('help-context.png','image/png')
            if p.path=='/api/status':return self.respond(s.status())
            if p.path=='/api/workspace':return self.respond({'items':s.workspace.list(s.repo,s.commit),'commit':s.commit})
            if p.path=='/api/workspace/history':
                ledger=s.workspace.history(s.repo)
                ledger['items']=s.workspace.revalidation(ledger['items'],s.repo,s.commit)
                return self.respond({**ledger,'current_commit':s.commit})
            if p.path=='/api/files':s.require_selected_commit();return self.respond({'files':entries(s.repo,s.commit),'commit':s.commit})
            if p.path=='/api/file':s.require_selected_commit();return self.respond({'content':file_at(s.repo,q.get('path',[''])[0],s.commit)})
            if p.path=='/api/duplicates':return self.respond(duplicates_doc(s.report) if s.report and s.report.is_file() else {'stats':{},'items':[],'groups':{}})
            if p.path=='/api/findings':return self.respond(finding_cases(duplicates_doc(s.report) if s.report and s.report.is_file() else {'items':[]},s.commit))
            if p.path=='/api/analysis':return self.respond(s.analysis())
            if p.path=='/api/triage':return self.respond(public_summary(s.triage()))
            if p.path=='/api/professional/dossier':
                s.require_selected_commit()
                pkg=professional_dossier(s.triage(),q.get('id',[''])[0],s.commit,
                    lambda path:file_at(s.repo,path,s.commit),q.get('level',['balanced'])[0])
                return self.respond(pkg)
            if p.path=='/api/triage/findings':
                def arg(name,default):return q.get(name,[default])[0]
                return self.respond(filter_findings(s.triage(),area=arg('area','all'),queue=arg('queue','all'),
                    analyzer=arg('analyzer','all'),hide_noise=arg('hide_noise','0')=='1',
                    offset=int(arg('offset','0')),limit=int(arg('limit','50'))))
            if p.path=='/api/coverage':return self.respond(s.coverage())
            if p.path=='/api/evidence':return self.respond(s.evidence(q.get('type',[''])[0],q.get('id',[''])[0],q.get('level',['balanced'])[0]))
            if p.path=='/api/source-range':return self.respond(s.source_range(q.get('path',[''])[0],q.get('first',[''])[0],q.get('last',[''])[0]))
            if p.path=='/api/search':return self.respond(s.search(q.get('q',[''])[0]))
            if p.path=='/api/context':return self.respond(s.context(q.get('path',[''])[0]))
            return self.respond({'error':'No encontrado'},404)
        except Exception as e:self.respond({'error':str(e)[:400]},400)
    def do_POST(self):
        if not self.local_request(): return self.forbidden()
        try:
            origin=self.headers.get('Origin','');host=self.headers.get('Host','')
            if origin != 'http://'+host:raise ValueError('Origen no autorizado')
            if self.headers.get('X-Repo-Studio-Token')!=self.server.state.token:raise ValueError('Token incorrecto')
            n=int(self.headers.get('Content-Length','0'))
            if n<0 or n>MAX_BODY:raise ValueError('Petición demasiado grande')
            body=json.loads(self.rfile.read(n)) if n else {}
            p=urllib.parse.urlparse(self.path).path;s=self.server.state
            if p=='/api/select':s.select(body.get('path',''));return self.respond(s.status())
            if p=='/api/workspace/update':
                s.require_selected_commit()
                if body.get('kind')=='professional':
                    find_finding(s.triage(),body.get('id'))
                return self.respond(s.workspace.update(s.repo,s.commit,body.get('kind'),body.get('id'),body.get('progress'),body.get('decision'),body.get('notes'),s.finding_source_paths(body.get('kind'),body.get('id'))))
            if p=='/api/workspace/export':
                s.require_selected_commit()
                return self.respond(s.workspace.exported(s.repo,s.commit,body.get('kind'),body.get('id'),body.get('level'),body.get('method'),body.get('sha256')))
            if p=='/api/audit':
                s.start_audit()
                return self.respond({'started':True},202)
            return self.respond({'error':'No encontrado'},404)
        except Exception as e:self.respond({'error':str(e)[:400]},400)

def is_windows():
    return os.name == 'nt'

def default_data_dir():
    if is_windows():
        base = pathlib.Path(os.environ.get('LOCALAPPDATA') or (pathlib.Path.home() / 'AppData' / 'Local'))
        return base / 'RepoStudio' / 'data'
    base = pathlib.Path(os.environ.get('XDG_STATE_HOME') or (pathlib.Path.home() / '.local' / 'state'))
    return base / 'repo-studio'

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--repo',required=True);a.add_argument('--data',default=str(default_data_dir()))
    a.add_argument('--jscpd-report');a.add_argument('--repowise-index');a.add_argument('--jscpd-bin');a.add_argument('--repowise-bin');a.add_argument('--port',type=int,default=8765)
    a.add_argument('--triage-report',help='Previously normalized read-only analysis report (JSON)')
    opts=a.parse_args(argv)
    state=State(opts.repo,opts.data,opts.jscpd_report,opts.repowise_index,opts.repowise_bin,opts.jscpd_bin,opts.triage_report)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',opts.port),Handler);server.state=state
    print(f'Repo Studio: http://127.0.0.1:{server.server_port}',flush=True)
    print('Solo lectura. Ctrl+C para salir.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
