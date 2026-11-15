#!/usr/bin/env python3
"""Repo Studio browser E2E: isolated Git fixture + local server + Playwright.

No writes to installed Repo Studio, the user’s actual repositories.
Outputs are created in a user-specified --output directory or Downloads.
"""
from __future__ import annotations
import argparse, json, os, pathlib, shutil, socket, subprocess, sys, tempfile, time, traceback, urllib.request, zipfile
from datetime import datetime, timezone

APP=pathlib.Path(__file__).resolve().parents[1]

def command(*args,cwd=None):
    return subprocess.run(list(map(str,args)),cwd=cwd,check=True,capture_output=True,text=True,timeout=30)

def fixture(repo):
    repo.mkdir()
    (repo/'alpha.py').write_text("""import beta

def _unused_helper(x):
    return x + 2

def complex_example(a, b, c, d):
    if a:
        if b:
            if c:
                if d:
                    return 1
    return 0
""",encoding='utf-8')
    (repo/'beta.py').write_text("""import alpha

def other():
    return 3
""",encoding='utf-8')
    command('git','init','-q',repo)
    command('git','-C',repo,'add','.')
    command('git','-C',repo,'-c','user.email=e2e@example.invalid','-c','user.name=E2E Fixture','commit','-qm','isolated E2E fixture')
    return command('git','-C',repo,'rev-parse','HEAD').stdout.strip()

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]

def wait_up(url,process):
    for _ in range(90):
        if process.poll() is not None:raise RuntimeError('Server exited before readiness')
        try:
            with urllib.request.urlopen(url+'/api/status',timeout=0.3) as r:
                if r.status==200:return
        except Exception:time.sleep(0.15)
    raise RuntimeError('Server did not become ready')

