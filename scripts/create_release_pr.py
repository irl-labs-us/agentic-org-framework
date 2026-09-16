#!/usr/bin/env python3
"""Create or repair the configured integration-to-release PR with a complete body.

The helper fetches both persistent branches, derives the release manifest from
their merge base, renders all metadata required by Git governance, and passes
the completed body to GitHub atomically. It never merges the pull request.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from framework_config import (
    DEFAULT_LEDGER_URL,
    FrameworkConfigError,
    load_framework_config,
)

# TODO: point this at your project's live Git-work lease ledger (a pinned
# tracking issue that records lease grants — see docs/GIT_OPERATIONS_COVENANT.md).
LIVE_LEDGER_URL = DEFAULT_LEDGER_URL
LEASE_PATTERN = re.compile(r"^GIT-\d{4}-\d{3}$")
MAX_PR_BODY_BYTES = 60_000


class ReleasePreparationError(RuntimeError):
    """Release PR preparation cannot continue safely."""


@dataclass(frozen=True)
class ReleaseContext:
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    merge_base: str
    files: tuple[str, ...]


def run(*command: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ReleasePreparationError(f"{' '.join(command)} failed: {detail}")
    return result.stdout.strip()


def git(repo: Path, *args: str) -> str:
    return run("git", "-C", str(repo), *args)


def validate_release_metadata(
    lease_id: str,
    grant_url: str,
    *,
    ledger_url: str = LIVE_LEDGER_URL,
) -> None:
    if not LEASE_PATTERN.fullmatch(lease_id):
        raise ReleasePreparationError("lease ID must match GIT-YYYY-NNN")
    grant_url_pattern = re.compile(
        rf"^{re.escape(ledger_url)}#issuecomment-\d+$"
    )
    if not grant_url_pattern.fullmatch(grant_url):
        raise ReleasePreparationError(
            "grant URL must identify a numeric LEASE GRANTED comment in the live ledger at "
            f"{ledger_url}#issuecomment-<digits>"
        )


def validate_manifest_paths(files: tuple[str, ...]) -> None:
    for path in files:
        if not path or any(character in path for character in ("\n", "\r", "`")):
            raise ReleasePreparationError(
                f"release path cannot be represented in the PR manifest: {path!r}"
            )


def collect_release_context(
    repo: Path, remote: str, base_branch: str, head_branch: str
) -> ReleaseContext:
    if base_branch == head_branch:
        raise ReleasePreparationError(
            "release base and integration head branches must differ"
        )

    git(
        repo,
        "fetch",
        "--prune",
        "--no-tags",
        remote,
        f"+refs/heads/{base_branch}:refs/remotes/{remote}/{base_branch}",
        f"+refs/heads/{head_branch}:refs/remotes/{remote}/{head_branch}",
    )
    base_ref = f"{remote}/{base_branch}"
    head_ref = f"{remote}/{head_branch}"
    base_sha = git(repo, "rev-parse", base_ref)
    head_sha = git(repo, "rev-parse", head_ref)
    merge_base = git(repo, "merge-base", base_sha, head_sha)
    files = tuple(
        line
        for line in git(
            repo, "diff", "--name-only", f"{base_sha}...{head_sha}"
        ).splitlines()
        if line
    )
    if not files:
        raise ReleasePreparationError("integration branch has no release changes after the merge base")
    return ReleaseContext(
        base_ref=base_ref,
        base_sha=base_sha,
        head_ref=head_ref,
        head_sha=head_sha,
        merge_base=merge_base,
        files=files,
    )


def render_release_mechanical_sections(
    context: ReleaseContext,
    *,
    lease_id: str | None,
    grant_url: str | None,
    solo_mode: bool,
    ledger_url: str = LIVE_LEDGER_URL,
) -> tuple[str, str, str, str]:
    """Render branch integration, lease content, manifest, and merge authority."""

    ceo_placeholder = "{CEO}"
    strategy_lead_placeholder = "{Strategy & Portfolio Lead}"
    if solo_mode:
        branch_integration_lease = (
            "- Git-work lease: N/A — solo-operator mode "
            "(see GIT_OPERATIONS_COVENANT.md)"
        )
        lease_content = ""
        steward_line = "the operator"
        risk_evidence = (
            "High-risk production release; current-head CI, integration verification, specialist evidence "
            "for included high-risk changes, and a deliberate operator second pass required"
        )
        deploy_authority = (
            "The PR authorizes no merge by itself; only the operator merges, "
            "after a deliberate second pass"
        )
    else:
        if lease_id is None or grant_url is None:
            raise ReleasePreparationError(
                "multi-human release rendering requires a lease ID and live-ledger grant URL"
            )
        validate_release_metadata(lease_id, grant_url, ledger_url=ledger_url)
        branch_integration_lease = (
            f"- Git-work lease ID: {lease_id}\n- Live-ledger lease grant: {grant_url}"
        )
        lease_content = (
            f"- Git-work lease ID: {lease_id}\n"
            f"- Live-ledger grant link: {grant_url}\n"
            "- Lease expiry: See live grant\n"
            f"- Closeout owner and disposition: {ceo_placeholder} / "
            f"{strategy_lead_placeholder}; close after release merge or PR closure"
        )
        steward_line = ceo_placeholder
        risk_evidence = (
            "High-risk production release; current-head CI, integration verification, specialist evidence "
            "for included high-risk changes, and Merge Steward decision required"
        )
        deploy_authority = (
            "The PR authorizes no merge by itself; only the recorded Merge Steward may merge"
        )

    validate_manifest_paths(context.files)
    manifest = "\n".join(f"- `{path}`" for path in context.files)
    branch_integration = f"""{branch_integration_lease}
