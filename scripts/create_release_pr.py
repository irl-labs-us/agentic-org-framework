#!/usr/bin/env python3
"""Create or repair the staging-to-main release PR with a complete body.

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


# TODO: point this at your project's live Git-work lease ledger (a pinned
# tracking issue that records lease grants — see docs/GIT_OPERATIONS_COVENANT.md).
LIVE_LEDGER_URL = "https://github.com/<org>/<repo>/issues/<lease-ledger-issue-number>"
LEASE_PATTERN = re.compile(r"^GIT-\d{4}-\d{3}$")
GRANT_URL_PATTERN = re.compile(
    rf"^{re.escape(LIVE_LEDGER_URL)}#issuecomment-\d+$"
)
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


def validate_release_metadata(lease_id: str, grant_url: str) -> None:
    if not LEASE_PATTERN.fullmatch(lease_id):
        raise ReleasePreparationError("lease ID must match GIT-YYYY-NNN")
    if not GRANT_URL_PATTERN.fullmatch(grant_url):
        raise ReleasePreparationError(
            "grant URL must identify a numeric LEASE GRANTED comment in the live ledger at "
            f"{LIVE_LEDGER_URL}#issuecomment-<digits>"
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
    if base_branch not in {"main", "master"} or head_branch != "staging":
        raise ReleasePreparationError(
            "release path must be exactly staging -> main or staging -> master"
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
        raise ReleasePreparationError("staging has no release changes after the merge base")
    return ReleaseContext(
        base_ref=base_ref,
        base_sha=base_sha,
        head_ref=head_ref,
        head_sha=head_sha,
        merge_base=merge_base,
        files=files,
    )


def render_release_body(
    context: ReleaseContext,
    *,
    lease_id: str | None,
    grant_url: str | None,
    evidence: str,
    solo_mode: bool = False,
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
    strategy_lead_placeholder = "{Strategy & Portfolio Lead}"

    if solo_mode:
        branch_integration_lease = "- Git-work lease: N/A — solo-operator mode (see GIT_OPERATIONS_COVENANT.md)"
        lease_section = ""
        steward_line = "the operator"
        risk_evidence = (
            "High-risk production release; current-head CI, staging verification, specialist evidence "
            "for included high-risk changes, and a deliberate operator second pass required"
        )
        deploy_authority = "The PR authorizes no merge by itself; only the operator merges, after a deliberate second pass"
    else:
        assert lease_id is not None and grant_url is not None
        validate_release_metadata(lease_id, grant_url)
        branch_integration_lease = (
            f"- Git-work lease ID: {lease_id}\n- Live-ledger lease grant: {grant_url}"
        )
        lease_section = f"""
## Git-work lease

- Git-work lease ID: {lease_id}
- Live-ledger grant link: {grant_url}
- Lease expiry: See live grant
- Closeout owner and disposition: {ceo_placeholder} / {strategy_lead_placeholder}; close after release merge or PR closure
"""
        steward_line = ceo_placeholder
        risk_evidence = (
            "High-risk production release; current-head CI, staging verification, specialist evidence "
            "for included high-risk changes, and Merge Steward decision required"
        )
        deploy_authority = "The PR authorizes no merge by itself; only the recorded Merge Steward may merge"

    validate_manifest_paths(context.files)
    manifest = "\n".join(f"- `{path}`" for path in context.files)
    base_branch = context.base_ref.rsplit("/", 1)[-1]
    body = f"""## Outcome

Release the exact verified `staging` state to production through `{base_branch}` without adding feature work during release integration.

## Coordination and scope

- Mission or case: Governed staging-to-{base_branch} release
- Accountable owner: {ceo_placeholder}, CEO and Merge Steward
- Writer scope: Persistent `staging` release head only; no release-PR code edits
- Independent reviewer: Required high-risk release evidence recorded below
- Expected overlapping files and owning writer: Release manifest below; feature ownership remains with the originating staging PRs

## Branch integration

