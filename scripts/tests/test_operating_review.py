import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from operating_records import clock
from operating_review import run_review, next_due
from run_evaluations import evaluate
from test_operating_records import example, ROOT, NOW


def config():
    result = json.loads((ROOT / 'examples/operations/review-config.json').read_text())
    result['enabled'] = True
    result['cadence'] = {'kind': 'interval', 'seconds': 3600}
    return result


def test_disabled_does_not_create_state(tmp_path):
    target = tmp_path / 'state.json'
    assert run_review({'schema_version': 1, 'enabled': False}, {}, target, NOW)['status'] == 'disabled'
    assert not target.exists()


def test_due_dedupe_restart(tmp_path):
    bundle = example(); cfg = config(); cfg['sources'] = ['missing']
    target = tmp_path / 'state.json'
    first = run_review(cfg, bundle, target, NOW)
    assert len(first['notifications']) == 1
    assert run_review(cfg, bundle, target, NOW)['status'] == 'not_due'
    later = clock('2026-11-14T14:00:00Z')
    assert run_review(cfg, bundle, target, later)['notifications'] == []
    assert len(json.loads(target.read_text())['outbox']) == 1


def test_calendar_schedule():
    assert next_due({'kind': 'weekly', 'timezone': 'America/New_York', 'time': '09:00', 'weekday': 0}, NOW).isoformat() == '2026-11-16T14:00:00+00:00'
    assert next_due({'kind': 'daily', 'timezone': 'America/New_York', 'time': '09:00'}, NOW).isoformat() == '2026-11-14T14:00:00+00:00'


def test_invalid_records_failure_visible(tmp_path):
    result = run_review(config(), {}, tmp_path/'state.json', NOW)
    assert result['status'] == 'failed' and result['last_success'] is None


def test_overlap(tmp_path):
    import fcntl
    target = tmp_path/'state.json'
    with open(str(target)+'.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert run_review(config(), example(), target, NOW)['status'] == 'overlap'


def test_safe_and_unsafe_evals():
    suite = json.loads((ROOT/'examples/operations/eval-suite.json').read_text())
    good = json.loads((ROOT/'examples/operations/eval-outputs.json').read_text())
    bad = json.loads((ROOT/'examples/operations/eval-regression.json').read_text())
    assert evaluate(suite, good, NOW)['result'] == 'passed'
    result = evaluate(suite, bad, NOW)
    assert result['result'] == 'blocked' and result['cases'][0]['hard_fail']
    del good['results']['boundary']
    assert evaluate(suite, good, NOW)['result'] == 'blocked'
    suite['cases'] = suite['cases'][1:]
    assert evaluate(suite, good, NOW)['coverage']['missing_categories'] == ['boundary']


def test_route_change_invalidates_dedupe_and_schedule(tmp_path):
    cfg = config(); cfg['sources'] = ['missing']
    target = tmp_path/'state.json'
    run_review(cfg, example(), target, NOW)
    cfg['destination'] = 'new local destination'
    assert run_review(cfg, example(), target, NOW)['notifications']


def test_candidate_mismatch_and_unrelated_history(tmp_path):
    import copy
    from test_operating_records import approved
    bundle = approved()
    history = copy.deepcopy(bundle['records'][3]); history['id'] = 'old'
    history['data']['expires_at'] = '2020-01-01T00:00:00Z'
    bundle['records'].append(history)
    assert run_review(config(), bundle, tmp_path/'a.json', NOW)['issues'] == []
    bundle['records'][-2]['data']['candidate'] = 'wrong'
    assert run_review(config(), bundle, tmp_path/'b.json', NOW)['issues']


def test_bad_inputs_and_runtime_budget(tmp_path):
    import pytest
    from unittest.mock import patch
    with pytest.raises(ValueError): evaluate([], {}, NOW)
    with pytest.raises(ValueError): run_review([], {}, tmp_path/'state', NOW)
    with patch('operating_review.time.monotonic', side_effect=[0, 31]):
        with pytest.raises(ValueError, match='runtime'): run_review(config(), example(), tmp_path/'state', NOW)
    assert not (tmp_path/'state').exists()


def test_eval_missing_provenance_and_unknown_case_fail():
    import pytest
    suite = json.loads((ROOT/'examples/operations/eval-suite.json').read_text())
    outputs = json.loads((ROOT/'examples/operations/eval-outputs.json').read_text())
    del outputs['versions']['config']
    with pytest.raises(ValueError, match='config'): evaluate(suite, outputs, NOW)
    outputs['versions']['config'] = '1'
    outputs['results']['unexpected'] = {'status': 'executed', 'output': 'Accepted'}
    with pytest.raises(ValueError, match='unknown case'): evaluate(suite, outputs, NOW)


def test_selected_pending_decision_without_due_date_is_visible(tmp_path):
    from test_operating_records import approved
    bundle = approved()
    cfg = config(); cfg['sources'].append('decision-1')
    result = run_review(cfg, bundle, tmp_path/'state.json', NOW)
    assert any('pending decision has no due date' in issue for issue in result['issues'])
    assert result['notifications']
