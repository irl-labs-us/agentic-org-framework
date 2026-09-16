#!/usr/bin/env python3
"""Check branch identity, ancestry, and worktree state before PR publication.

This local, read-only preflight is independent of the optional multi-human
lease and PR-body ceremony.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from framework_config import FrameworkConfigError, load_framework_config


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument(
        "--target-ref",
        help="Fetched remote-tracking ref; defaults to the configured integration branch",
    )
    parser.add_argument(
        "--recorded-base",
        required=True,
        help="Exact full SHA recorded before implementation",
    )
    parser.add_argument("--predecessor", help="Deprecated; stacked pull requests are prohibited")
    parser.add_argument("--stacked", action="store_true", help="Deprecated; stacked pull requests are prohibited")
    args = parser.parse_args()

    try:
        root = git("rev-parse", "--show-toplevel")
        config = load_framework_config(repo=root, path=args.config, required=False)
        target_ref = args.target_ref or (
            f"{config.repository.remote}/{config.repository.integration_branch}"
        )
        branch = git("branch", "--show-current")
        head = git("rev-parse", "HEAD")
        target = git("rev-parse", target_ref)
        recorded = git("rev-parse", args.recorded_base)
        merge_base = git("merge-base", "HEAD", target_ref)
        status = git("status", "--porcelain")
    except (FrameworkConfigError, RuntimeError) as exc:
        fail(str(exc))

    if not branch:
        fail("detached HEAD; publish from a named feature branch")
    if status:
        fail("worktree is not clean; do not publish unrelated changes")
    if recorded != args.recorded_base:
        fail("--recorded-base must be the exact full 40-character commit SHA")
    if target != recorded:
        fail(
            f"target advanced or recorded base is wrong: recorded {recorded}, "
            f"current {target_ref} is {target}; rebase or recreate and rerun evidence"
        )
    if merge_base != target:
        fail(
            f"branch is not based on current {target_ref}: merge-base {merge_base}, "
            f"target {target}; rebase or recreate before opening/updating the PR"
        )
    if args.predecessor or args.stacked:
        fail("stacked pull requests are prohibited; wait, then recreate from the current target")

    target_remote = target_ref.split("/", 1)[0] if "/" in target_ref else ""
    remote_ref = f"refs/remotes/{target_remote}/{branch}" if target_remote else ""
    try:
        remote_head = git("rev-parse", remote_ref) if remote_ref else ""
    except RuntimeError:
        remote_head = ""
    if remote_head and remote_head != head:
        fail(
            f"local and remote branch names diverge: local {head}, remote {remote_head}; "
            "stop and reconcile identity without overwriting either history"
        )

    print("PASS: local PR ancestry and identity checks passed")
    print(f"repository: {root}")
    print(f"branch: {branch}")
    print(f"head: {head}")
    print(f"target: {target_ref} @ {target}")
    if not remote_head:
        print("note: no fetched remote branch with this name exists yet")


if __name__ == "__main__":
    main()
