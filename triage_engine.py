"""Reproducible, local-only import of external analyzer evidence.

No project code executes. Raw diagnostics are kept in the original evidence directory;
this module builds a lossless-with-respect-to-fields normalized ledger and a separate
reversible triage view. Findings are not verified defects.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ANALYZERS = ("ruff", "pyright", "bandit", "vulture")
RAW_NOISE = {('bandit','B101'): 'assert_usage',
             ('pyright','reportMissingImports'): 'unresolved_import_environment'}


def _canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(',', ':'), default=str)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _area(path):
    if path.startswith('src/'):
        return 'production'
    if path.startswith('tests/') or path.startswith('test/') or '/tests/' in path:
        return 'tests'
    return 'other'


def _priority(item):
    """A review queue, not a defect/severity verdict."""
    area, tool, rule = item['area'], item['analyzer'], item.get('rule') or ''
    if area != 'production':
        return 'contextual'
    if (tool, rule) in RAW_NOISE:
        return 'environment_or_policy'
    if tool == 'bandit' and rule in ('B608','B314','B405'):
        return 'review_first'
    if tool == 'pyright' and rule not in ('reportMissingImports',):
        return 'review_first'
    if tool == 'bandit' and rule in ('B110','B112'):
        return 'review_next'
    if tool == 'vulture':
        return 'requires_reachability_proof'
    return 'untriaged'


def normalize(summary, findings, *, expected_commit=None, inventory=None):
    """Normalize the pilot without dropping a single raw entry.

    Inventory is an optional set of paths from a committed coverage manifest.
    Unrecognized paths are retained, but explicitly tagged as unverified.
    """
    if not isinstance(summary, dict) or not isinstance(findings, list):
        raise ValueError('Invalid pilot evidence data')
    commit = summary.get('repositoryCommit')
    if not isinstance(commit, str) or len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('Missing or invalid commit SHA')
    if expected_commit and commit != expected_commit:
        raise ValueError('Evidence SHA does not match the selected repository')
    records = summary.get('tools')
    if not isinstance(records, dict) or set(records) != set(ANALYZERS):
        raise ValueError('Missing or unexpected analyzer tool status')
    for name in ANALYZERS:
        rec=records[name]
        if not isinstance(rec,dict) or not str(rec.get('status','')).startswith('completed'):
            raise ValueError(f'{name} did not complete; refuse to claim full pilot ingestion')
        if not isinstance(rec.get('findingCount'),int) or rec['findingCount'] < 0:
            raise ValueError('Missing per-tool count')
    expected=summary.get('totals',{}).get('rawFindingCount')
    if not isinstance(expected,int) or len(findings) != expected:
        raise ValueError('Raw finding count mismatch')
    counts=Counter()
    seen={}
    ledger=[]
    for index,raw in enumerate(findings):
        if not isinstance(raw, dict):
            raise ValueError(f'Invalid raw finding {index}')
        tool=raw.get('analyzer')
        if tool not in ANALYZERS:
            raise ValueError('Unknown analyzer in finding')
        path=raw.get('path')
        if not isinstance(path,str) or not path or path.startswith('/') or '\\' in path or '..' in Path(path).parts:
            raise ValueError('Finding path is not a normalized relative path')
        line=raw.get('line')
        if not isinstance(line,int) or isinstance(line,bool) or line < 1:
            raise ValueError('Invalid line in source finding')
        counts[tool]+=1
        # The identity is exact on the source's meaningful fields, not a claim of semantic equivalence.
        key=(tool,path,line,raw.get('rule'),raw.get('message'))
        duplicate_of=seen.get(key)
        area=_area(path)
        item={'sourceIndex':index,'raw':raw,'analyzer':tool,'path':path,'line':line,
              'rule':raw.get('rule'),'area':area,
              'noiseReasons':[RAW_NOISE[(tool,raw.get('rule'))]] if (tool,raw.get('rule')) in RAW_NOISE else [],
              'inventoryStatus':('not_checked' if inventory is None else 'in_inventory' if path in inventory else 'not_in_inventory'),
              'duplicateOfSourceIndex':duplicate_of}
        item['reviewQueue']=_priority(item)
        item['id']=_sha(_canonical([commit,index,raw]).encode())[:20]
        ledger.append(item)
        if duplicate_of is None:
            seen[key]=index
    for name in ANALYZERS:
        if counts[name] != records[name]['findingCount']:
            raise ValueError(f'Per-tool finding count mismatch: {name}')
    areas=Counter(x['area'] for x in ledger)
    rules=Counter((x['analyzer'], str(x['rule'])) for x in ledger)
    noise=Counter(reason for x in ledger for reason in x['noiseReasons'])
    queues=Counter(x['reviewQueue'] for x in ledger if x['duplicateOfSourceIndex'] is None)
    path_unverified=sum(x['inventoryStatus']=='not_in_inventory' for x in ledger)
    return {'schemaVersion':1,'repositoryCommit':commit,
            'provenance':{'toolVersions':{n:records[n].get('toolVersion') for n in ANALYZERS},
                          'source':'P0-B standalone pilot; findings remain unverified'},
            'counts':{'raw':len(ledger),'uniqueExact':len(seen),'exactDuplicateEntries':len(ledger)-len(seen),
                      'byTool':dict(sorted(counts.items())), 'byArea':dict(sorted(areas.items())),
                      'noiseReasons':dict(sorted(noise.items())), 'reviewQueues':dict(sorted(queues.items())),
                      'pathsNotInInventory':path_unverified},
            'ruleCounts':[{'analyzer':tool,'rule':rule,'count':count} for (tool,rule),count in sorted(rules.items(),key=lambda p:(-p[1],p[0]))],
            'limitations':['Diagnostic counts do not equal confirmed defects.',
                           'Exact duplicate entries are retained and only visually deduplicated.',
                           'Noise classification is a reversible label, not a deletion or suppression.',
                           'A Pyright missing import may reflect unavailable dependencies in the isolated analyzer environment.',
                           'Vulture candidates require entrypoint and dynamic reference checking before removal.',
                           'File reachability and analyzer per-file coverage are not proven by this import.'],
            'findings':ledger}


def load_and_normalize(folder, *, expected_commit=None, coverage_path=None):
    folder=Path(folder)
    summary_path=folder/'summary.json'
    findings_path=folder/'findings.json'
    sb=summary_path.read_bytes(); fb=findings_path.read_bytes()
    summary=json.loads(sb); findings=json.loads(fb)
    inventory=None
    if coverage_path is not None:
        manifest=json.loads(Path(coverage_path).read_text(encoding='utf-8'))
        if manifest.get('repositoryCommit')!=summary.get('repositoryCommit'):
            raise ValueError('Coverage manifest and evidence disagree on commit')
        inventory={x['path'] for x in manifest.get('files',[])}
        if len(inventory)!=manifest.get('inventoryCount'):
            raise ValueError('Coverage manifest inventory does not reconcile')
    report=normalize(summary,findings,expected_commit=expected_commit,inventory=inventory)
    report['provenance']['inputSha256']={'summary.json':_sha(sb),'findings.json':_sha(fb)}
    report['provenance']['inputFolder']=str(folder.resolve())
    return report


def public_summary(report):
    """Return a bounded and source-free summary suitable for an HTTP endpoint."""
    return {k:report[k] for k in ('schemaVersion','repositoryCommit','counts','ruleCounts','limitations')}


def filter_findings(report, *, area='all', queue='all', analyzer='all', hide_noise=False, offset=0, limit=50):
    if area not in ('all','production','tests','other') or queue not in ('all','review_first','review_next','contextual','environment_or_policy','requires_reachability_proof','untriaged') or analyzer not in ('all',*ANALYZERS):
        raise ValueError('Invalid filter')
    if not isinstance(offset,int) or offset<0 or not isinstance(limit,int) or limit<1 or limit>200:
        raise ValueError('Invalid pagination')
    filtered=[x for x in report['findings'] if x['duplicateOfSourceIndex'] is None
              and (area=='all' or x['area']==area)
              and (queue=='all' or x['reviewQueue']==queue)
              and (analyzer=='all' or x['analyzer']==analyzer)
              and (not hide_noise or not x['noiseReasons'])]
    # Avoid source content in UI/API by default: only diagnostic message and references.
    page=[{'id':x['id'],'analyzer':x['analyzer'],'path':x['path'],'line':x['line'],
           'rule':x['rule'],'message':x['raw'].get('message'),
           'severity':x['raw'].get('severity'),'confidence':x['raw'].get('confidence'),
           'area':x['area'],'reviewQueue':x['reviewQueue'],
           'noiseReasons':x['noiseReasons'],'inventoryStatus':x['inventoryStatus'],
           'sourceIndex':x['sourceIndex']} for x in filtered[offset:offset+limit]]
    return {'totalMatching':len(filtered),'offset':offset,'limit':limit,'items':page,
            'note':'Filtered view only. Original report retains every raw record.'}
