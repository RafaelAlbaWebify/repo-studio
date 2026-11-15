/* Repo Studio F1.2 — read-only side-by-side inspection, no libraries. */
'use strict';
let compareItem=null, comparePayload=null, compareRequest=0, syncingCompare=false, impactRequest=0;
const compareEl=id=>document.getElementById(id);
const compareLines=text=>{const lines=text.split('\n');if(lines.at(-1)==='')lines.pop();return lines;};
function compareSlice(lines,start,size,context){
  const padding=context==='all'?0:Number(context);
  const begin=context==='all'?1:Math.max(1,start-padding);
  const end=context==='all'?lines.length:Math.min(lines.length,start+size+padding-1);
  return {begin,end};
}
function populateComparePane(which,lines,start,size,otherLines,otherStart,context){
  const parent=compareEl('compareLines'+which);
  parent.replaceChildren();
  const range=compareSlice(lines,start,size,context),frag=document.createDocumentFragment();
  for(let n=range.begin;n<=range.end;n++){
    const matched=n>=start&&n<start+size;
    const peer=otherStart+(n-start);
    const different=matched && (peer>otherLines.length||lines[n-1]!==otherLines[peer-1]);
    const row=document.createElement('div');
    row.className='compare-line'+(matched?' is-match':'')+(different?' is-different':'')+(n===start?' is-boundary is-active':'');
    row.dataset.line=String(n);
    const num=document.createElement('span');num.className='lineNo';num.textContent=String(n);
    const code=document.createElement('span');code.className='lineText';code.textContent=lines[n-1]||' ';
    row.append(num,code);frag.appendChild(row);
  }
  parent.appendChild(frag);
}
function alignComparison(){
  for(const suffix of ['A','B']){
    const panel=compareEl('compareScroll'+suffix);
    const target=compareEl('compareLines'+suffix).querySelector('.is-boundary');
    if(target)panel.scrollTop=Math.max(0,target.offsetTop-panel.offsetTop-panel.clientHeight/3);
  }
}
function renderComparison(){
  if(!compareItem||!comparePayload)return;
  const x=compareItem,context=compareEl('compareContext').value;
  const a=comparePayload.a,b=comparePayload.b;
  const first=Number(x.firstLine)||1,second=Number(x.secondLine)||1,size=Math.max(1,Number(x.lines)||1);
  populateComparePane('A',a,first,size,b,second,context);
  populateComparePane('B',b,second,size,a,first,context);
  let differing=0;
  for(let n=0;n<size;n++){
    const left=a[first+n-1],right=b[second+n-1];
    if(left!==right)differing++;
  }
  compareEl('compareCount').textContent=`${size} detector-reported lines · ${differing} text differences in aligned range · ${a.length} / ${b.length} file lines`;
  compareEl('compareGrid').classList.toggle('wrap-lines',compareEl('compareWrap').checked);
  requestAnimationFrame(alignComparison);
}
async function compareSources(item){
  compareItem=item;comparePayload=null;impactRequest++;
  compareEl('impactResult').textContent='Inspect both dependency contexts before proposing consolidation.';
  const id=++compareRequest;
  setPage('compare');
  compareEl('compareNameA').textContent=item.first+':'+item.firstLine;
  compareEl('compareNameB').textContent=item.second+':'+item.secondLine;
  compareEl('compareCount').textContent='Loading committed sources…';
  compareEl('compareError').classList.add('hidden');
  for(const suffix of ['A','B'])compareEl('compareLines'+suffix).replaceChildren();
  compareEl('compareOpenA').onclick=()=>openFile(item.first,item.firstLine);
  compareEl('compareOpenB').onclick=()=>openFile(item.second,item.secondLine);
  try{
    const [a,b]=await Promise.all([
      api('/api/file?path='+encodeURIComponent(item.first)),
      api('/api/file?path='+encodeURIComponent(item.second))
    ]);
    if(id!==compareRequest)return;
    comparePayload={a:compareLines(a.content),b:compareLines(b.content)};
    renderComparison();
  }catch(e){
    if(id!==compareRequest)return;
    compareEl('compareCount').textContent='Comparison unavailable';
    compareEl('compareError').textContent=e.message;
    compareEl('compareError').classList.remove('hidden');
  }
}
function synchronizeCompare(source,target){
  if(syncingCompare||!compareEl('compareSync').checked)return;
  syncingCompare=true;
  const sourceY=Math.max(1,source.scrollHeight-source.clientHeight);
  const targetY=Math.max(0,target.scrollHeight-target.clientHeight);
  const sourceX=Math.max(1,source.scrollWidth-source.clientWidth);
  const targetX=Math.max(0,target.scrollWidth-target.clientWidth);
  target.scrollTop=(source.scrollTop/sourceY)*targetY;
  target.scrollLeft=(source.scrollLeft/sourceX)*targetX;
  requestAnimationFrame(()=>{syncingCompare=false;});
}
compareEl('compareBack').onclick=()=>setPage('duplicates');
compareEl('compareContext').onchange=renderComparison;
compareEl('compareScrollA').onscroll=()=>synchronizeCompare(compareEl('compareScrollA'),compareEl('compareScrollB'));
compareEl('compareScrollB').onscroll=()=>synchronizeCompare(compareEl('compareScrollB'),compareEl('compareScrollA'));

