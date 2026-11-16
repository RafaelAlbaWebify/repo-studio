'use strict';
// P0-B read-only investigation queue. No automatic edits, uploads or provider calls.
let triageCurrentRequest=0;
let triagePageOffset=0;
let triageLoadedCommit='';
const triageEl=id=>document.getElementById(id);
const triageText=(tag,value,cls='')=>{const n=document.createElement(tag);n.textContent=String(value??'');if(cls)n.className=cls;return n;};
function triageParams(){
 const params=new URLSearchParams({area:triageEl('triageArea').value,
 queue:triageEl('triageQueue').value,analyzer:triageEl('triageAnalyzer').value,
 hide_noise:triageEl('triageHideNoise').checked?'1':'0',offset:String(triagePageOffset),limit:'25'});
 return params.toString();
}
async function triageRefresh(reset=false){
 if(reset)triagePageOffset=0;
 const serial=++triageCurrentRequest;
 const list=triageEl('triageItems');list.replaceChildren(triageText('p','Loading existing analyzer evidence…','quiet'));
 triageEl('triageStatus').textContent='Reading local imported report';
 try{
  const summary=await api('/api/triage');
  if(serial!==triageCurrentRequest)return;
  if(summary.repositoryCommit!==state.commit)throw Error('Report commit differs from selected repository');
  const results=await api('/api/triage/findings?'+triageParams());
  if(serial!==triageCurrentRequest)return;
  triageLoadedCommit=summary.repositoryCommit;
  window.rsProfessionalPageItems=results.items;
  window.rsProfessionalPageCommit=summary.repositoryCommit;
  const counts=summary.counts;
  triageEl('triageStatus').textContent=`${counts.raw} raw records · ${counts.uniqueExact} exact unique · ${counts.exactDuplicateEntries} exact repeats · commit ${summary.repositoryCommit.slice(0,12)}`;
  triageEl('triageMatching').textContent=`Showing ${results.items.length?results.offset+1:0}–${results.offset+results.items.length} of ${results.totalMatching} matching records. Labels are review queues, not verified defects.`;
  triageEl('triagePrev').disabled=triagePageOffset===0;
  triageEl('triageNext').disabled=triagePageOffset+results.items.length>=results.totalMatching;
  list.replaceChildren();
  if(!results.items.length){list.append(triageText('p','No results for these filters. This does not establish absence of defects.','quiet'));return;}
  const frag=document.createDocumentFragment();
  for(const item of results.items){
   const card=triageText('article','','result');
   const header=triageText('div','','result-head');
   header.append(triageText('strong',`${item.path}:${item.line}`),triageText('span',`${item.analyzer} · ${item.rule||'unclassified'}`,'tag'));
   card.append(header);
   card.append(triageText('div',`${item.area} · ${item.reviewQueue} · ${item.inventoryStatus}`,'result-meta'));
   card.append(triageText('p',item.message||'No diagnostic message supplied.'));
   if(item.noiseReasons?.length)card.append(triageText('p',`Context label: ${item.noiseReasons.join(', ')} (not discarded)`,'quiet'));
   const actions=triageText('div','','result-actions');
   const source=triageText('button','Open committed source','result-action');source.type='button';
   source.addEventListener('click',()=>{if(triageLoadedCommit!==state.commit){toast('Repository changed; reload evidence first.');return;}openFile(item.path,item.line);});
   actions.append(source);
   const copy=triageText('button','Copy finding reference','result-action');copy.type='button';
   copy.addEventListener('click',()=>{
    const record={repositoryCommit:triageLoadedCommit,tool:item.analyzer,rule:item.rule,path:item.path,line:item.line,message:item.message,reviewQueue:item.reviewQueue,sourceIndex:item.sourceIndex,limitations:['Unverified diagnostic. Inspect callers, entrypoints and tests before changing code.']};
    navigator.clipboard.writeText(JSON.stringify(record,null,2)).then(()=>toast('Reference copied; check source before external sharing.')).catch(()=>toast('Clipboard unavailable.'));
   });
   actions.append(copy);
   if(window.rsProfessionalButton)actions.append(window.rsProfessionalButton(item,triageLoadedCommit));
   card.append(actions);frag.append(card);
  }
  list.append(frag);
 }catch(e){
  if(serial!==triageCurrentRequest)return;
  triageLoadedCommit='';list.replaceChildren(triageText('p','Professional evidence unavailable: '+e.message,'quiet'));
  triageEl('triageStatus').textContent='Not loaded — launch development Repo Studio with --triage-report matching this commit.';
  triageEl('triageMatching').textContent='';triageEl('triagePrev').disabled=true;triageEl('triageNext').disabled=true;
 }
}
for(const id of ['triageArea','triageQueue','triageAnalyzer','triageHideNoise'])triageEl(id).addEventListener('change',()=>triageRefresh(true));
triageEl('triageReload').addEventListener('click',()=>triageRefresh(true));
triageEl('triagePrev').addEventListener('click',()=>{triagePageOffset=Math.max(0,triagePageOffset-25);triageRefresh();});
triageEl('triageNext').addEventListener('click',()=>{triagePageOffset+=25;triageRefresh();});
document.querySelector('.nav[data-page="triage"]').addEventListener('click',()=>{void triageRefresh(true);});
