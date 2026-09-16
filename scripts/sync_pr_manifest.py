#!/usr/bin/env python3
"""Refresh a PR's ## Changed-file manifest section only, nothing else.

Root cause this exists to fix: `scripts/check_git_governance.py` requires a
PR body's "## Changed-file manifest" to exactly match the live base..head
diff -- correct as a safety property (it's what actually catches a PR body
that doesn't match what's really being merged), but it means the manifest
goes stale the instant another commit lands on a branch with an open PR,
and the "Git operations covenant" check fails again until someone manually
edits the PR body. That's exactly as true for an ordinary feature PR into
`staging` as it was for the persistent staging->main release PR (see
create_release_pr.py's --sync-mechanical, which solves the release case).

This script is deliberately narrower than that one. A feature PR's
"## Branch integration" section (per .github/pull_request_template.md) is a
mix of mechanical SHA-reference lines *and* human-checked `- [ ]` checklist
items -- check_git_governance.py's validate() never parses either from body
text (base/head SHAs come from the live GitHub event, not the body), so
there is no safety reason to regenerate that section, and a real risk of
silently unchecking boxes a human already verified. This script touches
only "## Changed-file manifest", leaving every other section -- including
Outcome, Coordination and scope, Branch integration's checklist, Git-work
lease, and Evidence -- exactly as a human last wrote them.

Usage (mirrors create_release_pr.py's --sync-mechanical):
    python scripts/sync_pr_manifest.py --repo . --repo-slug <org>/<repo> \
        --base staging --head <feature-branch> --remote origin

No-op (exit 0, not a failure) if no open PR matches --base/--head.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from framework_config import FrameworkConfigError, load_framework_config

class SyncError(RuntimeError):
    pass


def run(*command: str) -> str:
    result = subprocess.run(list(command), check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SyncError(f"{' '.join(command)} failed: {detail}")
    return result.stdout.strip()


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int]:
    """
    Line-index bounds (start, end) of a '## <heading>' section's body --
    start is the line right after the heading, end is the next '## '
    heading (or EOF). Was reimplemented identically in body_section() and
    replace_section() below (a same-file duplication, distinct from -- and
    safe to fix unlike -- the cross-script body_section() duplication in
    check_git_governance.py/check_pr_readiness.py/create_release_pr.py,
    which is a deliberate "stay independently runnable" tradeoff; code-
    review reuse finding, 2026-09-10).
    """
    start = None
    for index, line in enumerate(lines):
        if line.strip().casefold() == f"## {heading}".casefold():
            start = index + 1
            break
    if start is None:
        raise SyncError(f"existing PR body is missing '## {heading}'")
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return start, end


def body_section(body: str, heading: str) -> str:
    """Return a '## <heading>' section's raw text, stripped of surrounding blank lines."""
    lines = body.splitlines()
    start, end = _section_bounds(lines, heading)
    return "\n".join(lines[start:end])


def replace_section(body: str, heading: str, new_text: str) -> str:
    """Replace a '## <heading>' section's content in-place, preserving every other section verbatim."""
    lines = body.splitlines()
    start, end = _section_bounds(lines, heading)
    return "\n".join(lines[:start]) + "\n\n" + new_text.strip("\n") + "\n\n" + "\n".join(lines[end:])


def open_pr_numbers(repo_slug: str, base_branch: str, head_branch: str) -> list[int]:
    raw = run(
        "gh", "pr", "list", "--repo", repo_slug, "--state", "open",
        "--base", base_branch, "--head", head_branch, "--limit", "2", "--json", "number",
    )
    return [int(item["number"]) for item in json.loads(raw)]


