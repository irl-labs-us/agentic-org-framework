from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import check_git_governance as governance  # noqa: E402


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def governed_feature_repo(tmp_path: Path, changed_path: str = "app.py") -> tuple[Path, str, str, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "staging")
    git(repo, "config", "user.name", "Framework Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(repo, "add", "seed.txt")
    git(repo, "commit", "-m", "seed")
    base_sha = git(repo, "rev-parse", "HEAD")
    git(repo, "switch", "-c", "feature/fixture")
    target = repo / changed_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("changed\n", encoding="utf-8")
    git(repo, "add", changed_path)
    git(repo, "commit", "-m", "feature")
    head_sha = git(repo, "rev-parse", "HEAD")
    high_risk = "auth" in changed_path
    body = repo / "pr-body.md"
    body.write_text(
        "## Outcome\n\nFixture outcome.\n\n"
        "## Coordination and scope\n\nFixture scope.\n\n"
        "## Changed-file manifest\n\n"
        f"- `{changed_path}`\n\n"
        "## Authorized scope\n\n"
        "- Scope reference: MISSION-001\n"
        f"- Approved path: `{changed_path}`\n\n"
        "## Risk and review evidence\n\n"
        f"- Risk class: {'high' if high_risk else 'ordinary'}\n"
        "- Reviewer: Independent Reviewer\n"
        f"- Reviewer independence: {'independent' if high_risk else 'not-required'}\n"
        "- Decision: approve\n"
        f"- Reviewed head SHA: {head_sha}\n"
        "- Policy/config version: agentic-org-config/v1\n"
        "- Evidence references: test://fixture\n"
        "- Decision timestamp: 2026-09-15T12:00:00Z\n"
        "- Decision expiry: None\n\n"
        "## Evidence\n\nFixture evidence.\n",
        encoding="utf-8",
    )
    return repo, base_sha, head_sha, body


def args_for(repo: Path, base_sha: str, head_sha: str, body: Path) -> argparse.Namespace:
    return argparse.Namespace(
        repo=str(repo),
        base_ref="staging",
        head_ref="feature/fixture",
        base_sha=base_sha,
        head_sha=head_sha,
        body_file=str(body),
        prior_pr_count=0,
        solo_mode=True,
    )


def test_feature_governance_validates_exact_diff_in_solo_mode(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path)

    files, lines, high_risk = governance.validate(
        args_for(repo, base_sha, head_sha, body)
    )

    assert files == ["app.py"]
    assert lines == 1
    assert high_risk is False


def test_feature_governance_classifies_auth_scope_as_high_risk(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path, "src/auth_policy.py")

    files, _, high_risk = governance.validate(
        args_for(repo, base_sha, head_sha, body)
    )

    assert files == ["src/auth_policy.py"]
    assert high_risk is True


def test_feature_governance_rejects_nested_forbidden_artifacts(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path, "config/.env.local")

    with pytest.raises(governance.GovernanceError, match="forbidden local/generated artifacts"):
        governance.validate(args_for(repo, base_sha, head_sha, body))


def test_feature_governance_rejects_manifest_mismatch(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path)
    body.write_text(
        body.read_text(encoding="utf-8").replace("`app.py`", "`different.py`"),
        encoding="utf-8",
    )

    with pytest.raises(governance.GovernanceError, match="manifest mismatch"):
        governance.validate(args_for(repo, base_sha, head_sha, body))


def test_governance_uses_configured_branch_names_and_paths(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path, "policy/critical.txt")
    raw = json.loads((SCRIPT_DIR.parent / ".agentic-org.example.json").read_text())
    raw["repository"]["integration_branch"] = "develop"
    raw["repository"]["release_branch"] = "production"
    raw["git_governance"]["high_risk_paths"] = ["policy/"]
    config = repo / ".agentic-org.json"
    config.write_text(json.dumps(raw))
    body.write_text(
        body.read_text()
        .replace("Risk class: ordinary", "Risk class: high")
        .replace("Reviewer independence: not-required", "Reviewer independence: independent")
    )
    args = args_for(repo, base_sha, head_sha, body)
    args.base_ref = "develop"
    args.config = config

    files, _, high_risk = governance.validate(args)

    assert files == ["policy/critical.txt"]
    assert high_risk is True


def test_governance_rejects_placeholder_only_required_section(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path)
    body.write_text(body.read_text().replace("Fixture outcome.", "TBD"))

    with pytest.raises(governance.GovernanceError, match="empty or placeholder-only"):
        governance.validate(args_for(repo, base_sha, head_sha, body))


def test_governance_rejects_review_for_old_head(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path)
    body.write_text(body.read_text().replace(head_sha, "0" * 40))

    with pytest.raises(governance.GovernanceError, match="not current head"):
        governance.validate(args_for(repo, base_sha, head_sha, body))


def test_governance_reports_files_outside_authorized_scope_separately(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path)
    body.write_text(body.read_text().replace("Approved path: `app.py`", "Approved path: `docs/**`"))

    with pytest.raises(governance.GovernanceError, match="outside authorized scope: app.py"):
        governance.validate(args_for(repo, base_sha, head_sha, body))


def test_high_risk_scope_requires_independent_approval(tmp_path):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path, "src/auth_policy.py")
    body.write_text(body.read_text().replace("Reviewer independence: independent", "Reviewer independence: not-required"))

    with pytest.raises(governance.GovernanceError, match="independent reviewer"):
        governance.validate(args_for(repo, base_sha, head_sha, body))


@pytest.mark.parametrize("decision", ["block", "needs-work"])
def test_non_approving_review_decision_blocks_validation(tmp_path, decision):
    repo, base_sha, head_sha, body = governed_feature_repo(tmp_path)
    body.write_text(body.read_text().replace("Decision: approve", f"Decision: {decision}"))

    with pytest.raises(governance.GovernanceError, match=f"review decision is {decision}"):
        governance.validate(args_for(repo, base_sha, head_sha, body))