- Persistent release branch: `{context.head_ref}`
- Target branch / fetched tracking ref: `{context.base_ref}`
- Exact target base SHA: `{context.base_sha}`
- Exact release head SHA: `{context.head_sha}`
- Common merge base: `{context.merge_base}`
- Publication shape: Authorized persistent-branch release
- Merge Steward on duty: {steward_line}
- Risk class / review evidence: {risk_evidence}"""
    return branch_integration, lease_content, manifest, deploy_authority


def parse_release_lease_section(
    section: str,
    *,
    ledger_url: str = LIVE_LEDGER_URL,
) -> tuple[str, str]:
    """Read and validate release lease metadata from an existing PR body."""

    lease_match = re.search(r"\bGIT-\d{4}-\d{3}\b", section)
    grant_match = re.search(
        rf"{re.escape(ledger_url)}#issuecomment-\d+",
        section,
    )
    if lease_match is None or grant_match is None:
        raise ReleasePreparationError(
            "existing release PR's Git-work lease section must contain a valid lease ID "
            "and live-ledger grant URL"
        )
    lease_id = lease_match.group(0)
    grant_url = grant_match.group(0)
    validate_release_metadata(lease_id, grant_url, ledger_url=ledger_url)
    return lease_id, grant_url


def render_release_body(
    context: ReleaseContext,
    *,
    lease_id: str | None,
    grant_url: str | None,
    evidence: str,
    solo_mode: bool = False,
    ledger_url: str = LIVE_LEDGER_URL,
    scope_reference: str = "release-owner approval",
    authorized_paths: tuple[str, ...] | None = None,
    reviewer: str = "Independent Reviewer",
    reviewer_independence: str = "independent",
    decision: str = "approve",
    evidence_references: str = "release verification evidence",
    decision_timestamp: str = "2026-01-01T00:00:00Z",
    decision_expiry: str = "None",
) -> str:
    # Bare, non-f-string literals: SETUP.md's project-wide find-and-replace
    # substitutes {CEO}/{Strategy & Portfolio Lead} with real names across
    # every listed template file, this one included. Building these as
    # plain string literals (not inline f-string text) means the source
    # file contains the literal 5/28-character token find-replace expects
    # -- not a doubled-brace f-string escape, which find-replace wouldn't
    # cleanly match and which rendered as literal "{{CEO}}" in the output
    # if setup's substitution was skipped.
    ceo_placeholder = "{CEO}"
    branch_integration, lease_content, manifest, deploy_authority = (
        render_release_mechanical_sections(
            context,
            lease_id=lease_id,
            grant_url=grant_url,
            solo_mode=solo_mode,
            ledger_url=ledger_url,
        )
    )
    lease_section = (
        f"\n## Git-work lease\n\n{lease_content}\n" if lease_content else ""
    )
    base_branch = context.base_ref.rsplit("/", 1)[-1]
    integration_branch = context.head_ref.rsplit("/", 1)[-1]
    authorized_paths = authorized_paths or context.files
    validate_manifest_paths(authorized_paths)
    scope_lines = "\n".join(f"- Approved path: `{path}`" for path in authorized_paths)
    body = f"""## Outcome

