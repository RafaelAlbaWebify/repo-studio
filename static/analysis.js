'use strict';
/* Unified evidence export for duplication, AST cycles and complexity. */
let healthFindings=null, evidenceSelection=null, evidenceResult=null, healthVisible=60;
function renderHealth(){
  const list=$('#analysisList');list.replaceChildren();if(!healthFindings)return;
  const filter=$('#analysisType').value;
  const query=$('#analysisQuery').value.trim().toLocaleLowerCase();
  const sort=$('#analysisSort').value;
  const items=[...healthFindings.cycles,...healthFindings.complexity,...healthFindings.unused]
    .filter(x=>(filter==='all'||x.type===filter) && (!query || [x.title,x.file,...(x.files||[]),...(x.modules||[])].filter(Boolean).join(' ').toLocaleLowerCase().includes(query)));
  if(sort==='path')items.sort((a,b)=>(a.file||a.files?.[0]||'').localeCompare(b.file||b.files?.[0]||'') || a.id.localeCompare(b.id));
  if(sort==='complexity')items.sort((a,b)=>(b.cyclomaticApprox||0)-(a.cyclomaticApprox||0) || a.id.localeCompare(b.id));
  $('#analysisCount').textContent=`${Math.min(items.length,healthVisible)} of ${items.length} matching · ${healthFindings.pythonFilesScanned} Python files`;
  $('#analysisNote').textContent=`${healthFindings.counts.cycles} import cycles · ${healthFindings.counts.complexity} complexity candidates · ${healthFindings.counts.unused} unused candidates (${healthFindings.unusedScanEligible?'eligible':'scan incomplete/disabled'}). AST-only, approximate; ${healthFindings.parseErrors.length} parse/size issues. No code executed.`;
  const more=$('#analysisMore');more.classList.toggle('hidden',items.length<=healthVisible);
  if(!items.length){list.append(el('div','No matching candidates. This does not prove the repository has no problems.','result'));return;}
  for(const f of items.slice(0,healthVisible)){
    const card=el('article','','result');
    const title=f.type==='cycle'?`Import cycle: ${f.modules.join(' ↔ ')}`:f.type==='unused'?`Possibly unused: ${f.file}:${f.line} · ${f.title}`:`Complexity: ${f.file}:${f.line} · ${f.title}`;
    card.append(el('div',title,'result-title'));
    const info=f.type==='cycle'?`${f.files.length} Python files · ${f.edges.length} static edges`:f.type==='unused'?'No static references to private module-level name found':`Approx. branching ${f.cyclomaticApprox} · ${f.lines} source lines`;
    card.append(el('div',info+' · candidate for review, not a defect','result-meta'));
    const details=el('details','','finding-details');details.append(el('summary','Evidence and limitations'));
    if(f.type==='cycle')for(const edge of f.edges.slice(0,25))details.append(el('div',`${edge.from} → ${edge.to}`,'finding-range'));
    for(const limitation of f.limitations)details.append(el('p',limitation,'quiet'));
    card.append(details);
    const actions=el('div','','result-actions');
    const b=el('button','Export for AI','compare-action');b.type='button';b.onclick=()=>openEvidence(f.type,f.id);actions.append(b);
    const loc=f.type==='cycle'?f.files[0]:f.file;
    const open=el('button','Open source','result-action');open.type='button';open.onclick=()=>openFile(loc,f.line||1);actions.append(open);
    card.append(actions);list.append(card);
  }

}
async function scanHealth(){
 const buttons=['runAnalysis','dashboardScan','insightsScan'].map(id=>document.getElementById(id)).filter(Boolean);
 if(buttons.some(b=>b.dataset.running==='yes'))return;
 const old=buttons.map(b=>[b,b.textContent,b.disabled]);
 buttons.forEach(b=>{b.dataset.running='yes';b.disabled=true;b.textContent='Analyzing…';});
 $('#busyBadge').textContent='Analyzing code…';
 $('#analysisNote').textContent='Reading committed Python files, detecting cycles and estimating complexity…';
 if(typeof showTaskActivity==='function')showTaskActivity('Analyzing committed Python files, dependencies and complexity…');
 const started=performance.now();
 try{
  healthFindings=await api('/api/analysis');healthVisible=60;
  dashboardLastAnalysis=new Date().toLocaleString([], {dateStyle:'short', timeStyle:'short'});
  renderHealth();if(typeof renderDashboard==='function')renderDashboard();if(typeof renderInsights==='function')renderInsights();
  buttons.forEach(b=>b.textContent='Refresh analysis');
  toast(`Code analysis completed in ${((performance.now()-started)/1000).toFixed(1)}s. Review findings before acting.`);
 }catch(e){$('#analysisNote').textContent='Analysis failed: '+e.message;toast(e.message);}
 finally{for(const [b,text,disabled] of old){b.dataset.running='no';b.disabled=disabled;b.textContent=healthFindings?'Refresh analysis':'Run code analysis';}$('#busyBadge').textContent='Idle';if(typeof hideTaskActivity==='function')hideTaskActivity();}
}
async function openEvidence(type,id){
 evidenceSelection={type,id};$('#evidenceModal').classList.remove('hidden');$('#evidenceText').value='Generating preview…';await refreshEvidence();
}
async function refreshEvidence(){
 if(!evidenceSelection)return;
 const {type,id}=evidenceSelection,level=$('#evidenceLevel').value;
 $('#evidenceSize').textContent='Preparing…';
 try{
  const result=await api('/api/evidence?type='+encodeURIComponent(type)+'&id='+encodeURIComponent(id)+'&level='+encodeURIComponent(level));
  if(!evidenceSelection||evidenceSelection.id!==id||$('#evidenceLevel').value!==level)return;
  evidenceResult=result;$('#evidenceText').value=result.markdown;
  const coverage=result.json?.evidenceCoverage;
  const coverageText=coverage ? ` · ${coverage.completeAnchors}/${coverage.requestedAnchors} complete anchors${coverage.anchorsComplete?'':' · PARTIAL EVIDENCE'}` : '';
  $('#evidenceSize').textContent=`≈${result.estimatedTokens.toLocaleString()} tokens (rough estimate)${coverageText}`;
 }catch(e){evidenceResult=null;$('#evidenceText').value='Error: '+e.message;$('#evidenceSize').textContent='';toast(e.message);}
}
function saveEvidence(text,filename,type){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('#runAnalysis').onclick=scanHealth;
function resetHealthVisible(){healthVisible=60;renderHealth();}
$('#analysisType').onchange=resetHealthVisible;
$('#analysisQuery').oninput=resetHealthVisible;
$('#analysisSort').onchange=resetHealthVisible;
$('#analysisMore').onclick=()=>{healthVisible+=60;renderHealth();};
function resetHealthForRepoChange(){healthFindings=null;dashboardLastAnalysis='Not analyzed';if(typeof resetDashboard==='function')resetDashboard();if(typeof resetInsights==='function')resetInsights();healthVisible=60;$('#analysisList').replaceChildren();$('#analysisCount').textContent='Not scanned yet';$('#analysisMore').classList.add('hidden');$('#analysisNote').textContent='Scan the selected commit to inspect code health.';}
$('#evidenceLevel').onchange=refreshEvidence;
$('#evidenceClose').onclick=()=>{$('#evidenceModal').classList.add('hidden');evidenceSelection=null;evidenceResult=null;};
$('#evidenceModal').addEventListener('click',event=>{if(event.target===$('#evidenceModal'))$('#evidenceClose').click();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!$('#evidenceModal').classList.contains('hidden'))$('#evidenceClose').click();});
$('#copyEvidence').onclick=async()=>{if(!evidenceResult)return;try{await navigator.clipboard.writeText($('#evidenceText').value);toast('Markdown copied. Review sensitive code before sharing.');}catch(e){toast('Clipboard access unavailable; select the preview text manually.');}};
$('#downloadEvidenceMd').onclick=()=>{if(!evidenceResult)return;saveEvidence($('#evidenceText').value,`${evidenceResult.fileStem}.md`,'text/markdown');};
$('#downloadEvidenceJson').onclick=()=>{if(!evidenceResult)return;saveEvidence(JSON.stringify(evidenceResult.json,null,2),`${evidenceResult.fileStem}.json`,'application/json');};
