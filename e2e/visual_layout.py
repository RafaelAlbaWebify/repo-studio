from pathlib import Path
from playwright.sync_api import sync_playwright
import json, re
root=Path(__file__).resolve().parents[1]/'static'
html=(root/'index.html').read_text()
css=(root/'style.css').read_text()
html=html.replace('<link rel="stylesheet" href="/style.css">','<style>'+css+'</style>')
html=re.sub(r'<script src="/[^" ]+" defer></script>','',html)
mock=r'''
const $=s=>document.querySelector(s);
const el=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;};
let state={commit:'1111111111111111111111111111111111111111',jscpdAvailable:true,reportReady:true,indexReady:true},dupItems=Array.from({length:462},(_,i)=>({id:i}));
let healthVisible=60, lastNavigated='';
function setPage(name){lastNavigated=name;document.querySelectorAll('.page').forEach(e=>e.classList.toggle('hidden',e.id!==name));}
function renderHealth(){}
function openFile(path,line){lastNavigated='source:'+path+':'+line;}
async function scanHealth(){}
const paths=['src/sample/agency_prospect_web.py','src/sample/crawl.py','src/sample/local_competitive_context_cli.py','tests/test_commercial_acceptance_runner.py','src/sample/market_intelligence.py'];
const items=[];for(let i=0;i<5;i++){for(let j=0;j<[5,5,4,4,3][i];j++){items.push({file:paths[i],cyclomaticApprox:10+j*3,title:'complex'+j,line:50+j});}}
let healthFindings={pythonFilesScanned:564,parseErrors:[],truncated:false,unusedScanEligible:false,counts:{cycles:1,complexity:231,unused:0},
cycles:[{files:['src/sample/browser_provider.py','src/sample/discovery.py'],modules:['sample.browser_provider','sample.discovery'],edges:[{},{}]}],complexity:items,unused:[]};
document.getElementById('repoName').textContent='sample-repo';
document.getElementById('repoPath').textContent='/home/demo/projects/sample-repo';
document.getElementById('commit').textContent='111111111111';
document.getElementById('filesCount').textContent='812';
document.getElementById('matches').textContent='462';
document.getElementById('pct').textContent='5.37%';
'''
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=Path.home()/'Downloads'/'repo-studio-responsive-check')
args=parser.parse_args()
out=args.output.expanduser().resolve()
out.mkdir(parents=True,exist_ok=True)
res=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for width,height in [(1920,960),(1648,772),(1440,800),(1366,650),(1280,720),(1100,760),(1024,700)]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.set_content(html,wait_until='domcontentloaded')
        page.add_script_tag(content=mock)
        page.add_script_tag(content=(root/'dashboard.js').read_text())
        page.evaluate("dashboardLastAnalysis='13/11/26, 18:50';renderDashboard();")
        dims=page.evaluate('''() => {
          const r=s=>{let e=document.querySelector(s);if(!e)return null;let x=e.getBoundingClientRect();return {top:Math.round(x.top),bottom:Math.round(x.bottom),height:Math.round(x.height),width:Math.round(x.width)}};
          return {viewport:{width:innerWidth,height:innerHeight},docWidth:document.documentElement.scrollWidth,docHeight:document.documentElement.scrollHeight,overview:r('#overview'),command:r('.overview-command-bar'),metric:r('.dashboard-metrics'),top:r('.dashboard-top-grid'),bottom:r('.dashboard-bottom-grid'),details:r('.overview-details'),hotspots:r('#dashHotspots'),queue:r('#dashPriority'),tool:r('#dashToolStates')};
        }''')
        # test drilldowns - first click: cycle routes to code health
        page.locator('[data-dash-type="cycle"]').first.click()
        dims['drilldown']=page.evaluate("lastNavigated")
        page.evaluate("setPage('overview')")
        page.locator('#dashHotspots .dash-hotspot-row').first.click()
        dims['hotspot_drilldown']=page.evaluate("lastNavigated")
        page.evaluate("setPage('overview')")
        page.locator('#dashPriority .dash-queue-item button').nth(1).click()
        dims['source_drilldown']=page.evaluate("lastNavigated")
        page.evaluate("setPage('overview')")
        page.locator('.overview-details summary').click()
        dims['details_opens']=page.locator('.overview-details').evaluate('(e)=>e.open')
        page.locator('.overview-details summary').click()
        dims['details_closes']=not page.locator('.overview-details').evaluate('(e)=>e.open')
        # capture only visible view; no crop tricks
        img=out/f'dashboard_{width}x{height}.png'
        page.screenshot(path=str(img))
        dims['image']=str(img)
        dims['errors']=errors
        res.append(dims)
        print(width,height,'doc',dims['docWidth'],dims['docHeight'],'details bottom',dims['details']['bottom'],'errors',errors)
        page.close()
    browser.close()
(out/'visual_report.json').write_text(json.dumps(res,indent=2))
assert all(x['docWidth']==x['viewport']['width'] for x in res),'Horizontal overflow detected'
assert all(x['docHeight']<=x['viewport']['height'] for x in res if x['viewport']['width']>=1261),'Unexpected desktop scroll'
assert all(x['drilldown']=='analysis' and x['hotspot_drilldown']=='analysis' and x['source_drilldown'].startswith('source:') and x['details_opens'] and x['details_closes'] and not x['errors'] for x in res),'Dashboard script/navigation failed'
print('VISUAL RESPONSIVE TEST: PASS')
