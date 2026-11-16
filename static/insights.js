'use strict';
/* Inspect only AST-observed cycle edges. Source locations and coverage come from
   the existing version/commit-pinned evidence API; never infer a safe refactor. */
let insightSelection='', insightEvidenceResult=null, insightRequestSerial=0;
const INSIGHT_NS='http://www.w3.org/2000/svg';
function insightNode(tag,attrs,text){const node=document.createElementNS(INSIGHT_NS,tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,String(v));if(text!=null)node.textContent=text;return node;}
function insightEmpty(node,text){node.replaceChildren(el('p',text,'insights-empty'));}
function resetInsights(){if(typeof wsRefresh==='function')queueMicrotask(()=>void wsRefresh());if(typeof builderReset==='function')builderReset('Repository changed. Reload evidence for this commit.');insightSelection='';insightEvidenceResult=null;insightRequestSerial++;$('#insightsCycle').replaceChildren();$('#insightsFinding').replaceChildren();$('#insightsGraph').replaceChildren();$('#insightsEdges').replaceChildren();insightEmpty($('#insightsCoverage'),'Run Python analysis to inspect evidence.');$('#insightsExport').disabled=true;$('#insightsStatus').textContent='Run Python analysis to explore relationships.';$('#insightsGraphMeta').textContent='Not analyzed';}
function insightFind(kind,id){if(kind==='duplication')return findingItems.find(f=>f.id===id);return (healthFindings?.[kind==='cycle'?'cycles':kind==='complexity'?'complexity':'unused']||[]).find(f=>f.id===id);}
function insightOption(select,value,label){const opt=document.createElement('option');opt.value=value;opt.textContent=label;select.append(opt);}
function renderInsights(){
 const cycleSelect=$('#insightsCycle'),findingSelect=$('#insightsFinding');
 const oldCycle=cycleSelect.value||insightSelection, oldFinding=findingSelect.value;
 cycleSelect.replaceChildren();findingSelect.replaceChildren();
 if(!healthFindings){resetInsights();return;}
 const cycles=healthFindings.cycles||[];
 for(const c of cycles)insightOption(cycleSelect,c.id,`${c.modules?.length||0} modules · ${c.edges?.length||0} edges · ${c.id}`);
 for(const c of cycles)insightOption(findingSelect,`cycle:${c.id}`,`Cycle · ${c.modules?.slice(0,2).join(' ↔ ')||c.id}`);
 for(const c of (healthFindings.complexity||[]).slice(0,80))insightOption(findingSelect,`complexity:${c.id}`,`Complexity · ${c.title} · ${c.file}:${c.line}`);
 if(healthFindings.unusedScanEligible)for(const c of (healthFindings.unused||[]).slice(0,40))insightOption(findingSelect,`unused:${c.id}`,`Possibly unused · ${c.title}`);
 for(const c of findingItems.slice(0,40))insightOption(findingSelect,`duplication:${c.id}`,`Duplication · ${c.first} ↔ ${c.second}`);
 if(cycles.length){cycleSelect.value=cycles.some(c=>c.id===oldCycle)?oldCycle:cycles[0].id;cycleSelect.disabled=false;$('#insightsEvidence').disabled=false;renderInsightsGraph();}
 else{cycleSelect.disabled=true;$('#insightsEvidence').disabled=true;$('#insightsGraph').replaceChildren();insightEmpty($('#insightsEdges'),'No static import cycles reported for this Python snapshot. This does not prove that all dependencies are known.');$('#insightsGraphMeta').textContent='No cycles reported';}
 if(oldFinding&&[...findingSelect.options].some(o=>o.value===oldFinding))findingSelect.value=oldFinding;
 insightSelection=cycleSelect.value;
 if(typeof wsRefresh==='function')void wsRefresh();
 $('#insightsStatus').textContent=`${cycles.length} static import cycles · ${healthFindings.pythonFilesScanned} Python files scanned · commit ${healthFindings.commit.slice(0,12)}. The graph shows cycles, not all dependencies.`;
}
function renderInsightsGraph(){
 const cycle=insightFind('cycle',$('#insightsCycle').value),svg=$('#insightsGraph'),edgeList=$('#insightsEdges');
 svg.replaceChildren();edgeList.replaceChildren();if(!cycle)return;
 const modules=cycle.modules||[], shown=modules.slice(0,10),edges=(cycle.edges||[]).filter(e=>shown.includes(e.from)&&shown.includes(e.to));
 $('#insightsGraphMeta').textContent=`${modules.length} modules · ${cycle.edges?.length||0} detected edges${modules.length>shown.length?' · graph truncated':''}`;
 const coords=new Map();shown.forEach((m,i)=>{const rad=2*Math.PI*i/Math.max(1,shown.length)-Math.PI/2;coords.set(m,{x:300+185*Math.cos(rad),y:115+75*Math.sin(rad)});});
 const defs=insightNode('defs',{}),marker=insightNode('marker',{id:'insightArrow',viewBox:'0 0 10 10',refX:8,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'});marker.append(insightNode('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#9c8ae8'}));defs.append(marker);svg.append(defs);
 for(const e of edges){
  const a=coords.get(e.from),b=coords.get(e.to),dx=b.x-a.x,dy=b.y-a.y,len=Math.max(1,Math.hypot(dx,dy)),ux=dx/len,uy=dy/len;
  const start={x:a.x+ux*28,y:a.y+uy*19},end={x:b.x-ux*32,y:b.y-uy*23};
  // Opposing directions use distinct lanes so arrowheads remain readable.
  const lane=(shown.length===2?Math.sign(shown.indexOf(e.to)-shown.indexOf(e.from))*0+35:12);
  const normal={x:-uy*lane,y:ux*lane};
  svg.append(insightNode('path',{d:`M ${start.x} ${start.y} Q ${(start.x+end.x)/2+normal.x} ${(start.y+end.y)/2+normal.y} ${end.x} ${end.y}`,stroke:'#9c8ae8','stroke-width':2,fill:'none','marker-end':'url(#insightArrow)'}));
 }
 for(const m of shown){const p=coords.get(m);svg.append(insightNode('rect',{x:p.x-58,y:p.y-17,width:116,height:34,rx:9,fill:'#292742',stroke:'#a894eb','stroke-width':1.4}));const short=m.split('.').at(-1);const text=insightNode('text',{x:p.x,y:p.y+4,'text-anchor':'middle',fill:'#f1f0ff','font-size':12},short.length>16?short.slice(0,15)+'…':short);text.append(insightNode('title',{},m));svg.append(text);}
 if(modules.length>shown.length)edgeList.append(el('p',`${modules.length-shown.length} modules omitted from graph to preserve readability; see Code health for the full finding.`,'quiet'));
 for(const e of (cycle.edges||[])){const row=el('div','','insights-edge');row.append(el('span',`${e.from} → ${e.to}`));const b=el('button','Find source','secondary');b.type='button';b.onclick=async()=>{
  try{const r=await api(`/api/evidence?type=cycle&id=${encodeURIComponent(cycle.id)}&level=compact`);const found=(r.json?.edgeLocations||[]).find(x=>x.from===e.from&&x.to===e.to);const line=found?.locations?.[0]?.line;if(!line||!found.path){toast('The import location could not be verified; see evidence limitations.');return;}openFile(found.path,line);}
  catch(err){toast('Evidence unavailable: '+err.message);}
 };row.append(b);edgeList.append(row);}
}
async function inspectInsightEvidence(){
 const selected=$('#insightsFinding').value;if(!selected){insightEmpty($('#insightsCoverage'),'No findings available for evidence inspection.');return;}
 const [kind,id]=selected.split(':'),level=$('#insightsLevel').value,serial=++insightRequestSerial;
 insightEvidenceResult=null;$('#insightsExport').disabled=true;insightEmpty($('#insightsCoverage'),'Checking exact source anchors…');
 try{
  const result=await api(`/api/evidence?type=${encodeURIComponent(kind)}&id=${encodeURIComponent(id)}&level=${encodeURIComponent(level)}`);
  if(serial!==insightRequestSerial||selected!==$('#insightsFinding').value||level!==$('#insightsLevel').value)return;
  insightEvidenceResult=result;$('#insightsExport').disabled=false;
  const coverage=result.json?.evidenceCoverage||{},root=$('#insightsCoverage');root.replaceChildren();
  const complete=Number(coverage.completeAnchors||0),required=Number(coverage.requestedAnchors||0),ok=!!coverage.anchorsComplete;
  const header=el('div','','insights-coverage-row');header.append(el('strong',ok?'Source anchors complete':'Evidence incomplete'),el('strong',`${complete}/${required} complete anchors`));root.append(header);
  const track=el('div','','insights-track');const fill=el('span');rsStyle(fill,'width',required?`${Math.min(100,100*complete/required)}%`:'0%');track.append(fill);root.append(track);
  if(kind==='cycle')root.append(el('div',`${coverage.edgesWithCompleteSource??0}/${coverage.reportedEdges??0} reported edges have complete source excerpts; ${coverage.edgesWithLocatedImports??0} located imports.`,'insights-caution'));
  root.append(el('div',`${coverage.missingOrPartialAnchors??0} missing/partial anchors · ${coverage.missingEvidenceItems??0} missing evidence items · ${level} context`,'insights-caution'));
  for(const miss of (result.json?.missingEvidence||[]).slice(0,6))root.append(el('div',`${miss.path||'Unknown source'}: ${miss.problem||miss.reason||'not available'}`,'insights-caution'));
  if(result.json?.snippets?.some(s=>s.truncated))root.append(el('div','Some excerpts are truncated; review the full source before making changes.','insights-caution'));
  root.append(el('p','This measures source coverage only. It does not establish correctness, safe deletion, or complete callers.','quiet'));
 }catch(err){if(serial===insightRequestSerial){insightEmpty($('#insightsCoverage'),'Evidence unavailable: '+err.message);toast(err.message);}}
}
function openInsights(cycleId){setPage('insights');if(!healthFindings){$('#insightsStatus').textContent='Analyze Python to explore relationships.';return;}renderInsights();if(cycleId&&[...$('#insightsCycle').options].some(o=>o.value===cycleId)){$('#insightsCycle').value=cycleId;renderInsightsGraph();}if(cycleId){$('#insightsFinding').value=`cycle:${cycleId}`;void inspectInsightEvidence();if(typeof wsRefresh==='function')void wsRefresh();}}
$('#insightsCycle').onchange=()=>{renderInsightsGraph();$('#insightsFinding').value=`cycle:${$('#insightsCycle').value}`;void inspectInsightEvidence();if(typeof wsRefresh==='function')void wsRefresh();};
$('#insightsFinding').onchange=inspectInsightEvidence;
$('#insightsLevel').onchange=inspectInsightEvidence;
$('#insightsRefresh').onclick=inspectInsightEvidence;
$('#insightsEvidence').onclick=()=>{$('#insightsFinding').value=`cycle:${$('#insightsCycle').value}`;void inspectInsightEvidence();if(typeof wsRefresh==='function')void wsRefresh();};
$('#insightsExport').onclick=()=>{const value=$('#insightsFinding').value;if(!value||!insightEvidenceResult)return;const [kind,id]=value.split(':');$('#evidenceLevel').value=$('#insightsLevel').value;void openEvidence(kind,id);};
$('#insightsScan').onclick=async()=>{await scanHealth();renderInsights();};
$('.nav[data-page="insights"]').addEventListener('click',()=>{renderInsights();});
