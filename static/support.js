'use strict';
/* Delayed contextual explanations without relaxing CSP or loading dependencies. */
const helpMap={triage:'Review imported professional diagnostics by area, analyzer and review queue. Labels do not prove defects or severity.',overview:'Repository summary, analysis status and links to the code behind each result.',findings:'Review grouped duplication cases; nothing is auto-deleted.',analysis:'Python AST import cycles, complexity and possible unused-code candidates.',insights:'Inspect detected import cycles and choose the evidence sent to an external AI.',duplicates:'Review jscpd clone matches; a match is not an instruction to remove code.',files:'Browse source from the selected Git commit in read-only mode.',symbols:'Search symbols in the optional Repowise index; validate the index provenance.',help:'Open the indexed user guide and illustrated workflows.',about:'Version, purpose, limitations and safety boundaries.'};
const fixedHelp={workspaceSave:'Persist a human review decision, progress and notes locally for this repository and commit.',workspaceReload:'Refresh saved investigation history; current-commit identity remains explicit.',workspaceExportFilter:'Filter investigations by recorded export history; saved reviews are not automatically exported.',workspaceFreshnessFilter:'Filter source revalidation: changed, unchanged, unverified or current commit. Unchanged source does not prove correctness.',workspaceProgressFilter:'Filter human-entered review progress without changing records.',workspaceDecisionFilter:'Filter human-entered decisions without automatically approving findings.',triageReload:'Reload the imported professional report without rerunning Ruff, Pyright, Bandit or Vulture.',triageQueue:'Filter reversible review queues; these are not verified severity ratings.',triageHideNoise:'Hide labeled noise from the current view; the original report remains unchanged.',auditBtn:'Run the optional jscpd duplication scan on committed files. Separate from Python AST analysis.',dashboardScan:'Analyze committed Python files for import cycles, complexity and conservative unused-code candidates.',runAnalysis:'Run the same Python code analysis shown on Overview.',insightsScan:'Run Python analysis to populate dependency and evidence views.',contextLoad:'Load source excerpts for the selected finding. Choose which snippets to include.',contextCopy:'Copy the human-selected investigation Markdown. Review private source first.',contextDownload:'Save selected evidence as a Markdown investigation.',insightsEvidence:'Inspect evidence coverage for the selected cycle.',insightsExport:'Open a source-backed export preview for human review.',selectBtn:'Switch to another local Git repository; resets selected analysis results.',openSearchBtn:'Search the configured Repowise index.',analysisType:'Filter Python candidate types.',analysisSort:'Sort candidates; no automatic severity verdicts.',contextBudget:'Approximate token budget (characters divided by four); not a real tokenizer count.',evidenceLevel:'Compact, Balanced and Extended control context amount, not confidence.',evidenceSize:'Estimated token count and evidence-anchor coverage.'};
for(const item of document.querySelectorAll('.nav')){const key=item.dataset.page;if(key&&helpMap[key])item.dataset.help=helpMap[key];}
for(const [id,description] of Object.entries(fixedHelp)){const node=document.getElementById(id);if(node&&!node.dataset.help)node.dataset.help=description;}
const tip=document.getElementById('hoverHelp');let timer=null,current=null;
function closeTip(){clearTimeout(timer);timer=null;current=null;tip.classList.add('hidden');}
/* RS_QA_CSP_TOOLTIP_V1: bounded CSSOM positioning; no inline style attributes. */
const rsTipPosition=(()=>{
 const sheet=[...document.styleSheets].find(s=>s.href&&new URL(s.href).pathname==='/style.css');
 if(!sheet)throw Error('Local stylesheet unavailable for tooltip');
 const index=sheet.insertRule('#hoverHelp{max-width:330px;left:12px;top:12px}',sheet.cssRules.length);
 const rule=sheet.cssRules[index];
 return (left,top,width)=>{
  for(const v of [left,top,width])if(!Number.isFinite(v)||v<0||v>10000)throw Error('Invalid tooltip geometry');
  rule.style.setProperty('max-width',width+'px');
  rule.style.setProperty('left',left+'px');
  rule.style.setProperty('top',top+'px');
 };
})();
function openTip(target){
 const explanation=target?.dataset?.help;if(!explanation)return;
 tip.textContent=explanation;
 const r=target.getBoundingClientRect(),width=Math.min(330,window.innerWidth-24);
 const left=Math.max(12,Math.min(r.left,window.innerWidth-width-12));
 rsTipPosition(left,r.bottom+10,width);
 tip.classList.remove('hidden');
 const rect=tip.getBoundingClientRect();
 if(rect.bottom>window.innerHeight-10)rsTipPosition(left,Math.max(12,r.top-rect.height-10),width);
}
document.addEventListener('pointerover',e=>{const t=e.target.closest('[data-help]');if(!t||current===t)return;closeTip();current=t;timer=setTimeout(()=>{if(current===t)openTip(t);},650);});
document.addEventListener('pointerout',e=>{const t=e.target.closest('[data-help]');if(t&&t===current&&!t.contains(e.relatedTarget))closeTip();});
document.addEventListener('focusin',e=>{const t=e.target.closest('[data-help]');if(t){closeTip();current=t;openTip(t);}});
document.addEventListener('focusout',()=>closeTip());
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeTip();});
window.addEventListener('scroll',closeTip,true);window.addEventListener('resize',closeTip);
function showTaskActivity(message){document.getElementById('taskActivityText').textContent=message;document.getElementById('taskActivity').classList.remove('hidden');}
function hideTaskActivity(){document.getElementById('taskActivity').classList.add('hidden');}
document.getElementById('aboutHelp').onclick=()=>setPage('help');
document.querySelectorAll('.help-index a').forEach(a=>a.onclick=e=>{e.preventDefault();const target=document.querySelector(a.getAttribute('href'));if(target)target.scrollIntoView({block:'start',behavior:'smooth'});});