{branch_integration_lease}
- Persistent release branch: `{context.head_ref}`
- Target branch / fetched tracking ref: `{context.base_ref}`
- Exact target base SHA: `{context.base_sha}`
- Exact release head SHA: `{context.head_sha}`
- Common merge base: `{context.merge_base}`
- Publication shape: Authorized persistent-branch release
- Merge Steward on duty: {steward_line}
- Risk class / review evidence: {risk_evidence}
{lease_section}
## Changed-file manifest

{manifest}

## Evidence

- Tests and checks: {evidence}
- Limitations or open gates: Release merge remains prohibited until all current-head checks, staging verification{"" if solo_mode else ", live-ledger match"}, and the final {"operator" if solo_mode else "Merge Steward"} freshness decision pass
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


def sync_release_pr_mechanical_sections(
    *,
    repo: Path,
    remote: str,
    base_branch: str,
    head_branch: str,
    repo_slug: str,
    solo_mode: bool,
) -> str | None:
    """
    Refresh only the mechanically-derived sections (Branch integration,
    Changed-file manifest -- and, in multi-operator mode, Git-work lease)
    of the single open staging->main release PR, preserving Outcome,
    Coordination and scope, and Evidence exactly as a human last wrote
    them. Intended for CI to run on every push to staging, so the
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
            "multiple open staging release PRs exist; close or reconcile them before continuing"
        )
    pr_number = existing[0]

    old_body = run(
        "gh", "pr", "view", str(pr_number), "--repo", repo_slug, "--json", "body", "-q", ".body"
    )

    context = collect_release_context(repo, remote, base_branch, head_branch)
    # Placeholder evidence: this fresh render exists only to extract the
    # mechanically-derived sections from; the real Evidence text below
    # comes from the existing PR body, not this placeholder.
    fresh_body = render_release_body(
        context, lease_id=None, grant_url=None, evidence="__PLACEHOLDER__", solo_mode=solo_mode
    )

    outcome = body_section(old_body, "Outcome")
    coordination = body_section(old_body, "Coordination and scope")
    evidence = body_section(old_body, "Evidence")
    branch_integration = body_section(fresh_body, "Branch integration")
    manifest = body_section(fresh_body, "Changed-file manifest")

    lease_block = ""
    if not solo_mode:
        lease_block = "\n## Git-work lease\n\n" + body_section(old_body, "Git-work lease") + "\n"

    new_body = f"""## Outcome

{outcome}

## Coordination and scope

{coordination}

## Branch integration

{branch_integration}
{lease_block}
## Changed-file manifest

{manifest}

## Evidence