def compute_manifest(
    repo: Path, remote: str, base_branch: str, head_branch: str
) -> tuple[list[str], str]:
    """Returns (sorted changed-file paths, head_sha) -- head_sha is returned
    too (not just used internally) so sync() below can reuse it instead of
    re-running an identical `git rev-parse` a second time (code-review
    efficiency finding, 2026-09-10)."""
    run(
        "git", "-C", str(repo), "fetch", "--prune", "--no-tags", remote,
        f"+refs/heads/{base_branch}:refs/remotes/{remote}/{base_branch}",
        f"+refs/heads/{head_branch}:refs/remotes/{remote}/{head_branch}",
    )
    base_sha = run("git", "-C", str(repo), "rev-parse", f"{remote}/{base_branch}")
    head_sha = run("git", "-C", str(repo), "rev-parse", f"{remote}/{head_branch}")
    release_path = base_branch in {"main", "master"} and head_branch == "staging"
    if not release_path:
        # Mirrors check_git_governance.py's own ancestry precondition for the
        # feature path. Without this, a feature branch that has fallen behind
        # base_branch (e.g. another PR merged into staging after this branch
        # forked) would get a `git diff base..head` two-dot compare -- which,
        # unlike `git log`, does NOT scope to their merge-base -- silently
        # producing a manifest polluted with base_branch's own unrelated
        # changes instead of failing clearly. The PR would still fail
        # check_git_governance.py's real ancestry check regardless; better to
        # say so here than publish a misleading manifest first.
        ancestor = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", base_sha, head_sha],
            check=False,
        )
        if ancestor.returncode != 0:
            raise SyncError(
                f"{remote}/{base_branch} ({base_sha}) is not an ancestor of "
                f"{remote}/{head_branch} ({head_sha}) -- the branch has fallen behind "
                f"{base_branch} and needs to rebase or recreate from its current tip before "
                "any manifest refresh would be meaningful (see GIT_OPERATIONS_COVENANT.md)"
            )
    operator = "..." if release_path else ".."
    files = run("git", "-C", str(repo), "diff", "--name-only", f"{base_sha}{operator}{head_sha}").splitlines()
    files = [line for line in files if line]
    if not files:
        raise SyncError(f"no changes between {base_branch} and {head_branch} after the relevant base")
    return sorted(files), head_sha


def live_pr_metadata(repo_slug: str, pr_number: int) -> dict[str, str]:
    raw = run(
        "gh", "pr", "view", str(pr_number), "--repo", repo_slug,
        "--json", "body,headRefOid",
    )
    value = json.loads(raw)
    body = value.get("body") or ""
    head = value.get("headRefOid") or ""
    if not isinstance(body, str) or not isinstance(head, str):
        raise SyncError("GitHub returned malformed PR metadata")
    return {"body": body, "headRefOid": head}


def dispatch_governance_validation(
    *, repo_slug: str, head_branch: str, head_sha: str, workflow_file: str = "git-governance.yml"
) -> str:
    """
    Dispatch trusted validation for the exact head, or identify a bounded
    pending state when GitHub has not materialized the pull-request run yet.

    This exists because editing a PR body via `gh pr edit` with the ambient
    GITHUB_TOKEN does *not* trigger a new `pull_request` "edited" event --
    GitHub explicitly suppresses workflow-triggering for anything done by the
    default token, to prevent infinite loops (see GitHub's docs on
    triggering a workflow from a workflow). Without this, a stale "Git
    operations covenant" failure sits on the PR forever, even after the
    manifest that caused it is fixed -- exactly what happened the first time
    this automation shipped without it.

    A pull_request run uses the workflow from the trusted base branch. Re-run
    that exact run rather than dispatching candidate-branch workflow code.
    """
    raw = run(
        "gh", "run", "list", "--repo", repo_slug, "--branch", head_branch,
        "--workflow", workflow_file, "--json", "databaseId,headSha,conclusion,status", "--limit", "10",
    )
    match = next((r for r in json.loads(raw) if r["headSha"] == head_sha), None)
    if match is None:
        return f"governance validation pending for {head_sha[:8]}: exact-head run not visible yet"
    run_id = match["databaseId"]
    if match["status"] != "completed":
        return f"governance validation pending in run {run_id} for {head_sha[:8]}"
    try:
        run("gh", "run", "rerun", str(run_id), "--repo", repo_slug)
    except SyncError as exc:
        raise SyncError(
            f"manifest updated but exact-head governance run {run_id} could not be dispatched: {exc}"
        ) from exc
    return f"dispatched trusted governance run {run_id} for {head_sha[:8]}; result pending"