/* Evidence is read-only and informational. Missing relationships never mean safe removal. */
function contextDetails(context,path){
  const target=context?.targets?.[path];
  if(!target)return {available:false,symbols:0,groups:[],message:'No indexed context returned'};
  const groups=[];
  const seen=new Set();
  function walk(node,depth=0){
    if(!node||typeof node!=='object'||depth>5)return;
    for(const [key,val] of Object.entries(node)){
      if(['callers','callees','imports','references'].includes(key)&&Array.isArray(val)){
        if(val.length){const sample=val.slice(0,6).map(x=>typeof x==='string'?x:JSON.stringify(x).slice(0,180));
          const signature=key+JSON.stringify(sample);if(!seen.has(signature)){groups.push({name:key,count:val.length,sample});seen.add(signature);}}
      }else if(key!=='symbols'&&val&&typeof val==='object')walk(val,depth+1);
    }
  }
  walk(target);
  return {available:true,symbols:target.docs?.symbols?.length||0,groups:groups.slice(0,10)};
}
function evidenceSection(label,path,result){
  const section=document.createElement('section');section.className='evidence-source';
  const h=document.createElement('h3');h.textContent=label+' · '+path;section.append(h);
  const summary=document.createElement('p');summary.className='quiet';
  if(result.error){summary.textContent='Context unavailable: '+result.error;section.append(summary);return section;}
  if(!result.available){summary.textContent=result.message;section.append(summary);return section;}
  summary.textContent=result.symbols+' indexed symbols · '+result.groups.length+' populated relationship groups (not exhaustive)';section.append(summary);
  if(!result.groups.length){const note=document.createElement('p');note.className='quiet';note.textContent='No relationships returned. This does NOT establish that the file has no consumers.';section.append(note);}
  for(const group of result.groups){const d=document.createElement('details');d.className='evidence-group';
    const title=document.createElement('summary');title.textContent=group.name+' ('+group.count+')';d.append(title);
    for(const item of group.sample){const entry=document.createElement('div');entry.className='evidence-reference';entry.textContent=item;d.append(entry);}section.append(d);
  }
  return section;
}
async function inspectImpact(){
  if(!compareItem)return;
  const current=compareItem,seq=++impactRequest;
  const target=compareEl('impactResult');target.replaceChildren();target.textContent='Retrieving indexed dependencies for both files…';
  compareEl('reviewImpact').disabled=true;
  try{
    const paths=[current.first,current.second];
    const contexts=await Promise.all(paths.map(async path=>{
      try{return contextDetails(await api('/api/context?path='+encodeURIComponent(path)),path);}
      catch(err){return {error:err.message};}
    }));
    if(seq!==impactRequest||compareItem!==current)return;
    target.replaceChildren();
    const note=document.createElement('p');note.className='evidence-warning';
    note.textContent='Static references may be incomplete (dynamic imports, framework routing, reflective calls). Duplication is not proof that code should be merged. No tests or runtime tracing have been executed.';
    target.append(note);
    paths.forEach((path,i)=>target.append(evidenceSection(i?'Source B':'Source A',path,contexts[i])));
    const verdict=document.createElement('p');verdict.className='quiet';
    verdict.textContent='Decision: manual review required. Verify behavior, security boundaries, callers and tests before suggesting changes.';
    target.append(verdict);
  }catch(err){if(seq===impactRequest)target.textContent=err.message;}
  finally{if(seq===impactRequest)compareEl('reviewImpact').disabled=false;}
}
compareEl('reviewImpact').onclick=inspectImpact;
compareEl('compareWrap').onchange=renderComparison;
compareEl('compareWide').onchange=()=>document.body.classList.toggle('wide-comparison',compareEl('compareWide').checked);
document.body.classList.toggle('wide-comparison',compareEl('compareWide').checked);
