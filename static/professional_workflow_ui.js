'use strict';
/* RS_PROFESSIONAL_WORKFLOW_V1: commit-bound investigation actions and bounded dossiers. */
(function () {
  let selectedId='', dossierLevel='balanced', dossierData=null, pendingSerial=0;
  // RS_MODAL_FOCUS_SAFE_V1: preserve keyboard focus, trap Tab inside dialog and restore on close.
  let modalOpener=null;
  function closeModal(){const m=document.getElementById('rsProfessionalDialog');if(!m||m.classList.contains('hidden'))return;m.classList.add('hidden');if(modalOpener?.isConnected)modalOpener.focus();modalOpener=null;}
  const element=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n;};
  function addButton(parent, label, cb){const b=element('button',label,'result-action');b.type='button';b.addEventListener('click',cb);parent.append(b);return b;}
  function modal(){
    let m=document.getElementById('rsProfessionalDialog');if(m)return m;
    m=element('div',undefined,'rs-professional-dialog hidden');m.id='rsProfessionalDialog';m.setAttribute('role','dialog');m.setAttribute('aria-modal','true');m.setAttribute('aria-label','Professional investigation');
    const inner=element('div',undefined,'rs-professional-body');
    const heading=element('div',undefined,'rs-professional-heading');heading.append(element('strong','Professional investigation — unverified candidate'));
    addButton(heading,'Close',closeModal);inner.append(heading);
    const note=element('p','Review notes are stored in the existing local Workspace, scoped to repository and commit. No source is modified.','quiet');inner.append(note);
    const controls=element('div',undefined,'rs-professional-controls');
    const progress=element('select');progress.id='rsProProgress';for(const opt of ['pending','reviewing','reviewed'])progress.append(new Option(opt,opt));
    const decision=element('select');decision.id='rsProDecision';for(const opt of ['undecided','keep','investigate','propose_change'])decision.append(new Option(opt,opt));
    const level=element('select');level.id='rsProLevel';for(const opt of ['compact','balanced','extended'])level.append(new Option(opt,opt));level.value='balanced';
    const progressLabel=element('label','Progress');progressLabel.htmlFor=progress.id;const decisionLabel=element('label','Decision');decisionLabel.htmlFor=decision.id;const levelLabel=element('label','Context');levelLabel.htmlFor=level.id;controls.append(progressLabel,progress,decisionLabel,decision,levelLabel,level);inner.append(controls);
    const notes=element('textarea');notes.id='rsProNotes';notes.rows=3;notes.maxLength=4000;notes.placeholder='Evidence and conclusions (not a verified defect by default)';inner.append(notes);
    const acts=element('div',undefined,'rs-professional-actions');
    addButton(acts,'Save investigation',async()=>{
      try {await post('/api/workspace/update',{kind:'professional',id:selectedId,progress:progress.value,decision:decision.value,notes:notes.value});status.textContent='Saved in local Workspace for this commit';}
      catch(e){status.textContent='Save failed: '+e.message;}
    });
    addButton(acts,'Generate dossier',async()=>{
      const serial=++pendingSerial;status.textContent='Loading bounded committed source…';
      try{const d=await api('/api/professional/dossier?id='+encodeURIComponent(selectedId)+'&level='+encodeURIComponent(level.value));if(serial!==pendingSerial)return;
        dossierData=d;preview.value=d.markdown;status.textContent='Unverified dossier ready; check all content before sharing';
      }catch(e){status.textContent='Dossier failed: '+e.message;}
    });
    addButton(acts,'Copy dossier',async()=>{if(!dossierData){status.textContent='Generate a dossier first';return;}try{await navigator.clipboard.writeText(dossierData.markdown);status.textContent='Dossier copied; review before external sharing';}catch(e){status.textContent='Copy failed: '+e.message;}});
    inner.append(acts);
    const status=element('p','','quiet');status.id='rsProStatus';status.setAttribute('role','status');inner.append(status);
    const preview=element('textarea');preview.id='rsProPreview';preview.readOnly=true;preview.spellcheck=false;preview.rows=16;preview.placeholder='Generate dossier to display the exact bounded source evidence';inner.append(preview);
    m.append(inner);document.body.append(m);m.addEventListener('click',e=>{if(e.target===m)closeModal();});
    document.addEventListener('keydown',e=>{if(m.classList.contains('hidden'))return;if(e.key==='Escape'){e.preventDefault();closeModal();return;}if(e.key==='Tab'){const eligible=[...m.querySelectorAll('button,select,textarea,input,a[href],[tabindex]')].filter(x=>!x.disabled&&x.getClientRects().length&&x.tabIndex>=0);if(!eligible.length){e.preventDefault();return;}const first=eligible[0],last=eligible[eligible.length-1];if(e.shiftKey&&(document.activeElement===first||!m.contains(document.activeElement))){e.preventDefault();last.focus();}else if(!e.shiftKey&&(document.activeElement===last||!m.contains(document.activeElement))){e.preventDefault();first.focus();}}});return m;
  }
  async function open(item, commit){
    if(!item?.id||commit!==state.commit){toast('Evidence or repository changed; reload first');return;}
    modalOpener=document.activeElement;selectedId=item.id;dossierData=null;const m=modal();m.classList.remove('hidden');m.querySelector('.rs-professional-heading button')?.focus();document.getElementById('rsProPreview').value='';
    const status=document.getElementById('rsProStatus');status.textContent='Loading saved review…';
    const currentId=item.id;
    try{const data=await api('/api/workspace');if(currentId!==selectedId||commit!==state.commit)return;
      const previous=(data.items||[]).find(x=>x.finding_type==='professional'&&x.finding_id===item.id);
      document.getElementById('rsProProgress').value=previous?.progress||'pending';
      document.getElementById('rsProDecision').value=previous?.decision||'undecided';
      document.getElementById('rsProNotes').value=previous?.notes||'';
      status.textContent=previous?'Existing investigation loaded':'New investigation — not yet saved';
    }catch(e){status.textContent='Workspace load failed: '+e.message;}
  }
  // Event delegation: triage cards are recreated by filter/pagination without losing actions.
  document.addEventListener('click',e=>{
    const b=e.target.closest?.('[data-rs-pro-id]');if(!b)return;
    const id=b.dataset.rsProId, item=window.rsProfessionalPageItems?.find(x=>x.id===id);
    if(item)open(item,window.rsProfessionalPageCommit);
  });
  window.rsProfessionalButton=(item,commit)=>{
    const b=element('button','Investigate / dossier','result-action');b.type='button';b.dataset.rsProId=item.id;
    return b;
  };
})();
