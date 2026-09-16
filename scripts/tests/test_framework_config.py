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
