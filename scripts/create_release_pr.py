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
- Closeout owner and disposition: {{CEO}} / {{Strategy & Portfolio Lead}}; close after release merge or PR closure
"""
        steward_line = "{CEO}"
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
- Accountable owner: {{CEO}}, CEO and Merge Steward
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
    args = parser.parse_args()
    if not args.solo_mode and (not args.lease_id or not args.grant_url):
        parser.error("--lease-id and --grant-url are required unless --solo-mode is set")
    return args


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    try:
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
