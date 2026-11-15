'use strict';
let workspaceItems=[];
let wsRefreshSerial=0;
let wsHistorySerial=0;
const ws=id=>document.getElementById(id);
function wsIdentity(){const value=ws('insightsFinding').value;const i=value.indexOf(':');return i<1?null:{kind:value.slice(0,i),id:value.slice(i+1)};}
async function wsRefresh(){
 const serial=++wsRefreshSerial;const identity=wsIdentity();ws('workspaceIdentity').textContent=identity?`${identity.kind} · ${identity.id} · ${state.commit.slice(0,12)}`:'Select a finding';
 try{const response=await api('/api/workspace');if(serial!==wsRefreshSerial||response.commit!==state.commit||JSON.stringify(identity)!==JSON.stringify(wsIdentity()))return;workspaceItems=response.items;
 const item=identity&&workspaceItems.find(x=>x.finding_type===identity.kind&&x.finding_id===identity.id);
 ws('workspaceProgress').value=item?.progress||'pending';ws('workspaceDecision').value=item?.decision||'undecided';ws('workspaceNotes').value=item?.notes||'';
 ws('workspaceHistory').textContent=item?`Saved ${item.updated_at}; exports: ${item.exports.length} (${item.exports.map(e=>e.method+' '+e.level+' '+e.created_at).join('; ')})`:'No saved review or export for this commit.';
 ws('workspaceSave').disabled=!identity;
 }catch(e){ws('workspaceMessage').textContent=e.message;}
}
ws('workspaceSave').onclick=async()=>{const identity=wsIdentity();if(!identity)return;try{
 await post('/api/workspace/update',{...identity,progress:ws('workspaceProgress').value,decision:ws('workspaceDecision').value,notes:ws('workspaceNotes').value});
 ws('workspaceMessage').textContent='Review saved locally';await wsRefresh();await wsLoadHistory();
 }catch(e){ws('workspaceMessage').textContent='Save failed: '+e.message;}};
ws('insightsFinding').addEventListener('change',wsRefresh);
async function wsRecordExport(method,pkg){const identity=wsIdentity();if(!identity||!pkg?.markdown)return;
 const bytes=new TextEncoder().encode(pkg.markdown);const digest=await crypto.subtle.digest('SHA-256',bytes);
 const sha256=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
 await post('/api/workspace/export',{...identity,method,level:builderLevel,sha256});await wsRefresh();await wsLoadHistory();
}
setTimeout(wsRefresh,0);

// Cross-commit ledger is read-only: an old commit is never treated as a present finding.
let wsHistoryItems=[];
function wsRenderHistory(){
 const query=ws('workspaceFilter').value.trim().toLocaleLowerCase();
 const progress=ws('workspaceProgressFilter').value;
 const decision=ws('workspaceDecisionFilter').value;
 const exported=ws('workspaceExportFilter').value;
 const freshness=ws('workspaceFreshnessFilter').value;
 const matches=wsHistoryItems.filter(item=>(progress==='all'||item.progress===progress)&&
  (decision==='all'||item.decision===decision)&&
  (exported==='all'||(exported==='exported'?item.export_count>0:item.export_count===0))&&
  (freshness==='all'||(freshness==='unknown'?String(item.revalidation||'').startsWith('unknown'):item.revalidation===freshness))&&
  [item.finding_type,item.finding_id,item.commit_sha,item.notes,item.decision].some(v=>String(v||'').toLocaleLowerCase().includes(query)));
 const list=ws('workspaceLedger');list.replaceChildren();
 ws('workspaceLedgerSummary').textContent=`${matches.length} matching saved investigations (up to ${wsHistoryItems.length} recently updated records).`;
 if(!matches.length){list.append(el('p','No saved investigations match these filters.','quiet'));return;}
 for(const item of matches){
  const current=item.commit_sha===state.commit;
  const entry=el('div','','workspace-ledger-entry');
  entry.append(el('strong',`${item.finding_type} · ${item.finding_id}`));
  entry.append(el('div',`${item.progress} · ${item.decision} · ${item.export_count} exports · ${current?'CURRENT COMMIT':'HISTORICAL COMMIT'}`,'quiet'));
  const revalidation={current_snapshot:'Review tied to current commit',source_changed:'Source files changed — revalidate this review',source_unchanged:'Tracked evidence files unchanged — historical review; no finding equivalence implied',unknown_legacy:'Historical review — source anchors unavailable',unknown_commit:'Historical review — commit comparison unavailable'};
  entry.append(el('div',revalidation[item.revalidation]||'Review currency unknown','quiet'));
  entry.append(el('div',`Commit ${item.commit_sha.slice(0,12)} · Last updated ${item.updated_at}`,'quiet'));
  if(item.notes)entry.append(el('p',item.notes));
  if(current){
   const button=el('button','Select in current investigation','secondary');button.type='button';
   const choice=`${item.finding_type}:${item.finding_id}`;
   const found=[...ws('insightsFinding').options].some(o=>o.value===choice);
   button.disabled=!found;
   button.title=found?'Select this finding in the current analysis':'Not available in the current finding selector';
   button.addEventListener('click',()=>{ws('insightsFinding').value=choice;ws('insightsFinding').dispatchEvent(new Event('change'));wsRefresh();});
   entry.append(button);
  }
  list.append(entry);
 }
}
async function wsLoadHistory(){
 wsHistoryItems=[];ws('workspaceLedger').replaceChildren();
 const serial=++wsHistorySerial;try{
  const result=await api('/api/workspace/history');
  if(serial!==wsHistorySerial||result.current_commit!==state.commit)return;
  wsHistoryItems=result.items||[];
  wsRenderHistory();
  if(result.truncated)ws('workspaceLedgerSummary').textContent+=` Showing newest ${wsHistoryItems.length} of ${result.total}; older entries are not loaded.`;
 }catch(err){ws('workspaceLedgerSummary').textContent='History could not be loaded: '+err.message;}
}
ws('workspaceFilter').addEventListener('input',wsRenderHistory);
ws('workspaceProgressFilter').addEventListener('change',wsRenderHistory);
ws('workspaceDecisionFilter').addEventListener('change',wsRenderHistory);
ws('workspaceExportFilter').addEventListener('change',wsRenderHistory);
ws('workspaceFreshnessFilter').addEventListener('change',wsRenderHistory);
ws('workspaceReload').addEventListener('click',()=>{void wsRefresh();void wsLoadHistory();});
void wsLoadHistory();
