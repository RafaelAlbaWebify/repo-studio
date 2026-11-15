#!/usr/bin/env python3
"""Summarize manually recorded matched AI investigations (no API calls).

All token counts must be taken from model/provider usage logs. Zero is valid only
if the provider reported zero; unknown values are left empty, never guessed.
"""
import argparse
import csv
import json
from pathlib import Path

FIELDS = ('case_id','workflow','input_tokens','output_tokens','elapsed_seconds','quality_pass','followups','notes')

def read(path):
    rows = []
    with path.open(newline='',encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError('CSV is missing required columns: '+', '.join(FIELDS))
        for i, row in enumerate(reader, 2):
            if not any((v or '').strip() for v in row.values()):
                continue
            case = (row['case_id'] or '').strip()
            workflow = (row['workflow'] or '').strip().lower()
            if not case or workflow not in ('baseline','repo_studio'):
                raise ValueError(f'Row {i}: case_id and workflow baseline/repo_studio required')
            measure = {}
            for field in ('input_tokens','output_tokens','followups'):
                raw=(row[field] or '').strip()
                if not raw:
                    measure[field] = None
                elif not raw.isdecimal():
                    raise ValueError(f'Row {i}: invalid {field}')
                else:
                    measure[field] = int(raw)
            raw=(row['elapsed_seconds'] or '').strip()
            try: measure['elapsed_seconds'] = float(raw) if raw else None
            except ValueError: raise ValueError(f'Row {i}: invalid elapsed_seconds')
            if measure['elapsed_seconds'] is not None and measure['elapsed_seconds'] < 0:
                raise ValueError(f'Row {i}: negative elapsed_seconds')
            quality=(row['quality_pass'] or '').strip().lower()
            if quality not in ('','yes','no'):
                raise ValueError(f'Row {i}: quality_pass must be yes/no/blank')
            measure['quality_pass']=None if not quality else quality=='yes'
            rows.append((case,workflow,measure))
    return rows

def summarize(rows):
    cases={}
    for case,workflow,measure in rows:
        by_workflow=cases.setdefault(case,{})
        if workflow in by_workflow: raise ValueError('Duplicate case/workflow: '+case+' '+workflow)
        by_workflow[workflow]=measure
    comparisons=[]
    excluded=[]
    for case,flows in sorted(cases.items()):
        if set(flows) != {'baseline','repo_studio'}:
            excluded.append({'case_id':case,'reason':'Both workflows required'})
            continue
        a,b=flows['baseline'],flows['repo_studio']
        if any(x[k] is None for x in (a,b) for k in ('input_tokens','output_tokens','quality_pass')):
            excluded.append({'case_id':case,'reason':'Tokens or independently judged quality missing'})
            continue
        base=a['input_tokens']+a['output_tokens']; assisted=b['input_tokens']+b['output_tokens']
        comparisons.append({'case_id':case,'baseline_tokens':base,'repo_studio_tokens':assisted,
            'delta_tokens':assisted-base,'reduction_pct':round(100*(base-assisted)/base,2) if base>0 else None,
            'baseline_quality_pass':a['quality_pass'],'repo_studio_quality_pass':b['quality_pass'],
            'elapsed_baseline_seconds':a['elapsed_seconds'],'elapsed_repo_studio_seconds':b['elapsed_seconds'],
            'baseline_followups':a['followups'],'repo_studio_followups':b['followups']})
    # Aggregate only comparable cases where both workflows meet the quality threshold.
    eligible=[r for r in comparisons if r['baseline_quality_pass'] and r['repo_studio_quality_pass']]
    baseline=sum(x['baseline_tokens'] for x in eligible);assisted=sum(x['repo_studio_tokens'] for x in eligible)
    return {'cases_recorded':len(cases),'paired_with_quality':len(comparisons),'quality_matched_pairs':len(eligible),
        'baseline_total_tokens_quality_matched':baseline,'repo_studio_total_tokens_quality_matched':assisted,
        'quality_matched_reduction_pct':round(100*(baseline-assisted)/baseline,2) if baseline>0 else None,
        'comparisons':comparisons,'excluded':excluded,
        'caution':'Measured model usage only. Include ALL turns and follow-ups. Never extrapolate from chars/4.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('csv_path',type=Path);p.add_argument('--output',type=Path)
    args=p.parse_args();report=summarize(read(args.csv_path));output=json.dumps(report,indent=2,ensure_ascii=False)
    if args.output:args.output.write_text(output+'\n',encoding='utf-8')
    print(output)
if __name__=='__main__':main()
