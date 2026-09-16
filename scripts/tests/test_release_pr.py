from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

import create_release_pr as release  # noqa: E402


def context(*, head_sha: str = "b" * 40) -> release.ReleaseContext:
    return release.ReleaseContext(
        base_ref="origin/main",
        base_sha="a" * 40,
        head_ref="origin/staging",
        head_sha=head_sha,
        merge_base="c" * 40,
        files=("app.py", "docs/release.md"),
    )


def test_multi_operator_mechanical_render_requires_lease_metadata():
    with pytest.raises(release.ReleasePreparationError, match="requires a lease ID"):
        release.render_release_mechanical_sections(
            context(),
            lease_id=None,
            grant_url=None,
            solo_mode=False,
        )


def test_multi_operator_release_sync_preserves_lease_and_human_sections(monkeypatch, tmp_path):
    ledger_url = f"{release.LIVE_LEDGER_URL}#issuecomment-42"
    old_body = f"""## Outcome

Human outcome text.

## Coordination and scope

Human coordination text.

## Branch integration

Old mechanical text.

## Git-work lease

- Git-work lease ID: GIT-2026-007
- Live-ledger grant link: {ledger_url}
- Lease expiry: 2026-09-30T00:00:00Z
- Human closeout note: preserve this exactly.

## Changed-file manifest

- `old.py`

## Evidence

Human evidence text.
"""
    updated_body: list[str] = []

    monkeypatch.setattr(release, "open_release_pr_numbers", lambda *args: [12])
    monkeypatch.setattr(release, "collect_release_context", lambda *args: context())

    def fake_run(*command, **kwargs):
        if command[:3] == ("gh", "pr", "view"):
            return json.dumps({"body": old_body, "headRefOid": "b" * 40})
        if command[:3] == ("gh", "pr", "edit"):
            body_path = Path(command[command.index("--body-file") + 1])
            updated_body.append(body_path.read_text(encoding="utf-8"))
            return "updated"
        if command[:2] == ("gh", "api"):
            return json.dumps({"workflow_runs": []})
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(release, "run", fake_run)

    result = release.sync_release_pr_mechanical_sections(
        repo=tmp_path,
        remote="origin",
        base_branch="main",
        head_branch="staging",
        repo_slug="example/project",
        solo_mode=False,
    )

    assert result == (
        "refreshed mechanical sections of PR #12; "
        "governance validation pending for bbbbbbbb: exact-head run not visible yet"
    )
    assert len(updated_body) == 1
    body = updated_body[0]
    assert "Human outcome text." in body
    assert "Human coordination text." in body
    assert "Human evidence text." in body
    assert "Human closeout note: preserve this exactly." in body
    assert body.count("## Git-work lease") == 1
    assert f"- Exact release head SHA: `{'b' * 40}`" in body
    assert "- `app.py`" in body
    assert "- `docs/release.md`" in body
    assert "old.py" not in body


def test_multi_operator_release_sync_rejects_invalid_preserved_lease(monkeypatch, tmp_path):
    old_body = """## Outcome
Outcome.
## Coordination and scope
Coordination.
## Branch integration
Old.
## Git-work lease
Missing structured lease metadata.
## Changed-file manifest
- `old.py`
## Evidence
Evidence.
"""
    monkeypatch.setattr(release, "open_release_pr_numbers", lambda *args: [12])
    monkeypatch.setattr(release, "collect_release_context", lambda *args: context())
    monkeypatch.setattr(
        release,
        "run",
        lambda *args, **kwargs: json.dumps({"body": old_body, "headRefOid": "b" * 40}),
    )

    with pytest.raises(release.ReleasePreparationError, match="must contain a valid lease"):
        release.sync_release_pr_mechanical_sections(
            repo=tmp_path,
            remote="origin",
            base_branch="main",
            head_branch="staging",
            repo_slug="example/project",
            solo_mode=False,
        )


def test_solo_release_body_has_no_lease_section():
    body = release.render_release_body(
        context(),
        lease_id=None,
        grant_url=None,
        evidence="Tests passed.",
        solo_mode=True,
    )

    assert "## Git-work lease" not in body
    assert "Git-work lease: N/A — solo-operator mode" in body
    assert f"- Reviewed head SHA: {'b' * 40}" in body
    assert "## Authorized scope" in body
    assert "## Risk and review evidence" in body


@pytest.mark.parametrize(
    "body, expected",
    [
        (
            "## Branch integration\n\n- Git-work lease: N/A — solo-operator mode\n",
            True,
        ),
        (
            "## Branch integration\n\n- Governed release\n\n## Git-work lease\n\n- Lease\n",
            False,
        ),
    ],
)
def test_release_sync_infers_operator_mode_from_existing_body(body, expected):
    assert release.infer_release_sync_solo_mode(body) is expected


def test_release_sync_refuses_ambiguous_operator_mode():
    with pytest.raises(release.ReleasePreparationError, match="cannot infer"):
        release.infer_release_sync_solo_mode(
            "## Branch integration\n\n- Operator mode was not recorded.\n"
        )
