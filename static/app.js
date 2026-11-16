'use strict';
let token='', files=[], dupItems=[], findingItems=[], state={}, selectedFile='', expandedDirs=new Set(), treeRoot=null, activeLine=0;
const $=s=>document.querySelector(s), $$=s=>document.querySelectorAll(s);
const el=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;};
async function api(path,options={}){const r=await fetch(path,{cache:'no-store',...options});const d=await r.json();if(!r.ok)throw Error(d.error||`HTTP ${r.status}`);return d;}
function toast(msg){const m=$('#message');m.textContent=String(msg);setTimeout(()=>{if(m.textContent===msg)m.textContent='';},7000);}
function setPage(name){$$('.page').forEach(x=>x.classList.toggle('hidden',x.id!==name));$$('.nav').forEach(x=>x.classList.toggle('active',x.dataset.page===name));$('#currentPage').textContent=({overview:'Overview',findings:'Review findings',analysis:'Code health',insights:'Dependency explorer',duplicates:'Duplications',files:'Repository files',symbols:'Symbol search',compare:'Compare sources',help:'Help & guide',about:'About Repo Studio'})[name]||name;}
function treeOf(paths){const root={name:'',dirs:new Map(),files:[]};for(const path of paths){const parts=path.split('/');let node=root;for(const part of parts.slice(0,-1)){if(!node.dirs.has(part))node.dirs.set(part,{name:part,dirs:new Map(),files:[]});node=node.dirs.get(part);}node.files.push({name:parts.at(-1),path});}return root;}
function matchesTree(node,query,prefix=''){if(!query)return true;if(node.files.some(f=>f.path.toLowerCase().includes(query)))return true;for(const [name,child] of node.dirs)if(matchesTree(child,query,prefix+name+'/'))return true;return false;}
function renderFiles(){const q=$('#fileFilter').value.trim().toLowerCase(),list=$('#fileList');list.replaceChildren();if(!treeRoot)return;
function visit(node,prefix='',depth=0){const dirs=[...node.dirs].sort((a,b)=>a[0].localeCompare(b[0]));for(const [name,child] of dirs){const path=prefix+name+'/';if(!matchesTree(child,q))continue;const expanded=q!==''||expandedDirs.has(path);const btn=el('button','','tree-row');btn.type='button';rsStyle(btn,"padding-left",`${10+depth*15}px`);btn.setAttribute('aria-expanded',String(expanded));btn.append(el('span',expanded?'▾':'▸','tree-symbol'),el('span',name,'tree-name'));btn.title=path;btn.onclick=()=>{if(expandedDirs.has(path))expandedDirs.delete(path);else expandedDirs.add(path);renderFiles();};list.append(btn);if(expanded)visit(child,path,depth+1);}
for(const f of [...node.files].sort((a,b)=>a.name.localeCompare(b.name))){if(q&&!f.path.toLowerCase().includes(q))continue;const btn=el('button','','tree-row'+(selectedFile===f.path?' is-selected':''));btn.type='button';rsStyle(btn,"padding-left",`${10+depth*15}px`);btn.append(el('span','◇','tree-symbol'),el('span',f.name,'tree-name'));btn.title=f.path;btn.onclick=()=>openFile(f.path);list.append(btn);}}
visit(treeRoot);if(!list.children.length)list.append(el('div','No matching files.','empty-text'));}
async function openFile(path,line=0){setPage('files');selectedFile=path;activeLine=Number(line)||0;const parts=path.split('/');let prefix='';for(const part of parts.slice(0,-1)){prefix+=part+'/';expandedDirs.add(prefix);}$('#fileFilter').value='';renderFiles();$('#fileTitle').textContent=path;$('#fileMeta').textContent='Loading committed HEAD…';$('#contextBtn').disabled=true;$('#contextResults').classList.add('hidden');$('#contextResults').replaceChildren();const parent=$('#fileContent');parent.replaceChildren(el('div','Loading source…','empty-text'));
try{const d=await api('/api/file?path='+encodeURIComponent(path));if(selectedFile!==path)return;const lines=d.content.split('\n');if(lines.at(-1)==='')lines.pop();parent.replaceChildren();const fragment=document.createDocumentFragment();for(let i=0;i<lines.length;i++){const row=el('div','','sourceLine'+(activeLine===i+1?' is-target':''));row.dataset.line=i+1;const number=el('span',String(i+1),'lineNo');const code=el('span',lines[i]||' ','lineText');row.append(number,code);fragment.append(row);}parent.append(fragment);$('#fileMeta').textContent=lines.length.toLocaleString()+' lines · HEAD';$('#contextBtn').disabled=!(state.indexReady&&state.repowiseAvailable);const target=parent.querySelector('.is-target');if(target)target.scrollIntoView({block:'center',behavior:'instant'});else $('#sourceScroll').scrollTop=0;}catch(e){parent.replaceChildren(el('div',e.message,'empty-text'));$('#fileMeta').textContent='Unavailable';toast(e.message);}}
function dupMatches(x,query){return !query||[x.first,x.second,x.fragment,x.language].some(v=>String(v||'').toLowerCase().includes(query));}
function renderDup(){const filter=$('#groupFilter').value,query=$('#dupFilter').value.toLowerCase().trim(),list=$('#dupList');list.replaceChildren();const view=dupItems.filter(x=>(filter==='all'||x.group===filter)&&dupMatches(x,query));$('#matchCount').textContent=`${view.length} / ${dupItems.length} matches`;$('#dupMore').textContent=view.length>120?`Showing first 120 of ${view.length} results. Refine your filter to see the rest.`:'';if(!view.length){list.append(el('div','No matches for this filter.','result'));return;}
const fragment=document.createDocumentFragment();for(const x of view.slice(0,120)){const card=el('article','','result'),head=el('div','','result-head');const title=el('div',`${x.first}:${x.firstLine} ↔ ${x.second}:${x.secondLine}`,'result-title');head.append(title,el('span',`${x.lines} lines`,'tag'));card.append(head,el('div',`${x.group} · ${x.language} · review candidate only`,'result-meta'));const acts=el('div','','result-actions');const compare=el('button','Compare side by side','compare-action');compare.type='button';compare.onclick=()=>compareSources(x);acts.append(compare);for(const [label,path,line] of [['Open first source',x.first,x.firstLine],['Open second source',x.second,x.secondLine]]){const b=el('button',label,'result-action');b.type='button';b.onclick=()=>openFile(path,line);acts.append(b);}if(x.fragment){const preview=el('pre',x.fragment);preview.className='';const toggle=el('button','Expand excerpt','result-action');toggle.type='button';toggle.onclick=()=>{preview.classList.toggle('expanded');toggle.textContent=preview.classList.contains('expanded')?'Collapse excerpt':'Expand excerpt';};card.append(preview);acts.append(toggle);}card.append(acts);fragment.append(card);}list.append(fragment);}

