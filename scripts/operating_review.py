#!/usr/bin/env python3
"""Advisory local review; explicit host scheduling is separate. No external sends."""
import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from operating_records import clock, instant, load, validate, freshness, readiness


def validate_config(config):
    if not isinstance(config, dict): raise ValueError('config must be an object')
    if config.get('schema_version') != 1 or type(config.get('enabled')) is not bool:
        raise ValueError('config requires schema_version 1 and boolean enabled')
    if not config['enabled']: return
    for key in ['owner', 'destination', 'required_response', 'sources', 'threshold', 'max_runtime_seconds', 'max_cost', 'cadence', 'permitted_actions']:
        if key not in config: raise ValueError(f'missing config {key}')
    if not config['owner'] or not config['sources'] or not config['destination'] or not config['required_response']: raise ValueError('owner, sources, destination and response cannot be empty')
    if config['permitted_actions'] != ['recommend'] or config['max_cost'] != 0:
        raise ValueError('offline review supports recommend only and max_cost 0')
    if type(config['max_runtime_seconds']) not in (int, float) or not math.isfinite(config['max_runtime_seconds']) or not 0 < config['max_runtime_seconds'] <= 300: raise ValueError('runtime must be between 0 and 300 seconds')
    if config['threshold'] != 'Any missing, stale, expired or invalid evidence': raise ValueError('unsupported threshold; only built-in freshness review is implemented')
    if not isinstance(config['sources'], list) or not all(isinstance(s, str) for s in config['sources']): raise ValueError('sources must be record ids')
    if not isinstance(config['cadence'], dict): raise ValueError('cadence must be an object')
    cadence = config['cadence']
    if cadence.get('kind') == 'interval':
        if type(cadence.get('seconds')) is not int or cadence['seconds'] <= 0: raise ValueError('interval seconds must be positive')
    elif cadence.get('kind') in {'daily', 'weekly'}:
        ZoneInfo(cadence['timezone'])
        datetime.strptime(cadence['time'], '%H:%M')
        if cadence['kind'] == 'weekly' and (type(cadence.get('weekday')) is not int or not 0 <= cadence['weekday'] <= 6): raise ValueError('weekday must be 0 (Monday) through 6')
    else: raise ValueError('unknown cadence kind')


def next_due(cadence, now):
    if cadence['kind'] == 'interval': return now + timedelta(seconds=cadence['seconds'])
    zone = ZoneInfo(cadence['timezone'])
    local = now.astimezone(zone)
    hour, minute = map(int, cadence['time'].split(':'))
    # Round-trip through UTC normalizes nonexistent spring-forward local times.
    for days in range(9):
        candidate = (local + timedelta(days=days)).replace(hour=hour, minute=minute, second=0, microsecond=0, fold=0)
        if cadence['kind'] == 'weekly' and candidate.weekday() != cadence['weekday']: continue
        candidate = candidate.astimezone(now.tzinfo)
        if candidate > now: return candidate
    raise ValueError('unable to calculate next due')


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as handle:
            json.dump(value, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def run_review(config, bundle, state_path, now, force=False):
    started = time.monotonic()
    validate_config(config)
    if not config['enabled']: return {'status': 'disabled', 'notifications': []}
    # flock releases automatically on interruption; there is no stale lock to steal.
    import fcntl
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(state_path) + '.lock', 'a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return {'status': 'overlap', 'notifications': []}
        state = load(state_path) if state_path.exists() else {}
        if not isinstance(state, dict): raise ValueError('invalid state object')
        config_digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        if not force and config_digest == state.get('config_digest') and state.get('next_due') and instant(state['next_due']) > now:
            return {'status': 'not_due', 'notifications': [], 'next_due': state['next_due']}
        errors = validate(bundle)
        issues = errors
        if not errors:
            index = {r['id']: r for r in bundle['records']}
            selected = set()
            def visit(rid):
                if rid in selected or rid not in index: return
                selected.add(rid)
                row = index[rid]
                for ref in row['links']: visit(ref)
                for key in ['objective', 'strategy']:
                    if key in row['data']: visit(row['data'][key])
                for key in ['evidence', 'evidence_plan']:
                    for ref in row['data'].get(key, []): visit(ref)
            for rid in config['sources']: visit(rid)
            scoped = dict(bundle, records=[index[rid] for rid in selected])
            issues = freshness(scoped, now)
            ready = readiness(bundle, now)
            issues = sorted(set(issues + ready['errors'] + ready['issues']))
        if not errors:
            ids = {r['id'] for r in bundle['records']}
            issues += [f'missing source: {source}' for source in config['sources'] if source not in ids]
        digest = hashlib.sha256(json.dumps([sorted(issues), config_digest]).encode()).hexdigest()
        notifications = []
        if issues and digest != state.get('issue_digest'):
            notifications = [{'owner': config['owner'], 'destination': config['destination'], 'required_response': config['required_response'], 'issues': issues}]
        result = {'status': 'failed' if errors else 'reviewed', 'notifications': notifications, 'issues': issues,
                  'last_attempt': now.isoformat(), 'next_due': next_due(config['cadence'], now).isoformat(),
                  'issue_digest': digest, 'config_digest': config_digest, 'last_success': state.get('last_success'),
                  'delivery': 'local persisted outbox only; no external delivery', 'max_cost': 0}
        if not errors: result['last_success'] = now.isoformat()
        # Persist the outbox with dedupe state in one replacement. Consumers must dedupe delivery themselves.
        result['outbox'] = (state.get('outbox', []) + notifications)[-100:]
        if time.monotonic() - started > config['max_runtime_seconds']:
            raise ValueError('review runtime budget exceeded before persistence')
        atomic_write(state_path, result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', default='docs/operations/records.json')
    parser.add_argument('--config', default='docs/operations/review-config.json')
    parser.add_argument('--state', default='docs/operations/review-state.json')
    parser.add_argument('--now'); parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    try:
        config = load(args.config)
        validate_config(config)
        bundle = load(args.records) if config.get('enabled') else {}
        result = run_review(config, bundle, args.state, clock(args.now), args.force)
        print(json.dumps(result, indent=2)); return int(result['status'] == 'failed')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)})); return 1

if __name__ == '__main__': raise SystemExit(main())
