#!/usr/bin/env python3
"""Portable, declarative operational records. Never authenticates or grants authority."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

TYPES = {'strategy', 'objective', 'mission', 'evidence', 'finding', 'decision', 'evaluation', 'approval', 'control', 'review'}
STATUSES = {'draft', 'proposed', 'active', 'approved', 'rejected', 'superseded', 'complete', 'unknown', 'passed', 'failed', 'expired'}
REQUIRED = {
    'strategy': ['problem', 'policy'], 'objective': ['strategy', 'success_criteria'],
    'mission': ['objective', 'scope', 'allocation', 'attempts', 'checkpoint', 'problem', 'mechanism', 'alternatives', 'assumption', 'baseline', 'success_criteria', 'stop_criteria', 'evidence_plan'],
    'evidence': ['kind', 'summary', 'access_owner', 'retention'],
    'finding': ['evidence', 'confidence', 'recommendation'],
    'decision': ['question', 'evidence', 'rationale'],
    'evaluation': ['candidate', 'result', 'cases', 'limits'],
    'approval': ['approver', 'scope', 'candidate', 'policy_revision', 'evidence', 'expires_at', 'reuse', 'authentication'],
    'control': ['scope', 'enforcement', 'evidence'],
    'review': ['scope', 'destination', 'required_response'],
}


def instant(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamps require an explicit timezone')
    return dt.astimezone(timezone.utc)


def clock(value=None):
    return instant(value) if value else datetime.now(timezone.utc)


def load(path):
    if Path(path).stat().st_size > 2_000_000: raise ValueError('JSON input exceeds 2 MB limit')
    return json.loads(Path(path).read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f'non-finite JSON number: {value}')))


def validate(bundle):
    errors = []
    if not isinstance(bundle, dict) or bundle.get('schema_version') != 1:
        return ['root schema_version must be 1']
    rows = bundle.get('records')
    if not isinstance(rows, list) or not isinstance(bundle.get('versions'), dict):
        return ['records must be a list and versions must be a mapping']
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append('record must be an object'); continue
        rid = row.get('id', '?')
        for key in ['id', 'type', 'version', 'owner', 'status', 'created_at', 'updated_at', 'source', 'links', 'dependencies', 'data']:
            if key not in row or row[key] is None or row[key] == '':
                errors.append(f'{rid}: missing {key}')
        if not isinstance(row.get('owner'), str) or not row.get('owner', '').strip() or str(row.get('owner', '')).strip().lower() in {'tbd', 'todo', 'unknown', 'owner'}: errors.append(f'{rid}: owner must be named')
        if not isinstance(rid, str) or rid in ids:
            errors.append(f'{rid}: invalid or duplicate identity')
        else:
            ids.add(rid)
        if not isinstance(row.get('type'), str) or row.get('type') not in TYPES: errors.append(f'{rid}: unknown type')
        if not isinstance(row.get('status'), str) or row.get('status') not in STATUSES: errors.append(f'{rid}: unknown status')
        if type(row.get('version')) is not int or row.get('version', 0) < 1: errors.append(f'{rid}: version must be positive integer')
        try:
            if instant(row['updated_at']) < instant(row['created_at']): raise ValueError('updated before created')
        except (KeyError, ValueError, TypeError, AttributeError) as exc: errors.append(f'{rid}: invalid timestamps ({exc})')
        if not isinstance(row.get('source'), dict) or not all(row['source'].get(k) for k in ['ref', 'version']): errors.append(f'{rid}: source requires ref and version')
        if not isinstance(row.get('dependencies'), dict): errors.append(f'{rid}: dependencies must be a mapping')
        if not isinstance(row.get('links'), list): errors.append(f'{rid}: links must be a list')
        data = row.get('data')
        if not isinstance(data, dict): errors.append(f'{rid}: data must be a mapping'); continue
        for field in REQUIRED.get(row.get('type') if isinstance(row.get('type'), str) else '', []):
            if field not in data or data[field] is None or data[field] == '' or data[field] == []: errors.append(f'{rid}: missing data.{field}')
        if row.get('type') == 'evidence' and str(data.get('kind')) not in {'observation', 'reported', 'inference', 'unknown', 'not_applicable'}: errors.append(f'{rid}: invalid evidence kind')
        if row.get('type') == 'mission':
            allocation = data.get('allocation')
            attempts = data.get('attempts')
            if not isinstance(allocation, dict) or not allocation or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in allocation.values()): errors.append(f'{rid}: allocation requires nonnegative numeric limits')
            if not isinstance(attempts, dict) or type(attempts.get('used')) is not int or type(attempts.get('maximum')) is not int or not 0 <= attempts.get('used', -1) <= attempts.get('maximum', -1) or not 1 <= attempts.get('maximum', 0) <= 2: errors.append(f'{rid}: invalid attempt limits')
        if row.get('type') == 'mission' and str(data.get('checkpoint')) not in {'funding', 'implementation', 'release', 'observed_use'}: errors.append(f'{rid}: invalid checkpoint')
        for key in ['objective', 'strategy']:
            if key in data and not isinstance(data[key], str): errors.append(f'{rid}: {key} must be a record id')
        for key in ['evidence', 'evidence_plan']:
            if key in data and (not isinstance(data[key], list) or not all(isinstance(ref, str) for ref in data[key])): errors.append(f'{rid}: {key} must be a list of record ids')
        if 'due_at' in data:
            try: instant(data['due_at'])
            except (ValueError, TypeError, AttributeError): errors.append(f'{rid}: invalid due_at')
        if 'expires_at' in data:
            try: instant(data['expires_at'])
            except (ValueError, TypeError, AttributeError): errors.append(f'{rid}: invalid expiry')
        if 'max_age_seconds' in data and (type(data['max_age_seconds']) not in (int, float) or not math.isfinite(data['max_age_seconds']) or data['max_age_seconds'] <= 0): errors.append(f'{rid}: invalid max_age_seconds')
        if row.get('type') == 'approval':
            for key in ['approver', 'scope', 'candidate', 'policy_revision', 'reuse']:
                if not isinstance(data.get(key), str) or not data.get(key, '').strip(): errors.append(f'{rid}: {key} must be nonempty text')
            try: instant(data.get('expires_at'))
            except (ValueError, TypeError, AttributeError): errors.append(f'{rid}: invalid approval expiry')
            if str(data.get('authentication')) not in {'declaration', 'external_verification'}: errors.append(f'{rid}: invalid authentication label')
    for row in rows:
        if not isinstance(row, dict): continue
        references = list(row.get('links', [])) if isinstance(row.get('links'), list) else []
        data = row.get('data', {})
        if isinstance(data, dict):
            for key in ['strategy', 'objective']:
                if key in data: references.append(data[key])
            for key in ['evidence', 'evidence_plan']:
                if isinstance(data.get(key), list): references.extend(data[key])
        for ref in references:
            if not isinstance(ref, str) or ref not in ids: errors.append(f'{row.get("id")}: unresolved link {ref}')
    if bundle.get('current_mission') is not None and (not isinstance(bundle['current_mission'], str) or not any(isinstance(r, dict) and r.get('id') == bundle['current_mission'] and r.get('type') == 'mission' for r in rows)): errors.append('current_mission must reference a mission')
    if any(not isinstance(k, str) or not isinstance(v, str) or not v for k, v in bundle['versions'].items()): errors.append('versions must contain nonempty string values')
    return errors


def freshness(bundle, now):
    issues = []
    for row in bundle['records']:
        for key, version in row['dependencies'].items():
            if bundle['versions'].get(key) != version:
                issues.append(f'{row["id"]}: dependency {key} changed or missing')
        data = row['data']
        if instant(row['updated_at']) > now: issues.append(f'{row["id"]}: future-dated record')
        if row['type'] == 'decision' and row['status'] == 'proposed' and not data.get('due_at'): issues.append(f'{row["id"]}: pending decision has no due date')
        if row['type'] == 'decision' and row['status'] == 'proposed' and data.get('due_at') and instant(data['due_at']) <= now: issues.append(f'{row["id"]}: decision overdue')
        if row['type'] == 'evaluation' and data.get('result') != 'passed': issues.append(f'{row["id"]}: evaluation {data.get("result")}')
        expiry = data.get('expires_at')
        if expiry and instant(expiry) <= now: issues.append(f'{row["id"]}: expired')
        if row['type'] == 'evidence' and data.get('kind') == 'unknown': issues.append(f'{row["id"]}: evidence unknown')
        if data.get('max_age_seconds') is not None and (now - instant(row['updated_at'])).total_seconds() > data['max_age_seconds']: issues.append(f'{row["id"]}: stale telemetry')
    return issues


def record_digest(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def readiness(bundle, now):
    errors = validate(bundle)
    if errors: return {'complete': False, 'approved': False, 'errors': errors, 'issues': []}
    index = {r['id']: r for r in bundle['records']}
    mission = index.get(bundle.get('current_mission'))
    if mission is None:
        return {'complete': False, 'approved': False, 'errors': ['no current mission'], 'issues': []}
    def related(start):
        closure, pending = set(), list(start)
        while pending:
            rid = pending.pop()
            if rid in closure or rid not in index: continue
            closure.add(rid)
            row = index[rid]
            pending.extend(row['links'])
            for key in ['objective', 'strategy']:
                if key in row['data']: pending.append(row['data'][key])
            for key in ['evidence', 'evidence_plan']:
                pending.extend(row['data'].get(key, []))
        return closure
    closure = related([mission['id']])
    objective = index.get(mission['data'].get('objective'))
    strategy = index.get(objective['data'].get('strategy')) if objective else None
    if not objective or objective['type'] != 'objective': errors.append('mission requires linked objective')
    elif objective['status'] in {'rejected', 'expired', 'superseded', 'failed', 'unknown'}: errors.append('mission objective is no longer valid')
    if mission['data']['attempts']['used'] >= mission['data']['attempts']['maximum']: errors.append('attempt limit reached; record escalation and new authorization before further remediation')
    if not strategy or strategy['type'] != 'strategy': errors.append('objective requires linked strategy')
    elif strategy['status'] not in {'active', 'approved'}: errors.append('strategy is not approved/active')
    if mission['status'] not in {'active', 'approved'}: errors.append('mission is not approved/active')
    approvals = [r for r in bundle['records'] if r['type'] == 'approval' and r['data']['scope'] == mission['id'] and r['status'] == 'approved']
    def evidence_issues(selected):
        scoped = dict(bundle, records=[index[rid] for rid in selected])
        found = freshness(scoped, now)
        for rid in selected:
            row = index[rid]
            if row['type'] == 'evaluation':
                if row['data']['candidate'] != mission['data'].get('candidate'): found.append(f'{rid}: evaluation candidate does not match mission')
                if row['status'] not in {'passed', 'complete', 'approved'}: found.append(f'{rid}: evaluation status {row["status"]}')
                if row['data']['result'] != 'passed': found.append(f'{rid}: evaluation did not pass')
                cases = row['data']['cases']
                if not isinstance(cases, list) or not cases or any(isinstance(case, dict) and (case.get('result') != 'passed' or case.get('hard_fail')) for case in cases): found.append(f'{rid}: evaluation cases do not establish a pass')
            if row['type'] == 'evidence' and row['status'] in {'rejected', 'expired', 'superseded', 'failed', 'unknown'}: found.append(f'{rid}: evidence status {row["status"]}')
            if row['type'] == 'evidence' and row['data']['kind'] in {'reported', 'inference', 'not_applicable'} and row['status'] != 'approved': found.append(f'{rid}: evidence requires owner review')
        return found
    issues = evidence_issues(closure)
    valid_approvals = []
    for approval in approvals:
        data = approval['data']
        if instant(data['expires_at']) <= now: continue
        if not all(data.get(key) == mission['data'].get(key) and data.get(key) for key in ['candidate', 'policy_revision']): continue
        selected = closure | related([approval['id']])
        if evidence_issues(selected): continue
        bindings = data.get('bindings', {})
        required_bindings = selected - {approval['id']}
        if not isinstance(bindings, dict) or any(bindings.get(rid) != record_digest(index[rid]) for rid in required_bindings): continue
        if not approval['dependencies'] or any(bundle['versions'].get(k) != v for k, v in approval['dependencies'].items()): continue
        if any(index[e]['type'] not in {'evidence', 'evaluation'} for e in data['evidence']): continue
        if not all(approval['dependencies'].get('record:' + e) == str(index[e]['version']) for e in data['evidence']): continue
        valid_approvals.append(approval)
    if not valid_approvals: issues.append('no current candidate/policy/evidence-bound recorded approval')
    complete = not errors and not issues
    return {'complete': complete, 'approved': complete and bool(valid_approvals),
            'authenticated': False, 'errors': errors, 'issues': issues,
            'approval_note': 'approved means valid recorded declaration only; identity authentication and deployed enforcement are not verified.'}


def startup(bundle, now):
    result = readiness(bundle, now)
    if validate(bundle): return result
    result['current_mission'] = next((r for r in bundle['records'] if r['id'] == bundle.get('current_mission')), None)
    result['strategy_and_objectives'] = [r for r in bundle['records'] if r['type'] in {'strategy', 'objective'} and r['status'] not in {'superseded', 'rejected'}]
    result['pending_decisions'] = [r['id'] for r in bundle['records'] if r['type'] == 'decision' and r['status'] == 'proposed']
    result['controls'] = [r for r in bundle['records'] if r['type'] == 'control']
    result['authority'] = 'Advisory summary; consult authoritative records and the named owner.'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'readiness', 'startup', 'gate'])
    parser.add_argument('--records', default='docs/operations/records.json')
    parser.add_argument('--now')
    parser.add_argument('--approval-policy', choices=['authenticated', 'recorded'], default='authenticated')
    args = parser.parse_args()
    try:
        bundle = load(args.records)
        result = {'errors': validate(bundle)} if args.command == 'validate' else globals()['readiness' if args.command == 'gate' else args.command](bundle, clock(args.now))
        print(json.dumps(result, indent=2))
        return int(bool(result.get('errors')) or (args.command in {'readiness', 'gate'} and not result['complete']) or (args.command == 'gate' and not result.get('approved' if args.approval_policy == 'recorded' else 'authenticated', False)))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'errors': [str(exc)]})); return 1

if __name__ == '__main__': raise SystemExit(main())