function renderFindings(){
  const q=$('#findingFilter').value.trim().toLowerCase(),group=$('#findingGroup').value,list=$('#findingList');list.replaceChildren();
  const visible=findingItems.filter(c=>(group==='all'||c.group===group)&&(!q||[c.first,c.second,...c.reviewTopics].join(' ').toLowerCase().includes(q)));
  $('#findingCount').textContent=`${visible.length} / ${findingItems.length} cases`;
  $('#findingMore').textContent=visible.length>80?`Showing 80 of ${visible.length}. Refine the filter to see more.`:'';
  if(!visible.length){list.append(el('div','No cases for this filter.','result'));return;}
  const frag=document.createDocumentFragment();
  for(const c of visible.slice(0,80)){
    const card=el('article','','result finding-card'),head=el('div','','result-head');
    head.append(el('div',`${c.first} ↔ ${c.second}`,'result-title'),el('span',`${c.count} matches`,'tag'));card.append(head);
    card.append(el('div',`${c.group} · ${c.coveredLinesA} / ${c.coveredLinesB} affected source lines · ${c.reviewStatus}`,'result-meta'));
    const details=el('details','','finding-details'),summary=el('summary','Evidence and review checklist');details.append(summary);
    const note=el('p','Detector-reported regions. Coverage is not estimated savings.','quiet');details.append(note);
    for(const m of c.matches.slice(0,25)){
      const row=el('div',`A:${m.firstLine} ↔ B:${m.secondLine} · ${m.lines} lines`,'finding-range');
      const b=el('button','Compare','result-action');b.type='button';b.onclick=()=>compareSources({first:c.first,second:c.second,firstLine:m.firstLine,secondLine:m.secondLine,lines:m.lines});row.append(b);details.append(row);
    }
    if(c.matches.length>25)details.append(el('div',`Additional matches: ${c.matches.length-25}`,'quiet'));
    const h=el('h3','Review before proposing changes');details.append(h);
    for(const topic of c.reviewTopics)details.append(el('p','• '+topic,'finding-topic'));
    for(const limit of c.limitations)details.append(el('p','Limitation: '+limit,'quiet'));
    card.append(details);
    const acts=el('div','','result-actions');
    const b=el('button','Compare longest match','compare-action');b.type='button';b.onclick=()=>{const m=c.matches[0];compareSources({first:c.first,second:c.second,firstLine:m.firstLine,secondLine:m.secondLine,lines:m.lines});};acts.append(b);
    const exp=el('button','Export for AI','result-action');exp.type='button';exp.onclick=()=>openEvidence('duplication',c.id);acts.append(exp);
    card.append(acts);frag.append(card);
  }
  list.append(frag);
}
async function loadFindings(){const d=await api('/api/findings');findingItems=d.cases||[];renderFindings();}