Release the exact verified `{integration_branch}` state to production through `{base_branch}` without adding feature work during release integration.

## Coordination and scope

- Mission or case: Governed {integration_branch}-to-{base_branch} release
- Accountable owner: {ceo_placeholder}, CEO and Merge Steward
- Writer scope: Persistent `{integration_branch}` release head only; no release-PR code edits
- Independent reviewer: Required high-risk release evidence recorded below
- Expected overlapping files and owning writer: Release manifest below; feature ownership remains with the originating integration PRs

## Branch integration

{branch_integration}
{lease_section}
## Changed-file manifest

{manifest}

## Authorized scope

- Scope reference: {scope_reference}
{scope_lines}

## Risk and review evidence

- Risk class: high
- Reviewer: {reviewer}
- Reviewer independence: {reviewer_independence}
- Decision: {decision}
- Reviewed head SHA: {context.head_sha}
- Policy/config version: agentic-org-config/v1
- Evidence references: {evidence_references}
- Decision timestamp: {decision_timestamp}
- Decision expiry: {decision_expiry}

## Evidence

- Tests and checks: {evidence}
- Limitations or open gates: Release merge remains prohibited until all current-head checks, integration verification{"" if solo_mode else ", live-ledger match"}, and the final {"operator" if solo_mode else "Merge Steward"} freshness decision pass
- Deployment/production authority: {deploy_authority}
"""
    body_size = len(body.encode("utf-8"))
    if body_size > MAX_PR_BODY_BYTES:
        raise ReleasePreparationError(
            f"release PR body is {body_size} bytes; limit is {MAX_PR_BODY_BYTES}; "
            "narrow or separately archive evidence before publication"
        )
    return body


def body_section(body: str, heading: str) -> str:
    """
    Return the raw text of a '## <heading>' section (everything up to the
    next '## ' heading or end of body), stripped of leading/trailing blank
    lines. Duplicated from check_git_governance.py rather than imported,
    so this script stays independently runnable regardless of invocation
    directory (matches how check_git_governance.py itself is invoked).
    """
    lines = body.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {heading}".casefold():
            start = index + 1
            break
    if start is None:
        raise ReleasePreparationError(f"existing PR body is missing '## {heading}'")
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip("\n")


def replace_body_section(body: str, heading: str, content: str) -> str:
    lines = body.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {heading}".casefold():
            start = index + 1
            break
    if start is None:
        raise ReleasePreparationError(f"existing PR body is missing '## {heading}'")
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[:start]) + "\n\n" + content.strip("\n") + "\n\n" + "\n".join(lines[end:])


def live_release_pr_metadata(repo_slug: str, pr_number: int) -> dict[str, str]:
    raw = run(
        "gh", "pr", "view", str(pr_number), "--repo", repo_slug,
        "--json", "body,headRefOid",
    )
    value = json.loads(raw)
    body = value.get("body") or ""
    head = value.get("headRefOid") or ""
    if not isinstance(body, str) or not isinstance(head, str):
        raise ReleasePreparationError("GitHub returned malformed release PR metadata")
    return {"body": body, "headRefOid": head}


def infer_release_sync_solo_mode(body: str) -> bool:
    """Infer operator mode from an existing governed release PR body."""

    headings = {
        line.strip().casefold()
        for line in body.splitlines()
        if line.startswith("## ")
    }
    if "## git-work lease" in headings:
        return False
    branch_integration = body_section(body, "Branch integration")
    if "solo-operator mode" in branch_integration.casefold():
        return True
    raise ReleasePreparationError(
        "cannot infer release operator mode: expected a Git-work lease section "
        "or a solo-operator marker in Branch integration"
    )


def sync_release_pr_mechanical_sections(
    *,
    repo: Path,
    remote: str,
    base_branch: str,
    head_branch: str,
    repo_slug: str,
    solo_mode: bool | None,
    ledger_url: str = LIVE_LEDGER_URL,
) -> str | None:
    """
    Refresh only the mechanically-derived sections (Branch integration,
    Changed-file manifest -- and, in multi-human mode, Git-work lease)
    of the single open integration-to-release PR, preserving Outcome,
    Coordination and scope, and Evidence exactly as a human last wrote
    them. Intended for CI to run on every push to the integration branch, so the
    manifest/SHA fields never go stale between real review passes --
    without silently discarding curated evidence content on every push.

    Returns a message describing what happened, or None if there is no
    open release PR to refresh (a deliberate no-op, not an error -- this
    must not surprise-create a PR that doesn't already exist).
    """
    existing = open_release_pr_numbers(repo_slug, base_branch, head_branch)
    if not existing:
        return None
    if len(existing) > 1:
        raise ReleasePreparationError(
            "multiple open release PRs exist; close or reconcile them before continuing"
        )
    pr_number = existing[0]

    for attempt in range(2):
        context = collect_release_context(repo, remote, base_branch, head_branch)
        observed = live_release_pr_metadata(repo_slug, pr_number)
        if observed["headRefOid"] != context.head_sha:
            if attempt == 0:
                continue
            raise ReleasePreparationError(
                f"release PR head changed during synchronization: fetched {context.head_sha}, "
                f"live {observed['headRefOid']}"
            )
        old_body = observed["body"]
        effective_solo = solo_mode if solo_mode is not None else infer_release_sync_solo_mode(old_body)
        lease_id = None
        grant_url = None
        if not effective_solo:
            lease_id, grant_url = parse_release_lease_section(
                body_section(old_body, "Git-work lease"),
                ledger_url=ledger_url,
            )
        branch_integration, _, manifest, _ = render_release_mechanical_sections(
            context,
            lease_id=lease_id,
            grant_url=grant_url,
            solo_mode=effective_solo,
            ledger_url=ledger_url,
        )
        new_body = replace_body_section(old_body, "Branch integration", branch_integration)
        new_body = replace_body_section(new_body, "Changed-file manifest", manifest)
        preflight = live_release_pr_metadata(repo_slug, pr_number)
        if preflight != observed:
            if attempt == 0:
                continue
            raise ReleasePreparationError(
                "release PR body or head changed during synchronization; retry from fresh state"
            )
        body_size = len(new_body.encode("utf-8"))
        if body_size > MAX_PR_BODY_BYTES:
            raise ReleasePreparationError(
                f"refreshed release PR body is {body_size} bytes; limit is {MAX_PR_BODY_BYTES}"
            )
        if new_body == old_body:
            result = f"release PR #{pr_number} mechanical sections already current"
        else:
            body_file = materialize_release_body(new_body)
            try:
                run("gh", "pr", "edit", str(pr_number), "--repo", repo_slug, "--body-file", str(body_file))
            finally:
                body_file.unlink(missing_ok=True)
            after = live_release_pr_metadata(repo_slug, pr_number)
            if after["headRefOid"] != context.head_sha:
                raise ReleasePreparationError(
                    "release PR head changed while publishing mechanical sections; refreshed review is required"
                )
            result = f"refreshed mechanical sections of PR #{pr_number}"
        dispatch = dispatch_governance_validation(
            repo_slug=repo_slug,
            pr_number=pr_number,
            head_sha=context.head_sha,
        )
        return f"{result}; {dispatch}"
    raise ReleasePreparationError("release synchronization did not reach a stable PR state")


def dispatch_governance_validation(
    *, repo_slug: str, pr_number: int, head_sha: str, workflow_file: str = "git-governance.yml"
) -> str:
    """Dispatch the trusted pull-request workflow for this exact head.

    Completed runs are rerun regardless of their prior conclusion. An existing
    queued run or a run GitHub has not exposed yet is reported as a bounded
    pending state. Candidate-branch workflow code is never dispatched.
    """
    raw = run(
        "gh", "api",
        f"repos/{repo_slug}/actions/workflows/{workflow_file}/runs?event=pull_request_target&per_page=100",
    )
    runs = json.loads(raw).get("workflow_runs", [])
    match = _exact_pr_run(runs, pr_number=pr_number, head_sha=head_sha)
    if match is None:
        return f"governance validation pending for {head_sha[:8]}: exact-head run not visible yet"
    run_id = match["id"]
    if match["status"] != "completed":
        return f"governance validation pending in run {run_id} for {head_sha[:8]}"
    try:
        run("gh", "run", "rerun", str(run_id), "--repo", repo_slug)
    except ReleasePreparationError as exc:
        raise ReleasePreparationError(
            f"release metadata updated but exact-head governance run {run_id} could not be dispatched: {exc}"
        ) from exc
    return f"dispatched trusted governance run {run_id} for {head_sha[:8]}; result pending"


def _exact_pr_run(runs: list[dict], *, pr_number: int, head_sha: str) -> dict | None:
    return next(
        (
            item
            for item in runs
            if any(
                pr.get("number") == pr_number
                and (pr.get("head") or {}).get("sha") == head_sha
                for pr in item.get("pull_requests", [])
            )
        ),
        None,
    )


def rerun_stale_check(
    *, repo_slug: str, pr_number: int, head_sha: str, workflow_file: str = "git-governance.yml"
) -> str:
    """Compatibility alias for deterministic exact-head dispatch."""

    return dispatch_governance_validation(
        repo_slug=repo_slug,
        pr_number=pr_number,
        head_sha=head_sha,
        workflow_file=workflow_file,
    )


def materialize_release_body(body: str) -> Path:
    descriptor, raw_path = tempfile.mkstemp(prefix="release-pr-", suffix=".md")
    path = Path(raw_path)
    descriptor_open = True
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor_open = False
            handle.write(body)
            handle.flush()
        return path
    except BaseException:
        if descriptor_open:
            os.close(descriptor)
        path.unlink(missing_ok=True)
        raise


def publish_rendered_release_pr(
    body: str,
    *,
    repo_slug: str,
    base_branch: str,
    head_branch: str,
    title: str,
) -> str:
    body_file = materialize_release_body(body)
    try:
        return publish_release_pr(
            repo_slug=repo_slug,
            base_branch=base_branch,
            head_branch=head_branch,
            title=title,
            body_file=body_file,
        )
    finally:
        body_file.unlink(missing_ok=True)


def open_release_pr_numbers(repo_slug: str, base_branch: str, head_branch: str) -> list[int]:
    raw = run(
        "gh",
        "pr",
        "list",
        "--repo",
        repo_slug,
        "--state",
        "open",
        "--base",
        base_branch,
        "--head",
        head_branch,
        "--limit",
        "2",
        "--json",
        "number",
    )
    return [int(item["number"]) for item in json.loads(raw)]


def publish_release_pr(
    *,
    repo_slug: str,
    base_branch: str,
    head_branch: str,
    title: str,
    body_file: Path,
) -> str:
    existing = open_release_pr_numbers(repo_slug, base_branch, head_branch)
    if len(existing) > 1:
        raise ReleasePreparationError(
            "multiple open release PRs exist; close or reconcile them before continuing"
        )
    if existing:
        return run(
            "gh",
            "pr",
            "edit",
            str(existing[0]),
            "--repo",
            repo_slug,
            "--title",
            title,
            "--body-file",
            str(body_file),
        )
    return run(
        "gh",
        "pr",
        "create",
        "--repo",
        repo_slug,
        "--base",
        base_branch,
        "--head",
        head_branch,
        "--title",
        title,
        "--body-file",
        str(body_file),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Local repository path")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--repo-slug", help="owner/repo; overrides project config")
    parser.add_argument("--remote", help="Git remote; overrides project config")
    parser.add_argument("--base", help="Release branch; overrides project config")
    parser.add_argument("--head", help="Integration branch; overrides project config")
    parser.add_argument(
        "--lease-id",
        help="Required unless --solo-mode (a single-operator repo has no lease ledger)",
    )
    parser.add_argument(
        "--grant-url",
        help="Required unless --solo-mode (a single-operator repo has no lease ledger)",
    )
    parser.add_argument(
        "--solo-mode",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Single-operator repo: omit the lease-ledger section entirely instead of "
            "requiring --lease-id/--grant-url. Defaults to the configured profile. "
            "With --sync-mechanical, omitting "
            "both mode flags safely infers the mode from the existing PR body."
        ),
    )
    parser.add_argument(
        "--evidence",
        help="Meaningful current-head tests and integration verification summary",
    )
    parser.add_argument("--scope-reference", help="Approved mission, release, or scope record")
    parser.add_argument(
        "--authorized-path",
        action="append",
        help="Approved exact path or directory/** prefix; repeat for each boundary",
    )
    parser.add_argument("--reviewer", help="Named independent release reviewer")
    parser.add_argument(
        "--reviewer-independence",
        choices=("independent", "not-required"),
        default="independent",
    )
    parser.add_argument(
        "--decision",
        choices=("approve", "block", "needs-work"),
        default="approve",
    )
    parser.add_argument("--evidence-ref", action="append", help="Review evidence reference; repeatable")
    parser.add_argument("--decision-timestamp", help="ISO-8601 review decision timestamp")
    parser.add_argument("--decision-expiry", default="None", help="ISO-8601 expiry or None")
    parser.add_argument("--title")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the complete body without calling GitHub",
    )
    parser.add_argument(
        "--sync-mechanical",
        action="store_true",
        help=(
            "Refresh only the Branch integration / Changed-file manifest sections of the "
            "single open release PR, preserving Outcome / Coordination and scope / Evidence "
            "exactly as last written. No-op (not an error) if no release PR is currently open. "
            "Intended for CI on every push to the configured integration branch, so manifests never go stale between real "
            "review passes without silently discarding curated evidence."
        ),
    )
    args = parser.parse_args()
    return args


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    try:
        config = load_framework_config(repo=repo, path=args.config, required=False)
        repo_slug = args.repo_slug or config.repository.slug
        remote = args.remote or config.repository.remote
        base_branch = args.base or config.repository.release_branch
        head_branch = args.head or config.repository.integration_branch
        solo_mode = config.solo_mode if args.solo_mode is None else args.solo_mode
        ledger_url = config.git_governance.ledger_url or LIVE_LEDGER_URL
        if not solo_mode and not args.sync_mechanical and (
            not args.lease_id or not args.grant_url
        ):
            raise ReleasePreparationError(
                "--lease-id and --grant-url are required in multi-human mode"
            )
        if not args.sync_mechanical:
            required = {
                "--scope-reference": args.scope_reference,
                "--authorized-path": args.authorized_path,
                "--reviewer": args.reviewer,
                "--evidence-ref": args.evidence_ref,
                "--decision-timestamp": args.decision_timestamp,
                "--evidence": args.evidence,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ReleasePreparationError(
                    "structured release authorization requires " + ", ".join(missing)
                )
        if args.sync_mechanical:
            result = sync_release_pr_mechanical_sections(
                repo=repo,
                remote=remote,
                base_branch=base_branch,
                head_branch=head_branch,
                repo_slug=repo_slug,
                solo_mode=args.solo_mode,
                ledger_url=ledger_url,
            )
            print(result if result else "no open release PR to refresh; nothing to do")
            return
        context = collect_release_context(repo, remote, base_branch, head_branch)
        body = render_release_body(
            context,
            lease_id=args.lease_id,
            grant_url=args.grant_url,
            evidence=args.evidence,
            solo_mode=solo_mode,
            ledger_url=ledger_url,
            scope_reference=args.scope_reference,
            authorized_paths=tuple(args.authorized_path),
            reviewer=args.reviewer,
            reviewer_independence=args.reviewer_independence,
            decision=args.decision,
            evidence_references="; ".join(args.evidence_ref),
            decision_timestamp=args.decision_timestamp,
            decision_expiry=args.decision_expiry,
        )
        if args.dry_run:
            print(body, end="")
            return
        result = publish_rendered_release_pr(
            body,
            repo_slug=repo_slug,
            base_branch=base_branch,
            head_branch=head_branch,
            title=args.title or f"Release {head_branch} to {base_branch}",
        )
        print(result)
        print(f"release base: {context.base_ref} @ {context.base_sha}")
        print(f"release head: {context.head_ref} @ {context.head_sha}")
        print(f"manifest: {len(context.files)} files from merge base {context.merge_base}")
    except (FrameworkConfigError, ReleasePreparationError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
