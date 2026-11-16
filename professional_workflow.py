"""Commit-pinned, bounded investigation dossiers for imported diagnostics.

No execution, no dependency claims, no speculative fixes. Source comes from the
verified committed Git tree. Separate from existing AST evidence export.
"""
from __future__ import annotations
import hashlib
import json

LEVELS={'compact':10,'balanced':22,'extended':45}
MAX_DOSSIER_CHARS=17000


def find_finding(report, finding_id):
    if not isinstance(finding_id,str) or len(finding_id)!=20 or any(c not in '0123456789abcdef' for c in finding_id):
        raise ValueError('Invalid professional finding id')
    matches=[x for x in report['findings'] if x.get('id')==finding_id]
    if len(matches)!=1 or matches[0].get('duplicateOfSourceIndex') is not None:
        raise ValueError('Unknown or duplicate professional finding')
    finding=matches[0]
    if finding.get('inventoryStatus')!='in_inventory':
        raise ValueError('Cannot open finding outside verified inventory')
    return finding


def dossier(report, finding_id, commit, read_source, level='balanced'):
    if level not in LEVELS: raise ValueError('Invalid dossier level')
    if report.get('repositoryCommit') != commit: raise ValueError('Stale imported evidence')
    item=find_finding(report,finding_id)
    path=item['path']; line=item['line']
    try:
        source=read_source(path)
    except (OSError,ValueError,TimeoutError) as exc:
        raise ValueError('Pinned source unavailable for dossier') from exc
    lines=source.splitlines()
    if line>len(lines): raise ValueError('Finding line outside committed file')
    radius=LEVELS[level]
    first=max(1,line-radius); last=min(len(lines),line+radius)
    excerpt='\n'.join(f'{number:>5} | {lines[number-1]}' for number in range(first,last+1))
    payload={
        'schemaVersion':1,'kind':'professional','id':finding_id,
        'repositoryCommit':commit,'path':path,'line':line,
        'analyzer':item['analyzer'],'rule':item.get('rule'),
        'severityReported':item.get('raw',{}).get('severity'),
        'confidenceReported':item.get('raw',{}).get('confidence'),
        'reviewQueue':item['reviewQueue'],'area':item['area'],
        'message':item['raw'].get('message',''),
        'sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
        'excerptStart':first,'excerptEnd':last,'sourceLineCount':len(lines),
        'sourceExcerpt':excerpt,
        'sourceComplete':first==1 and last==len(lines),
        'consumerCoverage':'not_evaluated',
        'dependencyCoverage':'not_evaluated',
        'testCoverage':'not_evaluated',
        'verification':'UNVERIFIED_CANDIDATE',
        'reviewChecklist':[
            'Determine whether this path is reachable from supported entrypoints',
            'Inspect callers, data invariants, exception paths and dynamic references',
            'Identify relevant tests and reproduce behavior before proposing fixes',
            'Compare expected and actual behavior; decide whether to retain or change'
        ]
    }
    markdown=(
        f'# Professional investigation — {item["analyzer"]}: {item.get("rule") or "unclassified"}\n\n'
        f'- Repository commit: `{commit}`\n- Finding ID: `{finding_id}`\n'
        f'- Location: `{path}:{line}`\n- Review queue: `{item["reviewQueue"]}` (heuristic)\n'
        f'- Analyzer-reported severity: `{payload["severityReported"]}`\n'
        f'- Analyzer-reported confidence: `{payload["confidenceReported"]}`\n'
        f'- Validation: **UNVERIFIED**. No runtime, reachability, dependencies or tests verified.\n'
        f'- Committed source SHA-256: `{payload["sourceSha256"]}`\n'
        f'- Source context: lines {first}–{last} of {len(lines)}; '
        f'{"complete" if payload["sourceComplete"] else "PARTIAL"}.\n\n'
        f'## Diagnostic\n\n{payload["message"]}\n\n'
        f'## Committed source excerpt\n\n```python\n{excerpt}\n```\n\n'
        '## Investigate before making changes\n\n'+
        '\n'.join(f'- [ ] {q}' for q in payload['reviewChecklist'])+'\n\n'
        '**Limitations:** Only a bounded committed-source excerpt is supplied. '
        'Callers, entrypoints, dependencies and tests are NOT included or verified. '
        'This report is not proof of a bug and contains no recommended patch.\n'
    )
    if len(markdown)>MAX_DOSSIER_CHARS:
        raise ValueError('Dossier exceeds safety size; choose smaller context level')
    payload['markdown']=markdown
    return payload