async function loadDup(){const d=await api('/api/duplicates');dupItems=d.items||[];$('#matches').textContent=state.reportReady?dupItems.length.toLocaleString():'Not analyzed';$('#pct').textContent=state.reportReady&&typeof d.stats?.percentage==='number'?d.stats.percentage.toFixed(2)+'%':'Not analyzed';renderDup();}
async function load(){state=await api('/api/status');token=state.token;$('#repoName').textContent=state.repository.split('/').pop();$('#repoPath').textContent=state.repository;$('#repoInput').value=state.repository;$('#commit').textContent=state.commit.slice(0,12);$('#busyBadge').textContent=state.busy?'Auditing…':'Idle';$('#auditBtn').disabled=state.busy||!state.jscpdAvailable;$('#auditBtn').title=state.jscpdAvailable?'Scan committed files for duplicates':'Unavailable: jscpd is not installed or not in PATH';$('#auditAvailability').textContent=state.jscpdAvailable?'':'jscpd missing — optional analyzer. Install or configure jscpd to enable this scan.';$('#jscpdState').textContent=state.jscpdAvailable?'available':'missing';$('#repowiseState').textContent=state.indexReady?'index connected':'no index selected';$('#indexOverview').textContent=state.indexReady?'Symbol search and per-file relationship inspection available. Git history requires a full Git snapshot.':'No Repowise index configured for this repository.';const f=await api('/api/files');files=f.files;treeRoot=treeOf(files);$('#filesCount').textContent=files.length.toLocaleString();if(!expandedDirs.size)expandedDirs=new Set(['src/']);renderFiles();await loadDup();await loadFindings();if(typeof renderDashboard==='function')renderDashboard();if(state.error)toast(state.error);if(typeof wsLoadHistory==='function')void wsLoadHistory();if(typeof wsRefresh==='function')void wsRefresh();}
async function post(path,data){return api(path,{method:'POST',headers:{'Content-Type':'application/json','X-Repo-Studio-Token':token},body:JSON.stringify(data)});}
async function loadContext(){if(!selectedFile)return;const panel=$('#contextResults');panel.replaceChildren(el('div','Retrieving indexed relationships…'));panel.classList.remove('hidden');$('#contextBtn').disabled=true;try{const path=selectedFile,d=await api('/api/context?path='+encodeURIComponent(path));if(selectedFile!==path)return;panel.replaceChildren();const target=d.targets?.[path];if(!target){panel.append(el('div','No context returned for this file.'));return;}panel.append(el('h3','Repowise · indexed context'));const doc=target.docs||{};if(doc.symbols)panel.append(el('div',`${doc.symbols.length} indexed symbols`,'quiet'));
let groups=0;function examine(obj,key,depth=0){if(groups>=10||depth>2||!obj||typeof obj!=='object')return;for(const [k,v] of Object.entries(obj)){if(groups>=10)break;if(['callers','callees','imports','references'].includes(k)&&Array.isArray(v)&&v.length){groups++;const section=el('div','','context-group');section.append(el('strong',`${k} (${v.length})`));for(const item of v.slice(0,8)){let label=typeof item==='string'?item:JSON.stringify(item).slice(0,200);section.append(el('div',label,'quiet'));}panel.append(section);}else if(k!=='symbols'&&k!=='docs'&&v&&typeof v==='object')examine(v,k,depth+1);}}examine(target,'');if(!groups)panel.append(el('div','No callable relationships returned. This is not evidence of zero dependencies.','quiet'));}catch(e){panel.replaceChildren(el('div',e.message));toast(e.message);}finally{$('#contextBtn').disabled=!(state.indexReady&&state.repowiseAvailable);}}
$$('.nav').forEach(b=>b.onclick=()=>setPage(b.dataset.page));$('#findingGroup').onchange=renderFindings;$('#findingFilter').oninput=renderFindings;$('#groupFilter').onchange=renderDup;$('#dupFilter').oninput=renderDup;$('#fileFilter').oninput=renderFiles;$('#contextBtn').onclick=loadContext;$('#openSearchBtn').onclick=()=>setPage('symbols');$('#treeToggle').onclick=()=>{if(expandedDirs.size){expandedDirs.clear();$('#treeToggle').textContent='Expand all';}else{for(const path of files){let prefix='';for(const part of path.split('/').slice(0,-1)){prefix+=part+'/';expandedDirs.add(prefix);}}$('#treeToggle').textContent='Collapse all';}renderFiles();};
$('#selectBtn').onclick=async()=>{try{await post('/api/select',{path:$('#repoInput').value});selectedFile='';expandedDirs.clear();if(typeof resetHealthForRepoChange==='function')resetHealthForRepoChange();await load();if(typeof resetDashboard==='function')resetDashboard();if(typeof resetInsights==='function')resetInsights();toast('Repository selected. Existing audit results were cleared.');}catch(e){toast(e.message);}};
$('#auditBtn').onclick=async()=>{
 const btn=$('#auditBtn');btn.disabled=true;const previous=btn.textContent;btn.textContent='Scanning duplicates…';
 if(typeof showTaskActivity==='function')showTaskActivity('Scanning committed files for duplication with jscpd…');
 try{
  await post('/api/audit',{});toast('Duplication scan started.');
  const timer=setInterval(async()=>{
   try{
    const s=await api('/api/status');$('#busyBadge').textContent=s.busy?'Scanning duplications…':'Idle';
    if(!s.busy){clearInterval(timer);await load();toast(s.error||'Duplication scan completed.');btn.textContent=previous;btn.disabled=!state.jscpdAvailable;if(typeof hideTaskActivity==='function')hideTaskActivity();}
   }catch(e){clearInterval(timer);btn.textContent=previous;btn.disabled=false;if(typeof hideTaskActivity==='function')hideTaskActivity();toast(e.message);}
  },1000);
 }catch(e){btn.disabled=false;btn.textContent=previous;if(typeof hideTaskActivity==='function')hideTaskActivity();toast(e.message);}
};
$('#symbolForm').onsubmit=async e=>{e.preventDefault();const list=$('#symbolResults');list.replaceChildren(el('div','Searching local index…','result'));try{const d=await api('/api/search?q='+encodeURIComponent($('#symbolQuery').value));list.replaceChildren();if(!d.results?.length){list.append(el('div','No symbols found.','result'));return;}for(const x of d.results){const card=el('button','','result link-card');card.type='button';card.append(el('div',x.qualified_name||x.name||x.title||'Result','result-title'),el('div',`${x.path||'unknown'}:${x.line||'—'} · ${x.kind||x.type||''}`,'result-meta'));if(x.path&&files.includes(x.path)){card.onclick=()=>openFile(x.path,x.line);}else{card.disabled=true;card.title='Source unavailable in committed HEAD';}list.append(card);}}catch(e){list.replaceChildren(el('div','Search failed: '+e.message,'result'));}};
load().catch(e=>toast(e.message));