def main():
    parser=argparse.ArgumentParser(description='Isolated Playwright E2E tests for Repo Studio')
    parser.add_argument('--output',type=pathlib.Path,default=pathlib.Path.home()/'Downloads'/'repo-studio-e2e-results')
    parser.add_argument('--chromium',default=None,help='Optional absolute path to Chromium; otherwise Playwright bundled Chromium')
    parser.add_argument('--headed',action='store_true',help='Show browser during tests')
    args=parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright, expect
    except ImportError:
        print('MISSING DEPENDENCY: python -m pip install playwright && python -m playwright install chromium',file=sys.stderr)
        return 2
    out=args.output.expanduser().resolve()
    out.mkdir(parents=True,exist_ok=True)
    for stale in out.iterdir():
        if stale.is_file() and (stale.name.startswith(('FAIL-', '0')) and stale.suffix=='.png' or stale.name in ('report.json','REPO_STUDIO_E2E_RESULTS.zip','server.log','evidence-export.md','evidence-export.json')):
            stale.unlink()
    report={'timestamp':datetime.now(timezone.utc).isoformat(),'suite':'Repo Studio 0.8.4 E2E dependency explorer','checks':[],'browser_errors':[],'console_errors':[],'http_errors':[],'screenshots':[],'downloads':[],'environment':{'python':sys.version.split()[0],'chromium':args.chromium or 'Playwright-managed'},'result':'incomplete'}
    page=None
    def check(name,action):
        try:
            details=action();report['checks'].append({'name':name,'status':'PASS','details':str(details or '')[:600]});return True
        except Exception as exc:
            report['checks'].append({'name':name,'status':'FAIL','error':str(exc)[:1200]})
            # A failed check must not leave a dialog open and block later tests.
            try:
                if page and not page.is_closed():
                    name_slug=''.join(c if c.isalnum() else '-' for c in name.lower())[:55]
                    path=out/('FAIL-'+name_slug+'.png')
                    page.screenshot(path=str(path),full_page=True,timeout=3000)
                    report['screenshots'].append(path.name)
            except Exception:
                pass
            return False
    with tempfile.TemporaryDirectory(prefix='repo-studio-e2e-') as tmp:
        temp=pathlib.Path(tmp); repo=temp/'fixture';commit=fixture(repo);port=free_port()
        url=f'http://127.0.0.1:{port}'
        report['fixture_commit']=commit
        log_path=out/'server.log'
        with log_path.open('w',encoding='utf-8') as serverlog:
            env=os.environ.copy()
            for k in list(env):
                if k.endswith('_API_KEY') or k.endswith('_TOKEN') or k.endswith('_SECRET'):env.pop(k,None)
            env.update(PYTHONDONTWRITEBYTECODE='1',BROWSER='true')
            proc=subprocess.Popen([sys.executable,'-B',str(APP/'studio.py'),'--repo',str(repo),'--data',str(temp/'data'),'--port',str(port)],stdin=subprocess.DEVNULL,stdout=serverlog,stderr=subprocess.STDOUT,env=env,cwd=str(APP))
            try:
                wait_up(url,proc)
                with sync_playwright() as p:
                    opts={'headless':not args.headed,'args':['--no-sandbox']}
                    if args.chromium:opts['executable_path']=args.chromium
                    browser=p.chromium.launch(**opts)
                    try:
                        ctx=browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True)
                        page=ctx.new_page();page.set_default_timeout(5000)
                        page.on('pageerror',lambda exc:report['browser_errors'].append(str(exc)[:500]))
                        page.on('console',lambda msg:report['console_errors'].append({'text':msg.text[:500], 'location':msg.location}) if msg.type=='error' else None)
                        page.on('response',lambda r:report['http_errors'].append({'url':r.url.split('?')[0],'status':r.status}) if r.status>=400 else None)
                        def screenshot(name):
                            path=out/(name+'.png');page.screenshot(path=str(path),full_page=True,animations='disabled');report['screenshots'].append(path.name)
                        def overview():
                            page.goto(url,wait_until='domcontentloaded',timeout=15000)
                            expect(page.locator('#filesCount')).to_have_text('2',timeout=10000)
                            assert page.locator('#commit').inner_text().strip()!='—'
                            screenshot('01-overview');return '2 tracked source files and commit shown'
                        if not check('Overview and committed Git identity',overview):
                            raise RuntimeError('Overview E2E failed; remaining UI checks skipped')
                        def health():
                            page.locator('[data-page="analysis"]').click()
                            page.locator('#runAnalysis').click()
                            expect(page.locator('#analysisCount')).to_contain_text('matching',timeout=20000)
                            note=page.locator('#analysisNote').inner_text()
                            assert 'import cycles' in note and 'unused candidates' in note, note
                            screenshot('02-code-health');return note
                        check('Code health scan',health)
                        def dashboard():
                            page.locator('[data-page="overview"]').click()
                            expect(page.locator('#dashCycles')).to_have_text('1')
                            assert int(page.locator('#dashPython').inner_text()) == 2
                            assert page.locator('#dashToolStates').get_by_text('Not analyzed').count() >= 0
                            assert page.locator('#dashComplexity').inner_text().strip().isdigit()
                            assert page.locator('#dashDonutTotal').inner_text().strip() != '—'
                            assert page.locator('#dashDistribution .dash-legend-row').count() >= 2
                            assert page.locator('#dashPriority .dash-queue-item').count() >= 1
                            assert page.locator('#dashDuplicates').inner_text().strip() == '—'
                            screenshot('02b-dashboard')
                            page.locator('[data-dash-type="cycle"]').click()
                            expect(page.locator('#analysisType')).to_have_value('cycle')
                            assert not page.locator('#analysis').is_hidden()
                            return 'dashboard measured counts and cycle drilldown'
                        check('Dashboard measured signals and drilldown',dashboard)
                        def insights():
                            page.locator('[data-page="overview"]').click()
                            page.locator('#dashPriority .dash-queue-item button').first.click()
                            expect(page.locator('#insights')).to_be_visible()
                            expect(page.locator('#insightsCycle option')).to_have_count(1)
                            expect(page.locator('#insightsEdges .insights-edge')).to_have_count(2)
                            expect(page.locator('#insightsCoverage')).to_contain_text('2/2 complete anchors',timeout=12000)
                            expect(page.locator('#insightsCoverage')).to_contain_text('2/2 reported edges',timeout=12000)
                            for level in ('compact','balanced','extended'):
                                page.locator('#insightsLevel').select_option(level)
                                expect(page.locator('#insightsCoverage')).to_contain_text('2/2 complete anchors',timeout=12000)
                            screenshot('02c-dependency-evidence')
                            page.locator('#insightsEdges .insights-edge button').first.click()
                            expect(page.locator('#files')).to_be_visible(timeout=10000)
                            expect(page.locator('#fileMeta')).to_contain_text('lines',timeout=10000)
                            return '2 grounded edges, 3 context levels, verified source drilldown'
                        check('Dependency explorer and evidence coverage',insights)
                        def context_builder():
                            page.locator('[data-page="insights"]').click()
                            page.locator('#insightsFinding').select_option(index=0)
                            per_level={}
                            for level in ('compact','balanced','extended'):
                                page.locator('#insightsLevel').select_option(level)
                                page.locator('#contextLoad').click()
                                expect(page.locator('#contextFragments .context-fragment').first).to_be_visible(timeout=12000)
                                count=page.locator('#contextFragments .context-fragment').count()
                                assert count >= 2, f'{level}: two import edges require excerpts, found {count}'
                                expect(page.locator('#contextSummary')).to_contain_text(f'{count} selected')
                                page.locator('#contextFragments .context-fragment input').last.uncheck()
                                expect(page.locator('#contextSummary')).to_contain_text('1 excluded')
                                with page.expect_download(timeout=10000) as dl:
                                    page.locator('#contextDownload').click()
                                download=dl.value
                                assert download.suggested_filename.endswith('.md')
                                dest=out/f'context-{level}.md';download.save_as(str(dest));report['downloads'].append(dest.name)
                                output=dest.read_text(encoding='utf-8')
                                assert 'EXCLUDED BY USER' in output
                                assert 'Original exporter reported complete anchors:' in output
                                assert commit in output
                                assert 'No code was executed, modified or automatically sent to an AI.' in output
                                assert 'Do not edit files or claim that deletion or refactoring is safe.' in output
                                assert '## Included source evidence' in output
                                per_level[level]={'bytes':len(output.encode()),'excerpts':count}
                            # A changed evidence level must invalidate the current selection until reloaded.
                            page.locator('#insightsLevel').select_option('balanced')
                            expect(page.locator('#contextDownload')).to_be_disabled()
                            expect(page.locator('#contextSummary')).to_contain_text('No evidence selected')
                            screenshot('02d-context-builder')
                            return 'Exported all evidence levels with deliberate omission, provenance and invalidation: '+str(per_level)
                        check('Human-controlled context builder',context_builder)
                        def filters():
                            page.locator('[data-page="analysis"]').click()
                            page.locator('#analysisType').select_option('cycle')
                            assert 'matching' in page.locator('#analysisCount').inner_text()
                            page.locator('#analysisQuery').fill('not-a-matching-module-12345')
                            assert '0 of 0 matching' in page.locator('#analysisCount').inner_text()
                            page.locator('#analysisQuery').fill('')
                            page.locator('#analysisSort').select_option('path')
                            screenshot('03-filters');return 'cycle filter, search empty state, sort by path'
                        check('Search, filters and sorting',filters)
                        def unused():
                            page.locator('[data-page="analysis"]').click()
                            page.locator('#analysisType').select_option('unused')
                            assert 'matching' in page.locator('#analysisCount').inner_text()
                            screenshot('04-unused');return page.locator('#analysisCount').inner_text()
                        check('Potentially unused review',unused)
                        def exports():
                            page.locator('[data-page="analysis"]').click()
                            page.locator('#analysisType').select_option('cycle')
                            buttons=page.locator('#analysisList button.compare-action')
                            assert buttons.count()>0,'no import-cycle export candidate in fixture'
                            buttons.first.click()
                            page.locator('#evidenceText').wait_for()
                            captured={}
                            for level in ('compact','balanced','extended'):
                                page.locator('#evidenceLevel').select_option(level)
                                expect(page.locator('#evidenceSize')).to_contain_text('tokens',timeout=10000)
                                md=page.locator('#evidenceText').input_value()
                                assert 'alpha' in md and 'beta' in md, f'missing cycle evidence at {level}'
                                captured[level]=len(md)
                            screenshot('05-evidence')
                            with page.expect_download(timeout=10000) as dl:
                                page.locator('#downloadEvidenceMd').click()
                            download=dl.value
                            assert download.suggested_filename.endswith('.md')
                            dest=out/'evidence-export.md';download.save_as(str(dest));report['downloads'].append(dest.name)
                            with page.expect_download(timeout=10000) as dl:
                                page.locator('#downloadEvidenceJson').click()
                            download=dl.value
                            dest=out/'evidence-export.json';download.save_as(str(dest))
                            exported=json.loads(dest.read_text())
                            assert isinstance(exported,dict)
                            report['downloads'].append(dest.name)
                            page.locator('#evidenceClose').click()
                            return 'Markdown lengths '+str(captured)+'; MD/JSON downloads valid'
                        try:
                            check('Evidence levels and MD/JSON downloads',exports)
                        finally:
                            # Even a failed export must not intercept the next navigation.
                            if page.locator('#evidenceModal').is_visible():
                                page.locator('#evidenceClose').click()
                                expect(page.locator('#evidenceModal')).to_be_hidden()
                        def fileviewer():
                            page.locator('[data-page="files"]').click()
                            page.locator('#fileList').get_by_text('alpha.py').first.click(timeout=10000)
                            expect(page.locator('#fileContent')).to_contain_text('unused_helper',timeout=10000)
                            screenshot('06-file-viewer');return 'committed source displayed'
                        check('Repository file viewer',fileviewer)
                        report['result']='PASS' if all(x['status']=='PASS' for x in report['checks']) and not report['browser_errors'] and not report['console_errors'] and not report['http_errors'] else 'FAIL'
                    finally:browser.close()
            except Exception as exc:
                report['fatal_error']=str(exc)
                report['traceback']=traceback.format_exc(limit=6)
                report['result']='BLOCKED' if ('ERR_BLOCKED_BY_ADMINISTRATOR' in str(exc) or any('ERR_BLOCKED_BY_ADMINISTRATOR' in c.get('error','') for c in report['checks'])) else 'FAIL'
            finally:
                proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    with zipfile.ZipFile(out/'REPO_STUDIO_E2E_RESULTS.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted(out.iterdir()):
            if file.is_file() and file.name!='REPO_STUDIO_E2E_RESULTS.zip':z.write(file,arcname=file.name)
    print('RESULT:',report['result'])
    for r in report['checks']:print(r['status'],r['name'],r.get('error',''))
    if report.get('fatal_error'):print('BLOCKER:',report['fatal_error'])
    print('Report:',out/'report.json')
    print('Bundle:',out/'REPO_STUDIO_E2E_RESULTS.zip')
    return 0 if report['result']=='PASS' else 1

if __name__=='__main__':sys.exit(main())
