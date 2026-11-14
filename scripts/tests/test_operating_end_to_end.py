"""Exercise handoff across installer, evaluation, review, and readiness boundaries."""
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from operating_records import clock, load, readiness
from operating_review import run_review
from framework_doctor import diagnose_readiness


def test_recorded_approval_never_becomes_production_authority(tmp_path):
    records = load(ROOT / 'examples/operations/approved-records.json')
    folder = tmp_path / 'docs/operations'
    folder.mkdir(parents=True)
    (folder / 'records.json').write_text(json.dumps(records))
    strategy = tmp_path / 'docs/strategy/STRATEGY.md'
    strategy.parent.mkdir()
    strategy.write_text('Owner-approved fixture strategy')
    errors, _ = diagnose_readiness(tmp_path, 'mission', now='2026-11-14T13:00:00Z')
    assert errors == []
    errors, _ = diagnose_readiness(tmp_path, 'production', now='2026-11-14T13:00:00Z')
    assert any('authenticated external approval' in e for e in errors)


def test_two_review_cycles_detect_changed_assumption_and_keep_unrelated_history(tmp_path):
    records = load(ROOT / 'examples/operations/approved-records.json')
    config = load(ROOT / 'examples/operations/review-config.json')
    config.update(enabled=True, sources=['evidence-1'])
    config['cadence'] = {'kind': 'interval', 'seconds': 3600}
    now = clock('2026-11-14T13:00:00Z')
    assert readiness(records, now)['complete']
    first = run_review(config, records, tmp_path / 'state.json', now)
    # Evidence arrives that changes the strategy's original causal assumption.
    changed = copy.deepcopy(records)
    changed['records'][0]['data']['problem'] = 'New evidence contradicts the original diagnosis'
    assert not readiness(changed, now)['complete']
    second = run_review(config, changed, tmp_path / 'state.json', clock('2026-11-14T14:00:00Z'))
    assert second['notifications']
    assert first['last_success']
    assert second['next_due']
    third = run_review(config, changed, tmp_path / 'state.json', clock('2026-11-14T15:00:00Z'))
    assert not third['notifications']


def test_eval_cli_blocks_regression_and_keeps_versioned_evidence(tmp_path):
    for name, expected in [('eval-outputs.json', 0), ('eval-regression.json', 1)]:
        output = tmp_path / name
        result = subprocess.run([sys.executable, str(ROOT/'scripts/run_evaluations.py'),
            '--suite', str(ROOT/'examples/operations/eval-suite.json'),
            '--outputs', str(ROOT/'examples/operations'/name), '--output', str(output),
            '--now', '2026-11-14T13:00:00Z'], capture_output=True, text=True)
        assert result.returncode == expected, result.stdout + result.stderr
        evidence = load(output)
        assert evidence['candidate'] and evidence['suite_digest']
        assert evidence['coverage']['total'] > 0


def test_attempt_ceiling_and_rejected_objective_block_even_with_recorded_approval():
    from operating_records import validate
    original = load(ROOT / 'examples/operations/approved-records.json')
    now = clock('2026-11-14T13:00:00Z')
    excessive = copy.deepcopy(original)
    mission = next(r for r in excessive['records'] if r['type'] == 'mission')
    mission['data']['attempts']['maximum'] = 3
    assert validate(excessive)
    rejected = copy.deepcopy(original)
    next(r for r in rejected['records'] if r['type'] == 'objective')['status'] = 'rejected'
    assert not readiness(rejected, now)['complete']
