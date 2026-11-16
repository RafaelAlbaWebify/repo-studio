#!/usr/bin/env python3
"""Import an existing P0-B pilot run; never execute project source or analyzers."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from triage_engine import load_and_normalize, public_summary, filter_findings


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--coverage',type=Path,required=True)
    p.add_argument('--sha',required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    report=load_and_normalize(args.input, expected_commit=args.sha, coverage_path=args.coverage)
    if report['counts']['pathsNotInInventory']:
        raise ValueError('Evidence includes paths not present in the selected commit inventory')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=args.output.with_suffix(args.output.suffix+'.tmp')
    tmp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    tmp.replace(args.output)
    brief=public_summary(report)
    print(json.dumps({'result':'P0B_TRIAGE_PASS','output':str(args.output),'counts':brief['counts'],
                      'topRules':brief['ruleCounts'][:8],
                      'productionFirstCandidates':filter_findings(report,area='production',queue='review_first',limit=10)['totalMatching']},indent=2,ensure_ascii=False))

if __name__=='__main__':main()
