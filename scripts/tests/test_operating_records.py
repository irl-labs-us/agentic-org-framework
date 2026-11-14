import copy
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from operating_records import validate, readiness, clock, record_digest

ROOT = Path(__file__).resolve().parents[2]
NOW = clock('2026-11-14T13:00:00Z')


def example():
    return json.loads((ROOT / 'examples/operations/records.json').read_text())


def approved():
    bundle = example()
    index = {r['id']: r for r in bundle['records']}
    index['strategy-1']['status'] = 'approved'
    mission = index['mission-1']
    mission['status'] = 'active'
    mission['data'].update(candidate='fixture-1', policy_revision='policy-1')
    approval = copy.deepcopy(index['evidence-1'])
    approval.update(id='approval-1', type='approval', status='approved', dependencies={'strategy': '1', 'record:evidence-1': '1'})
    approval['data'] = dict(approver='Named owner', scope='mission-1', candidate='fixture-1', policy_revision='policy-1', evidence=['evidence-1'], expires_at='2026-11-15T13:00:00Z', reuse='one candidate', authentication='declaration')
    bundle['versions']['record:evidence-1'] = '1'
    approval['data']['bindings'] = {rid: record_digest(index[rid]) for rid in ['mission-1', 'objective-1', 'strategy-1', 'evidence-1']}
    bundle['records'].append(approval)
    return bundle


def test_example_structural_but_not_approved():
    assert validate(example()) == []
    assert not readiness(example(), NOW)['complete']


def test_recorded_approval_is_not_authenticated():
    result = readiness(approved(), NOW)
    assert result['complete'] and result['approved']
    assert not result['authenticated']


def test_approval_bindings():
    for key in ['candidate', 'policy_revision']:
        bundle = approved()
        bundle['records'][-1]['data'][key] = 'changed'
        assert not readiness(bundle, NOW)['approved']
    bundle = approved()
    bundle['records'][-1]['data']['expires_at'] = NOW.isoformat()
    assert not readiness(bundle, NOW)['approved']


def test_dependency_scoped_freshness():
    bundle = approved()
    unrelated = copy.deepcopy(bundle['records'][3]); unrelated['id'] = 'unrelated'
    unrelated['dependencies'] = {'other-policy': 'old'}
    bundle['records'].append(unrelated)
    assert readiness(bundle, NOW)['complete']
    bundle['versions']['strategy'] = '2'
    assert not readiness(bundle, NOW)['complete']


def test_changed_evidence_version_invalidates_approval():
    bundle = approved(); bundle['records'][3]['version'] = 2
    assert not readiness(bundle, NOW)['approved']


def test_unknown_and_unowned_fail():
    bundle = approved(); bundle['records'][3]['data']['kind'] = 'unknown'
    assert not readiness(bundle, NOW)['complete']
    bundle = approved(); bundle['records'][2]['owner'] = ''
    assert validate(bundle)


def test_malformed_records_fail_without_traceback():
    for key, value in [('type', []), ('links', [[]]), ('dependencies', []), ('data', []), ('id', []), ('status', [])]:
        bundle = example(); bundle['records'][0][key] = value
        assert validate(bundle)


def test_record_content_changes_invalidate_approval():
    for rid, key, value in [('mission-1', 'scope', 'new scope'), ('strategy-1', 'policy', 'new policy')]:
        bundle = approved()
        next(r for r in bundle['records'] if r['id'] == rid)['data'][key] = value
        assert not readiness(bundle, NOW)['approved']
    bundle = approved(); bundle['records'][0]['version'] = 2
    assert not readiness(bundle, NOW)['approved']
    bundle = approved(); bundle['records'][2]['owner'] = False
    assert validate(bundle)
    bundle = approved(); bundle['records'][3]['status'] = 'rejected'
    assert not readiness(bundle, NOW)['approved']


def test_evaluation_candidate_must_match_even_with_current_bindings():
    bundle = approved()
    evidence = bundle['records'][3]
    evidence.update(type='evaluation', status='passed')
    evidence['data'] = {'candidate': 'different-candidate', 'result': 'passed', 'cases': ['case-1'], 'limits': ['synthetic']}
    bundle['records'][-1]['data']['bindings'][evidence['id']] = record_digest(evidence)
    result = readiness(bundle, NOW)
    assert not result['complete']
    assert any('candidate does not match' in issue for issue in result['issues'])


def test_nonfinite_limits_and_json_rejected(tmp_path):
    import pytest
    from operating_records import load
    for value in [float('nan'), float('inf'), float('-inf')]:
        bundle = approved()
        bundle['records'][2]['data']['allocation'] = {'hours': value}
        assert validate(bundle)
    path = tmp_path/'records.json'
    path.write_text('{"value": NaN}')
    with pytest.raises(ValueError, match='non-finite'): load(path)


def test_historical_approval_does_not_poison_valid_replacement():
    bundle = approved()
    old = copy.deepcopy(bundle['records'][-1])
    old['id'] = 'historical-approval'
    old['data']['expires_at'] = '2026-11-13T13:00:00Z'
    old['data']['candidate'] = 'previous-candidate'
    bundle['records'].append(old)
    assert readiness(bundle, NOW)['approved']
    bundle['records'][-2]['data']['expires_at'] = old['data']['expires_at']
    assert not readiness(bundle, NOW)['approved']


def test_withdrawn_or_contradictory_evaluation_cannot_authorize_mission():
    for status, cases in [('superseded', ['case-1']), ('failed', ['case-1']),
                          ('passed', [{'result': 'failed'}]), ('passed', [{'result': 'passed', 'hard_fail': True}])]:
        bundle = approved()
        evidence = bundle['records'][3]
        evidence.update(type='evaluation', status=status)
        evidence['data'] = {'candidate': 'fixture-1', 'result': 'passed', 'cases': cases, 'limits': ['synthetic']}
        bundle['records'][-1]['data']['bindings'][evidence['id']] = record_digest(evidence)
        assert not readiness(bundle, NOW)['complete']
