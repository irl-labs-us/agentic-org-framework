from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from framework_config import (  # noqa: E402
    FrameworkConfigError,
    load_framework_config,
    parse_framework_config,
)


def example() -> dict:
    return json.loads((ROOT / ".agentic-org.example.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("profile", ["lightweight", "solo"])
def test_non_multi_profiles_accept_no_ledger(profile):
    raw = example()
    raw["profile"] = profile

    config = parse_framework_config(raw)

    assert config.profile == profile
    assert config.solo_mode is True


def test_multi_profile_requires_numeric_ledger_issue():
    raw = example()
    raw["profile"] = "multi"
    raw["git_governance"]["operator_mode"] = "multi-human"
    raw["git_governance"]["ledger_url"] = "https://github.com/acme/product/issues/17"

    config = parse_framework_config(raw)

    assert config.solo_mode is False
    assert config.git_governance.ledger_url.endswith("/17")


def test_multi_agent_profile_can_use_single_human_operation():
    raw = example()
    raw["profile"] = "multi"

    config = parse_framework_config(raw)

    assert config.profile == "multi"
    assert config.solo_mode is True
    assert config.git_governance.operator_mode == "single-human"


def test_unknown_fields_fail_closed():
    raw = example()
    raw["surprise"] = True

    with pytest.raises(FrameworkConfigError, match="unknown field"):
        parse_framework_config(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("integration_branch", "bad branch"),
        ("release_branch", "../main"),
    ],
)
def test_invalid_branch_names_are_rejected(field, value):
    raw = example()
    raw["repository"][field] = value

    with pytest.raises(FrameworkConfigError, match="valid branch name"):
        parse_framework_config(raw)


def test_load_uses_project_config_when_present(tmp_path):
    path = tmp_path / ".agentic-org.json"
    path.write_text(json.dumps(example()), encoding="utf-8")

    config = load_framework_config(repo=tmp_path, required=True)

    assert config.source_path == path
    assert config.repository.integration_branch == "staging"


def test_required_config_reports_missing_file(tmp_path):
    with pytest.raises(FrameworkConfigError, match="missing .agentic-org.json"):
        load_framework_config(repo=tmp_path, required=True)


def test_lightweight_profile_accepts_reduced_configuration():
    raw = example()
    raw["profile"] = "lightweight"
    raw["leadership"] = {"principal": "Owner"}
    raw["git_governance"] = {"operator_mode": "single-human", "ledger_url": None}
    raw["modules"] = {}

    config = parse_framework_config(raw)

    assert config.leadership.strategy_lead == "Owner"
    assert config.leadership.assurance_owner == "Independent Reviewer"
    assert config.modules.agent_governance is True
    assert config.modules.manifest_sync is False
    assert config.git_governance.high_risk_paths
    assert config.git_governance.forbidden_paths


def small_team() -> dict:
    raw = example()
    raw["git_governance"]["operator_mode"] = "small-team"
    raw["git_governance"]["operators"] = ["Operator A", "Operator B"]
    raw["git_governance"]["operators_approver"] = "Operator A"
    return raw


def test_small_team_mode_drops_lease_but_stays_governed():
    config = parse_framework_config(small_team())

    assert config.small_team_mode is True
    assert config.governed_mode is True
    assert config.lease_required is False
    assert config.solo_mode is False
    assert config.git_governance.operators == ("Operator A", "Operator B")
    assert config.git_governance.operators_approver == "Operator A"


@pytest.mark.parametrize(
    "operators, message",
    [
        (None, "operators must be an array"),
        (["Only One"], "two or more people"),
        (["Same", "same"], "must not contain duplicates"),
    ],
)
def test_small_team_mode_requires_a_real_roster(operators, message):
    raw = small_team()
    raw["git_governance"]["operators"] = operators

    with pytest.raises(FrameworkConfigError, match=message):
        parse_framework_config(raw)


def test_small_team_mode_requires_roster_approver_and_null_ledger():
    raw = small_team()
    del raw["git_governance"]["operators_approver"]
    with pytest.raises(FrameworkConfigError, match="operators_approver"):
        parse_framework_config(raw)

    raw = small_team()
    raw["git_governance"]["ledger_url"] = "https://github.com/acme/product/issues/17"
    with pytest.raises(FrameworkConfigError, match="small-team operator mode must set"):
        parse_framework_config(raw)


def test_operator_roster_is_rejected_outside_small_team_mode():
    raw = example()
    raw["git_governance"]["operators"] = ["Operator A", "Operator B"]

    with pytest.raises(FrameworkConfigError, match="apply only to small-team"):
        parse_framework_config(raw)


@pytest.mark.parametrize("sessions", ["one", "parallel"])
def test_agent_sessions_is_independent_of_operator_mode(sessions):
    for raw in (example(), small_team()):
        raw["git_governance"]["agent_sessions"] = sessions
        config = parse_framework_config(raw)
        assert config.parallel_sessions is (sessions == "parallel")


def test_agent_sessions_defaults_to_parallel_and_rejects_unknown_values():
    raw = example()
    del raw["git_governance"]["agent_sessions"]
    assert parse_framework_config(raw).git_governance.agent_sessions == "parallel"

    raw["git_governance"]["agent_sessions"] = "many"
    with pytest.raises(FrameworkConfigError, match="agent_sessions must be one of"):
        parse_framework_config(raw)