{evidence}
"""
    body_size = len(new_body.encode("utf-8"))
    if body_size > MAX_PR_BODY_BYTES:
        raise ReleasePreparationError(
            f"refreshed release PR body is {body_size} bytes; limit is {MAX_PR_BODY_BYTES}; "
            "narrow or separately archive the accumulated Evidence/Outcome content before publication"
        )
    body_file = materialize_release_body(new_body)
    try:
        run("gh", "pr", "edit", str(pr_number), "--repo", repo_slug, "--body-file", str(body_file))
    finally:
        body_file.unlink(missing_ok=True)
    result = f"refreshed mechanical sections of PR #{pr_number}"
    rerun_note = rerun_stale_check(repo_slug=repo_slug, head_branch=head_branch, head_sha=context.head_sha)
    if rerun_note:
        result += f"; {rerun_note}"
    return result


def rerun_stale_check(
    *, repo_slug: str, head_branch: str, head_sha: str, workflow_file: str = "git-governance.yml"
) -> str | None:
    """
    Find the most recent run of `workflow_file` for `head_branch` whose head
    SHA matches `head_sha`, and re-run it if it previously failed.

    This exists because editing a PR body via `gh pr edit` with the ambient
    GITHUB_TOKEN does *not* trigger a new `pull_request` "edited" event --
    GitHub explicitly suppresses workflow-triggering for anything done by the
    default token, to prevent infinite loops (see GitHub's docs on
    triggering a workflow from a workflow). Without this, a stale "Git
    operations covenant" failure sits on the PR forever, even after the
    manifest that caused it is fixed.

    Returns a message describing what happened, or None if there's no
    matching run or it didn't previously fail (nothing to do).
    """
    raw = run(
        "gh", "run", "list", "--repo", repo_slug, "--branch", head_branch,
        "--workflow", workflow_file, "--json", "databaseId,headSha,conclusion,status", "--limit", "10",
    )
    match = next((r for r in json.loads(raw) if r["headSha"] == head_sha), None)
    if match is None or match["status"] != "completed" or match["conclusion"] != "failure":
        return None
    run_id = match["databaseId"]
    try:
        run("gh", "run", "rerun", str(run_id), "--repo", repo_slug)
    except ReleasePreparationError as exc:
        # A rerun failing (e.g. the run aged out of GitHub's ~30-day rerun
        # window) shouldn't turn an otherwise-successful manifest sync into
        # a reported failure -- surface it as a note, not an exception.
        return f"manifest refreshed, but could not re-trigger stale {workflow_file} run {run_id}: {exc}"
    return f"re-triggered stale {workflow_file} run {run_id} for {head_sha[:8]} (GITHUB_TOKEN edits don't trigger it themselves)"


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
            "multiple open staging release PRs exist; close or reconcile them before continuing"
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
    parser.add_argument("--repo-slug", required=True, help="owner/repo, e.g. <org>/<repo>")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--base", default="main", choices=("main", "master"))
    parser.add_argument("--head", default="staging", choices=("staging",))
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
        action="store_true",
        help=(
            "Single-operator repo: omit the lease-ledger section entirely instead of "
            "requiring --lease-id/--grant-url. Must match SOLO_MODE in "
            "scripts/check_git_governance.py or the governance check will still demand "
            "a lease section this body doesn't have."
        ),
    )
    parser.add_argument(
        "--evidence",
        default="Current-head CI and staging release verification pending",
    )
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
            "Intended for CI on every push to staging, so manifests never go stale between real "
            "review passes without silently discarding curated evidence."
        ),
    )
    args = parser.parse_args()
    if not args.solo_mode and (not args.lease_id or not args.grant_url):
        parser.error("--lease-id and --grant-url are required unless --solo-mode is set")
    if args.sync_mechanical and not args.solo_mode:
        parser.error(
            "--sync-mechanical currently only supports --solo-mode; "
            "sync_release_pr_mechanical_sections() doesn't thread --lease-id/--grant-url "
            "through to render_release_body(), so multi-operator mode would fail with an "
            "unhandled assertion instead of a clean error. Wire lease/grant support through "
            "before using --sync-mechanical outside solo-mode."
        )
    return args


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    try:
        if args.sync_mechanical:
            result = sync_release_pr_mechanical_sections(
                repo=repo,
                remote=args.remote,
                base_branch=args.base,
                head_branch=args.head,
                repo_slug=args.repo_slug,
                solo_mode=args.solo_mode,
            )
            print(result if result else "no open release PR to refresh; nothing to do")
            return
        context = collect_release_context(repo, args.remote, args.base, args.head)
        body = render_release_body(
            context,
            lease_id=args.lease_id,
            grant_url=args.grant_url,
            evidence=args.evidence,
            solo_mode=args.solo_mode,
        )
        if args.dry_run:
            print(body, end="")
            return
        result = publish_rendered_release_pr(
            body,
            repo_slug=args.repo_slug,
            base_branch=args.base,
            head_branch=args.head,
            title=args.title or f"Release staging to {args.base}",
        )
        print(result)
        print(f"release base: {context.base_ref} @ {context.base_sha}")
        print(f"release head: {context.head_ref} @ {context.head_sha}")
        print(f"manifest: {len(context.files)} files from merge base {context.merge_base}")
    except (ReleasePreparationError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
