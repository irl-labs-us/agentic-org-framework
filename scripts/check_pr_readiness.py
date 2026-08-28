#!/usr/bin/env python3
"""Fail closed when a local branch is not ready to open or update a PR.

Run this after fetching the target remote. The script is intentionally read-only.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


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
    parser.add_argument(
        "--target-ref",
        default="origin/staging",
        help="Fetched remote-tracking ref the PR will target (default: origin/staging)",
    )
    parser.add_argument(
        "--recorded-base",
        required=True,
        help="Exact full SHA recorded in the mission or handoff before implementation",
    )
    parser.add_argument(
        "--predecessor",
        help="Deprecated; stacked pull requests are prohibited",
    )
    parser.add_argument(
        "--stacked",
        action="store_true",
        help="Deprecated; stacked pull requests are prohibited",
    )
    args = parser.parse_args()

    try:
        root = git("rev-parse", "--show-toplevel")
        branch = git("branch", "--show-current")
        head = git("rev-parse", "HEAD")
        target = git("rev-parse", args.target_ref)
        recorded = git("rev-parse", args.recorded_base)
        merge_base = git("merge-base", "HEAD", args.target_ref)
        status = git("status", "--porcelain")
    except RuntimeError as exc:
        fail(str(exc))

    if not branch:
        fail("detached HEAD; publish from a named feature branch")
    if status:
        fail("worktree is not clean; do not publish or resolve conflicts around unrelated changes")
    if recorded != args.recorded_base:
        fail("--recorded-base must be the exact full 40-character commit SHA")
    if target != recorded:
        fail(
            f"target advanced or recorded base is wrong: recorded {recorded}, "
            f"current {args.target_ref} is {target}; rebase or recreate and rerun evidence"
        )
    if merge_base != target:
        fail(
            f"branch is not based on current {args.target_ref}: merge-base {merge_base}, "
            f"target {target}; rebase or recreate before opening/updating the PR"
        )
    if args.predecessor or args.stacked:
        fail("stacked pull requests are prohibited; wait, then recreate from the current target")

    target_remote = args.target_ref.split("/", 1)[0] if "/" in args.target_ref else ""
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
    print(f"target: {args.target_ref} @ {target}")
    print("publication: independent")
    if not remote_head:
        print("note: no fetched remote branch with this name exists yet")


if __name__ == "__main__":
    main()
