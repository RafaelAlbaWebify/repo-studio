#!/usr/bin/env python3
"""Generate a full per-file P0-A coverage manifest for a local Git clone."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coverage_engine import coverage_report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-python', type=int, default=2500)
    args=p.parse_args()
    report=coverage_report(args.repo, max_analyzer_files=args.max_python)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    summary={key:report[key] for key in ('repositoryCommit','inventoryCount','pythonFileCount',
        'pythonAstStates','pythonInventoryReconciled','currentUnusedGlobalGateEligible',
        'elapsedSeconds','manifestSha256')}
    summary['dynamicFileCount']=len(report['dynamicIntrospectionFiles'])
    summary['output']=str(args.output)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if report['engineStates']['python_ast'] != 'completed':
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