/* Repo Studio 0.8: reconnect after an explicitly approved local update. */
(() => {
  let original = null;
  async function checkServer() {
    try {
      const response = await fetch('/api/status', {cache: 'no-store'});
      if (!response.ok) return;
      const data = await response.json();
      if (!data.token) return;
      if (original === null) original = data.token;
      else if (original !== data.token) window.location.reload();
    } catch (_) { /* Transient restart: keep the existing view. */ }
  }
  void checkServer();
  setInterval(checkServer, 2500);
})();

/* RS_SOURCE_VIEW_V1 — deterministic, read-only code-view controls. */
document.addEventListener('DOMContentLoaded', () => {
  const source = document.getElementById('sourceScroll');
  const tools = document.querySelector('#files .fileTools');
  if (!source || !tools || document.getElementById('rsSourceWrap')) return;
  const group = document.createElement('span');
  group.className = 'rs-source-controls';
  group.setAttribute('role','group');
  group.setAttribute('aria-label','Code display options');
  function button(id,label,title,onClick) {
    const b=document.createElement('button');
    b.type='button'; b.id=id; b.textContent=label; b.title=title;
    b.setAttribute('aria-label',title); b.addEventListener('click',onClick);
    group.append(b);return b;
  }
  const wrap=button('rsSourceWrap','Wrap lines','Wrap long source lines',()=>{
    const active=source.classList.toggle('rs-wrap');
    wrap.setAttribute('aria-pressed',String(active));
    left.disabled=active;right.disabled=active;
    if(active)source.scrollLeft=0;
  });
  wrap.setAttribute('aria-pressed','false');
  const left=button('rsSourceLeft','←','Scroll code left',()=>source.scrollBy({left:-Math.max(180,source.clientWidth*.65),behavior:'auto'}));
  const right=button('rsSourceRight','→','Scroll code right',()=>source.scrollBy({left:Math.max(180,source.clientWidth*.65),behavior:'auto'}));
  tools.append(group);
});
