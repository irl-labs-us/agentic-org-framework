#!/usr/bin/env python3
"""Create a single-use feature worktree from freshly fetched remote staging."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

if __package__:
    from scripts.check_git_governance import is_prohibited_integration_ref
else:
    from check_git_governance import is_prohibited_integration_ref


FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class BranchCreationError(RuntimeError):
    """Raised before branch creation when a governance invariant fails."""


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise BranchCreationError(f"git {' '.join(args)} failed: {detail}")
    return result


def create_feature_worktree(
    *,
    repo: Path,
    branch: str,
    worktree: Path,
    recorded_base: str,
    remote: str = "origin",
) -> str:
    repo = Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip())
    requested_worktree = worktree.expanduser()
    if requested_worktree.exists() or requested_worktree.is_symlink():
        raise BranchCreationError(f"worktree path already exists: {requested_worktree}")
    worktree = requested_worktree.resolve()
    target = "staging"

    if not FULL_SHA.fullmatch(recorded_base):
        raise BranchCreationError("recorded base must be an exact lowercase 40-character SHA")
    if branch in {"main", "master", "staging"}:
        raise BranchCreationError("feature branch may not use a protected branch name")
    if is_prohibited_integration_ref(branch):
        raise BranchCreationError("archive and frozen branch identities are prohibited")
    git(repo, "check-ref-format", "--branch", branch)
    git(repo, "remote", "get-url", remote)
    git(repo, "check-ref-format", "--branch", target)

    if worktree.exists() or worktree.is_symlink():
        raise BranchCreationError(f"worktree path already exists: {worktree}")
    local_branch = git(
        repo,
        "for-each-ref",
        "--format=%(refname)",
        f"refs/heads/{branch}",
    )
    if local_branch.stdout.strip():
        raise BranchCreationError(f"local branch already exists: {branch}")

    remote_branch = git(repo, "ls-remote", "--heads", remote, f"refs/heads/{branch}")
    if remote_branch.stdout.strip():
        raise BranchCreationError(f"remote branch already exists: {remote}/{branch}")

    target_ref = f"refs/remotes/{remote}/{target}"
    forced_refspec = f"+refs/heads/{target}:{target_ref}"
    git(repo, "fetch", "--prune", remote, forced_refspec)
    fetched_base = git(repo, "rev-parse", target_ref).stdout.strip()
    if fetched_base != recorded_base:
        raise BranchCreationError(
            f"remote {remote}/{target} advanced: lease records {recorded_base}, "
            f"freshly fetched tip is {fetched_base}; obtain a superseding lease grant"
        )

    creation = git(
        repo,
        "worktree",
        "add",
        "--detach",
        str(worktree),
        target_ref,
        check=False,
    )
    if creation.returncode:
        detail = creation.stderr.strip() or creation.stdout.strip()
        raise BranchCreationError(
            f"git worktree add failed: {detail}; no feature branch was created; "
            "inspect any partial worktree state before retrying"
        )

    branch_creation = git(worktree, "switch", "-c", branch, check=False)
    if branch_creation.returncode:
        detail = branch_creation.stderr.strip() or branch_creation.stdout.strip()
        raise BranchCreationError(
            f"feature branch creation failed after detached worktree creation: {detail}; "
            f"preserve and inspect detached worktree {worktree} before retrying"
        )
    created_head = git(worktree, "rev-parse", "HEAD").stdout.strip()
    created_branch = git(worktree, "branch", "--show-current").stdout.strip()
    if created_head != fetched_base or created_branch != branch:
        raise BranchCreationError(
            "post-creation identity verification failed; preserve the worktree and escalate"
        )
    return fetched_base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", required=True, help="Unique single-use feature branch")
    parser.add_argument("--worktree", required=True, type=Path, help="New isolated path")
    parser.add_argument("--recorded-base", required=True, help="Full SHA from the live lease grant")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    args = parser.parse_args()

    try:
        base = create_feature_worktree(
            repo=args.repo,
            branch=args.branch,
            worktree=args.worktree,
            recorded_base=args.recorded_base,
            remote=args.remote,
        )
    except BranchCreationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print("PASS: feature branch created from freshly fetched remote staging")
    print(f"branch: {args.branch}")
    print(f"worktree: {args.worktree.expanduser().resolve()}")
    print(f"base: {args.remote}/staging @ {base}")


if __name__ == "__main__":
    main()
