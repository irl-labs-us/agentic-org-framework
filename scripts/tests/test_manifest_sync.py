from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import sync_pr_manifest as manifest_sync  # noqa: E402


PR_BODY = """## Outcome

Human outcome.

## Coordination and scope

Human scope.

## Branch integration

- [x] Human verification remains checked.

## Changed-file manifest

- `old.py`

## Authorized scope

- Scope reference: MISSION-001
- Approved path: `app.py`
- Approved path: `docs/**`

## Risk and review evidence

- Risk class: ordinary
- Reviewer: Human Reviewer
- Reviewer independence: not-required
- Decision: approve
- Reviewed head SHA: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
- Policy/config version: agentic-org-config/v1
- Evidence references: test://human-review
- Decision timestamp: 2026-09-15T12:00:00Z
- Decision expiry: None

## Evidence

Human evidence.
"""


def test_feature_manifest_sync_changes_only_the_manifest(monkeypatch, tmp_path):
    updated_bodies: list[str] = []
    monkeypatch.setattr(manifest_sync, "open_pr_numbers", lambda *args: [21])
    monkeypatch.setattr(
        manifest_sync,
        "compute_manifest",
        lambda *args: (["app.py", "docs/guide.md"], "f" * 40),
    )

    def fake_run(*command):
        if command[:3] == ("gh", "pr", "view"):
            return json.dumps({"body": PR_BODY, "headRefOid": "f" * 40})
        if command[:3] == ("gh", "pr", "edit"):
            body_path = Path(command[command.index("--body-file") + 1])
            updated_bodies.append(body_path.read_text(encoding="utf-8"))
            return "updated"
        if command[:3] == ("gh", "run", "list"):
            return json.dumps([])
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(manifest_sync, "run", fake_run)

    result = manifest_sync.sync(
        repo=tmp_path,
        remote="origin",
        base_branch="staging",
        head_branch="feature/fixture",
        repo_slug="example/project",
    )

    assert result == (
        "refreshed changed-file manifest of PR #21 (2 files); "
        "governance validation pending for ffffffff: exact-head run not visible yet"
    )
    assert len(updated_bodies) == 1
    body = updated_bodies[0]
    assert "Human outcome." in body
    assert "Human scope." in body
    assert "- [x] Human verification remains checked." in body
    assert "Human evidence." in body
    assert "- Scope reference: MISSION-001" in body
    assert "- Reviewed head SHA: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in body
    assert "- `app.py`" in body
    assert "- `docs/guide.md`" in body
    assert "old.py" not in body


def test_manifest_sync_dispatches_completed_exact_head_run(monkeypatch):
    calls: list[tuple[str, ...]] = []

    def fake_run(*command):
        calls.append(command)
        if command[:3] == ("gh", "run", "list"):
            return json.dumps(
                [
                    {
                        "databaseId": 404,
                        "headSha": "a" * 40,
                        "status": "completed",
                        "conclusion": "failure",
                    }
                ]
            )
        if command[:3] == ("gh", "run", "rerun"):
            return "queued"
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(manifest_sync, "run", fake_run)

    note = manifest_sync.dispatch_governance_validation(
        repo_slug="example/project",
        head_branch="feature/fixture",
        head_sha="a" * 40,
    )

    assert note is not None
    assert "dispatched trusted governance run 404" in note
    assert any(call[:3] == ("gh", "run", "rerun") for call in calls)


def test_manifest_sync_is_a_noop_without_an_open_pr(monkeypatch, tmp_path):
    monkeypatch.setattr(manifest_sync, "open_pr_numbers", lambda *args: [])

    assert (
        manifest_sync.sync(
            repo=tmp_path,
            remote="origin",
            base_branch="staging",
            head_branch="feature/fixture",
            repo_slug="example/project",
        )
        is None
    )


def test_manifest_sync_recomputes_once_when_live_head_changes(monkeypatch, tmp_path):
    heads = iter(["a" * 40, "b" * 40])
    monkeypatch.setattr(manifest_sync, "open_pr_numbers", lambda *args: [21])
    monkeypatch.setattr(
        manifest_sync,
        "compute_manifest",
        lambda *args: (["app.py"], next(heads)),
    )
    views = iter(
        [
            {"body": PR_BODY, "headRefOid": "b" * 40},
            {"body": PR_BODY, "headRefOid": "b" * 40},
            {"body": PR_BODY, "headRefOid": "b" * 40},
            {"body": PR_BODY, "headRefOid": "b" * 40},
        ]
    )

    def fake_run(*command):
        if command[:3] == ("gh", "pr", "view"):
            return json.dumps(next(views))
        if command[:3] == ("gh", "pr", "edit"):
            return "updated"
        if command[:3] == ("gh", "run", "list"):
            return "[]"
        raise AssertionError(command)

    monkeypatch.setattr(manifest_sync, "run", fake_run)

    result = manifest_sync.sync(
        repo=tmp_path,
        remote="origin",
        base_branch="staging",
        head_branch="feature/fixture",
        repo_slug="example/project",
    )

    assert "bbbbbbbb" in result