def rerun_stale_check(
    *, repo_slug: str, head_branch: str, head_sha: str, workflow_file: str = "git-governance.yml"
) -> str:
    """Compatibility alias for the deterministic dispatch path."""

    return dispatch_governance_validation(
        repo_slug=repo_slug,
        head_branch=head_branch,
        head_sha=head_sha,
        workflow_file=workflow_file,
    )


def sync(*, repo: Path, remote: str, base_branch: str, head_branch: str, repo_slug: str) -> str | None:
    existing = open_pr_numbers(repo_slug, base_branch, head_branch)
    if not existing:
        return None
    if len(existing) > 1:
        raise SyncError(f"multiple open PRs from {head_branch} to {base_branch}; reconcile before continuing")
    pr_number = existing[0]

    for attempt in range(2):
        manifest_lines, head_sha = compute_manifest(repo, remote, base_branch, head_branch)
        observed = live_pr_metadata(repo_slug, pr_number)
        if observed["headRefOid"] != head_sha:
            if attempt == 0:
                continue
            raise SyncError(
                f"PR head changed during manifest computation: fetched {head_sha}, "
                f"live {observed['headRefOid']}"
            )
        old_body = observed["body"]
        manifest_text = "\n".join(f"- `{path}`" for path in manifest_lines)
        new_body = replace_section(old_body, "Changed-file manifest", manifest_text)
        preflight = live_pr_metadata(repo_slug, pr_number)
        if preflight != observed:
            if attempt == 0:
                continue
            raise SyncError("PR body or head changed during manifest synchronization; retry from fresh state")

        if new_body == old_body:
            result = f"PR #{pr_number} manifest already current"
        else:
            descriptor, raw_path = tempfile.mkstemp(prefix="pr-manifest-", suffix=".md")
            body_file = Path(raw_path)
            try:
                with open(descriptor, "w", encoding="utf-8") as handle:
                    handle.write(new_body)
                run("gh", "pr", "edit", str(pr_number), "--repo", repo_slug, "--body-file", str(body_file))
            finally:
                body_file.unlink(missing_ok=True)
            after = live_pr_metadata(repo_slug, pr_number)
            if after["headRefOid"] != head_sha:
                raise SyncError("PR head changed while publishing the manifest; refreshed review is required")
            result = f"refreshed changed-file manifest of PR #{pr_number} ({len(manifest_lines)} files)"

        dispatch = dispatch_governance_validation(
            repo_slug=repo_slug,
            head_branch=head_branch,
            head_sha=head_sha,
        )
        return f"{result}; {dispatch}"
    raise SyncError("manifest synchronization did not reach a stable PR state")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", default=".", help="Local repository path")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--repo-slug", help="owner/repo; overrides project config")
    parser.add_argument("--remote", help="Git remote; overrides project config")
    parser.add_argument("--base", help="PR base branch; overrides project config")
    parser.add_argument("--head", required=True, help="PR head branch, e.g. the feature branch")
    args = parser.parse_args()

    try:
        repo = Path(args.repo).resolve()
        config = load_framework_config(repo=repo, path=args.config, required=False)
        repo_slug = args.repo_slug or config.repository.slug
        remote = args.remote or config.repository.remote
        base = args.base or config.repository.integration_branch
        result = sync(
            repo=repo,
            remote=remote,
            base_branch=base,
            head_branch=args.head,
            repo_slug=repo_slug,
        )
        print(result if result else f"no open PR from {args.head} to {base}; nothing to do")
    except (FrameworkConfigError, SyncError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
