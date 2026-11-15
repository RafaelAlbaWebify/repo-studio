'use strict';
/* Measured only. Drill-down links and honest missing-data states. No network dependencies. */
let dashboardLastAnalysis='Not analyzed';
function dashText(id,value){const node=document.getElementById(id);if(node)node.textContent=String(value);}
function dashStat(label,value,description){const item=el('div','','dash-state');item.append(el('strong',label),el('span',value,'dash-state-value'),el('span',description,'quiet'));return item;}
function updateDashboardStatus(){
 if(!state||!state.commit)return;
 dashText('dashCommit',`Commit ${state.commit.slice(0,12)}`);
 dashText('lastAnalysis',dashboardLastAnalysis);
 const toolchainReady = state.jscpdAvailable && state.indexReady && !!healthFindings;
 const toolchainLabel = toolchainReady ? 'All ready' : (state.jscpdAvailable || state.indexReady || healthFindings ? 'Partial' : 'Minimal');
 dashText('toolchainSummary', toolchainLabel);
 const area=$('#dashToolStates');area.replaceChildren();
 area.append(dashStat('Git snapshot','Available','Committed HEAD · read-only'));
 area.append(dashStat('jscpd',state.reportReady?'Report loaded':state.jscpdAvailable?'Not analyzed':'Not configured',state.reportReady?'Review duplication results':state.jscpdAvailable?'Run duplication audit':'Not measured ≠ zero'));
 area.append(dashStat('Repowise',state.indexReady?'Index connected':'Not configured',state.indexReady?'Check index provenance before interpreting relations':'No relationship index selected'));
 area.append(dashStat('Python AST',healthFindings?'Analyzed':'Not analyzed',healthFindings?`${healthFindings.pythonFilesScanned} files scanned`:'Select Analyze Python'));
 dashText('dashDuplicates',state.reportReady?dupItems.length.toLocaleString():'—');
 dashText('dashDupStatus',state.reportReady?'jscpd matches · not distinct defects':state.jscpdAvailable?'Audit not run':'Analyzer unavailable');
}
function resetDashboard(){
 ['dashPython','dashCycles','dashComplexity','dashUnused'].forEach(id=>dashText(id,'—'));
 dashText('dashPythonStatus','Not analyzed');dashText('dashUnusedStatus','Not analyzed');
 dashText('dashDonutTotal','—');$('#dashDonut').style.background='conic-gradient(#343746 0 100%)';
 $('#dashDonut').setAttribute('aria-label','No Python scan available');
 $('#dashDistribution').replaceChildren(el('p','Run Python analysis to display findings.','quiet'));
 $('#dashHotspots').replaceChildren(el('p','No analysis performed.','quiet'));
 $('#dashPriority').replaceChildren(el('p','Run Python analysis to see evidence-backed candidates.','quiet'));
 dashText('dashCaveat','An unavailable analyzer never means zero findings.');
 if(!healthFindings) dashboardLastAnalysis='Not analyzed';
 updateDashboardStatus();
}
function dashGo(type,path=''){
 setPage('analysis');$('#analysisType').value=type;$('#analysisQuery').value=path;
 healthVisible=60;renderHealth();
}
function dashReviewDup(){setPage('duplicates');}
function dashQueueItem(title,detail,action,callback){
 const item=el('div','','dash-queue-item');
 const copy=el('div','','dash-queue-copy');copy.append(el('strong',title),el('span',detail,'quiet'));
 const button=el('button',action+' →','secondary');button.type='button';button.onclick=callback;
 item.append(copy,button);return item;
}
function renderDashboard(){
 updateDashboardStatus();if(!healthFindings){resetDashboard();return;}
 const h=healthFindings,counts=h.counts||{},number=n=>Number(n||0).toLocaleString();
 dashText('dashPython',number(h.pythonFilesScanned));
 dashText('dashPythonStatus',h.parseErrors?.length?`${h.parseErrors.length} parse/size limitations`:'AST scan finished');
 dashText('dashCycles',counts.cycles??'—');dashText('dashComplexity',counts.complexity??'—');
 dashText('dashUnused',h.unusedScanEligible?(counts.unused??'—'):'N/A');
 dashText('dashUnusedStatus',h.unusedScanEligible?'Eligible static scan':'Not eligible · no conclusion');
 const rows=[{type:'cycle',name:'Import cycles',count:Number(counts.cycles||0),color:'#a18aff'},
             {type:'complexity',name:'Complexity',count:Number(counts.complexity||0),color:'#4baec6'}];
 if(h.unusedScanEligible)rows.push({type:'unused',name:'Possibly unused',count:Number(counts.unused||0),color:'#d6a46b'});
 const total=rows.reduce((n,r)=>n+r.count,0),root=$('#dashDistribution');root.replaceChildren();
 let pct=0,stops=[];
 for(const r of rows){
   const b=el('button','','dash-legend-row');b.type='button';b.dataset.type=r.type;
   b.setAttribute('aria-label',`Review ${r.count} ${r.name} candidates`);
   const dot=el('span','','dash-legend-dot');dot.style.background=r.color;
   b.append(dot,el('span',r.name,'dash-legend-name'),el('strong',number(r.count)));b.onclick=()=>dashGo(r.type);root.append(b);
   if(total){const next=pct+100*r.count/total;stops.push(`${r.color} ${pct}% ${next}%`);pct=next;}
 }
 $('#dashDonut').style.background=total?`conic-gradient(${stops.join(',')})`:'conic-gradient(#343746 0 100%)';
 $('#dashDonut').setAttribute('aria-label',`${total} AST candidates distributed among ${rows.map(x=>x.name).join(', ')}`);
 const center=$('#dashDonutTotal');center.replaceChildren(el('strong',number(total)),el('small','AST candidates'));
 if(!h.unusedScanEligible)root.append(el('p','Unused analysis not eligible; excluded from total.','quiet'));
 const grouped=new Map();
 for(const f of h.complexity||[]){if(!f.file)continue;const x=grouped.get(f.file)||{file:f.file,count:0,peak:0};x.count++;x.peak=Math.max(x.peak,Number(f.cyclomaticApprox)||0);grouped.set(f.file,x);}
 const tops=[...grouped.values()].sort((a,b)=>b.count-a.count||b.peak-a.peak||a.file.localeCompare(b.file)).slice(0,5);
 const hot=$('#dashHotspots');hot.replaceChildren();
 if(!tops.length)hot.append(el('p','No complexity candidates in the analyzed files.','quiet'));
 const max=Math.max(1,...tops.map(x=>x.count));
 for(const x of tops){const b=el('button','','dash-hotspot-row');b.type='button';b.title=`${x.file}: ${x.count} complexity candidates; highest approximate branching ${x.peak}`;
 const top=el('div','','dash-hotspot-header');top.append(el('span',x.file,'dashboard-hotspot-path'),el('strong',number(x.count)));
 const track=el('span','','dashboard-track'),fill=el('span','','dashboard-fill');fill.style.width=`${100*x.count/max}%`;track.append(fill);b.append(top,track);
 b.onclick=()=>dashGo('complexity',x.file);hot.append(b);}
 const queue=$('#dashPriority');queue.replaceChildren();
 const cycle=(h.cycles||[]).find(c=>c.files?.length);
 if(cycle)queue.append(dashQueueItem(`Import cycle · ${cycle.files.length} files`,`${cycle.edges?.length||0} static dependency edges · inspect import locations`, 'Explore cycle',()=>openInsights(cycle.id)));
 const complex=[...(h.complexity||[])].sort((a,b)=>(Number(b.cyclomaticApprox)||0)-(Number(a.cyclomaticApprox)||0))[0];
 if(complex)queue.append(dashQueueItem(`Complexity · ${complex.title}`,`${complex.file}:${complex.line} · approx. branching ${complex.cyclomaticApprox} · review candidate`,'Inspect source',()=>openFile(complex.file,complex.line)));
 if(state.reportReady&&dupItems.length)queue.append(dashQueueItem(`${number(dupItems.length)} duplicate matches`,'jscpd matches · check overlap before suggesting changes','Review duplicates',dashReviewDup));
 if(!queue.children.length)queue.append(el('p','No review candidates in the available analyses.','quiet'));
 dashText('dashCaveat',`AST: ${h.pythonFilesScanned} Python files · ${(h.parseErrors||[]).length} parse/size issues · ${h.truncated?'truncated results':'no overall truncation reported'}. Counts are candidates, not defects or severity scores.`);
 updateDashboardStatus();
}
$('#dashboardScan').onclick=async()=>{await scanHealth();};
$('#dashDupReview').onclick=dashReviewDup;
document.querySelectorAll('[data-dash-type]').forEach(b=>b.onclick=()=>dashGo(b.dataset.dashType));
