#!/usr/bin/env python3
"""Isolated Chromium E2E acceptance for Repo Studio 0.9.8 Workspace."""
import argparse, datetime, hashlib, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time, traceback, urllib.request, zipfile
from playwright.sync_api import sync_playwright, expect
APP = pathlib.Path(__file__).resolve().parents[1]

def run(*args, cwd=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30).stdout.strip()

def git_fixture(repo):
    repo.mkdir()
    (repo/'alpha.py').write_text('import beta\n\ndef alpha():\n    return beta.beta()\n')
    (repo/'beta.py').write_text('import alpha\n\ndef beta():\n    return 1\n')
    run('git','init','-q',str(repo)); run('git','-C',repo,'add','.')
    run('git','-C',repo,'-c','user.name=E2E','-c','user.email=e2e@example.invalid','commit','-qm','first snapshot')
    return run('git','-C',repo,'rev-parse','HEAD')

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]

def wait(url, proc):
    for _ in range(100):
        if proc.poll() is not None: raise RuntimeError('Backend terminated during startup')
        try:
            with urllib.request.urlopen(url+'/api/status', timeout=.4) as response:
                if response.status==200:return
        except Exception:time.sleep(.15)
    raise TimeoutError('Backend did not start')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=pathlib.Path,required=True)
    ap.add_argument('--chromium',type=str,default=None)
    ap.add_argument('--headed',action='store_true')
    args=ap.parse_args(); out=args.output.expanduser().resolve();out.mkdir(parents=True,exist_ok=True)
    report={'version':'0.9.8','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result':'FAIL','checks':[],'console_errors':[],'page_errors':[],'http_errors':[],'screenshots':[],'notes':['Only disposable Git fixture and dedicated SQLite are used. No existing user repositories or app installation are modified.']}
    proc=None;browser=None;ctx=None;page=None;log=None
    def snap(name):
        if page and not page.is_closed():
            dest=out/(name+'.png');page.screenshot(path=str(dest),full_page=True,timeout=8000);report['screenshots'].append(dest.name)
    def check(name,fn):
        try:
            info=fn();report['checks'].append({'name':name,'result':'PASS','details':str(info or '')[:500]});print('PASS',name,flush=True)
        except Exception as e:
            report['checks'].append({'name':name,'result':'FAIL','details':str(e)[:1000]});print('FAIL',name,str(e),flush=True)
            try:snap('FAIL-'+str(len(report['checks'])))
            except Exception:pass
            raise
    try:
        with tempfile.TemporaryDirectory(prefix='repo-studio-workspace-e2e-') as temp:
            tmp=pathlib.Path(temp);repo=tmp/'fixture';data=tmp/'sqlite';commit1=git_fixture(repo);p=port();url=f'http://127.0.0.1:{p}'
            report['fixture_commit_initial']=commit1;report['server_url']='127.0.0.1:<ephemeral>'
            log=(out/'server.log').open('w',encoding='utf-8')
            def start():
                nonlocal_placeholder=None
                env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';env['BROWSER']='true'
                for k in list(env):
                    if k.endswith(('_API_KEY','_TOKEN','_SECRET')):env.pop(k,None)
                server=subprocess.Popen([sys.executable,'-B',str(APP/'studio.py'),'--repo',str(repo),'--data',str(data),'--port',str(p)],cwd=str(APP),env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                wait(url,server);return server
            proc=start()
            with sync_playwright() as pw:
                try:
                    options={'headless':not args.headed}
                    if args.chromium: options['executable_path']=args.chromium
                    browser=pw.chromium.launch(**options)
                    ctx=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
                    ctx.tracing.start(screenshots=True,snapshots=True,sources=True)
                    page=ctx.new_page();page.set_default_timeout(12000)
                    page.on('pageerror',lambda e:report['page_errors'].append(str(e)[:800]))
                    page.on('console',lambda m:report['console_errors'].append(m.text[:800]) if m.type=='error' else None)
                    page.on('response',lambda r:report['http_errors'].append({'status':r.status,'path':r.url.split('?')[0].split(':')[0][-100:]}) if r.status>=400 else None)
                    def analyze():
                        page.locator('[data-page="analysis"]').click();page.locator('#runAnalysis').click()
                        expect(page.locator('#analysisCount')).to_contain_text('matching',timeout=25000)
                        page.locator('[data-page="insights"]').click()
                        expect(page.locator('#insightsFinding option').first).to_be_attached(timeout=15000)
                        expect(page.locator('#workspaceSave')).to_be_enabled(timeout=12000)
                        val=page.locator('#insightsFinding').input_value();assert val.startswith('cycle:'),val
                        return val
                    check('Open, analyze fixture and select cycle',lambda:(page.goto(url,wait_until='domcontentloaded'),analyze())[1])
                    snap('01-initial-analysis')
                    def save():
                        page.locator('#workspaceProgress').select_option('reviewing')
                        page.locator('#workspaceDecision').select_option('investigate')
                        page.locator('#workspaceNotes').fill('QA-098-WORKSPACE-PERSISTENCE — human decision must remain commit-specific')
                        page.locator('#workspaceSave').click()
                        expect(page.locator('#workspaceMessage')).to_contain_text('Review saved locally')
                        expect(page.locator('#workspaceHistory')).to_contain_text('Saved',timeout=12000)
                        expect(page.locator('#workspaceLedger')).to_contain_text('QA-098-WORKSPACE-PERSISTENCE')
                    check('Save progress, decision and notes',save);snap('02-review-saved')
                    def filter_ledger():
                        page.locator('#workspaceProgressFilter').select_option('reviewing')
                        page.locator('#workspaceDecisionFilter').select_option('investigate')
                        page.locator('#workspaceExportFilter').select_option('not_exported')
                        page.locator('#workspaceFilter').fill('QA-098-WORKSPACE-PERSISTENCE')
                        expect(page.locator('#workspaceLedger .workspace-ledger-entry')).to_have_count(1)
                        page.locator('#workspaceFilter').fill('unlikely-no-matches-zz')
                        expect(page.locator('#workspaceLedger')).to_contain_text('No saved investigations match')
                        page.locator('#workspaceFilter').fill('')
                        page.locator('#workspaceExportFilter').select_option('all')
                    check('History search, review and decision filters',filter_ledger)
                    def refresh():
                        page.reload(wait_until='domcontentloaded')
                        analyze()
                        expect(page.locator('#workspaceNotes')).to_have_value('QA-098-WORKSPACE-PERSISTENCE — human decision must remain commit-specific',timeout=12000)
                        expect(page.locator('#workspaceProgress')).to_have_value('reviewing')
                        expect(page.locator('#workspaceDecision')).to_have_value('investigate')
                    check('Reload browser preserves review',refresh)
                    def export():
                        page.locator('#contextLoad').click()
                        expect(page.locator('#contextDownload')).to_be_enabled(timeout=15000)
                        with page.expect_download(timeout=12000) as d:page.locator('#contextDownload').click()
                        download=d.value;destination=out/'workspace-export.md';download.save_as(str(destination))
                        raw=destination.read_text();assert commit1 in raw and 'Included source evidence' in raw
                        expect(page.locator('#workspaceHistory')).to_contain_text('exports: 1',timeout=15000)
                        page.locator('#workspaceExportFilter').select_option('exported')
                        expect(page.locator('#workspaceLedger .workspace-ledger-entry')).to_have_count(1)
                        return download.suggested_filename
                    check('Download evidence and automatically register export',export);snap('03-export-logged')
                    def restart():
                        nonlocal proc
                        proc.terminate();proc.wait(timeout=8);proc=start()
                        page.reload(wait_until='domcontentloaded');analyze()
                        expect(page.locator('#workspaceNotes')).to_have_value('QA-098-WORKSPACE-PERSISTENCE — human decision must remain commit-specific')
                        expect(page.locator('#workspaceHistory')).to_contain_text('exports: 1')
                    check('Restart backend and recover SQLite state',restart)
                    def new_commit():
                        nonlocal proc
                        proc.terminate();proc.wait(timeout=8)
                        (repo/'alpha.py').write_text('import beta\n\ndef alpha():\n    return beta.beta() + 1\n')
                        run('git','-C',repo,'add','.')
                        run('git','-C',repo,'-c','user.name=E2E','-c','user.email=e2e@example.invalid','commit','-qm','modified alpha source')
                        commit2=run('git','-C',repo,'rev-parse','HEAD');report['fixture_commit_second']=commit2
                        proc=start();page.reload(wait_until='domcontentloaded');analyze()
                        expect(page.locator('#workspaceProgress')).to_have_value('pending')
                        expect(page.locator('#workspaceDecision')).to_have_value('undecided')
                        expect(page.locator('#workspaceNotes')).to_have_value('')
                        expect(page.locator('#workspaceLedger')).to_contain_text('HISTORICAL COMMIT')
                        expect(page.locator('#workspaceLedger')).to_contain_text('Source files changed',timeout=15000)
                    check('Changed commit: historical record, no inherited decision, source revalidation',new_commit);snap('04-cross-commit')
                    def freshness():
                        page.locator('#workspaceFreshnessFilter').select_option('source_changed')
                        expect(page.locator('#workspaceLedger .workspace-ledger-entry')).to_have_count(1)
                        page.locator('#workspaceFreshnessFilter').select_option('current_snapshot')
                        expect(page.locator('#workspaceLedger .workspace-ledger-entry')).to_have_count(0)
                    check('Source revalidation filter',freshness)
                    assert not report['page_errors'],f"Browser JS errors: {report['page_errors']}"
                    assert not report['http_errors'],f"HTTP errors: {report['http_errors']}"
                    report['result']='PASS'
                finally:
                    # Stop tracing and close browser while Playwright's event loop is alive.
                    if ctx:
                        try:
                            ctx.tracing.stop(path=str(out/'playwright-trace.zip'))
                        except Exception as e:
                            report['notes'].append('Trace not saved: '+str(e))
                        try:ctx.close()
                        except Exception:pass
                    if browser:
                        try:browser.close()
                        except Exception:pass
    except Exception as e:
        report['fatal_error']=str(e)[:2500];report['traceback']=traceback.format_exc(limit=8);report['result']='BLOCKED' if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(e) else 'FAIL'
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
        if log:log.close()
        (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        with zipfile.ZipFile(out/'REPO_STUDIO_WORKSPACE_E2E_RESULTS.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.iterdir()):
                if f.is_file() and f.name!='REPO_STUDIO_WORKSPACE_E2E_RESULTS.zip':z.write(f,arcname=f.name)
        print('\nFINAL:',report['result']);print('RESULTS ZIP:',out/'REPO_STUDIO_WORKSPACE_E2E_RESULTS.zip')
    return 0 if report['result']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
