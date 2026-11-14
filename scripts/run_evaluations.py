#!/usr/bin/env python3
"""Offline deterministic evaluation of supplied outputs; does not call an application."""
import argparse
import hashlib
import json
from operating_records import load, clock
from operating_review import atomic_write


def evaluate(suite, outputs, now):
    if not isinstance(suite, dict) or not isinstance(outputs, dict): raise ValueError('suite and outputs must be objects')
    if suite.get('schema_version') != 1 or outputs.get('schema_version') != 1: raise ValueError('schema_version must be 1')
    for key in ['id', 'version', 'rubric_version', 'cases', 'limits']:
        if not suite.get(key): raise ValueError(f'missing suite {key}')
    for key in ['candidate', 'versions', 'adapter', 'results']:
        if not outputs.get(key): raise ValueError(f'missing outputs {key}')
    if outputs['adapter'] != 'offline-supplied-output-v1': raise ValueError('unsupported adapter')
    if not isinstance(suite['cases'], list) or not isinstance(suite['limits'], list) or not isinstance(outputs['results'], dict) or not isinstance(outputs['versions'], dict): raise ValueError('invalid cases, limits, results or versions types')
    for key in ['model', 'prompt', 'tool', 'data', 'config', 'evaluator', 'policy', 'permissions']:
        if not isinstance(outputs['versions'].get(key), str) or not outputs['versions'][key].strip(): raise ValueError(f'missing version or reasoned N/A: {key}')
    if len(suite['cases']) > 10000: raise ValueError('case limit exceeded')
    results = []
    ids = set()
    for case in suite['cases']:
        if not isinstance(case, dict): raise ValueError('case must be an object')
        for key in ['id', 'input', 'expected', 'forbidden', 'category', 'risk', 'evaluator', 'evidence']:
            if key not in case: raise ValueError(f'case missing {key}')
        if not isinstance(case['id'], str) or not isinstance(case['expected'], str) or not isinstance(case['forbidden'], list) or not all(isinstance(term, str) and term for term in case['forbidden']): raise ValueError('invalid id, expected or forbidden values')
        if not isinstance(case['category'], str): raise ValueError('category must be a string')
        cid = case['id']
        if cid in ids: raise ValueError(f'duplicate case {cid}')
        ids.add(cid)
        actual = outputs['results'].get(cid)
        if not isinstance(actual, dict) or actual.get('status') != 'executed' or not isinstance(actual.get('output'), str):
            results.append({'id': cid, 'result': 'unknown', 'hard_fail': False, 'quality': None}); continue
        text = actual['output']
        hard = any(term in text for term in case['forbidden'])
        passed = text == case['expected']
        results.append({'id': cid, 'result': 'failed' if hard or not passed else 'passed', 'hard_fail': hard,
                        'quality': int(passed), 'output': text, 'efficiency': actual.get('efficiency'), 'category': case['category']})
    if set(outputs['results']) - ids: raise ValueError('outputs contain unknown case identities')
    if not isinstance(suite.get('required_categories', []), list) or not all(isinstance(c, str) for c in suite.get('required_categories', [])): raise ValueError('required_categories must be strings')
    missing = sorted(set(suite.get('required_categories', ['boundary', 'recovery'])) - {c['category'] for c in suite['cases']})
    passed = all(r['result'] == 'passed' for r in results) and not missing
    return {'schema_version': 1, 'suite': suite['id'], 'suite_version': suite['version'], 'rubric_version': suite['rubric_version'],
            'candidate': outputs['candidate'], 'versions': outputs['versions'], 'adapter': outputs['adapter'],
            'timestamp': now.isoformat(), 'result': 'passed' if passed else 'blocked', 'cases': results,
            'coverage': {'executed': sum(r['result'] != 'unknown' for r in results), 'total': len(results), 'missing_categories': missing},
            'suite_digest': hashlib.sha256(json.dumps(suite, sort_keys=True).encode()).hexdigest(),
            'limits': suite['limits'] + ['Supplied output authenticity is not verified. No deployment or customer outcome assurance.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True); parser.add_argument('--outputs', required=True)
    parser.add_argument('--output'); parser.add_argument('--now')
    args = parser.parse_args()
    try:
        result = evaluate(load(args.suite), load(args.outputs), clock(args.now))
        if args.output: atomic_write(args.output, result)
        print(json.dumps(result, indent=2)); return int(result['result'] != 'passed')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'result': 'blocked', 'error': str(exc)})); return 1

if __name__ == '__main__': raise SystemExit(main())
